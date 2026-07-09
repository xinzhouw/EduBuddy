"""
迁移脚本：向 users 表添加 language 列。

幂等：可重复执行。用于生产环境现有数据库的手动升级或审计。
SQLite 不支持 ALTER TABLE ADD COLUMN ... NOT NULL 无默认值，
故使用 server_default='zh' 确保迁移安全。
"""
from sqlalchemy import text


def _existing_columns(conn, table: str) -> set:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}  # r[1] = column name


def migrate_up(engine):
    """升级（幂等）：向 users 表添加 language 列"""
    with engine.connect() as conn:
        existing = _existing_columns(conn, "users")
        if "language" not in existing:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'zh'"
            ))
            conn.commit()
            print("✓ Added column 'language' to users table")
        else:
            print("⊘ Column 'language' already exists in users table (skipped)")


def migrate_down(engine):
    """降级（仅标记；SQLite 旧版不支持 DROP COLUMN）"""
    # SQLite < 3.35.0 不支持 DROP COLUMN；对于新版 SQLite 可使用：
    # ALTER TABLE users DROP COLUMN language;
    # 为兼容性，此处仅打印提示。
    print("⊘ migrate_down: SQLite does not reliably support DROP COLUMN. "
          "To revert, recreate the table without the 'language' column.")
