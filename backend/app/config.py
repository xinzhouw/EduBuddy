from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ===== LLM 提供商选择 =====
    llm_provider: str = "openai"  # 可选值: "openai", "anthropic"

    # ===== OpenAI 兼容模式配置 =====
    openai_api_key: str = ""
    openai_base_url: str = ""          # OpenAI 兼容接口地址，留空则使用官方地址
    openai_model: str = "gpt-4o"       # 模型名称，可改为兼容服务提供的模型名
    # 是否在请求中携带 temperature 参数。部分模型网关（如 Claude/Bedrock）
    # 不接受 temperature，会返回 400，此时将该项设为 false 即可。
    openai_use_temperature: bool = True

    # ===== Anthropic Claude 模式配置 =====
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""       # Claude 兼容接口地址，留空则使用官方地址
    anthropic_model: str = "claude-opus-4-8"
    anthropic_default_haiku_model: str = "claude-haiku-4-5"
    anthropic_default_sonnet_model: str = "claude-sonnet-4-6"
    anthropic_default_opus_model: str = "claude-opus-4-8"

    # ===== 通用配置 =====
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./data/edubuddy.db"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 20
    cors_origins: str = "http://localhost:5173,http://localhost:80"

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 访问令牌有效期 (分钟)
    refresh_token_expire_days: int = 7  # 刷新令牌有效期 (天)

    # Cookie 配置
    cookie_access_token_name: str = "access_token"
    cookie_secure: bool = False  # 生产环境应设置为 True
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"

    # ===== SMTP 邮件配置 =====
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@edubuddy.com"
    smtp_from_name: str = "EduBuddy"

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
