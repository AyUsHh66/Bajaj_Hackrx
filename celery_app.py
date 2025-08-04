# ==========================================================
# This is the complete and correct code for celery_app.py
# ==========================================================

# 1. Load variables from .env file FIRST. This is the most important step.
from dotenv import load_dotenv
load_dotenv()

# 2. Now that environment variables are loaded, import other modules.
from celery import Celery
from config import settings # 'settings' will now have the correct values.

# 3. Create the Celery app instance.
celery = Celery(
    "doc_processing_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks"]
)

celery.conf.update(
    task_track_started=True,
)