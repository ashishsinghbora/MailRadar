import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    celery_app = Celery(
        "mailradar",
        broker=settings.redis_url,
        backend=settings.redis_url
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
except Exception:
    celery_app = None


def dispatch_async_task(task_name: str, *args, **kwargs):
    if celery_app:
        try:
            return celery_app.send_task(task_name, args=args, kwargs=kwargs)
        except Exception as e:
            logger.warning(f"Could not dispatch via Celery ({e}); fallback to synchronous.")
    return None
