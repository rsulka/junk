# Nginx Reverse Proxy (Podman Rootless)

Konfiguracja Nginx jako reverse proxy działającego w kontenerze Podman bez uprawnień root.

## Szybki start

```bash
# Nadaj uprawnienia wykonywania
chmod +x start-nginx.sh

# Uruchom Nginx
./start-nginx.sh start

# Sprawdź status
./start-nginx.sh status
```

## Dostęp do aplikacji

| Aplikacja     | URL                      |
|---------------|--------------------------|
| Strona główna | `http://data:8080/`      |
| File Courier  | `http://data:8080/fc/`   |
| Health check  | `http://data:8080/health`|

> **Uwaga**: `data` to alias DNS dla Twojej maszyny. Dodaj go do `/etc/hosts` lub DNS:
>
> ```text
> <IP_MASZYNY>  data
> ```

## Komendy

```bash
./start-nginx.sh start    # Uruchom kontener
./start-nginx.sh stop     # Zatrzymaj kontener
./start-nginx.sh restart  # Restart kontenera
./start-nginx.sh logs     # Pokaż logi (follow)
./start-nginx.sh status   # Sprawdź status
./start-nginx.sh test     # Testuj konfigurację
```

## Struktura plików

```text
nginx/
├── nginx.conf           # Główna konfiguracja Nginx
├── conf.d/
│   └── default.conf     # Konfiguracja vhostów i reverse proxy
├── start-nginx.sh       # Skrypt zarządzania kontenerem
└── README.md            # Ta dokumentacja
```

## Dodawanie nowych aplikacji

Aby dodać nową aplikację (np. `app1`):

1. Edytuj `conf.d/default.conf`

2. Dodaj upstream:

   ```nginx
   upstream app1 {
       server host.containers.internal:8101;
   }
   ```

3. Dodaj lokalizację:

   ```nginx
   location /app1/ {
       proxy_pass http://app1/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Forwarded-Prefix /app1;
   }
   ```

4. Zrestartuj Nginx:

   ```bash
   ./start-nginx.sh restart
   ```

## Konfiguracja

### Porty

- **8080** - port zewnętrzny na hoście (Nginx)
- **8106** - port backendu File Courier

### Backend File Courier

Skonfigurowany na `host.containers.internal:8106`.
Zmień w `conf.d/default.conf` jeśli aplikacja działa na innym porcie.

## Rozwiązywanie problemów

### Sprawdź logi

```bash
./start-nginx.sh logs
```

### Testuj konfigurację

```bash
./start-nginx.sh test
```

### Sprawdź czy backend jest dostępny

```bash
curl http://localhost:8106/  # Port backendu File Courier
```

### Sprawdź połączenie sieciowe kontenera

```bash
podman exec nginx-proxy curl http://host.containers.internal:8106/
```
