import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)
SUBSCRIBERS_DB_PATH = DATA_DIR / "subscribers.db"

class SubscribersDatabase:
    def __init__(self):
        # print(f"[DEBUG] Путь к БД подписчиков: {SUBSCRIBERS_DB_PATH}")
        self.connection = sqlite3.connect(SUBSCRIBERS_DB_PATH)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self): # создание таблицы для хранения подписчиков, если её ещё нет
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE)""")

        self.connection.commit()

    def add_subscriber(self, chat_id): # добавление нового подписчика в базу данных, если его там ещё нет
        self.cursor.execute("""
        INSERT OR IGNORE
        INTO subscribers (chat_id)
        VALUES (?)""", (chat_id,))

        self.connection.commit()

        print(f"[INFO] Добавлен подписчик: {chat_id}")

    def get_all_subscribers(self): # получение списка всех подписчиков
        self.cursor.execute("""SELECT chat_id FROM subscribers""")

        rows = self.cursor.fetchall()

        return [row[0] for row in rows]

    def close(self): # закрытие соединения с базой данных
        self.connection.close()