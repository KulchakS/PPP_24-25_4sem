from fastapi import APIRouter, HTTPException, Body, Depends
from celery.result import AsyncResult

from app.celery_app.tasks import solve_traveling_salesperson
from app.celery_app.worker import celery_app # Для проверки статуса задачи, если нужно
from app.schemas.task_schemas import TSPTaskRequest, TSPTaskResponse

# Если у вас есть аутентификация из лаб 1/2, импортируйте и используйте ее
# from ..auth.dependencies import get_current_active_user # Пример
# from ..models.user_models import User # Пример

router = APIRouter(prefix="/api/v1") # Общий префикс для API v1

# --- ЗАГЛУШКИ ДЛЯ ЭНДПОИНТОВ ИЗ ЛАБОРАТОРНЫХ РАБОТ 1 и 2 ---
# Вам необходимо интегрировать сюда ваши существующие эндпоинты
# Например, эндпоинты для аутентификации, работы с пользователями, данными и т.д.

@router.get("/placeholder_lab1_lab2")
async def placeholder_endpoint():
    """
    Это заглушка. Замените ее и добавьте сюда эндпоинты 
    из ваших предыдущих лабораторных работ.
    """
    return {"message": "This is a placeholder for Lab 1 & 2 REST API functionality."}

# --- НОВЫЙ ЭНДПОИНТ ДЛЯ ЛАБОРАТОРНОЙ РАБОТЫ 3 ---

@router.post("/tsp/start_task", response_model=TSPTaskResponse)
async def start_tsp_task(
    task_request: TSPTaskRequest = Body(...),
    # current_user: User = Depends(get_current_active_user) # Если используете аутентификацию
):
    """
    Запускает задачу коммивояжера в Celery.
    Принимает `user_id` (для WebSocket уведомлений) и `points`.
    """
    # В реальном приложении user_id может браться из токена аутентифицированного пользователя
    # user_id_to_use = current_user.id 
    user_id_to_use = task_request.user_id # Пока берем из запроса

    if not user_id_to_use:
        raise HTTPException(status_code=400, detail="user_id is required.")

    # Запуск задачи Celery
    # .delay() это шорткат для .apply_async()
    celery_task = solve_traveling_salesperson.delay(user_id=user_id_to_use, points=task_request.points)
    
    task_id = celery_task.id
    
    return TSPTaskResponse(
        message="TSP task has been submitted.",
        task_id=task_id,
        # Можно добавить URL для проверки статуса через Celery backend, если это необходимо клиенту
        # status_url=f"/api/v1/tsp/task_status/{task_id}", 
        websocket_info=f"Connect to /ws/{user_id_to_use} for live updates."
    )

@router.get("/tsp/task_status/{task_id}")
async def get_tsp_task_status(task_id: str):
    """
    Возвращает статус задачи Celery по ее ID.
    Это стандартный способ проверки статуса через Celery.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    }
    if task_result.status == 'PROGRESS':
        response['progress'] = task_result.info.get('progress') if isinstance(task_result.info, dict) else task_result.info
    elif task_result.status == 'FAILURE':
        response['error_message'] = str(task_result.info) # Celery сохраняет исключение в info при ошибке

    return response

# Добавьте сюда другие эндпоинты, если они требуются по заданию или из предыдущих работ 