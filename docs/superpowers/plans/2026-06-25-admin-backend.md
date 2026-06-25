# 管理后台功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现管理后台功能，包括用户管理、登录日志记录、功能访问统计和仪表板展示。

**Architecture:** 采用 FastAPI 中间件自动拦截请求并记录到数据库，使用本地 GeoIP 库转换 IP 地址，后端提供统计查询 API，前端展示管理界面。

**Tech Stack:** 
- 后端：FastAPI 中间件、SQLAlchemy ORM、geoip2 库、APScheduler 定时任务
- 前端：Vue 3、Pinia、Element Plus、ECharts 图表
- 数据库：SQLite，新增 `audit_logs` 表，修改 `users` 表

## Global Constraints

- 日志保留期限：仅保留最近 3 个月的数据
- GeoIP 数据库：使用免费社区数据库
- 管理员角色：新增 `admin` 角色，仅 admin 可访问后台
- 自动清理：每日凌晨 2 点删除过期日志

---

## Task 1: 创建数据库迁移文件

**Files:**
- Create: `backend/app/migrations/001_add_admin_tables.sql`
- Modify: `backend/app/database.py` - 初始化时执行迁移

**Interfaces:**
- Produces: 已创建 `audit_logs` 表、修改 `users` 表结构

- [ ] **Step 1: 创建迁移 SQL 文件**

```sql
-- 添加迁移脚本：001_add_admin_tables.sql
-- 修改 users 表
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1;
ALTER TABLE users ADD COLUMN last_login DATETIME;
ALTER TABLE users ADD COLUMN login_count INTEGER NOT NULL DEFAULT 0;

-- 创建 audit_logs 表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    feature VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    city VARCHAR(100),
    country VARCHAR(100),
    status_code INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_time ON audit_logs(timestamp);
CREATE INDEX idx_audit_feature ON audit_logs(feature);
```

- [ ] **Step 2: 在 database.py 中添加迁移执行逻辑**

修改 `backend/app/database.py`，在 `init_db()` 函数中添加：

```python
def init_db():
    Base.metadata.create_all(bind=engine)
    # 执行迁移脚本
    with engine.connect() as conn:
        migration_file = Path(__file__).parent / "migrations" / "001_add_admin_tables.sql"
        if migration_file.exists():
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
                for statement in sql.split(';'):
                    if statement.strip():
                        conn.execute(text(statement))
            conn.commit()
```

- [ ] **Step 3: 创建 migrations 目录**

```bash
mkdir -p backend/app/migrations
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/migrations/001_add_admin_tables.sql backend/app/database.py
git commit -m "feat: add database migration for admin tables"
```

---

## Task 2: 创建 AuditLog ORM 模型

**Files:**
- Create: `backend/app/models/audit_log.py`
- Modify: `backend/app/models/__init__.py` - 导出 AuditLog

**Interfaces:**
- Produces: `AuditLog` 模型类，可用于数据库操作

- [ ] **Step 1: 创建 AuditLog 模型**

Create `backend/app/models/audit_log.py`:

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    feature = Column(String(50), nullable=False, index=True)  # ai_chat, notes, wrong_book, quiz, study_plan, homework, others
    action = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    endpoint = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    city = Column(String(100))
    country = Column(String(100))
    status_code = Column(Integer)
    
    # 关系
    user = relationship("User", back_populates="audit_logs")
```

- [ ] **Step 2: 修改 User 模型添加反向关系**

修改 `backend/app/models/user.py`，在 User 类中添加：

```python
from sqlalchemy.orm import relationship

class User(Base):
    # ... 现有字段 ...
    
    # 新增字段
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # 关系
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
```

- [ ] **Step 3: 更新 __init__.py 导出**

修改 `backend/app/models/__init__.py`，添加：

```python
from app.models.audit_log import AuditLog

__all__ = ["User", "Note", "ChatSession", "ChatMessage", "WrongItem", "WrongReview", 
           "StudyPlan", "PlanTask", "Document", "QuizSession", "Question", "AuditLog"]
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/audit_log.py backend/app/models/user.py backend/app/models/__init__.py
git commit -m "feat: add AuditLog model and extend User model"
```

---

## Task 3: 创建 GeoIP 工具

**Files:**
- Create: `backend/app/utils/geoip.py`
- Create: `backend/data/GeoLite2-City.mmdb` - 下载免费数据库

**Interfaces:**
- Produces: `get_city_country(ip_address: str) -> Tuple[str, str]` 函数

- [ ] **Step 1: 创建 geoip.py 工具**

Create `backend/app/utils/geoip.py`:

```python
import os
from pathlib import Path
from typing import Tuple, Optional
import geoip2.database

