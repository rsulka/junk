import json
from pathlib import Path
from loguru import logger

def hello_world():
    """
    Funkcja wczytuje wiadomość z pliku konfiguracyjnego i ją loguje.
    """
    config_path = Path("config.json")
    try:
        logger.debug(f"Próba odczytu pliku konfiguracyjnego: {config_path.absolute()}")
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        message = config["message"]
        logger.info(f"Pomyślnie wczytano wiadomość: '{message}'")
        # Zamiast print(), używamy loggera, który wyświetli to na ekranie
        # i zapisze do pliku zgodnie z konfiguracją w cli.py
        print(message) # Możemy zostawić print, jeśli chcemy mieć czysty output na stdout

    except FileNotFoundError:
        logger.error(f"Nie znaleziono pliku konfiguracyjnego: {config_path.absolute()}")
    except Exception:
        logger.exception("Wystąpił nieoczekiwany błąd.")