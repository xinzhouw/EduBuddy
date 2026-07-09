from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import get_settings
import os

settings = get_settings()

# 确保数据目录存在
db_path = settings.database_url.replace("sqlite:///", "")
os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import user, note, quiz, wrong_item, study_plan, document, homework, relation, advice, audit_log, image  # noqa
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def _apply_lightweight_migrations():
    """幂等地为已存在的表补充新增列。

    create_all 只创建缺失的表，不会给已存在的表加列。对于给现有表新增字段
    （如 chat_messages 的图片相关列），需在此显式 ALTER，保证已有部署重启即升级。
    """
    from sqlalchemy import text

    # (表名, 列名, 列类型[含默认值]) —— 新增列在此登记
    column_additions = [
        ("chat_messages", "image_ids", "TEXT"),
        ("chat_messages", "image_ocr_text", "TEXT"),
        ("chat_messages", "image_vision_desc", "TEXT"),
        ("users", "language", "VARCHAR(10) NOT NULL DEFAULT 'zh'"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in column_additions:
            existing = {
                row[1]
                for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            }
            if existing and column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        conn.commit()
