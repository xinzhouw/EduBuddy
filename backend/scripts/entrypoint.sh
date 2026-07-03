#!/bin/bash
set -e

echo "🔄 Starting EduBuddy Backend..."

# 1. 初始化数据库（创建表）
echo "📦 Initializing database schema..."
python3 -c "from app.database import init_db; init_db(); print('✓ Database schema initialized')"

# 2. 运行数据库迁移（如果有新列需要添加）
if [ -f "/app/scripts/migrate_db.py" ]; then
    echo "🔧 Running database migrations..."
    python3 /app/scripts/migrate_db.py
fi

# 3. 启动 FastAPI 应用
echo "🚀 Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
