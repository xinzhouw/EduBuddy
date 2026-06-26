from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.utils.rate_limiter import check_rate_limit_for_endpoint

settings = get_settings()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    # 尝试从 Authorization header 获取令牌
    token = None
    if credentials:
        token = credentials.credentials
    # 回退：从 Cookie 读取令牌（如果 header 中没有）
    elif request and settings.cookie_access_token_name in request.cookies:
        token = request.cookies[settings.cookie_access_token_name]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        token_type = payload.get("type", "access")
        if user_id is None:
            raise credentials_exception
        # 确保这是访问令牌，而不是刷新令牌
        if token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: str):
    """生成一个依赖，限定只有指定角色的用户才能访问该接口。

    用法示例：
        @router.get("/xxx")
        def handler(user: User = Depends(require_roles("teacher", "parent"))):
            ...
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {' / '.join(allowed_roles)} 角色",
            )
        return current_user

    return dependency


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址，考虑代理"""
    # 检查 X-Forwarded-For（来自代理）
    if request.headers.get("x-forwarded-for"):
        return request.headers.get("x-forwarded-for").split(",")[0].strip()
    # 检查 X-Real-IP（来自某些代理）
    if request.headers.get("x-real-ip"):
        return request.headers.get("x-real-ip")
    # 使用连接的远程地址
    return request.client.host if request.client else "unknown"


def verify_refresh_token(token: str) -> int:
    """
    验证刷新令牌并返回用户 ID

    Args:
        token: 刷新令牌

    Returns:
        用户 ID

    Raises:
        HTTPException: 令牌无效或已过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="刷新令牌无效或已过期",
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception


def require_rate_limit(endpoint: str):
    """生成一个依赖，检查端点的速率限制。

    用法示例：
        @router.post("/login")
        def handler(request: Request = Depends(require_rate_limit("login"))):
            ...
    """

    async def dependency(request: Request):
        ip_address = get_client_ip(request)
        allowed, remaining, retry_after = check_rate_limit_for_endpoint(ip_address, endpoint)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency

