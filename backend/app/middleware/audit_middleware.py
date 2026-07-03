import asyncio
import logging
from datetime import datetime
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models.audit_log import AuditLog
from app.utils.geoip import get_geoip_manager
from jose import jwt, JWTError
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# 功能路径映射
FEATURE_MAP = {
    "/api/ai": "ai_chat",
    "/api/notes": "notes",
    "/api/wrong-book": "wrong_book",
    "/api/quiz": "quiz",
    "/api/plan": "study_plan",
    "/api/homework": "homework",
    "/api/monitor": "monitor",
    "/api/auth": "auth",
    "/api/admin": "admin",
    "/api/advice": "advice",
    "/api/relations": "relations",
    "/api/stats": "stats",
}

def get_feature_from_path(path: str) -> str:
    """根据路径确定功能类别"""
    for prefix, feature in FEATURE_MAP.items():
        if path.startswith(prefix):
            return feature
    return "others"

def extract_user_id_from_token(request: Request) -> int:
    """从请求头提取 user_id"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except (JWTError, Exception):
        return None

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 提取必要信息
        user_id = extract_user_id_from_token(request)
        ip_address = request.client.host if request.client else "Unknown"
        feature = get_feature_from_path(request.url.path)
        action = request.method
        endpoint = request.url.path
        # 去掉查询字符串以简化记录
        if "?" in endpoint:
            endpoint = endpoint.split("?")[0]

        # 调用下一个中间件/路由处理
        response = await call_next(request)
        status_code = response.status_code

        # 异步记录日志（不阻塞响应）
        asyncio.create_task(
            _log_audit_async(user_id, feature, action, endpoint, ip_address, status_code)
        )

        return response

async def _log_audit_async(user_id: int, feature: str, action: str, endpoint: str,
                           ip_address: str, status_code: int):
    """异步记录审计日志"""
    db = SessionLocal()
    try:
        # 跳过无关的请求（未认证、other 类别）
        if user_id is None:
            return

        # 如果是登录失败，仍记录（因为 auth 路由被映射）
        if feature == "others":
            return

        geoip_manager = get_geoip_manager()
        city, country = geoip_manager.get_city_country(ip_address)

        audit_log = AuditLog(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            feature=feature,
            action=action,
            endpoint=endpoint,
            ip_address=ip_address,
            city=city,
            country=country,
            status_code=status_code
        )
        db.add(audit_log)
        db.commit()
        logger.debug(f"Audit log recorded for user {user_id}: {action} {endpoint}")
    except SQLAlchemyError as e:
        logger.error(f"Database error logging audit: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"Error logging audit: {e}")
    finally:
        db.close()
