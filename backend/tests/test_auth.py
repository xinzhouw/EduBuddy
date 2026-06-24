import pytest
import time
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPasswordValidateEndpoint:
    def test_validate_weak_password(self):
        response = client.post("/api/auth/password/validate", json={"password": "weak"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert len(data["issues"]) > 0

    def test_validate_strong_password(self):
        response = client.post("/api/auth/password/validate", json={"password": "SecurePass123!"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "strong"
        assert data["issues"] == []
        assert data["score"] >= 60


class TestRegisterWithPasswordValidation:
    def test_register_weak_password(self):
        response = client.post("/api/auth/register", json={
            "email": f"test_{uuid.uuid4().hex[:12]}@example.com",
            "password": "weak",
            "nickname": "test",
            "grade": "高一",
            "role": "student"
        })
        assert response.status_code == 400
        assert "不符合要求" in response.json()["detail"]

    def test_register_strong_password_success(self):
        response = client.post("/api/auth/register", json={
            "email": f"newuser_{uuid.uuid4().hex[:12]}@example.com",
            "password": "SecurePass123!",
            "nickname": "testuser",
            "grade": "高一",
            "role": "student"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"]


class TestChangePasswordEndpoint:
    @pytest.fixture
    def auth_user_token(self):
        # 创建测试用户（使用 uuid4 确保每次调用邮箱唯一）
        unique_id = uuid.uuid4().hex[:12]
        email = f"changepass_{unique_id}@example.com"
        response = client.post("/api/auth/register", json={
            "email": email,
            "password": "OldPass123!",
            "nickname": "testuser",
            "grade": "高一",
            "role": "student"
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_change_password_wrong_old_password(self, auth_user_token):
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "WrongPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": f"Bearer {auth_user_token}"}
        )
        assert response.status_code == 401
        assert "旧密码错误" in response.json()["detail"]

    def test_change_password_weak_new_password(self, auth_user_token):
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "weak"
            },
            headers={"Authorization": f"Bearer {auth_user_token}"}
        )
        assert response.status_code == 400
        assert "不符合要求" in response.json()["detail"]

    def test_change_password_same_as_old(self, auth_user_token):
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "OldPass123!"
            },
            headers={"Authorization": f"Bearer {auth_user_token}"}
        )
        assert response.status_code == 400
        assert "相同" in response.json()["detail"]

    def test_change_password_success(self, auth_user_token):
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": f"Bearer {auth_user_token}"}
        )
        assert response.status_code == 200
        assert "密码已修改" in response.json()["message"]
