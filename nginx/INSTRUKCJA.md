# Wdrożenie Nginx na misppa02 (Podman rootless)

Konfiguracja Nginx jako reverse proxy w kontenerze Podman bez uprawnień root.  
**F5 z SSL offloadingiem jest już skonfigurowane.**

---

## Architektura

```
Użytkownicy → https://data/app1, https://data/app2
                    │
                    ▼
         F5 Load Balancer (SSL offload) ✓
                    │ HTTP
                    ▼
         misppa02:8080 (Nginx w Podman)
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    app1 (port X)       app2 (port Y)
```

---

## Krok 1: Struktura katalogów

```bash
ssh <user>@misppa02

mkdir -p ~/nginx/conf.d
cd ~/nginx
```

---

## Krok 2: Plik `nginx.conf`

```bash
cat > ~/nginx/nginx.conf << 'EOF'
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    server_tokens off;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;

    # Ścieżki temp dla rootless
    client_body_temp_path /tmp/client_temp;
    proxy_temp_path /tmp/proxy_temp;
    fastcgi_temp_path /tmp/fastcgi_temp;
    uwsgi_temp_path /tmp/uwsgi_temp;
    scgi_temp_path /tmp/scgi_temp;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    include /etc/nginx/conf.d/*.conf;
}
EOF
```

---

## Krok 3: Plik `conf.d/default.conf`

> [!IMPORTANT]
> **Zmień adresy backendów** na rzeczywiste IP/porty aplikacji!

```bash
cat > ~/nginx/conf.d/default.conf << 'EOF'
# ZMIEŃ poniższe adresy na rzeczywiste porty aplikacji!
upstream app1 {
    server host.containers.internal:8101;  # ← ZMIEŃ
}

upstream app2 {
    server host.containers.internal:8102;  # ← ZMIEŃ
}

server {
    listen 8080;
    server_name data;

    location = / {
        default_type text/html;
        return 200 '<h1>Aplikacje</h1><ul><li><a href="/app1/">app1</a></li><li><a href="/app2/">app2</a></li></ul>';
    }

    location /app1/ {
        proxy_pass http://app1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header X-Forwarded-Prefix /app1;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /app2/ {
        proxy_pass http://app2/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header X-Forwarded-Prefix /app2;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
        access_log off;
    }
}
EOF
```

---

## Krok 4: Skrypt uruchomieniowy

```bash
cat > ~/nginx/start.sh << 'EOF'
#!/bin/bash
CONTAINER_NAME="nginx-proxy"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "${1:-start}" in
    start)
        podman rm -f "$CONTAINER_NAME" 2>/dev/null
        podman run -d \
            --name "$CONTAINER_NAME" \
            -p 8080:8080 \
            -v "${SCRIPT_DIR}/nginx.conf:/etc/nginx/nginx.conf:ro,Z" \
            -v "${SCRIPT_DIR}/conf.d:/etc/nginx/conf.d:ro,Z" \
            --restart unless-stopped \
            docker.io/library/nginx:alpine
        echo "✓ Nginx uruchomiony na porcie 8080"
        ;;
    stop)
        podman stop "$CONTAINER_NAME" && podman rm "$CONTAINER_NAME"
        echo "✓ Zatrzymano"
        ;;
    restart)
        $0 stop; $0 start
        ;;
    logs)
        podman logs -f "$CONTAINER_NAME"
        ;;
    test)
        podman run --rm \
            -v "${SCRIPT_DIR}/nginx.conf:/etc/nginx/nginx.conf:ro,Z" \
            -v "${SCRIPT_DIR}/conf.d:/etc/nginx/conf.d:ro,Z" \
            docker.io/library/nginx:alpine nginx -t
        ;;
    status)
        podman ps --filter "name=$CONTAINER_NAME"
        ;;
    *)
        echo "Użycie: $0 {start|stop|restart|logs|test|status}"
        ;;
esac
EOF

chmod +x ~/nginx/start.sh
```

---

## Krok 5: Uruchomienie

```bash
# Test konfiguracji
~/nginx/start.sh test

# Uruchom
~/nginx/start.sh start
```

---

## Krok 6: Weryfikacja

```bash
# Lokalnie
curl http://localhost:8080/health   # → OK
curl http://localhost:8080/app1/
curl http://localhost:8080/app2/

# Przez F5 (z dowolnej maszyny)
curl https://data/app1/
curl https://data/app2/
```

---

## Dodawanie nowych aplikacji

1. Edytuj `~/nginx/conf.d/default.conf`

2. Dodaj upstream i location:

   ```nginx
   upstream app3 {
       server host.containers.internal:8103;
   }
   
   location /app3/ {
       proxy_pass http://app3/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
       proxy_set_header X-Forwarded-Prefix /app3;
   }
   ```

3. Restart:

   ```bash
   ~/nginx/start.sh restart
   ```

---

## Troubleshooting

| Problem | Rozwiązanie |
|---------|-------------|
| 502 Bad Gateway | Sprawdź czy backend działa: `curl http://localhost:PORT/` |
| Connection refused | Sprawdź: `podman ps`, `~/nginx/start.sh logs` |
| Health check fail | `curl -I http://localhost:8080/health` → powinno być 200 |

---

## Checklist

- [ ] `mkdir -p ~/nginx/conf.d`
- [ ] Utworzono `nginx.conf`
- [ ] Utworzono `conf.d/default.conf` z **właściwymi portami backendów**
- [ ] Utworzono `start.sh`
- [ ] `~/nginx/start.sh test` → OK
- [ ] `~/nginx/start.sh start` → kontener działa
- [ ] `curl http://localhost:8080/health` → OK
- [ ] `curl https://data/app1/` → działa
