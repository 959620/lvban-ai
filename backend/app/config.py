from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# 始终相对 backend 目录加载，避免 uvicorn 工作目录变化读不到 .env
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "教务智能工作台"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./jiaowu.db"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://127.0.0.1:5174,http://127.0.0.1:5175"
    )

    openai_api_key: str = ""
    openai_base_url: str = "https://aihubmix.com/v1"
    openai_model: str = "gpt-5.6-luna"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # 非空环境变量优先（Zeabur）；空环境变量忽略，回退到 .env（本地）
        return init_settings, env_settings, dotenv_settings, file_secret_settings

    @property
    def cors_origin_list(self) -> list[str]:
        items = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        if items == ["*"]:
            return ["*"]
        return items


@lru_cache
def get_settings() -> Settings:
    return Settings()
