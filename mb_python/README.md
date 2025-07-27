# Narzędzie do Łączenia Plików z Pull Requestów Bitbucket

Proste narzędzie wiersza poleceń (CLI) do pobierania zmienionych plików z wielu otwartych pull requestów w repozytorium Bitbucket i łączenia ich w jednym lokalnym katalogu.

## Główne Funkcje

- Obsługa **Bitbucket Server** i **Bitbucket Cloud**.
- Pobieranie plików ze wszystkich otwartych PR lub tylko z tych **zatwierdzonych** (approved).
- **Interaktywne rozwiązywanie konfliktów**, gdy ten sam plik jest zmodyfikowany w wielu gałęziach.
- Automatyczne klonowanie repozytorium do tymczasowego katalogu roboczego.
- Możliwość zdefiniowania własnego katalogu docelowego dla połączonych plików.

## Wymagania

- Python 3.6+
- Git

## Instalacja i Konfiguracja

### 1. Instalacja zależności

Upewnij się, że masz zainstalowane wymagane biblioteki Python:

```bash
pip install -r requirements.txt
```

### 2. Plik konfiguracyjny

Przed pierwszym uruchomieniem utwórz plik o nazwie `.mb_config` w głównym katalogu projektu. Plik ten służy do przechowywania konfiguracji dostępu do Bitbucket i jest ignorowany przez system kontroli wersji (zgodnie z `.gitignore`).

**Szablon pliku `.mb_config`:**

```ini
# Adres URL instancji Bitbucket Server (jeśli dotyczy)
BITBUCKET_HOST="bitbucket.twojadomena.com"

# Ustaw na "true" dla Bitbucket Server lub "false" dla Bitbucket Cloud
IS_BITBUCKET_SERVER=false

# Nazwa projektu (dla Server) lub nazwa workspace (dla Cloud)
BITBUCKET_PROJECT_OR_WORKSPACE="nazwa_twojego_workspace"

# Token dostępowy do API Bitbucket z uprawnieniami do odczytu repozytoriów.
# Dla Server: Personal Access Token
# Dla Cloud: App Password
BITBUCKET_API_TOKEN="twoj_token_dostepowy"
```

## Użycie

Skrypt należy uruchamiać z wiersza poleceń, podając co najmniej nazwę repozytorium.

### Podstawowe polecenie

```bash
python3 mb.py --repo <nazwa-repozytorium>
```

To polecenie połączy pliki ze wszystkich otwartych pull requestów w repozytorium `<nazwa-repozytorium>` i umieści je w domyślnym katalogu `~/<nazwa-repozytorium>_merged`.

### Opcje

| Argument | Skrót | Opis |
|---|---|---|
| `--repo` | `-r` | **(Wymagane)** Nazwa repozytorium Bitbucket. |
| `--approved-only` | `-a` | Pobieraj tylko zatwierdzone (approved) pull requesty. |
| `--dest-dir` | `-d` | Określ niestandardowy katalog docelowy dla połączonych plików. |

### Przykłady

- **Pobieranie plików tylko z zatwierdzonych PR:**

  ```bash
  python3 mb.py --repo moje-repo --approved-only
  ```

- **Zapisanie połączonych plików w konkretnym katalogu:**

  ```bash
  python3 mb.py --repo moje-repo --dest-dir /tmp/gotowe_do_testow
  ```
