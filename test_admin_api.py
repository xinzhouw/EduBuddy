#!/usr/bin/env python3
"""测试 admin API 端点"""
import json
import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.services.admin_service import AdminService
from app.models.user import User

db = SessionLocal()

# 检查是否有 admin 用户
admin = db.query(User).filter(User.role == 'admin').first()
if not admin:
    print("❌ No admin user found")
    db.close()
    exit(1)

print(f"✅ Admin user found: {admin.email}")

# 测试获取用户列表
result = AdminService.get_users_list(db, page=1, page_size=20, search=None, role=None)
print(f"\n✅ User list API:")
print(f"   Total users: {result['total']}")
print(f"   Items in response: {len(result['items'])}")
print(f"   Keys in response: {list(result.keys())}")

if result['items']:
    first_user = result['items'][0]
    print(f"   First user keys: {list(first_user.keys())}")
    print(f"   First user: {json.dumps(first_user, indent=2, default=str)}")

# 测试仪表板统计
stats = AdminService.get_dashboard_stats(db)
print(f"\n✅ Dashboard stats API:")
print(f"   Active users (7d): {stats['active_users_7d']}")
print(f"   Total users: {stats['total_users']}")
print(f"   Feature top: {len(stats['feature_top'])} items")
print(f"   Active user top: {len(stats['active_user_top'])} items")

# 测试审计日志
audit = AdminService.get_audit_logs(db, page=1, page_size=50)
print(f"\n✅ Audit logs API:")
print(f"   Total logs: {audit['total']}")
print(f"   Items in response: {len(audit['items'])}")

db.close()
print("\n✅ All API tests passed!")
