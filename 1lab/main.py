import asyncio
import subprocess
import sys
import os

async def main():
    print("Запуск сервера и клиента...")
    # Запускаем сервер в фоновом режиме
    server_process = subprocess.Popen([sys.executable, "server.py"])
    # Даём серверу время на запуск
    await asyncio.sleep(1)

    # Запускаем клиент
    client_process = subprocess.Popen([sys.executable, "client.py"])
    
    # Ждём завершения процессов
    await asyncio.gather(
        asyncio.to_thread(server_process.wait),
        asyncio.to_thread(client_process.wait)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
        sys.exit(1)
        