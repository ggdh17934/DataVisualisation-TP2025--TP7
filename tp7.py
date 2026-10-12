"""Create and verify the required Northwind Metabase dashboard."""
# %% 1. Imports and private connections
import json
from pathlib import Path
import re

import pandas as pd
import psycopg2
from connection import configure_connection
from create_dashboard import CARDS, FILTERS, create_dashboard

ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
url = configure_connection()

# %% 2. Create the actual Metabase dashboard with every required chart and filter
client, state = create_dashboard()
dashboard_url = f"{client.url}/dashboard/{state['dashboard_id']}"

# %% 3. Execute and save the ten real Metabase query results
results = {}
for filename, label, _, _, _ in CARDS:
    response = client.request("POST", f"/api/card/{state['card_ids'][filename]}/query", {"parameters": []})
    if response.get("status") != "completed":
        raise RuntimeError(f"Metabase query failed: {label}: {response.get('error')}")
    columns = [column["name"] for column in response["data"]["cols"]]
    frame = pd.DataFrame(response["data"]["rows"], columns=columns)
    frame.to_csv(OUT / f"{filename}.csv", index=False)
    results[filename] = response["data"]["rows"]
    print(label, "—", len(frame), "result rows")
    print(frame.head(5).to_string(index=False))

# %% 4. Verify all five filters and combined selection against PostgreSQL
# Use a real order as the test selection, so every filter selects actual data.
base_sql = (ROOT / "queries" / "01_total_revenue.sql").read_text(encoding="utf-8")
join_sql = base_sql.split("where 1 = 1")[0].replace("with filtered as (", "")
with psycopg2.connect(url) as connection:
    with connection.cursor() as cursor:
        cursor.execute(join_sql + " order by fct_order_details.order_id limit 1")
        sample = dict(zip([column.name for column in cursor.description], cursor.fetchone()))
        cursor.execute("select category_name from northwind_warehouse.dim_categories order by category_name")
        categories = [row[0] for row in cursor.fetchall()]
year = sample["order_date"].year
selections = {"date_range": f"{year}-01-01~{year}-12-31",
              "category": [sample["category_name"], next(c for c in categories if c != sample["category_name"])],
              "country": [sample["country"]], "employee": [sample["employee_full_name"]],
              "product": [sample["product_name"]]}
filter_checks = []
for name, selection in [(name, {name: value}) for name, value in selections.items()] + [("combined", selections)]:
    api_parameters = [{"id": key, "type": FILTERS[key][1], "target": ["dimension", ["template-tag", key]],
                       "value": value} for key, value in selection.items()]
    api_result = client.request("POST", f"/api/card/{state['card_ids']['01_total_revenue']}/query",
                                {"parameters": api_parameters})
    if api_result.get("status") != "completed":
        raise RuntimeError(f"Filter failed: {name}: {api_result.get('error')}")
    sql_values = []
    def replace_filter(match):
        key = match.group(1)
        if key not in selection:
            return ""
        _, _, table, field = FILTERS[key]
        if key == "date_range":
            start, end = selection[key].split("~")
            sql_values.extend([start, end])
            return f"and {table}.{field} between %s::date and %s::date"
        sql_values.append(selection[key])
        return f"and {table}.{field} = any(%s)"
    plain_sql = re.sub(r"\[\[and \{\{(\w+)\}\}\]\]", replace_filter, base_sql)
    with psycopg2.connect(url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(plain_sql, sql_values)
            expected = float(cursor.fetchone()[0])
    actual = float(api_result["data"]["rows"][0][0])
    assert abs(actual - expected) < 0.01, f"Filter mismatch: {name}"
    filter_checks.append({"filter": name, "selection": selection, "revenue": actual, "verified": True})
    print("Verified filter:", name, "Revenue:", actual)

# %% 5. Verify the layout and write the required dashboard explanation
dashboard = client.request("GET", f"/api/dashboard/{state['dashboard_id']}")
assert len(dashboard["dashcards"]) == 10 and len(dashboard["parameters"]) == 5
assert all(len(card["parameter_mappings"]) == 5 for card in dashboard["dashcards"])
verification = {"dashboard_url": dashboard_url, "cards": 10, "filters": 5,
               "filter_checks": filter_checks,
               "total_revenue": float(results["01_total_revenue"][0][0]),
               "total_orders": int(results["02_total_orders"][0][0]),
               "average_order_value": float(results["03_average_order_value"][0][0]),
               "total_quantity": int(results["04_total_quantity"][0][0])}
(OUT / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
report = f"""# TP7 — Northwind Order Details Dashboard

The actual Metabase dashboard is available locally at {dashboard_url} while
Metabase is running. Its analytical source is the TP6 Supabase
`northwind_warehouse` schema, not a copied local analytical dataset.
Its separate local PostgreSQL application database stores Metabase settings.
The repository includes the teacher's Docker Compose method. On this computer,
Docker was unavailable, so official Metabase v0.64.1 was launched with portable
Java 25 and the same PostgreSQL application-storage approach.

## Four KPIs
Total revenue: **{verification['total_revenue']:,.4f}**.
Unique orders: **{verification['total_orders']:,}**.
Average order value = revenue / unique orders: **{verification['average_order_value']:,.2f}**.
Total quantity: **{verification['total_quantity']:,}**.
The source does not establish the monetary currency; no currency symbol is invented.

## Six required charts
Monthly revenue trend; revenue by category; top 10 products by revenue;
revenue by customer country; revenue by employee; mean shipping days by employee.
Shipping averages use distinct orders, preventing orders with many detail lines
from receiving extra weight. Unshipped orders have NULL delay and are excluded
from the shipping mean, rather than treated as immediate shipments.

## Five interactive filters
Order date range, category, customer country, employee and product name.
Field filters support the date interval and multi-selection; every filter is
connected to all ten cards. Each filter and a combined selection were executed
through Metabase and reconciled with an independently parameterized PostgreSQL
query within one cent. The category check includes two simultaneous values.
All ten cards were queried successfully and their real results saved as CSVs.

Four KPIs occupy the top row; six charts follow in three pairs on one page.
Filters narrow the same order-detail set, so the average-order denominator counts
orders represented in the selection. Top products always means top 10 within
the chosen filters. The SQL joins the fact with all five specified dimensions.
No unrelated dashboard, extra visualization or public sharing link is created.

Assignment: https://github.com/ahmed3991/DataVisualisation-TP2025/blob/main/TP7/TP7.md
"""
(OUT / "REPORT.md").write_text(report, encoding="utf-8")
print("Dashboard and filter checks passed:", dashboard_url)