class GeoIPManager:
    def __init__(self):
        db_path = Path(__file__).parent.parent.parent / "data" / "GeoLite2-City.mmdb"
        if db_path.exists():
            self.reader = geoip2.database.Reader(str(db_path))
        else:
            self.reader = None
    
    def get_city_country(self, ip_address: str) -> Tuple[str, str]:
        """
        根据 IP 地址获取城市和国家
        
        Args:
            ip_address: IP 地址
            
        Returns:
            (city, country) 元组，如果获取失败返回 ("Unknown", "Unknown")
        """
        if not self.reader or not ip_address:
            return "Unknown", "Unknown"
        
        try:
            response = self.reader.city(ip_address)
            city = response.city.name or "Unknown"
            country = response.country.iso_code or "Unknown"
            return city, country
        except Exception:
            return "Unknown", "Unknown"

# 全局单例
_geoip_manager = None

def get_geoip_manager() -> GeoIPManager:
    global _geoip_manager
    if _geoip_manager is None:
        _geoip_manager = GeoIPManager()
    return _geoip_manager
```

- [ ] **Step 2: 下载免费 GeoIP 数据库**

```bash
cd backend/data
# 下载 MaxMind 免费社区数据库
curl -L https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb -o GeoLite2-City.mmdb
# 如果上面链接失败，备用：
# wget https://github.com/allinurl/geoip-api/raw/master/GeoLite2-City.mmdb -O GeoLite2-City.mmdb
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/utils/geoip.py
git commit -m "feat: add GeoIP utility for IP location lookup"
```

---

## Task 4: 创建审计中间件

**Files:**
- Create: `backend/app/middleware/audit_middleware.py`
- Modify: `backend/app/main.py` - 注册中间件

**Interfaces:**
- Consumes: `AuditLog` 模型、`get_geoip_manager()` 函数、FastAPI app
- Produces: 自动拦截所有请求并记录日志

- [ ] **Step 1: 创建审计中间件**

Create `backend/app/middleware/audit_middleware.py`:

```python
import asyncio
from datetime import datetime
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.audit_log import AuditLog
from app.utils.geoip import get_geoip_manager
import jwt
from app.config import settings

# 功能路径映射
FEATURE_MAP = {
    "/api/ai": "ai_chat",
    "/api/notes": "notes",
    "/api/wrong-book": "wrong_book",
    "/api/quiz": "quiz",
    "/api/plan": "study_plan",
    "/api/homework": "homework",
    "/api/monitor": "monitor",
    "/api/auth": "auth",
    "/api/admin": "admin",
}

def get_feature_from_path(path: str) -> str:
    """根据路径确定功能类别"""
    for prefix, feature in FEATURE_MAP.items():
        if path.startswith(prefix):
            return feature
    return "others"

