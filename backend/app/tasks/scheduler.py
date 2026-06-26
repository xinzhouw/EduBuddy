import logging
from app.database import SessionLocal
from app.services.admin_service import AdminService
from app.utils.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)

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

def cleanup_rate_limiter_entries():
    """清理过期的速率限制条目"""
    try:
        limiter = get_rate_limiter()
        deleted = limiter.cleanup_expired_entries(max_age_seconds=3600)  # 1 小时
        logger.info(f"Cleaned up {deleted} expired rate limiter entries")
    except Exception as e:
        logger.error(f"Error cleaning up rate limiter entries: {e}")

def start_scheduler():
    """启动定时任务调度器"""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()
        # 每天凌晨 2 点执行审计日志清理
        scheduler.add_job(
            cleanup_old_audit_logs,
            CronTrigger(hour=2, minute=0),
            id="cleanup_old_logs",
            name="Cleanup old audit logs",
            replace_existing=True
        )
        # 每小时执行速率限制条目清理
        scheduler.add_job(
            cleanup_rate_limiter_entries,
            CronTrigger(minute=0),
            id="cleanup_rate_limiter",
            name="Cleanup rate limiter entries",
            replace_existing=True
        )

        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started")

        return scheduler
    except ImportError:
        logger.warning("apscheduler not installed, scheduled cleanup disabled")
        return None

def stop_scheduler(scheduler):
    """停止定时任务调度器"""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
