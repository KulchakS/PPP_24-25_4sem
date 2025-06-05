from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def send_email_async(email: str, subject: str, body: str):
    # Пример асинхронной задачи (отправка email)
    print(f"Отправка email на {email}: {subject} - {body}")
    return True