def extract_user_id_from_token(request: Request) -> int:
    """从请求头提取 user_id"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except:
        return None

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 提取必要信息
        user_id = extract_user_id_from_token(request)
        ip_address = request.client.host if request.client else "Unknown"
        feature = get_feature_from_path(request.url.path)
        action = request.method
        endpoint = request.url.path
        
        # 调用下一个中间件/路由处理
        response = await call_next(request)
        status_code = response.status_code
        
        # 异步记录日志（不阻塞响应）
        asyncio.create_task(
            _log_audit_async(user_id, feature, action, endpoint, ip_address, status_code)
        )
        
        return response

async def _log_audit_async(user_id: int, feature: str, action: str, endpoint: str, 
                           ip_address: str, status_code: int):
    """异步记录审计日志"""
    db = SessionLocal()
    try:
        # 跳过无关的请求
        if user_id is None or feature == "others":
            return
        
        geoip_manager = get_geoip_manager()
        city, country = geoip_manager.get_city_country(ip_address)
        
        audit_log = AuditLog(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            feature=feature,
            action=action,
            endpoint=endpoint,
            ip_address=ip_address,
            city=city,
            country=country,
            status_code=status_code
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")
    finally:
        db.close()
```

- [ ] **Step 2: 修改 main.py 注册中间件**

修改 `backend/app/main.py`，在 FastAPI app 初始化后添加：

```python
from app.middleware.audit_middleware import AuditMiddleware

# ... 现有代码 ...

app = FastAPI()

# 添加审计中间件（在其他中间件之前）
app.add_middleware(AuditMiddleware)

# ... 其他中间件和路由 ...
```

- [ ] **Step 3: 创建 middleware 目录的 __init__.py**

```bash
touch backend/app/middleware/__init__.py
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/middleware/audit_middleware.py backend/app/main.py backend/app/middleware/__init__.py
git commit -m "feat: add audit middleware for request logging"
```

---

## Task 5: 创建 Admin 服务

**Files:**
- Create: `backend/app/services/admin_service.py`

**Interfaces:**
- Consumes: `AuditLog` 模型、`User` 模型、SQLAlchemy Session
- Produces: 统计查询和用户管理业务逻辑函数

- [ ] **Step 1: 创建 admin_service.py**

Create `backend/app/services/admin_service.py`:

```python
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.models.user import User
from app.models.audit_log import AuditLog

class AdminService:
    @staticmethod
    def get_users_list(db: Session, page: int = 1, page_size: int = 20, 
                       search: str = None, role: str = None) -> Dict[str, Any]:
        """获取用户列表"""
        query = db.query(User).filter(User.role != 'admin')
        
        if search:
            query = query.filter(
                (User.email.contains(search)) | 
                (User.nickname.contains(search))
            )
        
        if role:
            query = query.filter(User.role == role)
        
        total = query.count()
        users = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": u.id,
                    "email": u.email,
                    "nickname": u.nickname,
                    "role": u.role,
                    "grade": u.grade,
                    "is_active": u.is_active,
                    "last_login": u.last_login,
                    "login_count": u.login_count,
                    "created_at": u.created_at
                }
                for u in users
            ]
        }
    
    @staticmethod
    def get_user_detail(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详情及统计"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # 计算登录统计
        last_7_days = datetime.utcnow() - timedelta(days=7)
        login_7d = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.feature == 'auth',
                AuditLog.action == 'POST',
                AuditLog.timestamp >= last_7_days
            )
        ).count()
        
        # 功能使用统计（最近 30 天）
        last_30_days = datetime.utcnow() - timedelta(days=30)
        feature_stats = db.query(
            AuditLog.feature,
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.status_code.in_([200, 201]),
                AuditLog.timestamp >= last_30_days
            )
        ).group_by(AuditLog.feature).all()
        
        return {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
            "grade": user.grade,
            "is_active": user.is_active,
            "last_login": user.last_login,
            "login_count": user.login_count,
            "login_7d": login_7d,
            "created_at": user.created_at,
            "feature_stats": [
                {"feature": f, "count": c} for f, c in feature_stats
            ]
        }
    
    @staticmethod
    def toggle_user_status(db: Session, user_id: int, is_active: bool) -> bool:
        """启用/禁用用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role != 'admin':
            user.is_active = is_active
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户及相关数据"""
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role != 'admin':
            db.delete(user)  # 级联删除由 ORM 关系定义
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_audit_logs(db: Session, page: int = 1, page_size: int = 50,
                       user_id: int = None, feature: str = None, 
                       start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """获取审计日志"""
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if feature:
            query = query.filter(AuditLog.feature == feature)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # 只显示最近 90 天的日志
        min_date = datetime.utcnow() - timedelta(days=90)
        query = query.filter(AuditLog.timestamp >= min_date)
        
        total = query.count()
        logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "timestamp": log.timestamp,
                    "feature": log.feature,
                    "action": log.action,
                    "endpoint": log.endpoint,
                    "ip_address": log.ip_address,
                    "city": log.city,
                    "country": log.country,
                    "status_code": log.status_code
                }
                for log in logs
            ]
        }
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """获取仪表板统计"""
        # 活跃用户数（最近 7 天）
        last_7_days = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
            AuditLog.timestamp >= last_7_days
        ).scalar() or 0
        
        # 总用户数（非 admin）
        total_users = db.query(func.count(User.id)).filter(User.role != 'admin').scalar() or 0
        
        # 功能使用排行（最近 30 天）
        last_30_days = datetime.utcnow() - timedelta(days=30)
        feature_top = db.query(
            AuditLog.feature,
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.status_code.in_([200, 201]),
                AuditLog.timestamp >= last_30_days
            )
        ).group_by(AuditLog.feature).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        # 活跃用户排行（最近 7 天）
        active_user_top = db.query(
            AuditLog.user_id,
            User.nickname,
            User.email,
            func.count(AuditLog.id).label('count')
        ).join(User).filter(
            AuditLog.timestamp >= last_7_days
        ).group_by(AuditLog.user_id).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        return {
            "active_users_7d": active_users,
            "total_users": total_users,
            "feature_top": [
                {"feature": f, "count": c} for f, c in feature_top
            ],
            "active_user_top": [
                {
                    "user_id": uid,
                    "nickname": nick,
                    "email": email,
                    "count": c
                }
                for uid, nick, email, c in active_user_top
            ]
        }
    
    @staticmethod
    def cleanup_old_logs(db: Session) -> int:
        """清理 90 天前的日志"""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
        db.commit()
        return deleted
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/admin_service.py
git commit -m "feat: add admin service with user management and statistics"
```

---

## Task 6: 创建 Admin 路由

**Files:**
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/main.py` - 注册路由

**Interfaces:**
- Consumes: `AdminService` 类、`User` 模型、FastAPI app、依赖注入
- Produces: Admin API 端点集合

- [ ] **Step 1: 创建 admin 路由**

Create `backend/app/routers/admin.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin(current_user: User = Depends(get_current_user)):
    """验证用户是否为管理员"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return current_user

