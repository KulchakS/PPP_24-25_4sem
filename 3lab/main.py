from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.endpoints import router as api_router
from app.websocket.endpoints import router as websocket_router
from app.websocket.connection_manager import manager as websocket_manager
# Импортируйте сюда конфигурацию базы данных и другие инициализации из Лаб 1/2, если необходимо
# from app.db.session import engine, Base # Пример

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при старте приложения
    print("FastAPI application starting up...")
    # Запуск прослушивателя Redis для WebSocket уведомлений
    await websocket_manager.start_redis_listener()
    
    # Если у вас есть база данных из Лаб 1/2, здесь можно создать таблицы (если не используются миграции Alembic)
    # try:
    #     Base.metadata.create_all(bind=engine)
    #     print("Database tables created or verified.")
    # except Exception as e:
    #     print(f"Error creating database tables: {e}")

    yield # Приложение работает здесь

    # Действия при завершении работы приложения
    print("FastAPI application shutting down...")
    # Остановка прослушивателя Redis
    await websocket_manager.stop_redis_listener()

# Создание экземпляра FastAPI приложения
app = FastAPI(
    title="Лабораторная работа №3 - API с WebSocket и Celery",
    description="Решение задачи коммивояжера с уведомлениями в реальном времени.",
    version="0.3.0",
    lifespan=lifespan # Подключение менеджера жизненного цикла
)

# Подключение роутеров
app.include_router(api_router, tags=["REST API"])
app.include_router(websocket_router, tags=["WebSocket"])

@app.get("/")
async def read_root():
    return {"message": "Добро пожаловать в API для Лабораторной работы №3!",
            "docs": "/docs",
            "redoc": "/redoc"}

# Для запуска приложения используйте Uvicorn:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
# Для запуска Celery воркера (в отдельном терминале, из папки 3lab/):
# celery -A app.celery_app.worker worker -l info -P eventlet # (для Windows можно gevent или solo)
# или
# celery -A app.celery_app.worker worker -l info # (если eventlet/gevent не нужны или вызывают проблемы)

