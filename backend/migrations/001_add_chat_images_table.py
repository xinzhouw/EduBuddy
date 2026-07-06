"""
迁移脚本：添加 chat_images 表和 chat_messages 的图片字段
"""


def migrate_up(engine):
    """升级"""
    with engine.connect() as conn:
        # 1. 添加 chat_messages 新字段
        conn.execute("""
            ALTER TABLE chat_messages ADD COLUMN image_ids TEXT;
        """)
        conn.execute("""
            ALTER TABLE chat_messages ADD COLUMN image_ocr_text TEXT;
        """)
        conn.execute("""
            ALTER TABLE chat_messages ADD COLUMN image_vision_desc TEXT;
        """)

        # 2. 创建 chat_images 表
        conn.execute("""
            CREATE TABLE chat_images (
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
            );
        """)

        # 3. 创建索引
        conn.execute("""
            CREATE INDEX idx_chat_image_session_user ON chat_images(session_id, user_id);
        """)
        conn.execute("""
            CREATE INDEX idx_chat_image_created ON chat_images(created_at);
        """)

        conn.commit()


def migrate_down(engine):
    """降级"""
    with engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS chat_images;")
        conn.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS image_ids;")
        conn.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS image_ocr_text;")
        conn.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS image_vision_desc;")
        conn.commit()
