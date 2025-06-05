import asyncio
import json
import uuid
import argparse

import aiohttp
import websockets

# Адрес сервера FastAPI
SERVER_URL = "http://127.0.0.1:8000"
# WebSocket URL (строится динамически на основе user_id)
WS_SERVER_BASE_URL = "ws://127.0.0.1:8000/ws"

# Словарь для хранения активных WebSocket соединений и задач, которые они отслеживают
# {user_id: {"ws": websocket_connection, "tasks": {task_id: callback_or_info}}}
active_ws_connections = {}

async def listen_to_websocket(user_id: str, ws_url: str):
    """Подключается к WebSocket и слушает сообщения для указанного user_id."""
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"[WebSocket Client - User {user_id}] Подключен к {ws_url}")
            active_ws_connections[user_id] = {"ws": websocket, "tasks": {}}
            while True:
                try:
                    message_str = await websocket.recv()
                    message = json.loads(message_str)
                    task_id = message.get("task_id", "N/A")
                    status = message.get("status", "N/A")
                    
                    print(f"\n[WebSocket - User {user_id} - Task {task_id}] Получено обновление:")
                    if status == "STARTED":
                        print(f"  Статус: {status} - {message.get('message')}")
                    elif status == "PROGRESS":
                        print(f"  Статус: {status} - Прогресс: {message.get('progress')}%")
                    elif status == "COMPLETED":
                        print(f"  Статус: {status}")
                        print(f"    Путь: {message.get('path')}")
                        print(f"    Дистанция: {message.get('total_distance')}")
                        # Здесь можно убрать задачу из отслеживаемых или закрыть соединение, если оно для одной задачи
                    else:
                        print(f"  Неизвестный формат: {message}")
                    print("Введите команду (например, 'start_tsp <user_id> <num_points>' или 'exit'): ", end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print(f"[WebSocket Client - User {user_id}] Соединение закрыто сервером.")
                    break
                except json.JSONDecodeError:
                    print(f"[WebSocket Client - User {user_id}] Ошибка декодирования JSON: {message_str}")
                except Exception as e:
                    print(f"[WebSocket Client - User {user_id}] Ошибка в цикле WebSocket: {e}")
                    break
    except websockets.exceptions.InvalidURI:
        print(f"[WebSocket Client - User {user_id}] Неверный URI для WebSocket: {ws_url}")
    except ConnectionRefusedError:
        print(f"[WebSocket Client - User {user_id}] Не удалось подключиться к WebSocket серверу {ws_url}. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"[WebSocket Client - User {user_id}] Не удалось подключиться к WebSocket: {e}")
    finally:
        if user_id in active_ws_connections:
            del active_ws_connections[user_id]
        print(f"[WebSocket Client - User {user_id}] Прослушивание завершено.")

async def start_tsp_task_api(user_id: str, num_points: int):
    """Отправляет запрос на запуск TSP задачи через REST API."""
    api_url = f"{SERVER_URL}/api/v1/tsp/start_task"
    payload = {
        "user_id": user_id,
        "points": list(range(1, num_points + 1)) # Генерируем простой список точек
    }
    # Placeholder для токена аутентификации, если он нужен
    # headers = {"Authorization": "Bearer your_jwt_token"}
    headers = {}

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    task_id = data.get("task_id")
                    print(f"[API Client] Задача TSP успешно отправлена. Task ID: {task_id}")
                    print(f"[API Client] {data.get('websocket_info')}")
                    return task_id
                else:
                    error_data = await response.text()
                    print(f"[API Client] Ошибка при отправке задачи: {response.status} - {error_data}")
                    return None
    except aiohttp.ClientConnectorError:
        print(f"[API Client] Не удалось подключиться к API серверу {api_url}. Убедитесь, что сервер запущен.")
        return None
    except Exception as e:
        print(f"[API Client] Ошибка при вызове API: {e}")
        return None

async def main_client_loop():
    """Главный цикл интерактивного консольного клиента."""
    print("Консольный клиент для Лабораторной работы №3")
    print("Доступные команды:")
    print("  start_tsp <user_id> <num_points> - Запустить новую TSP задачу")
    print("  connect_ws <user_id>             - Подключиться к WebSocket для user_id (если еще не активно)")
    print("  exit                               - Выход")
    print("--- Аутентификация (заглушка) ---")
    print("Предполагается, что user_id используется как идентификатор клиента.")
    print("В реальном приложении здесь был бы механизм получения токена.")
    print("----------------------------------")

    loop = asyncio.get_running_loop()
    listener_tasks = {}

    while True:
        try:
            command_input = await loop.run_in_executor(None, lambda: input("Введите команду: "))
            parts = command_input.strip().split()
            if not parts:
                continue

            action = parts[0].lower()

            if action == "exit":
                print("Завершение работы клиента...")
                break
            elif action == "start_tsp":
                if len(parts) == 3:
                    user_id_to_start = parts[1]
                    try:
                        num_points_to_start = int(parts[2])
                        if num_points_to_start <= 0:
                            print("Количество точек должно быть положительным числом.")
                            continue
                        
                        task_id = await start_tsp_task_api(user_id_to_start, num_points_to_start)
                        if task_id:
                            # Автоматически подключаемся к WebSocket для этого user_id, если еще не слушаем
                            if user_id_to_start not in listener_tasks or listener_tasks[user_id_to_start].done():
                                ws_url_dynamic = f"{WS_SERVER_BASE_URL}/{user_id_to_start}"
                                print(f"Автоматическое подключение к WebSocket для user_id: {user_id_to_start} ({ws_url_dynamic})")
                                listener_tasks[user_id_to_start] = asyncio.create_task(listen_to_websocket(user_id_to_start, ws_url_dynamic))
                            else:
                                print(f"Уже прослушивается WebSocket для user_id: {user_id_to_start}")
                    except ValueError:
                        print("Неверное количество точек. Введите целое число.")
                else:
                    print("Использование: start_tsp <user_id> <num_points>")
            
            elif action == "connect_ws":
                if len(parts) == 2:
                    user_id_to_connect = parts[1]
                    if user_id_to_connect not in listener_tasks or listener_tasks[user_id_to_connect].done():
                        ws_url_dynamic = f"{WS_SERVER_BASE_URL}/{user_id_to_connect}"
                        print(f"Подключение к WebSocket для user_id: {user_id_to_connect} ({ws_url_dynamic})")
                        listener_tasks[user_id_to_connect] = asyncio.create_task(listen_to_websocket(user_id_to_connect, ws_url_dynamic))
                    else:
                        print(f"Уже прослушивается WebSocket для user_id: {user_id_to_connect}")
                else:
                    print("Использование: connect_ws <user_id>")
            else:
                print(f"Неизвестная команда: {action}")
        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение работы клиента (Ctrl+C или EOF)...")
            break
        except Exception as e:
            print(f"Произошла ошибка в главном цикле: {e}")

    # Остановка всех активных задач прослушивания WebSocket
    for user_id, task in listener_tasks.items():
        if not task.done():
            print(f"Остановка WebSocket listener для user_id: {user_id}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"WebSocket listener для user_id {user_id} успешно остановлен.")
            except Exception as e:
                print(f"Ошибка при остановке WebSocket listener для user_id {user_id}: {e}")
    print("Клиент завершил работу.")

async def run_script_from_file(filepath: str):
    # TODO: Реализовать выполнение команд из файла, если это требуется по заданию
    # "Добавить поддержку выполнения скрипта из файла"
    print(f"Запуск команд из файла: {filepath} (не реализовано в этом скелете)")
    # Примерная логика:
    # try:
    #     with open(filepath, 'r') as f:
    #         for line in f:
    #             command = line.strip()
    #             if command and not command.startswith('#'): # пропуск пустых строк и комментариев
    #                 print(f">>> {command}")
    #                 # Здесь нужно будет адаптировать обработку команд из main_client_loop
    #                 # Это может потребовать рефакторинга обработчика команд
    #                 await process_command(command) # Нужна функция process_command
    # except FileNotFoundError:
    #     print(f"Файл скрипта не найден: {filepath}")
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Консольный клиент для Лабораторной работы №3.")
    parser.add_argument(
        "--script_file", 
        type=str, 
        help="Путь к файлу со скриптом команд для выполнения.",
        required=False
    )
    # Можно добавить другие аргументы, например, user_id по умолчанию или URL сервера

    args = parser.parse_args()

    try:
        if args.script_file:
            asyncio.run(run_script_from_file(args.script_file))
        else:
            asyncio.run(main_client_loop())
    except KeyboardInterrupt:
        print("\nКлиент принудительно завершен.") 