from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the path to the .env file in the parent directory (backend root)
ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Required fields (actively used)
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_PUBLISHABLE_KEY: str
    GROQ_API_KEY: str
    UPSTASH_REDIS_URL: str
    UPSTASH_REDIS_TOKEN: str
    ACCESS_TOKEN_TIME: int
    REFRESH_ACCESS_TOKEN_TIME: int
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    FRONTEND_URL: str
    PROJECT_EMAIL: str
    EMAIL_APP_PASSWORD: str
    ALGORITHM: str
    RESEND_API_KEY: str
    BREVO_API: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        extra="ignore",  # Ignore any extra environment variables
    )


settings = Settings()
