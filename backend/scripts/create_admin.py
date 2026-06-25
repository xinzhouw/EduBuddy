#!/usr/bin/env python3
"""
创建管理员账户的脚本

使用方法：
python scripts/create_admin.py <email> <password> [nickname]
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import SessionLocal, init_db
from app.models.user import User
from app.security import hash_password
from datetime import datetime

def create_admin(email: str, password: str, nickname: str = "Admin"):
    init_db()
    db = SessionLocal()

    try:
        # 检查邮箱是否已存在
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"错误：邮箱 {email} 已存在")
            return False

        # 创建管理员账户
        admin = User(
            email=email,
            password=hash_password(password),
            nickname=nickname,
            role="admin",
            is_active=True,
            grade="管理员",
            created_at=datetime.utcnow()
        )
        db.add(admin)
        db.commit()

        print(f"✓ 管理员账户创建成功")
        print(f"  邮箱：{email}")
        print(f"  昵称：{nickname}")
        print(f"  角色：admin")
        return True

    except Exception as e:
        print(f"错误：{e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法：python scripts/create_admin.py <email> <password> [nickname]")
        print("示例：python scripts/create_admin.py admin@example.com password123 管理员")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    nickname = sys.argv[3] if len(sys.argv) > 3 else "Admin"

    success = create_admin(email, password, nickname)
    sys.exit(0 if success else 1)
