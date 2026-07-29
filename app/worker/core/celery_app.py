from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "rapidao_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    imports=["app.worker.tasks.order_tasks"],
)

# Auto-discover de tarefas na pasta app.worker.tasks
celery_app.autodiscover_tasks(["app.worker"])

celery_app.conf.beat_schedule = {
    "expire-stale-orders-every-5-minutes": {
        "task": "app.worker.tasks.order_tasks.expire_stale_orders",
        "schedule": crontab(minute="*/5"),
    },
}
