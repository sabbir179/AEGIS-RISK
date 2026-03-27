from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    newsapi_key: str | None = None
    database_url: str = "sqlite:///./aegis_risk.db"
    refresh_minutes: int = 60
    default_query: str = "Israel Iran oil shipping Red Sea Suez UK supply chain"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
