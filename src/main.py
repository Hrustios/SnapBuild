from config_loader import load_competitors
from database import Database
from parser import PageParser
from diff_detector import DiffDetector
from telegram_bot import TelegramNotifier


def main():
    print("[INFO] Запуск сервиса мониторинга...\n")

    competitors = load_competitors()

    database = Database()
    database.create_tables()

    parser = PageParser()
    parser.start_browser()

    notifier = TelegramNotifier()

    total_changes = 0

    try:
        for competitor in competitors:
            competitor_name = competitor["name"]

            use_playwright = competitor.get(
                "use_playwright",
                False
            )

            print(
                f"\033[33m\n"
                f"[INFO] Обработка: "
                f"{competitor_name}\033[0m"
            )

            for original_url in competitor["urls"]:
                print(
                    f"[INFO] Проверка: "
                    f"{original_url}"
                )

                html, final_url = parser.fetch_page(
                    original_url,
                    use_playwright
                )

                if not html:
                    print(
                        "\033[31m[WARNING] "
                        "Страница не получена.\033[0m"
                    )

                    notifier.send_error(
                        competitor_name,
                        original_url,
                        "Страница не получена"
                    )

                    continue

                content, canonical_url = (
                    parser.extract_text(html)
                )

                if not content:
                    print(
                        "\033[31m[WARNING] "
                        "Не удалось извлечь текст.\033[0m"
                    )

                    notifier.send_error(
                        competitor_name,
                        original_url,
                        "Не удалось извлечь текст"
                    )

                    continue

                tracking_url = (
                    canonical_url
                    or final_url
                    or original_url
                )

                print(
                    f"[INFO] Final URL: "
                    f"{tracking_url}"
                )

                previous_snapshot = (
                    database.get_last_snapshot(
                        tracking_url
                    )
                )

                has_changes = (
                    DiffDetector.has_changes(
                        previous_snapshot,
                        content
                    )
                )

                if has_changes:
                    total_changes += 1

                    print(
                        "\033[32m[INFO] "
                        "Обнаружены изменения!"
                        "\033[0m"
                    )

                    changes = (
                        DiffDetector.get_changes(
                            previous_snapshot,
                            content
                        )
                    )

                    print("\nИзменения:")
                    print(changes[:500])

                    database.save_snapshot(
                        competitor_name,
                        tracking_url,
                        content
                    )

                    notifier.send_changes(
                        competitor_name,
                        tracking_url,
                        changes
                    )

                else:
                    print(
                        "[INFO] Изменений нет."
                    )

    finally:
        parser.stop_browser()
        database.close()

    if total_changes == 0:
        notifier.send_no_changes(
            len(competitors)
        )

    print("\n[INFO] Мониторинг завершён.")


if __name__ == "__main__":
    main()