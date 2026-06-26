from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin", tags=["管理后台"])

def require_admin(current_user: User = Depends(get_current_user)):
    """验证用户是否为管理员"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return current_user

@router.get("/users")
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
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
    return {"code": 200, "data": {"success": True}}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户"""
    if not AdminService.delete_user(db, user_id):
        raise HTTPException(status_code=400, detail="无法删除此用户")
    return {"code": 200, "data": {"success": True}}

@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = Query(None),
    feature: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
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
