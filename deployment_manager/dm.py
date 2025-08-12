import argparse
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Dict, Set

import requests
import re
import urllib3

# --- Stałe ---
LOCAL_REPO_DIR = Path("local_repo")
CONFIG_FILE_NAME = ".dm_config"

# Wyłącz ostrzeżenia o niezabezpieczonych żądaniach HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Konfiguracja ---

class Config:
    """Przechowuje konfigurację wczytaną z pliku."""
    def __init__(self, config_path: Path):
        if not config_path.exists():
            print(f"BŁĄD: Plik konfiguracyjny '{config_path}' nie został znaleziony.")
            print(f"Skopiuj 'mb_config.template' do '{CONFIG_FILE_NAME}' i uzupełnij go.")
            sys.exit(1)

        self.settings: Dict[str, str] = {}
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    self.settings[key.strip()] = value.strip().strip("'\"")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.settings.get(key, default)

# --- Klasy obsługi platform Bitbucket ---

class BitbucketPlatform(ABC):
    """Abstrakcyjna klasa bazowa dla platform Bitbucket."""
    def __init__(self, repo: str, token: str, project_or_workspace: str):
        self.repo = repo
        self.token = token
        self.project_or_workspace = project_or_workspace
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @abstractmethod
    def get_api_prs_url(self) -> str:
        pass

    @abstractmethod
    def get_clone_url(self) -> str:
        pass

    @abstractmethod
    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:
        pass

    @abstractmethod
    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:
        pass

class BitbucketServerPlatform(BitbucketPlatform):
    """Obsługa Bitbucket Server."""
    def __init__(self, repo: str, token: str, project_or_workspace: str, host: str):
        super().__init__(repo, token, project_or_workspace)
        self.host = host

    def get_api_prs_url(self) -> str:
        return f"https://{self.host}/rest/api/1.0/projects/{self.project_or_workspace}/repos/{self.repo}/pull-requests?state=OPEN&at=refs/heads/master"

    def get_clone_url(self) -> str:
        return f"git@{self.host}:{self.project_or_workspace.lower()}/{self.repo}.git"

    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:
        return pr_data.get("fromRef", {}).get("displayId")

    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:
        return any(r.get("approved") for r in pr_data.get("reviewers", []))

class BitbucketCloudPlatform(BitbucketPlatform):
    """Obsługa Bitbucket Cloud."""
    def get_api_prs_url(self) -> str:
        # Dodajemy pole 'participants', aby móc sprawdzić status zatwierdzenia
        return f"https://api.bitbucket.org/2.0/repositories/{self.project_or_workspace}/{self.repo}/pullrequests?state=OPEN&fields=%2Bvalues.participants"

    def get_clone_url(self) -> str:
        return f"git@bitbucket.org:{self.project_or_workspace}/{self.repo}.git"

    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:
        return pr_data.get("source", {}).get("branch", {}).get("name")

    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:
        return any(p.get("approved") for p in pr_data.get("participants", []))

# --- Funkcja fabrykująca ---

def create_platform(config: Config, repo: str) -> BitbucketPlatform:
    """Tworzy odpowiednią instancję platformy na podstawie konfiguracji."""
    is_server = config.get("IS_BITBUCKET_SERVER", "false").lower() == "true"
    token = config.get("BITBUCKET_API_TOKEN")
    project_or_workspace = config.get("BITBUCKET_PROJECT_OR_WORKSPACE")

    if not all([token, project_or_workspace]):
        print(f"BŁĄD: Zmienne BITBUCKET_API_TOKEN i BITBUCKET_PROJECT_OR_WORKSPACE muszą być ustawione w {CONFIG_FILE_NAME}.")
        sys.exit(1)

    if is_server:
        host = config.get("BITBUCKET_HOST")
        if not host:
            print(f"BŁĄD: Zmienna BITBUCKET_HOST musi być ustawiona dla Bitbucket Server w {CONFIG_FILE_NAME}.")
            sys.exit(1)
        print("Tryb: Bitbucket Server")
        return BitbucketServerPlatform(repo, token, project_or_workspace, host)
    
    print("Tryb: Bitbucket Cloud")
    return BitbucketCloudPlatform(repo, token, project_or_workspace)

# --- Funkcje pomocnicze ---

