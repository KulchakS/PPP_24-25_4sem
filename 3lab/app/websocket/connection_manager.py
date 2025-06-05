import asyncio
import json
from typing import Dict, List, Union

from fastapi import WebSocket
from redislite import Redislite # type: ignore

from app.core.config import REDISLITE_PATH #, WEBSOCKET_MAX_SIZE, WEBSOCKET_MAX_QUEUE, WEBSOCKET_READ_LIMIT, WEBSOCKET_WRITE_LIMIT # Эти константы пока не используются в менеджере
from app.celery_app.tasks import TASK_UPDATES_CHANNEL # Импортируем имя канала

class ConnectionManager:
    def __init__(self):
        # Словарь для хранения активных соединений: {user_id: WebSocket}
        # Предполагаем одно активное соединение на пользователя для простоты
        # Для нескольких соединений на пользователя нужна будет структура List[WebSocket]
        self.active_connections: Dict[str, WebSocket] = {}
        self.rdb_subscriber = Redislite(REDISLITE_PATH)
        self.pubsub = self.rdb_subscriber.pubsub(
            ignore_subscribe_messages=True
        )
        self._redis_listener_task = None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        # Если уже есть соединение для этого пользователя, можно его закрыть или отклонить новое
        # if user_id in self.active_connections:
        #     await self.active_connections[user_id].close(code=status.WS_1008_POLICY_VIOLATION)
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            # Не вызываем websocket.close() здесь, т.к. соединение может быть уже закрыто клиентом
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Union[str, dict], user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                if isinstance(message, dict):
                    await websocket.send_json(message)
                else:
                    await websocket.send_text(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                # Можно добавить логику удаления соединения, если оно больше не валидно
                # self.disconnect(user_id)

    async def broadcast(self, message: Union[str, dict]):
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    async def _redis_listener_blocking_call(self):
        """Вспомогательный метод для блокирующего вызова get_message."""
        return self.pubsub.get_message(timeout=1.0) # Блокирующий вызов

    async def _redis_listener(self):
        """Слушает сообщения из Redis канала и рассылает их."""
        is_subscribed = False
        try:
            # Операция подписки синхронная
            await asyncio.to_thread(self.pubsub.subscribe, TASK_UPDATES_CHANNEL)
            is_subscribed = True
            print(f"Subscribed to Redis channel: {TASK_UPDATES_CHANNEL}")
            while True:
                # Выполняем блокирующий вызов в отдельном потоке
                message = await asyncio.to_thread(self._redis_listener_blocking_call)
                
                if message and message["type"] == "message":
                    print(f"Received from Redis: {message['data']}") 
                    try:
                        data = json.loads(message["data"]) 
                        user_id_to_send = data.get("user_id")
                        payload_to_send = data.get("payload")
                        if user_id_to_send and payload_to_send:
                            await self.send_personal_message(payload_to_send, user_id_to_send)
                        else:
                            print(f"Invalid message structure from Redis: {data}")
                    except json.JSONDecodeError:
                        print(f"Could not decode JSON from Redis message: {message['data']}")
                    except Exception as e:
                        print(f"Error processing message from Redis: {e}")
                await asyncio.sleep(0.01) 
        except asyncio.CancelledError:
            print("Redis listener task explicitly cancelled.")
            raise # Передаем исключение дальше, чтобы stop_redis_listener мог его поймать
        except Exception as e:
            print(f"Redis listener error: {e}")
        finally:
            if is_subscribed and self.pubsub.connection: # Проверяем, есть ли активное соединение
                try:
                    # Операция отписки также синхронная
                    await asyncio.to_thread(self.pubsub.unsubscribe, TASK_UPDATES_CHANNEL)
                    print("Unsubscribed from Redis channel.")
                except Exception as e_unsub:
                    print(f"Error unsubscribing from Redis: {e_unsub}")
            print("Redis listener stopped.")

    async def start_redis_listener(self):
        if self._redis_listener_task is None or self._redis_listener_task.done():
            self._redis_listener_task = asyncio.create_task(self._redis_listener())
            print("Redis listener task started.")
        else:
            print("Redis listener task is already running.")

    async def stop_redis_listener(self):
        if self._redis_listener_task and not self._redis_listener_task.done():
            self._redis_listener_task.cancel()
            try:
                await self._redis_listener_task
            except asyncio.CancelledError:
                print("Redis listener task cancelled successfully.")
            self._redis_listener_task = None
        
        # Дополнительная проверка и попытка отписаться, если задача была прервана до finally в _redis_listener
        if self.pubsub.subscribed and self.pubsub.connection:
            try:
                await asyncio.to_thread(self.pubsub.unsubscribe, TASK_UPDATES_CHANNEL)
                print("Ensured unsubscription from Redis channel on stop.")
            except Exception as e_unsub_stop:
                print(f"Error during final unsubscription attempt: {e_unsub_stop}")
        if self.pubsub.subscribed:
            await self.pubsub.unsubscribe(TASK_UPDATES_CHANNEL) # Убедимся, что отписались
        # self.pubsub.close() # redislite pubsub не имеет close, он управляется rdb_subscriber
        print("Redis listener stopped and unsubscribed.")

# Глобальный экземпляр менеджера
manager = ConnectionManager() 