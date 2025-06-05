import os
import json
import asyncio
from datetime import datetime

class FileServer:
    def __init__(self, host='localhost', port=65432):
        self.host = host
        self.port = port
        self.root_dir = os.getcwd()
        self.file_data = {}
        self.update_file_data()

    def update_file_data(self):
        self.file_data = {}
        for root, dirs, files in os.walk(self.root_dir):
            relative_path = os.path.relpath(root, self.root_dir)
            self.file_data[relative_path] = {
                'files': files,
                'dirs': dirs
            }
        # Сохраняем данные в JSON-файл
        with open("file_structure.json", "w", encoding="utf-8") as f:
            json.dump(self.file_data, f, indent=4)

    async def handle_client(self, reader, writer):
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                message = data.decode().strip()

                if message.startswith("SET_DIR:"):
                    new_dir = message.split("SET_DIR:")[1]
                    if os.path.isdir(new_dir):
                        self.root_dir = new_dir
                        self.update_file_data()
                        writer.write(b"Directory changed\n")
                    else:
                        writer.write(b"Invalid directory\n")
                    await writer.drain()
                elif message == "GETDATA":
                    response = json.dumps(self.file_data).encode()
                    writer.write(response)
                    await writer.drain()
                else:
                    writer.write(b"Unknown command\n")
                    await writer.drain()
        except Exception as e:
            print(f"Ошибка обработки клиента: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"Сервер запущен на {self.host}:{self.port} в {datetime.now().strftime('%H:%M:%S')}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    server = FileServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Сервер остановлен пользователем")
    except Exception as e:
        print(f"Ошибка сервера: {e}")
        