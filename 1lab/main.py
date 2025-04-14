def main():
    print("Выберите режим работы:")
    print("1 - Запустить сервер")
    print("2 - Запустить клиент")
    
    choice = input("Введите номер: ")
    
    if choice == '1':
        from server import FileServer
        server = FileServer()
        server.start()
    elif choice == '2':
        from client import FileClient
        client = FileClient()
        try:
            client.run_interactive()
        finally:
            client.close()
    else:
        print("Неверный выбор")

if __name__ == "__main__":
    main()
