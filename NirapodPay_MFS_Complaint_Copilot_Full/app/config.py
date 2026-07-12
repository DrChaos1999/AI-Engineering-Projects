from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MFS Complaint Copilot"
    database_url: str = "sqlite:///./mfs_copilot.db"
    mock_llm: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    max_kb_results: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
