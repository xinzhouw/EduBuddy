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
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                    "login_count": u.login_count,
                    "created_at": u.created_at.isoformat() if u.created_at else None
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

        # 计算登录统计（最近 7 天）
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
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "login_count": user.login_count,
            "login_7d": login_7d,
            "created_at": user.created_at.isoformat() if user.created_at else None,
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
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
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
