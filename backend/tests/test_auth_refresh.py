"""
JWT 刷新令牌测试
"""
import pytest
import time
import uuid
from fastapi.testclient import TestClient
from jose import jwt
from app.main import app
from app.config import get_settings

client = TestClient(app)
settings = get_settings()


class TestRefreshTokenFlow:
    """测试刷新令牌流程"""

    @pytest.fixture
    def registered_user(self):
        """注册一个测试用户"""
        email = f"refresh_test_{uuid.uuid4().hex[:12]}@example.com"
        password = "SecurePass123!"
        response = client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "nickname": "testuser",
            "grade": "高一",
            "role": "student"
        })
        assert response.status_code == 200
        return {
            "email": email,
            "password": password,
            "tokens": response.json(),
        }

    def test_login_returns_refresh_token(self):
        """登录返回刷新令牌"""
        email = f"login_test_{uuid.uuid4().hex[:12]}@example.com"
        password = "SecurePass123!"
        # 注册
        client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "nickname": "testuser",
            "grade": "高一",
        })
        # 登录
        response = client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["expires_in"] == settings.access_token_expire_minutes * 60

    def test_access_token_type_is_access(self, registered_user):
        """访问令牌的类型应该是 'access'"""
        access_token = registered_user["tokens"]["access_token"]
        payload = jwt.decode(access_token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload.get("type") == "access"

    def test_refresh_token_type_is_refresh(self, registered_user):
        """刷新令牌的类型应该是 'refresh'"""
        refresh_token = registered_user["tokens"]["refresh_token"]
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload.get("type") == "refresh"

    def test_refresh_endpoint_returns_new_access_token(self, registered_user):
        """刷新端点返回新的访问令牌"""
        refresh_token = registered_user["tokens"]["refresh_token"]
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.access_token_expire_minutes * 60

    def test_refresh_with_invalid_token_returns_401(self):
        """使用无效的刷新令牌返回 401"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token_here"
        })
        assert response.status_code == 401
        assert "无效或已过期" in response.json()["detail"]

    def test_refresh_with_access_token_returns_401(self, registered_user):
        """使用访问令牌而非刷新令牌返回 401"""
        access_token = registered_user["tokens"]["access_token"]
        response = client.post("/api/auth/refresh", json={
            "refresh_token": access_token  # 错误的令牌类型
        })
        assert response.status_code == 401

    def test_new_access_token_can_be_used(self, registered_user):
        """新的访问令牌可以用于认证请求"""
        refresh_token = registered_user["tokens"]["refresh_token"]
        # 获取新的访问令牌
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        new_access_token = response.json()["access_token"]

        # 使用新的访问令牌获取用户信息
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {new_access_token}"
        })
        assert response.status_code == 200
        assert response.json()["data"]["email"] == registered_user["email"]

    def test_old_access_token_still_works_temporarily(self, registered_user):
        """旧的访问令牌在刷新后仍然有效（直到过期）"""
        # 旧的访问令牌应该仍然可用
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {registered_user['tokens']['access_token']}"
        })
        assert response.status_code == 200

    def test_refresh_token_expiry(self):
        """测试刷新令牌过期（不能实时测试，检查声明）"""
        email = f"expiry_test_{uuid.uuid4().hex[:12]}@example.com"
        password = "SecurePass123!"
        response = client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "nickname": "testuser",
            "grade": "高一",
        })
        refresh_token = response.json()["refresh_token"]
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])

        # 检查过期时间
        assert "exp" in payload
        # 过期时间应该是当前时间 + 7 天
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        time_diff = (exp_time - now).total_seconds()
        # 应该约等于 7 天（允许 60 秒误差）
        assert abs(time_diff - (7 * 86400)) < 60
