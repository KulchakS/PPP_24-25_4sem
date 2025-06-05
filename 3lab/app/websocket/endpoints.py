from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Path, HTTPException
from starlette import status

from app.websocket.connection_manager import manager

# Здесь может быть ваша логика аутентификации для WebSocket
# Например, функция, которая проверяет токен, переданный в query_params или subprotocol
async def get_user_from_token(token: str = Depends(lambda query_param: query_param)):
    if not token: # Простейшая заглушка
        # В реальном приложении здесь будет проверка токена
        # raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        # Для лабораторной пока что можно просто использовать токен как user_id или требовать его наличие
        print("Warning: No token provided for WebSocket connection.")
        return None # или какой-то default user_id, если это допустимо
    # Предположим, что токен - это и есть user_id для простоты
    return token

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str = Path(..., title="User ID to connect with")
    # token: str = Depends(get_user_from_token) # Если используем аутентификацию по токену
):
    """
    WebSocket endpoint.
    Client connects to ws://<server>/ws/<user_id>
    user_id is used for routing messages from Celery tasks.
    """
    # if not token: # Если get_user_from_token возвращает None при отсутствии/невалидности токена
    #     await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    #     return
    # current_user_id = token # Если токен = user_id
    
    current_user_id = user_id # Используем user_id из пути

    await manager.connect(websocket, current_user_id)
    print(f"WebSocket connection established for user: {current_user_id}")
    try:
        while True:
            # Этот эндпоинт в основном для получения сообщений от сервера.
            # Клиент может отправлять сообщения, например, для подтверждения получения (ping/pong)
            # или для запроса каких-то действий, не связанных с Celery задачами.
            data = await websocket.receive_text() 
            # await websocket.receive_json() # если ожидаем JSON от клиента
            
            print(f"Received message from user {current_user_id}: {data}")
            # Пример ответа на сообщение клиента
            # await manager.send_personal_message(f"Server received your message: {data}", current_user_id)
            
            # Если клиент должен уметь запрашивать что-то через WebSocket:
            # try:
            #     message_data = json.loads(data)
            #     if message_data.get("action") == "ping":
            #         await manager.send_personal_message({"response": "pong"}, current_user_id)
            # except json.JSONDecodeError:
            #     await manager.send_personal_message({"error": "Invalid JSON"}, current_user_id)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {current_user_id}")
    except Exception as e:
        print(f"Error in WebSocket endpoint for user {current_user_id}: {e}")
        # Попытка закрыть соединение, если оно еще открыто и произошла ошибка
        if not websocket.client_state == websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        manager.disconnect(current_user_id)
        print(f"Cleaned up connection for user: {current_user_id}")

# Важно: менеджер соединений (manager) должен запускать свой Redis listener
# Это обычно делается при старте FastAPI приложения (lifespan event).
# И останавливать при завершении работы приложения. 