@router.get("/users")
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    role: str = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    return AdminService.get_users_list(db, page, page_size, search, role)

@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户详情及统计"""
    user_detail = AdminService.get_user_detail(db, user_id)
    if not user_detail:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_detail

@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """启用/禁用用户"""
    if not AdminService.toggle_user_status(db, user_id, is_active):
        raise HTTPException(status_code=400, detail="无法修改此用户")
    return {"success": True}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户"""
    if not AdminService.delete_user(db, user_id):
        raise HTTPException(status_code=400, detail="无法删除此用户")
    return {"success": True}

@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: int = Query(None),
    feature: str = Query(None),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取审计日志"""
    return AdminService.get_audit_logs(db, page, page_size, user_id, feature, start_date, end_date)

@router.get("/stats/dashboard")
def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取仪表板统计"""
    return AdminService.get_dashboard_stats(db)
```

- [ ] **Step 2: 修改 main.py 注册 admin 路由**

修改 `backend/app/main.py`，在路由注册部分添加：

```python
from app.routers import admin

# ... 现有路由注册 ...

app.include_router(admin.router)
```

- [ ] **Step 3: 在 requirements.txt 中添加依赖**

修改 `backend/requirements.txt`，添加：

```
geoip2>=4.7.0
apscheduler>=3.10.0
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/routers/admin.py backend/app/main.py backend/requirements.txt
git commit -m "feat: add admin API routes and dependencies"
```

---

## Task 7: 添加定时清理任务

**Files:**
- Create: `backend/app/tasks/scheduler.py`
- Modify: `backend/app/main.py` - 启动定时任务

**Interfaces:**
- Consumes: `AdminService.cleanup_old_logs()` 方法
- Produces: 定时任务启动和管理

- [ ] **Step 1: 创建定时任务**

Create `backend/app/tasks/scheduler.py`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.services.admin_service import AdminService
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def cleanup_old_audit_logs():
    """清理过期的审计日志"""
    db = SessionLocal()
    try:
        deleted = AdminService.cleanup_old_logs(db)
        logger.info(f"Cleaned up {deleted} old audit logs")
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
    finally:
        db.close()

def start_scheduler():
    """启动定时任务调度器"""
    # 每天凌晨 2 点执行清理
    scheduler.add_job(
        cleanup_old_audit_logs,
        CronTrigger(hour=2, minute=0),
        id="cleanup_old_logs",
        name="Cleanup old audit logs",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")

def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
```

- [ ] **Step 2: 创建 tasks 目录的 __init__.py**

```bash
touch backend/app/tasks/__init__.py
```

- [ ] **Step 3: 修改 main.py 启动定时任务**

修改 `backend/app/main.py`，在应用启动时添加：

