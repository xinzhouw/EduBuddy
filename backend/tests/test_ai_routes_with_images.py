"""AI 图片相关路由的集成测试。

覆盖认证、权限与 404 分支；实际的 OCR/Vision 分析依赖外部服务，不在此测试。
"""
import io
import uuid

from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, init_db
from app.models.image import ChatImage
from app.models.note import ChatSession
from app.services import ai_service as ai_service_module

# 模块级 TestClient 不会触发 lifespan，手动确保建表（含 chat_images）
init_db()

client = TestClient(app)

STRONG_PW = "SecurePass123!"


def register_and_login() -> tuple[int, str]:
    """注册并登录一个新用户，返回 (user_id, access_token)。"""
    email = f"imgtest_{uuid.uuid4().hex[:12]}@example.com"
    reg = client.post("/api/auth/register", json={
        "email": email,
        "password": STRONG_PW,
        "nickname": "imgtest",
        "grade": "高一",
        "role": "student",
    })
    assert reg.status_code == 200, reg.text
    login = client.post("/api/auth/login", json={"email": email, "password": STRONG_PW})
    assert login.status_code == 200, login.text
    data = login.json()["data"]
    return data["user"]["id"], data["access_token"]


class TestGetSessionImages:
    def test_requires_auth(self):
        resp = client.get("/api/ai/chat/nonexistent-session/images")
        assert resp.status_code in (401, 403)

    def test_nonexistent_session_returns_404(self):
        _, token = register_and_login()
        resp = client.get(
            "/api/ai/chat/no-such-session/images",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestChatWithImageCreatesSession:
    """回归：带图片且无 session_id 时应新建会话并返回 200，而非 404。

    桩掉实际 AI 流式调用，避免依赖外部模型；只验证会话解析与图片保存流程。
    """

    def test_upload_image_new_session_no_404(self, monkeypatch):
        async def fake_stream(*args, **kwargs):
            # 断言路由传入的是普通字符串路径（非 ORM 对象），防止 DetachedInstanceError 回归
            image_paths = kwargs.get("image_paths")
            assert isinstance(image_paths, list) and len(image_paths) == 1
            assert isinstance(image_paths[0], str)
            yield "已收到图片"

        monkeypatch.setattr(
            ai_service_module.ai_service, "chat_stream_with_images", fake_stream
        )

        _, token = register_and_login()
        buf = io.BytesIO()
        Image.new("RGB", (60, 60), "white").save(buf, format="JPEG")
        buf.seek(0)

        resp = client.post(
            "/api/ai/chat",
            data={"question": "这道题", "subject": "数学"},  # 不传 session_id
            files={"images": ("q.jpg", buf, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.text
        assert "已收到图片" in body
        # 响应流末尾应带上新建的 session_id
        assert "session_id" in body

    def test_upload_image_bogus_session_still_404(self):
        _, token = register_and_login()
        buf = io.BytesIO()
        Image.new("RGB", (60, 60), "white").save(buf, format="JPEG")
        buf.seek(0)
        resp = client.post(
            "/api/ai/chat",
            data={"question": "x", "subject": "数学", "session_id": "no-such-session"},
            files={"images": ("q.jpg", buf, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestDeleteImage:
    def test_requires_auth(self):
        resp = client.delete("/api/ai/chat/images/whatever")
        assert resp.status_code in (401, 403)

    def test_nonexistent_image_returns_404(self):
        _, token = register_and_login()
        resp = client.delete(
            "/api/ai/chat/images/does-not-exist",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_cannot_delete_other_users_image(self):
        # 直接在 DB 插入一张属于 user_id=999999 的图片
        image_id = f"perm_{uuid.uuid4().hex[:12]}"
        db = SessionLocal()
        try:
            db.add(ChatImage(
                id=image_id,
                session_id="sess-other",
                user_id=999999,
                file_path="999999/sess-other/x.jpg",
                original_filename="x.jpg",
                file_size=100,
                file_type="jpg",
            ))
            db.commit()
        finally:
            db.close()

        _, token = register_and_login()
        resp = client.delete(
            f"/api/ai/chat/images/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

        # 清理
        db = SessionLocal()
        try:
            obj = db.query(ChatImage).filter(ChatImage.id == image_id).first()
            if obj:
                db.delete(obj)
                db.commit()
        finally:
            db.close()
