"""Aktualizacja słowników MDS na środowiskach innych niż DEV."""
from __future__ import annotations

import re
import shlex

from constants import (
    CODES_DIR_NAME,
    EXTRA_FILES_DIR_NAME,
    LOGS_DIR_NAME,
    LOG_UPDATE_DICTIONARIES,
)
from logger import info, warn, error
from sas_session import resolve_sas_cfg, open_sas_session
from ssh_executor import SSHExecutor, RemotePath
__all__ = ["update_dictionaries"]  # Publiczna funkcja modułu

def update_dictionaries(package_dir: RemotePath, env: str, ssh_executor: SSHExecutor) -> None:  # Aktualizacja słowników MDS
    """Aktualizuje słowniki MDS według plików CRISPR-*_mds.txt (poza DEV)."""
    if env == "DEV":
        info("Środowisko MDS DEV - brak działań.")
        return
    extra_files_dir = package_dir / CODES_DIR_NAME / EXTRA_FILES_DIR_NAME
    if not ssh_executor.exists(extra_files_dir):
        info(
            f"Katalog {extra_files_dir} nie istnieje. Pomijanie aktualizacji słowników MDS."
        )
        return
    try:
        ls_output = ssh_executor.run_command(f"ls -1 {shlex.quote(str(extra_files_dir))}")
        all_files = ls_output.stdout.strip().split("\n")  # Rozdział linii
    except Exception:
        warn(
            f"Nie udało się wylistować plików w {extra_files_dir}. Pomijanie."
        )
        return
    mds_files = [f for f in all_files if re.match(r"CRISPR-\d+_mds\.txt", f)]  # Filtr plików *_mds.txt
    if not mds_files:
        info("Brak plików _mds.txt do przetworzenia.")
        return
    sas_calls: list[str] = []  # Kolekcja wywołań makr
    id_pattern = re.compile(r"(CRISPR-\d+)_mds\.txt")  # Ekstrakcja identyfikatora CRISPR-123
    for filename in mds_files:  # Iteracja po plikach słownikowych
        match = id_pattern.match(filename)
        if not match:
            continue
        task_id = match.group(1)  # Id zadania CRISPR-xxx
        file_path = extra_files_dir / filename  # Pełna ścieżka zdalna
        info(f"Przetwarzanie pliku: {filename}")
        try:
            content = ssh_executor.read_file(file_path)
        except Exception:
            error(f"Nie udało się odczytać pliku {file_path}. Pomijanie.")
            continue
        dictionaries = [line.strip() for line in content.split("\n") if line.strip()]  # Lista nazw słowników
        if not dictionaries:
            info("  - Plik pusty, pomijanie.")
            continue
        for dictionary in dictionaries:  # Generowanie wywołań makr
            call = (
                f"%usr_zaktualizuj_slownik(slownik={dictionary}, id_zadania={task_id}, "
                f"srodowisko_docelowe={env});"
            )
            info(f"  - Dodano wywołanie: {call}")
            sas_calls.append(call)  # Dodanie do listy
    if not sas_calls:
        info("Nie wygenerowano wywołania makra.")
        return
    full_sas_code = "\n".join(sas_calls)  # Złożenie kodu SAS
    sas_config_name = resolve_sas_cfg(env)  # Konfiguracja saspy
    log_file = package_dir / LOGS_DIR_NAME / LOG_UPDATE_DICTIONARIES  # Ścieżka logu
    sas_session = None  # Uchwyt sesji SAS
    try:
        info(f"Nawiązywanie połączenia SAS z konfiguracją: {sas_config_name}")
        sas_session = open_sas_session(env)  # Start sesji
        info("Połączenie SAS nawiązane pomyślnie.")
        info("Wykonywanie skryptu aktualizacji słowników MDS")
        result = sas_session.submit(full_sas_code, results="TEXT")  # Uruchomienie makr
        log_content = result.get("LOG", "Nie udało się pobrać logu SAS.")  # Pobranie logu
        info(f"Zapisywanie logu SAS do: {log_file}")
        ssh_executor.write_file(log_file, log_content)  # Zapis logu do pliku
        if "ERROR:" in log_content:  # Detekcja błędów SAS
            error(
                "Wykryto błędy w logu SAS podczas aktualizacji słowników MDS."
            )
            raise RuntimeError("Błędy w wykonaniu skryptu aktualizacji słowników MDS.")
        info("Zakończono aktualizację słowników MDS.")
    except Exception as exc:  # Obsługa błędów procesu
        error(
            "Wykonanie skryptu aktualizacji słowników MDS nie powiodło się. "
            f"Szczegóły: {exc}."
        )
        raise
    finally:
        if sas_session:
            info("Zamykanie połączenia SAS")
            sas_session.endsas()
