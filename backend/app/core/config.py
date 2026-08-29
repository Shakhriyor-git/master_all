from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    env: str = "local"
    debug: bool = True
    secret_key: str = "change-me"
    public_url: str = "http://localhost:8000"

    # Database
    postgres_user: str = "brigada"
    postgres_password: str = "brigada"
    postgres_db: str = "brigada"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Telegram
    bot_token: str = ""
    webapp_url: str = "http://localhost:5173"
    bot_use_webhook: bool = False
    webhook_secret: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173"

    # AI (keyingi bosqichda)
    gemini_api_key: str = ""
    groq_api_key: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
