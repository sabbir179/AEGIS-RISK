from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys (Made required for the Agentic Loop)
    newsapi_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None  # <--- FIXED: Added this
    groq_api_key: str | None = None       # <--- FIXED: Added this
    
    # Database
    database_url: str = "sqlite:///./aegis_risk.db"
    
    # Settings
    refresh_minutes: int = 60
    default_query: str = "Israel Iran Red Sea Suez oil shipping fuel supply chain"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()