def run_command(command: str, cwd: Path) -> subprocess.CompletedProcess:
    """Uruchamia polecenie w powłoce, obsługuje błędy i zwraca wynik."""
    print(f"[{cwd}]$ {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas wykonywania polecenia: {command}\nStderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def get_pull_requests(platform: BitbucketPlatform) -> list:
    """Pobiera listę pull requestów z Bitbucket, obsługując paginację."""
    all_prs, url = [], platform.get_api_prs_url()
    while url:
        try:
            response = requests.get(url, headers=platform.headers, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            all_prs.extend(data.get("values", []))
            url = data.get("next")
        except requests.RequestException as e:
            print(f"BŁĄD: Nie udało się pobrać danych z API Bitbucket: {e}", file=sys.stderr)
            if e.response:
                print(f"Odpowiedź serwera: {e.response.text}", file=sys.stderr)
            sys.exit(1)
    return all_prs

def process_repository(platform: BitbucketPlatform, approved_only: bool) -> Set[str]:
    """Orkiestruje proces pobierania, klonowania i scalania PR. Zwraca zbiór zmienionych plików."""
    print(f"Sprawdzanie pull requestów dla repozytorium: {platform.repo}")
    active_prs = get_pull_requests(platform)

    if not active_prs:
        print("Brak aktywnych pull requestów do gałęzi master. Kończę pracę.")
        return set()

    if approved_only:
        print("Informacja: Filtruję tylko zatwierdzone (approved) pull requesty.")
        active_prs = [pr for pr in active_prs if platform.is_pr_approved(pr)]
        if not active_prs:
            print("Nie znaleziono żadnych ZATWIERDZONYCH pull requestów. Kończę pracę.")
            return set()

    print(f"Znaleziono {len(active_prs)} pull requestów do przetworzenia.")

    if LOCAL_REPO_DIR.exists():
        print(f"Usuwam istniejący katalog: {LOCAL_REPO_DIR}")
        shutil.rmtree(LOCAL_REPO_DIR)

    print("Klonowanie repozytorium...")
    run_command(f"git clone --branch master {platform.get_clone_url()} {LOCAL_REPO_DIR}", cwd=Path("."))

    changed_files: Set[str] = set()
    for pr in active_prs:
        branch = platform.get_branch_from_pr(pr)
        if not branch:
            continue
        
        pr_id = pr.get("id", "N/A")
        print(f"\n--- Scalanie PR #{pr_id}: gałąź '{branch}' ---")
        
        run_command(f"git fetch origin {branch}", cwd=LOCAL_REPO_DIR)
        
        diff_result = run_command(f"git diff --name-only master origin/{branch}", cwd=LOCAL_REPO_DIR)
        changed_files.update(diff_result.stdout.strip().splitlines())
        
        try:
            run_command(f"git merge origin/{branch} --no-edit", cwd=LOCAL_REPO_DIR)
            print(f"Gałąź '{branch}' została pomyślnie scalona.")
        except SystemExit:
            print(f"\n!!! KRYTYCZNY BŁĄD: Nie można scalić gałęzi '{branch}'.", file=sys.stderr)
            print("!!! Prawdopodobnie wystąpił konflikt scalania (merge conflict).", file=sys.stderr)
            print(f"!!! Sprawdź stan repozytorium w katalogu '{LOCAL_REPO_DIR}'.", file=sys.stderr)
            sys.exit(1)

    print("\n" + "="*60)
    print("Wszystkie wybrane pull requesty zostały pomyślnie scalone lokalnie.")
    return changed_files

def create_package(package_name: str, changed_files: Set[str]):
    """Tworzy paczkę z docelową strukturą katalogów."""
    print(f"\nTworzenie paczki: {package_name}")
    print("="*60)

    package_dir = Path(package_name)
    if package_dir.exists():
        print(f"Usuwam istniejący katalog paczki: {package_dir}")
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    codes_base_dir = package_dir / "codes"
    codes_base_dir.mkdir()
    package_code_dir = codes_base_dir / "kody"
    package_extra_files_dir = codes_base_dir / "dodatkowe_pliki"

    # Krok 1: Kopiuj tylko katalog 'kody' z repozytorium
    source_code_dir = LOCAL_REPO_DIR / "kody"
    if source_code_dir.is_dir():
        print(f"Kopiuję zawartość 'kody' do: {package_code_dir}")
        shutil.copytree(source_code_dir, package_code_dir)
    else:
        print("Informacja: Katalog 'kody' nie istnieje w repozytorium. Tworzę pusty katalog.")
        package_code_dir.mkdir()

    # Krok 2: Przetwarzanie 'dodatkowe_pliki'
    source_extra_files_dir = LOCAL_REPO_DIR / 'dodatkowe_pliki'
    package_extra_files_dir.mkdir(exist_ok=True)

    if source_extra_files_dir.is_dir():
        # Najpierw kopiujemy wszystkie zmienione pliki z 'dodatkowe_pliki'
        extra_files_to_copy = {
            f for f in changed_files 
            if f.startswith('dodatkowe_pliki/')
        }
        
        if extra_files_to_copy:
            print(f"\nKopiuję {len(extra_files_to_copy)} zmienionych plików z 'dodatkowe_pliki' do: {package_extra_files_dir}")
            for file_path_str in extra_files_to_copy:
                source_file = LOCAL_REPO_DIR / file_path_str
                relative_path = Path(file_path_str).relative_to('dodatkowe_pliki')
                dest_file = package_extra_files_dir / relative_path
                
                if source_file.exists():
                    print(f"  -> Kopiuję: {file_path_str}")
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, dest_file)
                else:
                    print(f"  -> Pomijam (plik nie istnieje w scalonym kodzie): {file_path_str}")
        else:
            print("\nInformacja: Brak zmienionych plików w 'dodatkowe_pliki' do skopiowania.")

        # Teraz, po skopiowaniu, szukamy plików do mergowania w katalogu docelowym
        files_to_merge = {}
        pattern = re.compile(r"^CRISPR-(\d+)_(.*)$")
        
        all_package_files = [p for p in package_extra_files_dir.rglob('*') if p.is_file()]
        
        for f_path in all_package_files:
            match = pattern.match(f_path.name)
            if match:
                number = int(match.group(1))
                target_filename = match.group(2)
                if target_filename not in files_to_merge:
                    files_to_merge[target_filename] = []
                files_to_merge[target_filename].append((number, f_path))

        if files_to_merge:
            print(f"\nMergowanie {len(files_to_merge)} grup plików z katalogu paczki:")
            for target_filename, file_list in files_to_merge.items():
                file_list.sort()
                
                target_path = package_dir / target_filename
                print(f"  -> Tworzenie pliku: {target_path} z {len(file_list)} plików.")
                
                with open(target_path, "wb") as outfile:
                    for _, f_path in file_list:
                        with open(f_path, "rb") as infile:
                            shutil.copyfileobj(infile, outfile)
                
                # Usuń oryginalne pliki po zmergowaniu
                # print(f"  -> Usuwanie {len(file_list)} oryginalnych plików.")
                # for _, f_path in file_list:
                #     f_path.unlink()
    else:
        print("Informacja: Katalog 'dodatkowe_pliki' nie istnieje w repozytorium.")

    print(f"\nZakończono! Paczka została utworzona w katalogu: '{package_dir}'")

# --- Główna logika ---

def main():
    """Główna funkcja programu."""
    parser = argparse.ArgumentParser(description="Narzędzie do łączenia zmian z pull requestów Bitbucket.")
    parser.add_argument("-r", "--repo", required=True, help="Nazwa repozytorium Bitbucket (repository slug).")
    parser.add_argument("-p", "--package-name", help="Opcjonalna nazwa paczki do utworzenia po scaleniu.")
    parser.add_argument("-a", "--approved-only", action="store_true", help="Przetwarzaj tylko zatwierdzone (approved) pull requesty.")
    args = parser.parse_args()

    config = Config(Path(CONFIG_FILE_NAME))
    platform = create_platform(config, args.repo)
    changed_files = process_repository(platform, args.approved_only)

    if args.package_name:
        if changed_files or LOCAL_REPO_DIR.exists():
            create_package(args.package_name, changed_files)
            # Sprzątanie po utworzeniu paczki
            if LOCAL_REPO_DIR.exists():
                print(f"Sprzątam tymczasowy katalog: {LOCAL_REPO_DIR}")
                shutil.rmtree(LOCAL_REPO_DIR)
        else:
            print("Informacja: Nie znaleziono żadnych zmian, więc paczka nie została utworzona.")
    elif LOCAL_REPO_DIR.exists():
        # Jeśli nie tworzymy paczki, zostawiamy katalog do wglądu
        print(f"Zaktualizowany kod znajduje się w katalogu: '{LOCAL_REPO_DIR}'")
        print("="*60)

if __name__ == "__main__":
    main()