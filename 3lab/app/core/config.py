import os
from redislite import Redislite

# Путь к файлу redislite, который будет использоваться Celery
# Он будет создан в корне проекта 3lab/
REDISLITE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "celery_redislite.db"))

# Инициализация redislite, если файл еще не существует (Celery также это сделает)
# Это просто для уверенности, что путь корректный и redislite доступен
try:
    rdb = Redislite(REDISLITE_PATH)
    print(f"Redislite DB for Celery will be at: {REDISLITE_PATH}")
except Exception as e:
    print(f"Error initializing Redislite for config: {e}")

# URL для брокера Celery (используем redislite)
CELERY_BROKER_URL = f"redis+socket://{REDISLITE_PATH}"

# URL для бэкенда Celery (используем redislite для хранения результатов)
CELERY_RESULT_BACKEND = f"redis+socket://{REDISLITE_PATH}"

# Список модулей с задачами Celery для автообнаружения
CELERY_INCLUDE_TASKS = ['app.celery_app.tasks']

# Настройки FastAPI, если нужны (например, для JWT, базы данных из лаб 1/2)
# SECRET_KEY = "your-secret-key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
# DATABASE_URL = "sqlite:///./your_app.db" # Замените на вашу БД из лаб 1/2

# WebSocket settings
WEBSOCKET_MAX_SIZE = None # Or some integer value like 2**20 (1MB)
WEBSOCKET_MAX_QUEUE = 32
WEBSOCKET_READ_LIMIT = 2**16
WEBSOCKET_WRITE_LIMIT = 2**16 