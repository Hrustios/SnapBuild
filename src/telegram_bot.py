#region импорты библиотек и их модулей
import os, sys, time, threading, subprocess, schedule, requests
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes)
#endregion

# добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from subscribers import SubscribersDatabase

# загрузка .env из корня проекта
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

start_time = "10:00" #общая переменная времени

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    database = SubscribersDatabase()
    database.add_subscriber(chat_id)
    database.close()

    await update.message.reply_text(
        "✅ Ты подписан на SnapBuild.\n"
        f"Теперь я буду отправлять измененния страниц в {start_time} каждый день."
    )


def run_main_script():
    print("\n[INFO] Запуск ежедневного мониторинга...")
    print(f"[INFO] Время запуска: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Получаем пути
        src_dir = Path(__file__).parent
        project_dir = src_dir.parent
        main_path = src_dir / "main.py"
        
        # Меняем рабочую директорию на корень проекта
        os.chdir(project_dir)
        
        # print(f"[DEBUG] Рабочая директория: {os.getcwd()}")
        # print(f"[DEBUG] Запуск: {sys.executable} {main_path}")
        
        # Запускаем main.py
        result = subprocess.run([sys.executable, str(main_path)], check=True, cwd=str(project_dir),
            capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"\033[31m[STDERR] {result.stderr}\033[0m")
        
        print(f"\033[32m[INFO] Мониторинг завершён.\033[0m")
        print(f"[INFO] Время завершения: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    #region обработка исклчюений
    except subprocess.CalledProcessError as error:
        print(f"\033[31m[ERROR] Ошибка запуска main.py: {error}\033[0m")
        print(f"\033[31m[STDOUT] {error.stdout}\033[0m")
        print(f"\033[31m[STDERR] {error.stderr}\033[0m")
        
    except Exception as error:
        print(f"\033[31m[ERROR] Неожиданная ошибка: {error}\033[0m")
    #endregion

def scheduler_loop():
    # Настройка расписания
    
    schedule.every().day.at(start_time).do(run_main_script)
    
    print(f"\033[33m[SYS_INFO] Планировщик запущен. Ожидание {start_time}...\033[0m")
    print(f"[INFO] Текущее время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверка, не нужно ли запустить сразу, если уже больше 10:00
    current_time = time.strftime("%H:%M")
    if current_time >= start_time:
        print(f"\033[33m[INFO] Текущее время позже {start_time}, запускаю мониторинг сейчас...\033[0m")
        run_main_script()
    
    while True:
        schedule.run_pending()
        time.sleep(30)

#region запуск бота
def run_bot():
    if not BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env")
        return

    app = (ApplicationBuilder().token(BOT_TOKEN).build())

    app.add_handler(CommandHandler("start", start_command))
    print("\033[32m[INFO] Telegram bot запущен.\033[0m")

    app.run_polling()
#endregion

class TelegramNotifier:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        
    def _send_to_all(self, text):
        if not self.bot_token:
            print("\033[31m[ERROR] Учётные данные бота не найдены.\033[0m")
            return

        database = SubscribersDatabase()
        subscribers = database.get_all_subscribers()
        database.close()

        if not subscribers:
            print("\033[31m[WARNING] Нет подписчиков :(\033[0m")
            return

        for chat_id in subscribers:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"\033[32m[INFO] Отправлено: {chat_id}")
                else:
                    print(f"\033[31m[ERROR] Ошибка {chat_id}: {response.text}\033[0m")
            except Exception as error:
                print(f"\033[31m[ERROR] Ошибка отправки {chat_id}: {error}\033[0m")

    #region отправка изменений
    def send_changes(self, competitor, url, changes):
        message = (
            f"❗ <b>Изменения у {competitor}</b> ❗\n\n"
            f"📎 <a href='{url}'>{url}</a>\n\n"
            f"📌 Изменения:\n"
            f"<code>{changes[:3000]}</code>"
        )
        self._send_to_all(message)
    #endregion
    
    #region отправка ошибки мониторинга
    def send_error(self, competitor, url, error):
        message = (
            f"⚠ <b>Ошибка мониторинга</b>\n\n"
            f"🎯 {competitor}\n"
            f"📎 {url}\n\n"
            f"Ошибка:\n"
            f"<code>{error}</code>"
        )
        self._send_to_all(message)
    #endregion
    
    #region отправка отсутствия изменений
    def send_no_changes(self, competitors_count):
        message = (
            "✅ <b>Мониторинг завершён</b>\n\n"
            f"Проверено конкурентов: {competitors_count}\n"
            "Изменений не найдено."
        )
        self._send_to_all(message)
    #endregion

if __name__ == "__main__":
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запуск планировщика в основном потоке
    scheduler_loop()