"""Publiczne API procesu wdrożeniowego (moduł konsolidujący).

Dawna nazwa pliku: ``service.py`` (zachowana ewentualnie tymczasowo dla kompatybilności).

Moduł agreguje funkcje odpowiedzialne za:
- analizę PR i zbieranie zmienionych plików,
- budowanie pakietu wdrożeniowego,
- eksport / import metadanych SAS,
- operacje pre_deploy (bash / SAS),
- aktualizację kodu modułu,
- aktualizację słowników MDS,
- redeploy jobów.
"""
from __future__ import annotations

from pr_analysis import analyze_pull_requests  # Funkcja analizująca PR i zbierająca listę zmienionych plików
from packaging import build_package  # Budowanie pakietu wdrożeniowego na serwerze
from metadata import export_metadata, import_metadata  # Eksport / import metadanych SAS
from predeploy import run_predeploy_bash, run_predeploy_sas  # Uruchomienie skryptów pre_deploy (bash/SAS)
from code_update import update_module_code  # Aktualizacja kodu modułu wg ścieżki z MDS.MODULY
from dictionaries import update_dictionaries  # Aktualizacja słowników MDS (poza DEV)
from jobs import redeploy_jobs  # Redeploy zmodyfikowanych jobów

__all__ = [  # Publicznie eksportowane funkcje
    "analyze_pull_requests",
    "build_package",
    "export_metadata",
    "import_metadata",
    "run_predeploy_bash",
    "run_predeploy_sas",
    "update_module_code",
    "update_dictionaries",
    "redeploy_jobs",
]
