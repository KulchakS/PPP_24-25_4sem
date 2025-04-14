import os
import json
import socket
from threading import Thread

class FileServer:
    def __init__(self, host='localhost', port=65432):
        self.host = host
        self.port = port
        self.root_dir = os.getcwd()
        self.update_file_data()

    def update_file_data(self):
        self.file_data = {}
        for root, dirs, files in os.walk(self.root_dir):
            relative_path = os.path.relpath(root, self.root_dir)
            self.file_data[relative_path] = {
                'files': files,
                'dirs': dirs
            }

    def handle_client(self, conn):
        try:
            while True:
                data = conn.recv(1024).decode().strip()
                if not data:
                    break

                if data == 'GETDATA':
                    response = json.dumps(self.file_data).encode()
                    conn.sendall(response)
                
        finally:
            conn.close()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Сервер запущен на {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                Thread(target=self.handle_client, args=(conn,)).start()
                