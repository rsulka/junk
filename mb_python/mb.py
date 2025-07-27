import argparse
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from abc import ABC, abstractmethod

from typing import Any, Optional

import requests

# --- Klasy obsługi platform Bitbucket ---

class BitbucketPlatform(ABC):
    """Abstrakcyjna klasa bazowa dla platform Bitbucket."""
    def __init__(self, host: Optional[str], project_or_workspace: Optional[str], repo: str):
        self.host = host
        self.project_or_workspace = project_or_workspace
        self.repo = repo

    @abstractmethod
    def get_api_url(self) -> str:
        pass

    @abstractmethod
    def get_repo_url(self) -> str:
        pass

    @abstractmethod
    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:
        pass

    @abstractmethod
    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:
        pass

class BitbucketServerPlatform(BitbucketPlatform):
    """Obsługa Bitbucket Server."""
    def get_api_url(self) -> str:
        return f"https://{self.host}/rest/api/1.0/projects/{self.project_or_workspace}/repos/{self.repo}/pull-requests?state=OPEN&order=NEWEST"

    def get_repo_url(self) -> str:
        return f"ssh://git@{self.host}/{self.project_or_workspace}/{self.repo}.git"

    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:
        return pr_data.get("fromRef", {}).get("displayId")

    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:
        return any(r.get("approved") for r in pr_data.get("reviewers", []))

class BitbucketCloudPlatform(BitbucketPlatform):
    """Obsługa Bitbucket Cloud."""
    def get_api_url(self) -> str:
        return f"https://api.bitbucket.org/2.0/repositories/{self.project_or_workspace}/{self.repo}/pullrequests?state=OPEN&fields=%2Bvalues.participants"

    def get_repo_url(self) -> str:
        return f"git@bitbucket.org:{self.project_or_workspace}/{self.repo}.git"

    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:
        return pr_data.get("source", {}).get("branch", {}).get("name")

    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:
        return any(p.get("approved") for p in pr_data.get("participants", []))

# --- Funkcje pomocnicze ---

def load_config(config_path):
    """Wczytuje konfigurację z pliku i ustawia zmienne środowiskowe."""
    try:
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    value = value.strip().strip("'\"")
                    os.environ[key.strip()] = value
    except FileNotFoundError:
        print(f"BŁĄD: Plik konfiguracyjny '{config_path}' nie został znaleziony.")
        sys.exit(1)

def run_command(command, cwd=None):
    """Uruchamia polecenie systemowe i zwraca jego wynik."""
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True, cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"BŁĄD: Polecenie '{e.cmd}' zakończyło się błędem.\nStderr: {e.stderr.strip()}")
        sys.exit(1)

def resolve_conflict_manually(file, sources):
    """Pyta użytkownika o wybór gałęzi w przypadku konfliktu."""
    print(f" ! KONFLIKT: Plik '{file}' został zmodyfikowany w gałęziach: {sources}")
    while True:
        try:
            for i, src in enumerate(sources, 1):
                print(f"  {i}) {src}")
            prompt = f"Wybierz, z której gałęzi pobrać plik '{file}' {list(range(1, len(sources) + 1))}: "
            choice = int(input(prompt)) - 1
            if 0 <= choice < len(sources):
                return sources[choice]
            print("Nieprawidłowy wybór.")
        except ValueError:
            print("Proszę podać numer.")

# --- Główna logika ---

