-- Dashboard: Lead Funnel (MQL/SQL-style conversion by score band)
-- KPI_Catalog.md: Lead-to-Conversion Rate, Conversion Rate by Score Band
-- Business question: Does our scoring model actually predict conversion? (Hot should convert
-- meaningfully more than Cold -- if not, the scoring weights need revisiting, per RISK-02.)
-- Source: vw_lead_funnel (migration 0004)

SELECT * FROM vw_lead_funnel ORDER BY conversion_rate DESC;
