"""Moduł CLI dla aplikacji Hello World."""
import sys
from pathlib import Path
from loguru import logger
from .hello_world import hello_world

def setup_logging():
    """Skonfiguruj loguru, aby logował do konsoli i pliku."""
    # Upewnij się, że katalog na logi istnieje
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger.remove()  # Usuń domyślną konfigurację
    logger.add(sys.stderr, level="INFO")
    logger.add(
        log_file,
        level="INFO",
        rotation="10 MB",    # Rotacja plików logów po osiągnięciu 10 MB
        retention="7 days",  # Przechowuj logi przez 7 dni
        backtrace=True,
        diagnose=True,
    )

def main():
    """Główna funkcja aplikacji."""
    setup_logging()
    logger.info("Aplikacja została uruchomiona.")
    hello_world()
    logger.info("Aplikacja zakończyła działanie.")
