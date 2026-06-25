import logging
from app.database import SessionLocal
from app.services.admin_service import AdminService

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

def start_scheduler():
    """启动定时任务调度器"""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()
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

        return scheduler
    except ImportError:
        logger.warning("apscheduler not installed, scheduled cleanup disabled")
        return None

def stop_scheduler(scheduler):
    """停止定时任务调度器"""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
