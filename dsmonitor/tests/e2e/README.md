# Testy E2E dla dsmonitor

Katalog zawiera zasoby do uruchomienia testów End-to-End przy użyciu kontenerów Podman.

## Wymagania

- Podman
- SSH client

## Szybki start

```bash
# Zbuduj obraz (jednorazowo)
make e2e-build

# Uruchom kontenery
make e2e-start

# Sprawdź status
make e2e-status

# Przetestuj połączenie SSH
make e2e-ssh

# Uruchom dsmonitor na kontenerach
make e2e-test

# Zatrzymaj kontenery
make e2e-stop

# Usuń kontenery
make e2e-clean
```

## Struktura danych testowych

```text
/data/           (~26 MB)
├── app_logs/archive/     # 20 plików × 500KB
├── backup/2024/          # 30 starych plików (>400 dni)
├── database/indexes/     # 180 małych plików
└── cache/old/            # 50 starych plików (>180 dni)

/home/testuser/  (~18 MB)
├── projects/app1/build/  # 100 plików + stare cache
├── projects/app2/logs/   # 60 plików × 80KB
└── documents/archive/    # 25 starych plików (>500 dni)
```

## Konfiguracja

Plik `config_e2e.yaml` definiuje dwa hosty:
- `test-server1` → localhost:2221
- `test-server2` → localhost:2222

Pole `ssh_host` pozwala rozdzielić nazwę wyświetlaną od rzeczywistego hosta SSH.

## Klucze SSH

Generowane automatycznie przez `make e2e-build`:
- `id_rsa` - klucz prywatny
- `id_rsa.pub` - klucz publiczny
