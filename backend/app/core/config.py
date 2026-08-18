"""通过 pydantic-settings 加载 .env；统一暴露给上层。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "youshu-ai"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 天

    database_url: str = "sqlite:///./youshu_ai.db"

    wx_app_id: str = ""
    wx_app_secret: str = ""

    ocr_backend: str = "mock"
    vision_backend: str = "mock"
    llm_backend: str = "mock"
    dashscope_api_key: str = ""
    deepseek_api_key: str = ""

    # MiniMax: 一个 key 覆盖 vision + llm (OpenAI 兼容协议)
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimaxi.com/v1"  # 兼容 OpenAI
    minimax_vl_model: str = "MiniMax-VL-01"             # 视觉模型 (需单独开通)
    minimax_text_model: str = "abab6.5s-chat"           # 文本模型 (实测可用)

    storage_dir: str = "./storage/uploads"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
