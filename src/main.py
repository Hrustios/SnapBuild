from config_loader import load_competitors
from database import Database
from parser import PageParser
from diff_detector import DiffDetector

def main():
    print("[INFO] Запуск сервиса мониторинга...\n")

    competitors = load_competitors()

    database = Database()
    database.create_tables()

    parser = PageParser()
    parser.start_browser()

    try:
        for competitor in competitors:
            competitor_name = competitor["name"]

            use_playwright = competitor.get("use_playwright",False)

            print(f"\033[33m\n[INFO] Обработка: {competitor_name}\033[0m")

            for original_url in competitor["urls"]:
                print(f"[INFO] Проверка: {original_url}")

                html, final_url = parser.fetch_page(original_url, use_playwright)

                if not html:
                    print("\033[31m[WARNING] Страница не получена.\033[0m")
                    continue

                content, canonical_url = (
                    parser.extract_text(html)
                )

                if not content:
                    print("\033[31m[WARNING] Не удалось извлечь текст.\033[0m")
                    continue

                tracking_url = (canonical_url or final_url or original_url)

                print(f"[INFO] Конечный URL страницы: {tracking_url}") # Конечный URL страницы нужен, потому что например Replit пересылает на url по дате последнего changelog'а

                previous_snapshot = (database.get_last_snapshot(tracking_url))

                has_changes = (DiffDetector.has_changes(previous_snapshot, content))

                if has_changes:
                    print("\033[32m[INFO] Обнаружены изменения!\033[0m")

                    changes = (DiffDetector.get_changes(previous_snapshot, content))

                    print("\nИзменения:")
                    print(changes[:500])

                    database.save_snapshot(competitor_name, tracking_url, content)

                else:
                    print("[INFO] Изменений нет.")

    finally:
        parser.stop_browser()
        database.close()

    print("\n[INFO] Мониторинг завершён.")

if __name__ == "__main__":
    main()