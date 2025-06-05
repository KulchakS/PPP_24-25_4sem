import time
import random
import json
import uuid # Для генерации уникальных ID задач, если не используется ID от Celery напрямую для уведомлений

from app.celery_app.worker import celery_app
from app.core.config import REDISLITE_PATH # Путь к БД redislite
from redislite import Redislite # Для pub/sub

# Получаем экземпляр redislite для публикации сообщений
# Важно, чтобы это был тот же файл БД, что и для Celery broker/backend
rdb_publisher = Redislite(REDISLITE_PATH)

# Имя канала в Redis для уведомлений о задачах
# Можно сделать его динамическим, если нужно разделять по пользователям, но для начала общий
TASK_UPDATES_CHANNEL = "task_updates"

def publish_task_update(data):
    """Публикует обновление задачи в Redis канал."""
    try:
        rdb_publisher.publish(TASK_UPDATES_CHANNEL, json.dumps(data))
        # print(f"Published to {TASK_UPDATES_CHANNEL}: {data}") # для отладки
    except Exception as e:
        print(f"Error publishing task update: {e}")

@celery_app.task(bind=True)
def solve_traveling_salesperson(self, user_id: str, points: list):
    """
    Simulates solving the traveling salesperson problem.
    - user_id: to identify the user (and potentially their WebSocket channel).
    - points: list of points/cities (for example, just a count).
    """
    task_id = self.request.id
    print(f"Task {task_id} for user {user_id} started with {len(points)} points.")

    # 1. Оповещение о начале выполнения задачи
    start_message = {
        "user_id": user_id, # Добавляем user_id для маршрутизации в WebSocket менеджере
        "payload": {
            "status": "STARTED",
            "task_id": task_id,
            "message": "Задача коммивояжера запущена"
        }
    }
    publish_task_update(start_message)
    self.update_state(state='STARTED', meta={'task_id': task_id, 'user_id': user_id})

    total_steps = 100  # Имитация шагов решения
    current_distance = 0
    current_path = []

    for i in range(total_steps):
        time.sleep(random.uniform(0.1, 0.3))  # Имитация работы
        progress = int(((i + 1) / total_steps) * 100)
        
        # Обновляем состояние Celery для внутреннего отслеживания
        self.update_state(state='PROGRESS', meta={'progress': progress, 'task_id': task_id, 'user_id': user_id})
        
        # 2. Оповещение о прогрессе выполнения (каждые 10%)
        if progress % 10 == 0 or progress == 100:
            progress_message = {
                "user_id": user_id,
                "payload": {
                    "status": "PROGRESS",
                    "task_id": task_id,
                    "progress": progress
                }
            }
            publish_task_update(progress_message)
        
        # Имитация построения пути и подсчета расстояния
        if i % 5 == 0:
            current_path.append(random.randint(1, len(points) if len(points) > 0 else 10))
        current_distance += random.uniform(1, 10)

    # Имитация окончательного пути и расстояния
    final_path = current_path + [current_path[0]] if current_path else list(range(1, min(len(points) + 1, 5))) + [1]
    final_distance = round(current_distance, 2)

    # 3. Оповещение о завершении задачи
    completion_message = {
        "user_id": user_id,
        "payload": {
            "status": "COMPLETED",
            "task_id": task_id,
            "path": final_path,
            "total_distance": final_distance
        }
    }
    publish_task_update(completion_message)
    
    print(f"Task {task_id} completed. Path: {final_path}, Distance: {final_distance}")
    # Результат задачи, который будет сохранен в бэкенде Celery
    return {
        "task_id": task_id,
        "user_id": user_id,
        "status": "COMPLETED", 
        "path": final_path, 
        "total_distance": final_distance
    }

# Можно добавить другие задачи Celery, если необходимо 