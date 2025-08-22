"""Wczytywanie pliku dm.conf (format key=value) do słownika."""
from __future__ import annotations

from pathlib import Path
import sys
from logger import error, warn
from constants import CONFIG_FILE_NAME


class Config:  # Prosta klasa mapująca plik key=value na słownik
    """Prosta mapa ustawień z pliku konfiguracyjnego.

    Jeśli podano env (DEV/UAT/PROD), podczas inicjalizacji wykonywana jest
    walidacja obecności wymaganych kluczy konfiguracyjnych. Pozwala to na
    wczesne wykrycie braków w pliku 'dm.conf'.
    """

    # Klucze wymagane niezależnie od środowiska
    BASE_REQUIRED_KEYS: list[str] = [
        "REMOTE_GIT_PATH",
        "PATH_TO_EXPORTPACKAGE",
        "PATH_TO_IMPORTPACKAGE",
        "PATH_TO_DEPLOYJOBS",
        "META_REPO",
        "APPSERVER",
        "DISPLAY",
        "BATCH_SERVER",
        "IS_BITBUCKET_SERVER",
        "BITBUCKET_API_TOKEN",
        "BITBUCKET_PROJECT_OR_WORKSPACE",
        "BITBUCKET_HOST",
        "DM_RUNTIME_BASE_DIR",
    ]

    # Szablony kluczy zależnych od środowiska (ENV zastępowane DEV/UAT/PROD)
    ENV_REQUIRED_KEY_TEMPLATES: list[str] = [
        "ENV_DEPLOY_USER",
        "ENV_SERVER_MACHINE",
        "ENV_SERVER_PORT",
        "ENV_DEPLOYEDJOBS_DIR",
        "ENV_META_PROFILE",
    ]

    def __init__(self, config_path: Path, env: str):  # Konstruktor wczytuje i waliduje konfigurację
        """Inicjalizuje konfigurację i waliduje kompletność dla środowiska.

        Parameters:
            config_path: Ścieżka do pliku konfiguracyjnego.
            env: Środowisko (DEV/UAT/PROD) – wymagane.
        Raises:
            SystemExit: Jeśli plik konfiguracyjny nie istnieje.
            ValueError: Jeśli env jest spoza dozwolonego zestawu lub brakuje kluczy.
        """
        allowed_envs = {"DEV", "UAT", "PROD"}
        env_up = env.upper()
        if env_up not in allowed_envs:  # Walidacja wartości env
            raise ValueError(f"Niepoprawne środowisko '{env}'. Dozwolone: {', '.join(sorted(allowed_envs))}")
        self._config: dict[str, str] = {}  # Wewnętrzny magazyn klucz->wartość
        if not config_path.is_file():
            error(
                f"Plik konfiguracyjny '{config_path}' nie został znaleziony.\nSkopiuj '{CONFIG_FILE_NAME}.template' do '{CONFIG_FILE_NAME}' i uzupełnij go."
            )
            sys.exit(1)
        with config_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):  # Pomijanie komentarzy
                    continue
                if "=" not in line:  # Walidacja formatu
                    warn(f"Pomijam linię bez '=': {line}")
                    continue
                key, value = line.split("=", 1)  # Podział na klucz i wartość
                self._config[key.strip()] = value.strip().strip('"')  # Zapis bez otaczających cudzysłowów
        self._validate_schema(env_up)  # Walidacja kompletności kluczy

    def _validate_schema(self, env: str) -> None:  # Prywatna metoda sprawdzająca wymagane klucze
        """Sprawdza obecność wymaganych kluczy i zgłasza ValueError przy brakach.

        Parameters:
            env: Środowisko (DEV/UAT/PROD)
        """
        required: list[str] = list(self.BASE_REQUIRED_KEYS)
        for tpl in self.ENV_REQUIRED_KEY_TEMPLATES:
            required.append(tpl.replace("ENV", env))
        missing = [k for k in required if k not in self._config or not self._config[k]]  # Brakujące
        empty_any = [k for k, v in self._config.items() if not v]  # Puste wartości
        problems: list[str] = []  # Kolekcja błędów
        if missing:
            problems.append("Brak wymaganych kluczy: " + ", ".join(missing))
        if empty_any:
            problems.append("Puste wartości dla kluczy: " + ", ".join(empty_any))
        if problems:
            raise ValueError("; ".join(problems))

    def get(self, key: str, default: str | None = None) -> str | None:
        """Zwraca wartość lub domyślną."""
        return self._config.get(key, default)

    def __contains__(self, key: str) -> bool: # Umożliwia idiom if "KLUCZ" in config
        return key in self._config

    def __repr__(self) -> str: # Pokaże listę dostępnych kluczy zamiast <Config object at 0x...>)
        return f"Config(keys={list(self._config)})"
