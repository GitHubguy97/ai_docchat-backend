from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "ai-docchat",
    broker=f"redis://127.0.0.1:{settings.redis_port}/{settings.redis_db}",
    backend=f"redis://127.0.0.1:{settings.redis_port}/{settings.redis_db}",
    include=['app.tasks']  # Direct include
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)