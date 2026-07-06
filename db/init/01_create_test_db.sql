-- Runs once, only on a brand-new Postgres data volume (postgres image
-- convention: everything in /docker-entrypoint-initdb.d/ runs on first
-- init, never again). Creates the separate test database the backend
-- test suite expects (tests/conftest.py), alongside the main app
-- database created automatically from POSTGRES_DB.
CREATE DATABASE crm_sales_analytics_test;
