"""
Celery 配置
异步任务队列配置，用于处理耗时的后台任务（PDF导出、批量操作等）
"""
from celery import Celery
from kombu import Queue

from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "ai_english_teaching",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.report_tasks"]
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化方式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 结果过期时间（24小时）
    result_expires=86400,

    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务执行配置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # worker 丢失时重新入队
    worker_prefetch_multiplier=1,  # 一次只取一个任务

    # 重试配置
    task_default_retry_delay=60,  # 默认重试延迟（秒）
    task_max_retries=3,  # 最大重试次数

    # 队列配置
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "reports": {
            "exchange": "reports",
            "routing_key": "report",
        },
        "exports": {
            "exchange": "exports",
            "routing_key": "export",
        },
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # 任务路由 - 将报告相关任务路由到专用队列
    task_routes={
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },

    # Beat 调度配置（定时任务）
    beat_schedule={
        "cleanup-expired-tasks": {
            "task": "app.tasks.report_tasks.cleanup_expired_tasks",
            "schedule": 3600.0,  # 每小时执行一次
            "options": {"queue": "default"},
        },
    },
)

# 任务命名空间 - 避免与其他应用的任务冲突
celery_app.conf.namespace = "celery"


def get_celery_app() -> Celery:
    """获取 Celery 应用实例"""
    return celery_app
