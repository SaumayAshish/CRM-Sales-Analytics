"""
Application configuration.

Traces to: Architecture.md SS7 (config-driven, no hardcoded secrets);
NFR-03 (JWT signing key stored as a secret, never committed).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://crm_user:crm_password@localhost:5432/crm_sales_analytics"
    jwt_secret_key: str = "dev-only-insecure-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    environment: str = "development"


settings = Settings()
