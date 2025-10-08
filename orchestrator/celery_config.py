from celery import Celery

# --- Celery Configuration ---
# We use Redis as both the message broker and the result backend.
# The broker URL points to a local Redis instance.
# The backend URL is where Celery stores the status and results of tasks.

# Use the explicit IPv4 loopback address to avoid network resolution issues.
CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

# Create a Celery instance.
# The first argument is the name of the current module.
# The 'include' argument tells Celery to look for tasks in the 'orchestrator.tasks' module.
celery_app = Celery(
    "orchestrator",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["orchestrator.tasks"]
)

# Optional: Configure Celery settings for more robustness.
# In this environment (no Redis), we use 'eager' mode to run tasks synchronously.
celery_app.conf.update(
    task_always_eager=True,          # Core setting: Run tasks locally, no broker needed.
    task_eager_propagates=True,      # Makes debugging easier by raising task exceptions.
    task_track_started=True,
    worker_hijack_root_logger=False,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

# To run a Celery worker from the project root, you would use the command:
# celery -A orchestrator.celery_config.celery_app worker --loglevel=info