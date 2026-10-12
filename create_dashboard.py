"""Create TP7's Metabase dashboard using the real TP6 Supabase warehouse."""
import json
import os
from pathlib import Path
import time
import uuid
from connection import configure_connection
from metabase_client import MetabaseClient

ROOT = Path(__file__).resolve().parent
FILTERS = {
    "date_range": ("Order date range", "date/range", "fct_order_details", "order_date"),
    "category": ("Product category", "string/=", "dim_categories", "category_name"),
    "country": ("Customer country", "string/=", "dim_customers", "country"),
    "employee": ("Employee", "string/=", "dim_employees", "employee_full_name"),
    "product": ("Product name", "string/=", "dim_products", "product_name"),
}
CARDS = [
    ("01_total_revenue", "Total Revenue", "scalar", None, "total_revenue"),
    ("02_total_orders", "Total Orders", "scalar", None, "total_orders"),
    ("03_average_order_value", "Average Order Value", "scalar", None, "average_order_value"),
    ("04_total_quantity", "Total Quantity Sold", "scalar", None, "total_quantity"),
    ("05_sales_trend", "Sales Trend by Month", "line", "month", "revenue"),
    ("06_sales_by_category", "Sales by Product Category", "bar", "category", "revenue"),
    ("07_top_products", "Top 10 Products by Revenue", "bar", "product", "revenue"),
    ("08_sales_by_country", "Sales by Customer Country", "bar", "country", "revenue"),
    ("09_employee_performance", "Employee Performance", "bar", "employee", "revenue"),
    ("10_shipping_performance", "Average Shipping Days by Employee", "bar", "employee", "average_shipping_days"),
]

def create_dashboard():
    configure_connection()
    client = MetabaseClient()
    state_path = ROOT / ".secrets" / "dashboard_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    state_path.parent.mkdir(exist_ok=True)
    if not state.get("database_id"):
        database = client.request("POST", "/api/database", {
            "name": "Northwind Supabase", "engine": "postgres", "is_full_sync": False,
            "details": {"host": os.environ["PGHOST"], "port": int(os.environ["PGPORT"]),
                "dbname": os.environ["PGDATABASE"], "user": os.environ["PGUSER"],
                "password": os.environ["PGPASSWORD"], "ssl": True,
                "ssl-mode": "require", "schema-filters-type": "inclusion",
                "schema-filters-patterns": "northwind_warehouse"}})
        state["database_id"] = database["id"]
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    database_id = state["database_id"]
    client.request("POST", f"/api/database/{database_id}/sync_schema", {})
    for attempt in range(40):
        metadata = client.request("GET", f"/api/database/{database_id}/metadata")
        field_ids = {(table["name"], field["name"]): field["id"]
                     for table in metadata.get("tables", []) if table.get("schema") == "northwind_warehouse"
                     for field in table.get("fields", [])}
        if all((table, field) in field_ids for _, _, table, field in FILTERS.values()):
            break
        time.sleep(2)
    else:
        raise RuntimeError("TP6 warehouse fields have not appeared in Metabase; run TP6 first and retry.")
    parameters = [{"id": name, "name": label, "slug": name, "type": kind,
                   "isMultiSelect": kind != "date/range", "required": False,
                   **({"values_query_type": "list"} if kind != "date/range" else {})}
                  for name, (label, kind, _, _) in FILTERS.items()]
    for name, (_, kind, table, field) in FILTERS.items():
        if kind != "date/range":
            identifier = field_ids[(table, field)]
            client.request("PUT", f"/api/field/{identifier}", {"has_field_values": "list", "semantic_type": "type/Category"})
            client.request("POST", f"/api/field/{identifier}/rescan_values", {})
    if not state.get("dashboard_id"):
        dashboard = client.request("POST", "/api/dashboard", {
            "name": "Northwind Order Details — TP7", "parameters": parameters,
            "description": "Northwind sales, customers, products, employees and shipping. Revenue uses the source's monetary unit."})
        state["dashboard_id"] = dashboard["id"]
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    dashboard_id = state["dashboard_id"]
    client.request("PUT", f"/api/dashboard/{dashboard_id}", {"parameters": parameters, "width": "full"})
    cards = []
    state.setdefault("card_ids", {})
    for index, (filename, label, display, dimension, metric) in enumerate(CARDS):
        tags = {name: {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, filename + name)), "name": name,
                       "display-name": title, "type": "dimension",
                       "dimension": ["field", field_ids[(table, field)], None],
                       "widget-type": kind, "required": False, "default": None}
                for name, (title, kind, table, field) in FILTERS.items()}
        query = {"database": database_id, "type": "native", "native": {
            "query": (ROOT / "queries" / f"{filename}.sql").read_text(encoding="utf-8"), "template-tags": tags}}
        settings = {"scalar.decimals": 2 if metric in {"total_revenue", "average_order_value"} else 0} if display == "scalar" else {
            "graph.dimensions": [dimension], "graph.metrics": [metric], "graph.show_values": False}
        card_data = {"name": label, "display": display, "dataset_query": query,
                     "visualization_settings": settings, "parameters": [
                         {"id": name, "type": kind, "name": title, "slug": name,
                          "target": ["dimension", ["template-tag", name]]}
                         for name, (title, kind, _, _) in FILTERS.items()]}
        existing = state["card_ids"].get(filename)
        card = client.request("PUT" if existing else "POST", f"/api/card/{existing}" if existing else "/api/card", card_data)
        card_id = card["id"]
        state["card_ids"][filename] = card_id
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        if index < 4:
            row, col, width, height = 0, index * 6, 6, 4
        else:
            row, col, width, height = 4 + ((index - 4) // 2) * 7, ((index - 4) % 2) * 12, 12, 7
        cards.append({"id": -(index + 1), "card_id": card_id, "row": row, "col": col,
                      "size_x": width, "size_y": height, "series": [],
                      "parameter_mappings": [{"parameter_id": name, "card_id": card_id,
                           "target": ["dimension", ["template-tag", name]]} for name in FILTERS],
                      "visualization_settings": {}})
    current = client.request("GET", f"/api/dashboard/{dashboard_id}")
    existing_slots = {slot["card_id"]: slot["id"] for slot in current.get("dashcards", [])}
    for card in cards:
        card["id"] = existing_slots.get(card["card_id"], card["id"])
    client.request("PUT", f"/api/dashboard/{dashboard_id}/cards", {"cards": cards})
    print("Created four KPIs, six charts and five connected filters.")
    print("Dashboard:", f"{client.url}/dashboard/{dashboard_id}")
    return client, state

if __name__ == "__main__":
    create_dashboard()
