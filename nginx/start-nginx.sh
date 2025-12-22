#!/bin/bash
# Skrypt do uruchomienia Nginx w kontenerze Podman rootless
# Użycie: ./start-nginx.sh [start|stop|restart|logs|status]

CONTAINER_NAME="nginx-proxy"
HOST_PORT="8080"
CONTAINER_PORT="8080"
IMAGE="docker.io/library/nginx:alpine"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

start() {
    echo "Uruchamianie kontenera $CONTAINER_NAME..."
    
    if podman container exists "$CONTAINER_NAME" 2>/dev/null; then
        echo "Kontener $CONTAINER_NAME już istnieje. Usuwanie..."
        podman rm -f "$CONTAINER_NAME"
    fi
    
    podman run -d \
        --name "$CONTAINER_NAME" \
        --network slirp4netns:port_handler=slirp4netns \
        -p "${HOST_PORT}:${CONTAINER_PORT}" \
        -v "${SCRIPT_DIR}/nginx.conf:/etc/nginx/nginx.conf:ro,Z" \
        -v "${SCRIPT_DIR}/conf.d:/etc/nginx/conf.d:ro,Z" \
        --restart unless-stopped \
        "$IMAGE"
    
    if [ $? -eq 0 ]; then
        echo "  Kontener uruchomiony pomyślnie"
        echo "  Nginx dostępny pod: http://localhost:${HOST_PORT}/"
        echo "  File Courier: http://localhost:${HOST_PORT}/fc/"
    else
        echo "✗ Błąd uruchamiania kontenera"
        exit 1
    fi
}

stop() {
    echo "Zatrzymywanie kontenera $CONTAINER_NAME..."
    podman stop "$CONTAINER_NAME" 2>/dev/null
    podman rm "$CONTAINER_NAME" 2>/dev/null
    echo " Kontener zatrzymany"
}

restart() {
    stop
    start
}

logs() {
    podman logs -f "$CONTAINER_NAME"
}

status() {
    if podman container exists "$CONTAINER_NAME" 2>/dev/null; then
        echo "Status kontenera $CONTAINER_NAME:"
        podman ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "Kontener $CONTAINER_NAME nie istnieje"
    fi
}

test_config() {
    echo "Testowanie konfiguracji Nginx..."
    podman run --rm \
        -v "${SCRIPT_DIR}/nginx.conf:/etc/nginx/nginx.conf:ro,Z" \
        -v "${SCRIPT_DIR}/conf.d:/etc/nginx/conf.d:ro,Z" \
        "$IMAGE" nginx -t
}

case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    test)
        test_config
        ;;
    *)
        echo "Użycie: $0 {start|stop|restart|logs|status|test}"
        exit 1
        ;;
esac
