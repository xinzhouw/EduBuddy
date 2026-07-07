"""
迁移脚本：添加 chat_images 表和 chat_messages 的图片字段。

幂等：可重复执行。主路径为应用启动时 init_db() 的 create_all 自动建表，
本脚本作为生产环境手动执行/审计的备用手段。SQLAlchemy 2.0 需用 text() 包裹裸 SQL。
"""
from sqlalchemy import text


def _existing_columns(conn, table: str) -> set:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}  # r[1] = column name


def migrate_up(engine):
    """升级（幂等）"""
    with engine.connect() as conn:
        # 1. 为 chat_messages 增加缺失的图片字段（SQLite 不支持 IF NOT EXISTS 列）
        existing = _existing_columns(conn, "chat_messages")
        for col in ("image_ids", "image_ocr_text", "image_vision_desc"):
            if col not in existing:
                conn.execute(text(f"ALTER TABLE chat_messages ADD COLUMN {col} TEXT"))

        # 2. 创建 chat_images 表（幂等）
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_images (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                ocr_text TEXT,
                vision_description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # 3. 创建索引（幂等）
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_chat_image_session_user "
            "ON chat_images(session_id, user_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_chat_image_created "
            "ON chat_images(created_at)"
        ))

        conn.commit()


def migrate_down(engine):
    """降级（仅删除 chat_images 表；SQLite 旧版不支持 DROP COLUMN，故保留新增列）"""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS chat_images"))
        conn.commit()
