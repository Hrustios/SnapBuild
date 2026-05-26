import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "snapshots.db"

class Database:
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.connection.cursor()

    def create_tables(self):
        # Создание таблицы снапшотов если ещё не существует

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor TEXT NOT NULL,
            url TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP )
        """)

        self.connection.commit()
        print("[INFO] Таблица snapshots готова.")

    def save_snapshot(self, competitor, url, content):
        # Сохранение снапшота страницы
        self.cursor.execute("""
        INSERT INTO snapshots 
        (competitor, url, content )
        VALUES (?, ?, ?)""",
        (competitor, url, content))

        self.connection.commit()

        print(f"\033[32m[INFO] Снапшот сохранён: {competitor}\033[0m")

    def get_last_snapshot(self, url):
        # Получение последнего снапшота страницы
        self.cursor.execute("""
        SELECT content FROM snapshots WHERE url = ?
        ORDER BY id DESC LIMIT 1 """, (url,))

        result = self.cursor.fetchone()

        if result: 
            return result[0]

        return None

    def close(self):
        self.connection.close()