```python
from contextlib import asynccontextmanager
from app.tasks.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    start_scheduler()
    yield
    # 关闭时
    stop_scheduler()

app = FastAPI(lifespan=lifespan)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/tasks/scheduler.py backend/app/tasks/__init__.py backend/app/main.py
git commit -m "feat: add scheduled task for cleaning up old audit logs"
```

---

## Task 8: 更新认证系统支持 admin 角色

**Files:**
- Modify: `backend/app/routers/auth.py` - 登录时更新 last_login 和 login_count
- Modify: `backend/app/config.py` - 添加 admin 角色配置

**Interfaces:**
- Consumes: `User` 模型
- Produces: 登录时更新用户统计字段

- [ ] **Step 1: 修改 auth.py 登录端点**

修改 `backend/app/routers/auth.py`，在登录成功后添加：

```python
from datetime import datetime

# 在登录成功处理中添加
user.last_login = datetime.utcnow()
user.login_count = (user.login_count or 0) + 1
db.commit()
```

完整的登录路由应该看起来像这样（找到 POST /api/auth/login）：

```python
@router.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 更新登录统计
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.commit()
    
    # 生成 token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }
```

- [ ] **Step 2: 修改 config.py 添加 admin 角色**

修改 `backend/app/config.py`，添加：

```python
ALLOWED_ROLES = ["student", "teacher", "parent", "admin"]
```

- [ ] **Step 3: 修改注册端点禁止创建 admin 账户**

修改 `backend/app/routers/auth.py`，在注册端点确保只能创建非 admin 用户：

```python
# 在 register 路由中
new_user.role = "student"  # 注册只能创建学生账户
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/routers/auth.py backend/app/config.py
git commit -m "feat: update auth system to support admin role and login stats"
```

---

## Task 9: 数据库初始化脚本

**Files:**
- Create: `backend/scripts/create_admin.py` - 创建管理员账户脚本

**Interfaces:**
- Consumes: `User` 模型、数据库连接
- Produces: 创建管理员账户的可执行脚本

- [ ] **Step 1: 创建管理员脚本**

Create `backend/scripts/create_admin.py`:

```python
#!/usr/bin/env python3
"""
创建管理员账户的脚本

使用方法：
python scripts/create_admin.py <email> <password> [nickname]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import SessionLocal, init_db
from app.models.user import User
from app.security import get_password_hash
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
            password_hash=get_password_hash(password),
            nickname=nickname,
            role="admin",
            is_active=True,
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
```

- [ ] **Step 2: 创建 scripts 目录**

```bash
mkdir -p backend/scripts
touch backend/scripts/__init__.py
```

- [ ] **Step 3: 提交**

```bash
git add backend/scripts/create_admin.py backend/scripts/__init__.py
git commit -m "feat: add admin creation script"
```

---

## Task 10: 修复导入和数据库初始化

**Files:**
- Modify: `backend/app/database.py` - 导入 User 模型确保表存在
- Modify: `backend/app/models/__init__.py` - 完整的模型导入

**Interfaces:**
- Produces: 正确的数据库初始化和模型导入

- [ ] **Step 1: 修改 database.py**

修改 `backend/app/database.py`，确保 init_db 正确导入所有模型：

```python
def init_db():
    # 导入所有模型确保表被创建
    from app.models.user import User
    from app.models.note import Note
    from app.models.chat_session import ChatSession
    from app.models.chat_message import ChatMessage
    from app.models.wrong_item import WrongItem
    from app.models.wrong_review import WrongReview
    from app.models.study_plan import StudyPlan
    from app.models.plan_task import PlanTask
    from app.models.document import Document
    from app.models.quiz_session import QuizSession
    from app.models.question import Question
    from app.models.audit_log import AuditLog
    
    Base.metadata.create_all(bind=engine)
    
    # 执行迁移脚本
    with engine.connect() as conn:
        migration_file = Path(__file__).parent / "migrations" / "001_add_admin_tables.sql"
        if migration_file.exists():
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
                for statement in sql.split(';'):
                    if statement.strip():
                        try:
                            conn.execute(text(statement))
                        except Exception as e:
                            # 某些语句可能已执行过，忽略错误
                            pass
            conn.commit()
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/database.py
git commit -m "fix: ensure all models are imported during database initialization"
```

---

现在后端实现已完成！前端实现在另一个计划中。

