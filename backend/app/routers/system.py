from fastapi import APIRouter
from app.config import get_settings
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/info")
def get_system_info():
    """获取系统信息（包括当前使用的 LLM 模型）"""
    settings = get_settings()

    provider = settings.llm_provider or "openai"

    if provider == "anthropic":
        model = settings.anthropic_model or "claude-opus-4-8"
        # 解析模型名称获取友好显示
        # claude-opus-4-8 -> Claude Opus 4.8
        parts = model.split('-')
        if len(parts) >= 2:
            family = parts[1].capitalize()  # opus -> Opus
            version = '-'.join(parts[2:]) if len(parts) > 2 else ""  # 4-8 -> 4-8
            model_short = f"{family} {version}".strip()
        else:
            model_short = model
        base_url = settings.anthropic_base_url or "https://api.anthropic.com"
    else:
        model = settings.openai_model or "gpt-4o"
        model_short = model
        base_url = settings.openai_base_url or "https://api.openai.com/v1"

    return {
        "code": 200,
        "data": {
            "llm_provider": provider,
            "llm_model": model,
            "llm_model_short": model_short,
            "llm_base_url": base_url,
            "app_version": "1.0.0",
            "app_name": "EduBuddy",
        }
    }
