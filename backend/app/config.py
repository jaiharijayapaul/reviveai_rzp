"""
Central application configuration.
Loaded from environment variables (.env in local dev). Never hardcode secrets.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://reviveai:reviveai@localhost:5432/reviveai"

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    ANTHROPIC_API_KEY: str = ""
    AGENT_MODEL: str = "claude-sonnet-4-6"

    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    # Guardrail defaults (paise, i.e. amount * 100), overridable per-merchant in DB
    MAX_AUTOMATED_AMOUNT: int = 5000000  # ₹50,000.00 in paise
    MAX_RECOVERY_ATTEMPTS: int = 2
    HIGH_RISK_REQUIRES_APPROVAL: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
