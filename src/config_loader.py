import yaml
from pathlib import Path

CONFIG_PATH = Path("config/competitors.yaml")

def load_competitors():
    # Загрузка списка конкурентов из YAML-конфига
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        competitors = config.get("competitors", [])

        print(f"[INFO] Загружено конкурентов: {len(competitors)}")

        return competitors

    except FileNotFoundError:
        print("\033[31m[ERROR] Файл competitors.yaml не найден.\033[0m")
        return []

    except yaml.YAMLError as error:
        print(f"\033[31m[ERROR] Ошибка YAML: {error}\033[0m")
        return []

    except Exception as error:
        print(f"\033[31m[ERROR] Непредвиденная ошибка: {error}\033[0m")
        return []