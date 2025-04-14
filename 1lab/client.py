import socket
import json

class FileClient:
    def __init__(self, host='localhost', port=65432):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def get_file_structure(self):
        self.socket.sendall(b'GETDATA')
        data = self.socket.recv(65536)  # Максимальный размер данных
        return json.loads(data.decode())

    def display_structure(self, data, indent=0):
        for path, content in data.items():
            print(' ' * indent + f"[{path}]")
            for file in content['files']:
                print(' ' * (indent + 2) + file)

    def run_interactive(self):
        structure = self.get_file_structure()
        print("\nСтруктура файлов:")
        self.display_structure(structure)

    def close(self):
        self.socket.close()
