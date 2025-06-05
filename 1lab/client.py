import socket
import json
import tkinter as tk
from tkinter import ttk, messagebox
import asyncio

class FileClient:
    def __init__(self, host='localhost', port=65432):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу")
            raise

        # Создаём графический интерфейс
        self.root = tk.Tk()
        self.root.title("Файловая структура")
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(expand=True, fill="both")

        # Поле для ввода директории
        self.dir_entry = tk.Entry(self.root)
        self.dir_entry.pack()
        self.dir_entry.insert(0, ".")
        tk.Button(self.root, text="Сменить директорию", command=self.change_dir).pack()

        # Обновляем дерево при запуске
        self.update_tree()

    def get_file_structure(self):
        try:
            self.socket.sendall(b"GETDATA")
            data = self.socket.recv(65536)
            return json.loads(data.decode())
        except (json.JSONDecodeError, socket.error) as e:
            messagebox.showerror("Ошибка", f"Не удалось получить данные: {e}")
            return {}

    def change_dir(self):
        new_dir = self.dir_entry.get().strip()
        try:
            self.socket.sendall(f"SET_DIR:{new_dir}".encode())
            response = self.socket.recv(1024).decode().strip()
            if "Invalid" not in response:
                self.update_tree()
            else:
                messagebox.showwarning("Предупреждение", "Неверная директория")
        except socket.error as e:
            messagebox.showerror("Ошибка", f"Ошибка смены директории: {e}")

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        structure = self.get_file_structure()
        for path, content in structure.items():
            parent = self.tree.insert("", "end", text=path)
            for file in content['files']:
                self.tree.insert(parent, "end", text=file)
            for directory in content['dirs']:
                self.tree.insert(parent, "end", text=f"[DIR] {directory}")

    def run(self):
        self.root.mainloop()

    def close(self):
        self.socket.close()
        self.root.quit()

if __name__ == "__main__":
    client = FileClient()
    try:
        client.run()
    finally:
        client.close()
        