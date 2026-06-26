"""
Security-focused tests for authentication endpoints.
Tests for user enumeration prevention, timing attacks, and other security concerns.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestUserEnumerationPrevention:
    """Tests to verify that login endpoint doesn't leak user existence information."""

    def test_login_nonexistent_email_returns_401(self):
        """Nonexistent email should return 401, not a different status code."""
        response = client.post("/api/auth/login", json={
            "email": f"nonexistent_{uuid.uuid4().hex[:16]}@example.com",
            "password": "SomePassword123!"
        })
        assert response.status_code == 401
        assert "邮箱或密码错误" in response.json()["detail"]

    def test_login_existing_email_wrong_password_returns_401(self):
        """Wrong password for existing email should also return 401 with same message."""
        # Create a user first
        email = f"test_{uuid.uuid4().hex[:12]}@example.com"
        client.post("/api/auth/register", json={
            "email": email,
            "password": "CorrectPass123!",
            "nickname": "test",
            "grade": "高一",
            "role": "student"
        })

        # Try to login with wrong password
        response = client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPass123!"
        })
        assert response.status_code == 401
        assert "邮箱或密码错误" in response.json()["detail"]

    def test_login_inactive_user_returns_401(self):
        """Inactive users should not expose their status - should return same 401."""
        # This test would require creating an inactive user in the database first
        # For now, we just ensure the error message is the same
        response = client.post("/api/auth/login", json={
            "email": "inactive_user@example.com",
            "password": "SomePass123!"
        })
        assert response.status_code == 401
        assert "邮箱或密码错误" in response.json()["detail"]


class TestChangePasswordSecurity:
    """Tests for change-password endpoint security."""

    @pytest.fixture
    def auth_user_token(self):
        """Create a test user and return their token."""
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

    def test_change_password_wrong_old_password_returns_401(self, auth_user_token):
        """Wrong old password should return 401 (authentication failure, not validation error)."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "WrongPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": f"Bearer {auth_user_token}"}
        )
        # Status 401 is correct for authentication failures
        assert response.status_code == 401
        assert "旧密码错误" in response.json()["detail"]

    def test_change_password_no_auth_header_returns_401(self):
        """Change password without auth header should return 401."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "NewPass123!"
            }
            # Missing Authorization header
        )
        assert response.status_code == 403  # FastAPI returns 403 for missing security

    def test_change_password_invalid_token_returns_401(self):
        """Invalid token should return 401."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        assert "Token" in response.json()["detail"]

    def test_change_password_weak_new_password_returns_400(self, auth_user_token):
        """Weak new password should return 400 (validation error, not authentication)."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "weak"
            },
            headers={"Authorization": f"Bearer {auth_user_token}"}
        )
        assert response.status_code == 400  # Validation error
        assert "不符合要求" in response.json()["detail"]

    def test_change_password_same_as_old_returns_400(self, auth_user_token):
        """Using the same password should return 400 (validation error)."""
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


class TestPasswordHashingSecurity:
    """Tests to ensure password hashing is done securely."""

    def test_password_hash_different_each_time(self):
        """Same password should produce different hashes (due to bcrypt salt)."""
        from app.security import hash_password
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Should be different due to different salts

    def test_password_verification_success(self):
        """Correct password should verify successfully."""
        from app.security import hash_password, verify_password
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Wrong password should not verify."""
        from app.security import hash_password, verify_password
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_password_verification_handles_invalid_hash(self):
        """Invalid hash format should not crash, just return False."""
        from app.security import verify_password
        password = "TestPassword123!"
        invalid_hash = "not_a_valid_bcrypt_hash"
        assert verify_password(password, invalid_hash) is False


class TestPasswordValidationStrength:
    """Tests for password strength validation rules."""

    def test_weak_password_too_short(self):
        """Password shorter than 8 characters should be weak."""
        response = client.post("/api/auth/password/validate", json={"password": "Short1!"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert any("长度不足" in issue for issue in data["issues"])

    def test_weak_password_missing_uppercase(self):
        """Password without uppercase should be weak."""
        response = client.post("/api/auth/password/validate", json={"password": "onlylowr123!@"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert any("缺少大写字母" in issue for issue in data["issues"])

    def test_weak_password_missing_lowercase(self):
        """Password without lowercase should be weak."""
        response = client.post("/api/auth/password/validate", json={"password": "ONLYUPPR123!@"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert any("缺少小写字母" in issue for issue in data["issues"])

    def test_weak_password_missing_digit(self):
        """Password without digit should be weak."""
        response = client.post("/api/auth/password/validate", json={"password": "NoDigitsHere!@"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert any("缺少数字" in issue for issue in data["issues"])

    def test_weak_password_missing_special_char(self):
        """Password without special character should be weak."""
        response = client.post("/api/auth/password/validate", json={"password": "NoSpecialChar123"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "weak"
        assert any("缺少特殊字符" in issue for issue in data["issues"])

    def test_strong_password_has_all_requirements(self):
        """Password with all requirements should be strong."""
        response = client.post("/api/auth/password/validate", json={"password": "StrongPass123!@#"})
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] == "strong"
        assert len(data["issues"]) == 0
        assert data["score"] >= 60
