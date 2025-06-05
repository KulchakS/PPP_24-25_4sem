from celery import Celery
from app.core import config

# Создание экземпляра Celery
# Имя 'app.celery_app' здесь используется для именования воркера, можно изменить
celery_app = Celery(
    __name__, # Можно заменить на имя вашего проекта, например 'lab3_project'
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=config.CELERY_INCLUDE_TASKS
)

# Конфигурация Celery из объекта config
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Тут можно добавить 'pickle', если нужно передавать сложные объекты
    result_serializer='json',
    timezone='Europe/Moscow', # Укажите ваш часовой пояс
    enable_utc=True,
    broker_connection_retry_on_startup=True, # Пытаться переподключиться к брокеру при старте
)

# Пример простой задачи для проверки, что Celery работает
@celery_app.task(name="debug_task")
def debug_task():
    print("Debug task executed")
    return "Debug task completed"

if __name__ == '__main__':
    # Эта часть для запуска воркера Celery напрямую (например, для отладки)
    # В продакшене вы будете запускать его командой: celery -A app.celery_app.worker worker -l info
    celery_app.start([
        'worker',
        '-l', 'info', # Уровень логирования (debug, info, warning, error, critical, fatal)
        # '-Q', 'default', # Можно указать очередь, если используете несколько
        # '-c', '1' # Количество параллельных воркеров (процессов)
    ]) 