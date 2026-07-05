-- Dashboard: Rep Performance (Average sales cycle length per rep)
-- KPI_Catalog.md: Sales Cycle Length
-- Business question: Which reps close deals fastest, and is anyone's cycle length a red flag?
-- Source: vw_sales_cycle_length (migration 0008)

SELECT * FROM vw_sales_cycle_length ORDER BY avg_sales_cycle_days ASC;
