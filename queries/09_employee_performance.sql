with filtered as (
    select fct_order_details.order_id, fct_order_details.order_date,
           fct_order_details.extended_price, fct_order_details.quantity,
           fct_order_details.shipping_delay_days,
           dim_categories.category_name, dim_products.product_name,
           dim_customers.country, dim_employees.employee_full_name,
           dim_suppliers.company_name as supplier_name
    from northwind_warehouse.fct_order_details
    join northwind_warehouse.dim_customers using (customer_pk)
    join northwind_warehouse.dim_employees using (employee_pk)
    join northwind_warehouse.dim_products using (product_pk)
    join northwind_warehouse.dim_categories on dim_products.category_id = dim_categories.category_id
    join northwind_warehouse.dim_suppliers on dim_products.supplier_id = dim_suppliers.supplier_id
    where 1 = 1
      [[and {{date_range}}]]
      [[and {{category}}]]
      [[and {{country}}]]
      [[and {{employee}}]]
      [[and {{product}}]]
)
select employee_full_name as employee, sum(extended_price) as revenue from filtered group by 1 order by 2 desc;
