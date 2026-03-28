from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the path to the .env file in the parent directory (backend root)
ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Required fields (actively used)
    SUPABASE_URL: str = Field(default="")
    SUPABASE_SERVICE_KEY: str = Field(default="")
    SUPABASE_PUBLISHABLE_KEY: str = Field(default="")
    GROQ_API_KEY: str = Field(default="")
    UPSTASH_REDIS_URL: str = Field(default="")
    UPSTASH_REDIS_TOKEN: str = Field(default="")
    ACCESS_TOKEN_TIME: int = Field(default=0)
    REFRESH_ACCESS_TOKEN_TIME: int = Field(default=0)
    JWT_SECRET_KEY: str = Field(default="")
    JWT_REFRESH_SECRET_KEY: str = Field(default="")
    FRONTEND_URL: str = Field(default="")
    PROJECT_EMAIL: str = Field(default="")
    EMAIL_APP_PASSWORD: str = Field(default="")
    ALGORITHM: str = Field(default="")
    RESEND_API_KEY: str = Field(default="")
    BREVO_API: str = Field(default="")
    BRAVE_SEARCH_API_KEY: str | None = None
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SENTRY_DSN: str | None = None  # Optional Sentry error monitoring

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        extra="ignore",  # Ignore any extra environment variables
    )


settings = Settings()
