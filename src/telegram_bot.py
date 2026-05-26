import asyncio
import os
import sys
import time
import threading
import subprocess
from pathlib import Path
import schedule
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from subscribers import SubscribersDatabase

# Загружаем .env из корня проекта
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat_id = update.effective_chat.id

    database = SubscribersDatabase()
    database.add_subscriber(chat_id)
    database.close()

    await update.message.reply_text(
        "✅ Ты подписан на SnapBuild.\n"
        "Теперь я буду получать обновления в 10:00 каждый день."
    )


def run_main_script():
    print("\n[INFO] Запускаю ежедневный мониторинг...")
    print(f"[INFO] Время запуска: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Получаем пути
        src_dir = Path(__file__).parent
        project_dir = src_dir.parent
        main_path = src_dir / "main.py"
        
        # Меняем рабочую директорию на корень проекта
        os.chdir(project_dir)
        
        print(f"[DEBUG] Рабочая директория: {os.getcwd()}")
        print(f"[DEBUG] Запуск: {sys.executable} {main_path}")
        
        # Запускаем main.py
        result = subprocess.run(
            [sys.executable, str(main_path)],
            check=True,
            cwd=str(project_dir),
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"[STDERR] {result.stderr}")
        
        print("[INFO] Мониторинг завершён.")
        print(f"[INFO] Время завершения: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    except subprocess.CalledProcessError as error:
        print(f"[ERROR] Ошибка запуска main.py: {error}")
        print(f"[STDOUT] {error.stdout}")
        print(f"[STDERR] {error.stderr}")
    except Exception as error:
        print(f"[ERROR] Неожиданная ошибка: {error}")


def scheduler_loop():
    # Настройка расписания
    start_time = "10:31"
    schedule.every().day.at(start_time).do(run_main_script)
    
    print(f"[INFO] Планировщик запущен. Ожидание {start_time}...")
    print(f"[INFO] Текущее время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверка, не нужно ли запустить сразу, если уже больше 10:00
    current_time = time.strftime("%H:%M")
    if current_time >= start_time:
        print(f"[INFO] Текущее время позже {start_time}, запускаю мониторинг сейчас...")
        run_main_script()
    
    while True:
        schedule.run_pending()
        time.sleep(30)


def run_bot():
    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env")
        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    print("[INFO] Telegram bot started.")

    app.run_polling()


class TelegramNotifier:
    def __init__(self):
        self.bot_token = BOT_TOKEN

    async def _send_to_all(self, text):
        if not self.bot_token:
            print("[ERROR] Telegram credentials not found.")
            return

        database = SubscribersDatabase()
        subscribers = database.get_all_subscribers()
        database.close()

        if not subscribers:
            print("[WARNING] Нет подписчиков.")
            return

        app = (
            ApplicationBuilder()
            .token(self.bot_token)
            .build()
        )

        await app.initialize()

        for chat_id in subscribers:
            try:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML"
                )
                print(f"[INFO] Отправлено: {chat_id}")
            except Exception as error:
                print(f"[ERROR] Ошибка отправки {chat_id}: {error}")

        await app.shutdown()

    def send_changes(self, competitor, url, changes):
        message = (
            f"🚨 <b>Изменения у {competitor}</b>\n\n"
            f"🔗 <a href='{url}'>{url}</a>\n\n"
            f"📌 Изменения:\n"
            f"<code>{changes[:3000]}</code>"
        )
        asyncio.run(self._send_to_all(message))

    def send_error(self, competitor, url, error):
        message = (
            f"⚠️ <b>Ошибка мониторинга</b>\n\n"
            f"🏢 {competitor}\n"
            f"🔗 {url}\n\n"
            f"Ошибка:\n"
            f"<code>{error}</code>"
        )
        asyncio.run(self._send_to_all(message))

    def send_no_changes(self, competitors_count):
        message = (
            "✅ <b>Мониторинг завершён</b>\n\n"
            f"Проверено конкурентов: {competitors_count}\n"
            "Изменений не найдено."
        )
        asyncio.run(self._send_to_all(message))
        

if __name__ == "__main__":
    # Запускаем бота и планировщик в отдельных потоках
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем планировщик в основном потоке
    scheduler_loop()