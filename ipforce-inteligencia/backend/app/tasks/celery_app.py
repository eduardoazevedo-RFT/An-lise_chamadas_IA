from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ipforce",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.sync", "app.tasks.transcricao", "app.tasks.analise"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_routes={
        "app.tasks.sync.*": {"queue": "default"},
        "app.tasks.transcricao.*": {"queue": "transcricao"},
        "app.tasks.analise.*": {"queue": "analise"},
    },
    beat_schedule={
        "sync-cdr-5min": {
            "task": "app.tasks.sync.sync_cdr_ultimos_30min",
            "schedule": 300.0,  # 5 minutos
        },
        "resumo-diario": {
            "task": "app.tasks.analise.gerar_resumo_diario",
            "schedule": 3600.0,  # a cada hora (verifica se ja gerou hoje)
        },
    },
)
