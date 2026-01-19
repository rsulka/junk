# dsmonitor

Narzędzie do monitorowania zajętości dysku na serwerach RHEL i AIX.

## Funkcje

- **Top N katalogów file-heavy** — identyfikuje katalogi zawierające głównie pliki (nie podkatalogi)
- **Kontekst rodzica** — pokazuje rozmiar katalogu nadrzędnego
- **Analiza stale** — wykrywa nieużywane pliki (wg mtime/atime/ctime)
- **Profile hostów** — różne ustawienia per host
- **Praca zdalna** — skanowanie wielu serwerów przez SSH
- **Dry-run** — podgląd komend bez wykonania

## Wymagania

- Python 3.13+
- GNU coreutils (`du`, `find`) na skanowanych hostach
- Na AIX: AIX Toolbox for Open Source Software

## Instalacja

```bash
# Z repozytorium
pip install -e .

# Lub bezpośrednio
pip install dsmonitor
```

## Użycie

### Tryb lokalny

```bash
# Skan lokalny
dsmonitor --local --paths /data /home --top-n 5

# Z większą szczegółowością
dsmonitor --local --paths /data --verbose
```

### Tryb zdalny (SSH)

```bash
# Z pliku konfiguracyjnego
dsmonitor --config config.yaml

# Pojedynczy host
dsmonitor --host server1 --paths /data --ssh-user admin

# Dry-run — podgląd komend SSH
dsmonitor --config config.yaml --dry-run --verbose
```

### Formaty wyjścia

```bash
# Tekst (domyślny)
dsmonitor --local --paths /data --format text

# JSON
dsmonitor --local --paths /data --format json --output report.json

# CSV
dsmonitor --local --paths /data --format csv --output report.csv
```

## Konfiguracja YAML

Skopiuj `config.example.yaml` i dostosuj:

```yaml
defaults:
  top_n: 20
  file_heavy_threshold: 0.8
  scan_depth: 20
  stale_days: 365
  excludes:
    - "*/.snapshot/*"

ssh:
  user: monitor
  port: 22

hosts:
  - name: server1.example.com
    paths:
      - /data
      - /home

  - name: server2.example.com
    paths:
      - /app
    scan_depth: 10
    ssh_user: admin

  # AIX wymaga GNU du z innej lokalizacji
  - name: aix-server.example.com
    paths:
      - /opt/app
    du_command: "/opt/freeware/bin/du"
```

## Parametry CLI

| Parametr | Opis | Domyślnie |
|----------|------|-----------|
| `--config, -c` | Plik konfiguracyjny YAML | - |
| `--local, -l` | Tryb lokalny (bez SSH) | false |
| `--host` | Host do skanowania | - |
| `--paths, -p` | Ścieżki do skanowania | - |
| `--top-n, -n` | Liczba wyników Top N | 20 |
| `--file-heavy-threshold, -t` | Próg ratio | 0.8 |
| `--scan-depth, -d` | Głębokość skanowania | 20 |
| `--exclude, -e` | Wykluczenia | - |
| `--stale-days` | Wiek plików stale | 365 |
| `--stale-kind` | Typ czasu (mtime/atime/ctime) | mtime |
| `--format, -f` | Format wyjścia (text/json/csv) | text |
| `--output, -o` | Plik wyjściowy | stdout |
| `--parallel` | Równoległość hostów | 10 |
| `--timeout` | Timeout per host (sek) | 1800 |
| `--dry-run` | Tylko wyświetl komendy | false |
| `--verbose, -v` | Szczegółowe logi | false |

## Przykład raportu

```text
======================================================================
DISK SPACE MONITOR - RAPORT
======================================================================
Data: 2026-01-18 13:45:00
Wersja: 0.1.0
Top N: 20 | Próg file-heavy: 0.8
Stare: 365 dni (mtime)

======================================================================
HOST: server1.example.com
======================================================================

ROOT: /data
  Rozmiar: 150.2 GB, Stare > 365 dni: 45.1 GB
────────────────────────────────────────────────────────

    1. /data/logs/app1
       Rozmiar: 25.3 GB (Stare > 365 dni: 20.1 GB)
       Pliki bezpośrednio: 24.8 GB (98%)
       Rodzic: /data/logs — 45.0 GB

    2. /data/backup/2024
       Rozmiar: 18.7 GB (Stare > 365 dni: 18.7 GB)
       Pliki bezpośrednio: 18.7 GB (100%)
       Rodzic: /data/backup — 52.3 GB
```

## Ograniczenia i uwagi

### Wpływ `scan_depth` na dokładność wyliczeń

Parametr `--scan-depth` (domyślnie: 20) ogranicza głębokość skanowania komendy `du`.
Ma to konsekwencje dla dokładności wyliczeń:

- **`file_heavy_ratio`** — wskaźnik obliczany jest jako stosunek rozmiaru plików
  bezpośrednio w katalogu do całkowitego rozmiaru. Przy głębszych zagnieżdżeniach
  (większych niż `scan_depth`) podkatalogi dalsze niż limit nie są uwzględniane
  w odejmowaniu.

- **`direct_files_size`** — rozmiar plików bezpośrednio w katalogu może być zawyżony,
  jeśli katalog zawiera głęboko zagnieżdżone struktury przekraczające `scan_depth`.

**Skutek:** Katalogi z dużą liczbą głęboko zagnieżdżonych podkatalogów mogą wyglądać
na bardziej "file-heavy" niż są w rzeczywistości.

**Zalecenie:** Dla dokładniejszych wyników zwiększ wartość `--scan-depth` lub ustaw
ją na wartość większą niż maksymalna głębokość struktury katalogów.

```bash
# Przykład: głębsze skanowanie dla większej dokładności
dsmonitor --local --paths /data --scan-depth 50
```