def main():
    """Główna funkcja programu."""
    parser = argparse.ArgumentParser(description="Narzędzie do łączenia zmian z pull requestów Bitbucket.")
    parser.add_argument("-r", "--repo", required=True, help="Nazwa repozytorium Bitbucket.")
    parser.add_argument("-a", "--approved-only", action="store_true", help="Pobieraj tylko zatwierdzone pull requesty.")
    parser.add_argument("-d", "--dest-dir", help="Katalog docelowy dla połączonych plików.")
    args = parser.parse_args()

    load_config(Path(".mb_config"))

    # --- Inicjalizacja platformy ---
    is_server = os.getenv("IS_BITBUCKET_SERVER", "false").lower() == "true"
    platform_class = BitbucketServerPlatform if is_server else BitbucketCloudPlatform
    platform = platform_class(
        host=os.getenv("BITBUCKET_HOST"),
        project_or_workspace=os.getenv("BITBUCKET_PROJECT_OR_WORKSPACE"),
        repo=args.repo
    )

    # --- Ustawienie katalogu docelowego ---
    merge_dir = Path(args.dest_dir) if args.dest_dir else Path.home() / f"{args.repo}_merged"
    if not args.dest_dir:
        print(f"Informacja: Katalog docelowy nie został podany. Używam domyślnego: {merge_dir}")

    if not shutil.which("git"):
        print("BŁĄD: Narzędzie 'git' nie jest zainstalowane.")
        sys.exit(1)

    # --- Krok 1: Pobieranie informacji o PR ---
    print("Krok 1: Pobieranie informacji o aktywnych pull requestach...")
    headers = {"Authorization": f"Bearer {os.getenv('BITBUCKET_API_TOKEN')}"}
    try:
        response = requests.get(platform.get_api_url(), headers=headers)
        response.raise_for_status()
        prs_data = response.json().get("values", [])
    except requests.RequestException as e:
        print(f"BŁĄD: Nie udało się pobrać danych z API Bitbucket: {e}")
        sys.exit(1)

    if args.approved_only:
        print("Informacja: Filtruję tylko zatwierdzone (approved) pull requesty.")
        prs_data = [pr for pr in prs_data if platform.is_pr_approved(pr)]

    branches = [b for pr in prs_data if (b := platform.get_branch_from_pr(pr))]
    if not branches:
        status = "ZATWIERDZONYCH" if args.approved_only else "otwartych"
        print(f"Nie znaleziono żadnych {status} pull requestów.")
        sys.exit(0)

    print("Znaleziono następujące gałęzie z otwartymi PR:\n - " + "\n - ".join(branches) + "\n")

    # --- Krok 2: Przygotowanie katalogu roboczego ---
    print("Krok 2: Przygotowywanie katalogu roboczego...")
    if merge_dir.exists():
        shutil.rmtree(merge_dir)
    run_command(f"git clone --quiet -b master {platform.get_repo_url()} {merge_dir}")

    # --- Krok 3: Analiza zmienionych plików ---
    print("Krok 3: Analiza zmienionych plików w każdej gałęzi...")
    file_branch_map = defaultdict(list)
    for branch in branches:
        print(f" - Przetwarzanie gałęzi: {branch}")
        run_command(f"git fetch --quiet origin {branch}", cwd=merge_dir)
        changed_files_str = run_command(f"git diff --name-only master origin/{branch}", cwd=merge_dir)
        for file in changed_files_str.splitlines():
            if file:
                file_branch_map[file].append(branch)

    # --- Krok 4: Scalanie plików i rozwiązywanie konfliktów ---
    print("\nKrok 4: Scalanie plików i rozwiązywanie konfliktów...")
    for file, sources in file_branch_map.items():
        if len(sources) == 1:
            branch_name = sources[0]
            print(f" > Zmiany w pliku '{file}' pochodzą tylko z gałęzi '{branch_name}'.")
        else:
            branch_name = resolve_conflict_manually(file, sources)

        check_exists_cmd = f"git cat-file -e origin/{branch_name}:{file}"
        file_exists = subprocess.run(check_exists_cmd, shell=True, cwd=merge_dir, capture_output=True).returncode == 0

        target_file_path = merge_dir / file
        if file_exists:
            print(f"   -> Stosuję zmiany dla '{file}' z gałęzi '{branch_name}'.")
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            content = run_command(f"git show origin/{branch_name}:{file}", cwd=merge_dir)
            target_file_path.write_text(content, encoding='utf-8', errors='surrogateescape')
        else:
            print(f"   -> Plik '{file}' został usunięty w '{branch_name}'. Usuwam go.")
            target_file_path.unlink(missing_ok=True)

    # --- Czyszczenie ---
    shutil.rmtree(merge_dir / ".git")

    print(f"\n{'='*69}\nZakończono! Połączone pliki znajdują się w katalogu: '{merge_dir}'\n{'='*69}")

if __name__ == "__main__":
    main()