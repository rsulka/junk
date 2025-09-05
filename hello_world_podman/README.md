# Hello World Project

## Budowa kontenera

`podman build -t hello .`

## Uruchomienie kontenera

`podman run --rm -v "$(pwd)/logs:/app/logs" hello`
