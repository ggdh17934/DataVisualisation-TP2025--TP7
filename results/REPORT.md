# TP7 — Northwind Order Details Dashboard

The actual Metabase dashboard is available locally at http://localhost:8000/dashboard/2 while
Metabase is running. Its analytical source is the TP6 Supabase
`northwind_warehouse` schema, not a copied local analytical dataset.
Its separate local PostgreSQL application database stores Metabase settings.
The repository includes the teacher's Docker Compose method. On this computer,
Docker was unavailable, so official Metabase v0.64.1 was launched with portable
Java 25 and the same PostgreSQL application-storage approach.

## Four KPIs
Total revenue: **448,386,633.1695**.
Unique orders: **16,282**.
Average order value = revenue / unique orders: **27,538.79**.
Total quantity: **15,538,602**.
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
