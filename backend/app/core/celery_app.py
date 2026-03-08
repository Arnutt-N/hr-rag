"""
Celery Configuration - Background Task Processing

Handles async tasks like:
- Document processing
- Embedding generation
- Report generation
- Email notifications
"""

import os
from celery import Celery
from celery.schedules import crontab

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

# Create Celery app
celery_app = Celery(
    "hr_rag",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.embedding_tasks",
        "app.tasks.report_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Bangkok",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task result settings
    result_expires=3600,  # 1 hour
    task_track_started=True,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Rate limiting
    task_annotations={
        "app.tasks.embedding_tasks.generate_embeddings": {
            "rate_limit": "10/m"
        }
    },
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_sessions",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "generate-daily-stats": {
            "task": "app.tasks.report_tasks.generate_daily_stats",
            "schedule": crontab(hour=0, minute=5),  # Daily at 00:05
        },
    },
)


def get_celery_app() -> Celery:
    """Get Celery application instance."""
    return celery_app
