"""Aktualizacja kodu modułu w lokalizacji wskazanej przez MDS.MODULY."""
from __future__ import annotations

from typing import Any

from constants import CODES_DIR_NAME, REPO_CODES_DIR_NAME
from config import Config
from logger import info, error
from sas_session import resolve_sas_cfg, open_sas_session
from ssh_executor import SSHExecutor, RemotePath

__all__ = ["update_module_code"]


def update_module_code(package_dir: RemotePath, config: Config, env: str, repo: str, ssh_executor: SSHExecutor) -> None:
    """Aktualizuje katalog kodu modułu według ścieżki z tabeli MDS.MODULY."""
    sas_session = None  # Uchwyt sesji
    target_path_str: str | None = None  # Docelowa ścieżka (string) odczytana z SAS
    try:
        sas_config_name = resolve_sas_cfg(env)
        info(f"Nawiązywanie połączenia SAS z konfiguracją: {sas_config_name}")
        sas_session = open_sas_session(env)
        info("Połączenie SAS nawiązane pomyślnie.")
        repo_lower = repo.lower()
        sas_code = f"""
            data _null_;
                set MDS.MODULY(where=(lowcase(MODUL) = '{repo_lower}'));
                call symputx('sciezka', trim(SCIEZKA_DO_MODULU));
                stop;
            run;
        """  # Kod SAS pobierający ścieżkę modułu z tabeli MDS.MODULY
        result = sas_session.submit(sas_code, results="TEXT")
        log_content = result.get("LOG", "")
        if "ERROR:" in log_content:
            error(
                "Wykryto błędy w logu SAS podczas pobierania ścieżki modułu."
            )
            raise RuntimeError("Błąd wykonania zapytania SAS o ścieżkę modułu.")
        raw_value: Any = sas_session.symget("sciezka")  # Odczyt makrozmiennej
        if raw_value is None:
            raise RuntimeError(
                f"Brak skonfigurowanej ścieżki dla modułu {repo} w tabeli MDS.MODULY."
            )
        if not isinstance(raw_value, str):  # Walidacja typu wartości
            raise TypeError(
                "Oczekiwano typu 'str' dla ścieżki modułu, otrzymano: "
                f"{type(raw_value).__name__}"
            )
        cleaned = raw_value.strip()
        if not cleaned:
            raise RuntimeError(
                f"Pusta ścieżka modułu {repo} po przetworzeniu wartości z SAS."
            )
        target_path_str = cleaned
        info(f"Pobrana ścieżka docelowa: {target_path_str}")
    except Exception as exc:
        error(
            f"Nie udało się pobrać ścieżki modułu z SAS. Szczegóły: {exc}."
        )
        raise
    finally:
        if sas_session:
            info("Zamykanie połączenia SAS")
            sas_session.endsas()
    source_dir = package_dir / CODES_DIR_NAME / REPO_CODES_DIR_NAME
    if not ssh_executor.exists(source_dir):
        info(
            f"Katalog źródłowy {source_dir} nie istnieje. Pomijanie wdrażania kodu modułu."
        )
        return
    target_path = RemotePath(target_path_str)  # Konwersja string -> RemotePath
    target_codes_dir = target_path / REPO_CODES_DIR_NAME
    info(f"Usuwanie istniejącego katalogu '{target_codes_dir}'.")
    ssh_executor.run_command(f"rm -rf {target_codes_dir}")
    info(f"Kopiowanie '{source_dir}' do '{target_path}'.")
    ssh_executor.run_command(
        f"cp -r {source_dir} {target_path}/"
    )
    info("Zakończono wdrażanie kodu modułu.")
