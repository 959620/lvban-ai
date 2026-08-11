"""
全局配置加载。

设计原因：
- 所有密钥与开关集中在此，业务代码不硬编码环境差异
- 使用 pydantic-settings，便于校验类型与缺省值
- 企业微信等第二阶段配置先占位，避免后期改调用链
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Edu-Agent 项目根目录（config/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置：从环境变量 / .env 读取。"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "Edu-Agent"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True

    # 数据库
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'edu_agent.db'}"

    # OpenAI（Step 7）
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 30.0

    # 通知开关
    notify_local: bool = True
    notify_email: bool = False
    notify_wecom: bool = False
    notify_email_dry_run: bool = False
    notify_wecom_dry_run: bool = False

    # 邮件
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    notify_email_to: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    # 企业微信
    wecom_webhook_url: str = ""
    wecom_corp_id: str = ""
    wecom_agent_id: str = ""
    wecom_secret: str = ""
    wecom_touser: str = "@all"
    wecom_msg_type: str = "markdown"  # text | markdown
    wecom_api_base: str = "https://qyapi.weixin.qq.com"
    wecom_timeout_seconds: float = 15.0

    # 调度
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    """进程内单例配置，避免重复读盘。"""
    return Settings()
