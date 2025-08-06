"""
Celery application configuration for background task processing.

This file sets up the Celery distributed task queue for handling:
1. Document processing tasks in the background
2. Asynchronous file parsing and ingestion
3. SSL configuration for secure Redis connections

The Celery app is configured to:
- Use Redis as both message broker and result backend
- Handle SSL connections properly
- Track task execution status
- Include tasks from the tasks module

Environment variables are loaded first to ensure proper configuration.
"""

# celery_app.py

# 1. Load environment variables from .env file FIRST.
from dotenv import load_dotenv
load_dotenv()

# --- FIX: Import the ssl module ---
import ssl

# 2. Now import other modules that depend on those variables.
from celery import Celery
from config import settings

# 3. Create the Celery app instance.
celery = Celery(
    "doc_processing_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks"]
)

# --- FIX: Use the ssl.CERT_NONE constant instead of a string ---
# This tells Celery how to handle the secure connection correctly.
celery.conf.update(
    task_track_started=True,
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    }
)
# --------------------------------------------------------
