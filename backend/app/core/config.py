from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SnapLecture API"
    app_version: str = "1.0.0"
    environment: str = "development"

    api_prefix: str = "/api"

    frontend_url: str = "http://localhost:3000"

    # Local-upload limits. YouTube streams are processed in chunks and do not
    # have an application duration cap.
    max_video_size_mb: int = 500
    max_video_duration_minutes: int = 120

    temp_directory: str = "temp"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
