from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "YouTube Rising Videos Finder"
    api_root_path: str = ""

    yt_api_key: str = Field(alias="YT_API_KEY")

    database_url: str = Field(alias="DATABASE_URL")

    redis_url: str = Field(alias="REDIS_URL")

    s3_endpoint: str | None = Field(default=None, alias="S3_ENDPOINT")
    s3_key: str | None = Field(default=None, alias="S3_KEY")
    s3_secret: str | None = Field(default=None, alias="S3_SECRET")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")

    tg_bot_token: str | None = Field(default=None, alias="TG_BOT_TOKEN")
    tg_chat_id: str | None = Field(default=None, alias="TG_CHAT_ID")


@lru_cache
def get_settings() -> Settings:
    return Settings()
