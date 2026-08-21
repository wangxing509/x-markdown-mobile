# -*- coding: utf-8 -*-
"""
定时任务调度器：APScheduler 管理每日定时刷新（时间可在设置中修改）
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from settings_store import effective_schedule

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
_refresh_fn = None


def start_scheduler(refresh_fn):
    """启动定时调度器（读取 ~/.xmarkdown/settings.json 的 schedule）"""
    global _refresh_fn
    _refresh_fn = refresh_fn
    if scheduler.running:
        reschedule()
        return

    sched = effective_schedule()
    if not sched.get("enabled", True):
        print("  [调度] 定时刷新已关闭（可在设置中开启）")
        return

    scheduler.add_job(
        refresh_fn,
        trigger=CronTrigger(
            hour=sched.get("hour", 9),
            minute=sched.get("minute", 0),
            timezone="Asia/Shanghai",
        ),
        id="daily_refresh",
        name=f"每日 {sched.get('hour', 9):02d}:{sched.get('minute', 0):02d} 刷新",
        replace_existing=True,
    )

    scheduler.start()
    print(f"  [调度] 每日 {sched.get('hour', 9):02d}:{sched.get('minute', 0):02d} 自动刷新已就绪")


def reschedule():
    """设置变更后重新排程"""
    global _refresh_fn
    if not scheduler.running or _refresh_fn is None:
        return
    sched = effective_schedule()
    try:
        scheduler.remove_job("daily_refresh")
    except Exception:
        pass
    if not sched.get("enabled", True):
        print("  [调度] 定时刷新已关闭")
        return
    scheduler.add_job(
        _refresh_fn,
        trigger=CronTrigger(
            hour=sched.get("hour", 9),
            minute=sched.get("minute", 0),
            timezone="Asia/Shanghai",
        ),
        id="daily_refresh",
        name=f"每日 {sched.get('hour', 9):02d}:{sched.get('minute', 0):02d} 刷新",
        replace_existing=True,
    )
    print(f"  [调度] 已更新为每日 {sched.get('hour', 9):02d}:{sched.get('minute', 0):02d}")


def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
