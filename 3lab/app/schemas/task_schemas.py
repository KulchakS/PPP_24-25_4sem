from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field

# Базовая схема для всех WebSocket сообщений от сервера к клиенту
class WebSocketMessageBase(BaseModel):
    status: str
    task_id: str

class TaskStartedMessage(WebSocketMessageBase):
    status: str = Field("STARTED", const=True)
    message: str

class TaskProgressMessage(WebSocketMessageBase):
    status: str = Field("PROGRESS", const=True)
    progress: int = Field(..., ge=0, le=100) # Прогресс от 0 до 100

class TaskCompletedMessage(WebSocketMessageBase):
    status: str = Field("COMPLETED", const=True)
    path: List[Union[int, str]] # Список узлов в пути
    total_distance: Union[int, float]

# Это объединение можно использовать для более строгой типизации при отправке/получении
# Однако FastAPI/WebSocket будет отправлять их как отдельные JSON
ServerTaskUpdateMessage = Union[TaskStartedMessage, TaskProgressMessage, TaskCompletedMessage]

# Схема для запроса на запуск задачи через REST API (пример)
class TSPTaskRequest(BaseModel):
    user_id: str # Идентификатор пользователя, для которого запускается задача
    points: List[Any] # В реальном приложении здесь будет более конкретный тип для точек
    # Например, List[Tuple[float, float]] для координат или List[str] для имен городов

# Схема для ответа от REST API при запуске задачи
class TSPTaskResponse(BaseModel):
    message: str
    task_id: str
    status_url: Optional[str] = None # URL для проверки статуса задачи через Celery (если нужно)
    websocket_info: Optional[str] = None # Информация о том, как подключиться к WebSocket 