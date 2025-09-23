# Podman – Cheatsheet (PL)

Podman to bezdaemonowy (daemonless), kompatybilny z Dockerem silnik kontenerów. Działa rootless (bez roota) oraz rootful. Poniżej skrót najważniejszych poleceń, przykładów, opcji i dobrych praktyk.

Spis treści:

- [Podman – Cheatsheet (PL)](#podman--cheatsheet-pl)
  - [Quick Reference](#quick-reference)
  - [Szybki start](#szybki-start)
  - [Obrazy (images)](#obrazy-images)
  - [Kontenery (containers)](#kontenery-containers)
  - [Pody (pods)](#pody-pods)
  - [Wolumeny (volumes)](#wolumeny-volumes)
  - [Sieci (networks)](#sieci-networks)
  - [Budowanie obrazów](#budowanie-obrazów)
    - [Zapis/odczyt obrazów i manifesty](#zapisodczyt-obrazów-i-manifesty)
  - [Rejestry i logowanie](#rejestry-i-logowanie)
  - [Sekrety (secrets)](#sekrety-secrets)
  - [Konfiguracja (containers.conf, storage.conf, policy.json)](#konfiguracja-containersconf-storageconf-policyjson)
  - [Bezpieczeństwo i dobre praktyki](#bezpieczeństwo-i-dobre-praktyki)
    - [Bezpieczeństwo – deep dive (seccomp, AppArmor)](#bezpieczeństwo--deep-dive-seccomp-apparmor)
  - [Systemd i autostart](#systemd-i-autostart)
    - [Quadlet (systemd .container/.pod)](#quadlet-systemd-containerpod)
      - [Gdzie umieszczać pliki i nazewnictwo](#gdzie-umieszczać-pliki-i-nazewnictwo)
      - [Mapowanie opcji Podman → Quadlet (\[Container\])](#mapowanie-opcji-podman--quadlet-container)
      - [Zaawansowane mapowania: EnvFile i Mount](#zaawansowane-mapowania-envfile-i-mount)
      - [Kompletny przykład: Pod + sieć + wolumen + 2 kontenery](#kompletny-przykład-pod--sieć--wolumen--2-kontenery)
      - [Healthcheck i AutoUpdate w Quadlet](#healthcheck-i-autoupdate-w-quadlet)
      - [Dobre praktyki i debugowanie](#dobre-praktyki-i-debugowanie)
      - [Quadlet: .kube (Kubernetes YAML jako usługa)](#quadlet-kube-kubernetes-yaml-jako-usługa)
  - [Kubernetes: play i generate](#kubernetes-play-i-generate)
  - [Compose i socket Docker API](#compose-i-socket-docker-api)
  - [Auto-update i healthcheck](#auto-update-i-healthcheck)
  - [Sprzątanie i diagnostyka](#sprzątanie-i-diagnostyka)
  - [Przydatne aliasy i różnice vs Docker](#przydatne-aliasy-i-różnice-vs-docker)
  - [Przykłady „od A do Z”](#przykłady-od-a-do-z)
    - [Prosty serwer WWW z danymi na hoście (SELinux)](#prosty-serwer-www-z-danymi-na-hoście-selinux)
    - [Aplikacja + Worker w jednym podzie](#aplikacja--worker-w-jednym-podzie)
    - [Budowanie i uruchomienie obrazu własnego](#budowanie-i-uruchomienie-obrazu-własnego)
    - [Minimalny real-world stack (Quadlet): pod + sieć + wolumeny + auto-update](#minimalny-real-world-stack-quadlet-pod--sieć--wolumeny--auto-update)
  - [Szybkie ściągi opcji](#szybkie-ściągi-opcji)
  - [Mini-FAQ](#mini-faq)
    - [Jak uruchomić kontener na porcie \<1024 bez roota?](#jak-uruchomić-kontener-na-porcie-1024-bez-roota)
    - [Jak uzyskać dostęp do hosta z kontenera (host.containers.internal)?](#jak-uzyskać-dostęp-do-hosta-z-kontenera-hostcontainersinternal)
    - [Jak ustawić stałe DNS dla kontenerów?](#jak-ustawić-stałe-dns-dla-kontenerów)
    - [Jak zmienić domyślny storage driver?](#jak-zmienić-domyślny-storage-driver)
    - [Jak debugować problemy z siecią rootless?](#jak-debugować-problemy-z-siecią-rootless)
    - [Jak używać GPU w kontenerach?](#jak-używać-gpu-w-kontenerach)
  - [Rootless (szczegóły)](#rootless-szczegóły)
    - [Mapowania UID/GID](#mapowania-uidgid)
    - [Opcja --userns=keep-id](#opcja---usernskeep-id)
    - [Ograniczenia rootless](#ograniczenia-rootless)
    - [Włączenie rootless dla użytkownika](#włączenie-rootless-dla-użytkownika)
  - [Multi-arch i buildx](#multi-arch-i-buildx)
    - [Budowanie dla wielu platform](#budowanie-dla-wielu-platform)
    - [Emulacja architektur (QEMU)](#emulacja-architektur-qemu)
  - [Monitorowanie i logi](#monitorowanie-i-logi)
    - [Zaawansowane logowanie](#zaawansowane-logowanie)
    - [Monitoring zasobów](#monitoring-zasobów)
    - [Integracja z systemd journal](#integracja-z-systemd-journal)
  - [CI/CD i automatyzacja](#cicd-i-automatyzacja)
    - [Budowanie w CI/CD](#budowanie-w-cicd)
    - [Testowanie obrazów](#testowanie-obrazów)
    - [Automatyzacja z systemd timers](#automatyzacja-z-systemd-timers)
    - [Skrypty utility](#skrypty-utility)

---

## Quick Reference

Najczęściej używane komendy w pigułce:

```bash
# Informacje i pomoc
podman version
podman info
podman <subcmd> --help

# Obrazy
podman pull alpine:latest
podman images
podman rmi IMAGE

# Kontenery
podman run --rm -it --name tmp alpine sh
podman ps -a
podman logs -f NAME
podman exec -it NAME sh
podman stop NAME && podman rm NAME

# Sieci, pody, wolumeny
podman network create mynet
podman pod create --name mypod -p 8080:8080
podman volume create data

# Budowanie i rejestry
podman build -t myimg:latest .
podman login quay.io && podman push myimg:latest quay.io/user/myimg:latest

# Systemd / Quadlet / Kubernetes
podman generate systemd --new --name mypod --files
podman auto-update --dry-run
podman play kube my.yaml
```

---

## Szybki start

```bash
# Wersja i podstawowe informacje
podman version
podman info

# Pomoc
podman --help
podman <subcmd> --help      # np. podman run --help

# Podstawowy kontener (rootless)
podman run --rm -it alpine:latest sh

# Mapowanie portów i katalogu
podman run -d --name web -p 8080:80 -v $(pwd)/html:/usr/share/nginx/html:Z nginx:alpine

# Lista działających i wszystkich kontenerów
podman ps
podman ps -a

# Logi i wejście do kontenera
podman logs -f web
podman exec -it web sh
```

Wskazówki:

- Rootless nie może robić bindów portów < 1024 bez dodatkowych ustawień. Używaj portów >1024 (np. 8080).
- Na systemach z SELinux używaj sufiksów :Z lub :z przy wolumenach bind, aby prawidłowo etykietować katalogi.

---

## Obrazy (images)

```bash
# Szukanie i pobieranie
podman search alpine
podman pull docker.io/library/alpine:latest

# Lista i inspekcja obrazów
podman images
podman image inspect alpine:latest | jq '.[0].Config'

# Tagowanie i wypychanie do rejestru
podman tag alpine:latest registry.example.com/team/alpine:3.20
podman push registry.example.com/team/alpine:3.20

# Usuwanie i sprzątanie
podman rmi alpine:latest
podman image prune -a     # ostrożnie – usuwa nieużywane obrazy
```

---

## Kontenery (containers)

Tworzenie i uruchamianie:

```bash
# Szybkie uruchomienie (tworzy, startuje)
podman run --name myapp -d -p 8080:80 nginx:alpine

# Tylko utworzenie (bez startu)
podman create --name worker alpine:latest sleep 3600
podman start worker

# Interaktywnie
podman run --rm -it --name shell alpine:latest sh
```

Zarządzanie cyklem życia:

```bash
podman stop myapp          # graceful stop
podman kill myapp          # natychmiastowe przerwanie
podman restart myapp
podman rm myapp            # usuń kontener (musi być zatrzymany)
podman rm -f myapp         # wymuś (stop + rm)
```

Diagnostyka i narzędzia:

```bash
podman logs -f myapp
podman top myapp
podman stats               # zużycie zasobów
podman inspect myapp | jq '.[0].HostConfig'
podman port myapp

# Kopiowanie plików
podman cp myapp:/etc/nginx/nginx.conf ./
podman cp ./index.html myapp:/usr/share/nginx/html/index.html

# Wejście do działającego kontenera
podman exec -it myapp sh
```

Limitowanie zasobów i bezpieczeństwo (przykłady):

```bash
podman run -d --name svc \
  --memory 256m --cpus 1.0 --pids-limit 256 \
  --read-only --tmpfs /tmp --tmpfs /run \
  --cap-drop ALL --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges \
  -p 8080:8080 quay.io/someteam/app:latest
```

Przydatne: commit, export/import

```bash
podman commit myapp myapp:snapshot
podman export -o myapp.tar myapp
podman import myapp.tar myapp:from-tar
```

---

## Pody (pods)

Pod to grupa kontenerów współdzieląca sieć i przestrzenie (namespace). Podman ma „infra” container jako bazę poda.

```bash
# Utworzenie poda z publikacją portu 8080
podman pod create --name mypod -p 8080:8080
podman pod ls
podman pod inspect mypod | jq '.'

# Dodanie kontenera do istniejącego poda
podman run -d --name api --pod mypod quay.io/team/api:latest
podman run -d --name worker --pod mypod quay.io/team/worker:latest

# Jednym poleceniem (nowy pod + kontener)
podman run -d --pod new:mypod -p 8080:8080 --name web nginx:alpine

# Porty mapujemy zwykle na poziomie poda (infra)
podman pod port mypod

# Zatrzymanie/uruchomienie/usunięcie całego poda
podman pod stop mypod
podman pod start mypod
podman pod rm -f mypod
```

---

## Wolumeny (volumes)

Rodzaje:

- Named volume (zarządzany przez Podmana)
- Bind mount (mapowanie katalogu z hosta)
- Tmpfs (w pamięci)

```bash
# Named volumes
podman volume create data
podman volume ls
podman volume inspect data | jq '.'
podman volume rm data

# Użycie named volume
podman run -d --name db -v data:/var/lib/postgresql/data:Z postgres:16

# Bind mount (z SELinux label)
podman run -d --name web -v $(pwd)/html:/usr/share/nginx/html:Z nginx:alpine

# Tmpfs
podman run --rm --tmpfs /run --tmpfs /tmp alpine:latest sh -c 'mount | grep tmpfs'

# Sprzątanie nieużywanych wolumenów
podman volume prune
```

SELinux:

- :Z — prywatna etykieta dla pojedynczego kontenera
- :z — współdzielona etykieta (gdy katalog używa wiele kontenerów)

Kopie zapasowe wolumenów:

```bash
# Backup named volume do tar.gz w bieżącym katalogu
podman run --rm -v data:/data -v $(pwd):/backup alpine \
  sh -c "tar czf /backup/data.tar.gz -C /data ."

# Przywrócenie z archiwum do wolumenu 'data'
podman run --rm -v data:/data -v $(pwd):/backup alpine \
  sh -c "tar xzf /backup/data.tar.gz -C /data"
```

---

## Sieci (networks)

Podman 4.x+ domyślnie używa netavark (zamiast CNI). Rootless korzysta zwykle ze slirp4netns.

```bash
podman network ls
podman network inspect podman
podman network create mynet
podman network rm mynet

# Uruchomienie kontenera w konkretnej sieci
podman run -d --name svc --network mynet quay.io/team/svc:latest

# Rootless: publikacja portu jest wspierana, ale <1024 wymaga dodatkowych ustawień systemowych
podman run -d -p 8080:80 nginx:alpine
```

Przydatne:

- --ip, --ip6 dla statycznych adresów w sieci bridge (rootful)
- --add-host, --dns, --dns-search dla kontrolowania rozwiązywania nazw

---

## Budowanie obrazów

```bash
# Dockerfile/Containerfile w bieżącym katalogu
podman build -t myimage:latest .

# Dedykowany plik
podman build -t myimage:dev -f Dockerfile.dev .

# Przekazywanie ARG/BUILD_ARGS
podman build --build-arg NODE_ENV=production -t app:prod .
```

Wskazówka: plik może nazywać się Dockerfile lub Containerfile. Pod spodem Podman używa Buildah.

### Zapis/odczyt obrazów i manifesty

```bash
# Zapis obrazu do tar i odczyt z tar
podman save -o myimage.tar myimage:latest
podman load -i myimage.tar

# Manifest multi-arch (x86_64, arm64, ...)
podman manifest create myapp:manifest
podman manifest add myapp:manifest docker://docker.io/library/alpine:3.20
podman manifest inspect myapp:manifest | jq '.'
```

---

## Rejestry i logowanie

```bash
# Logowanie do rejestru
podman login registry.example.com
podman logout registry.example.com

# Użycie skróconych nazw obrazów zależy od registries.conf
podman pull alpine          # rozwiązywany wg reguł short-name
```

Pliki konfiguracyjne (domyślnie):

- System: /etc/containers/registries.conf
- Użytkownik: ~/.config/containers/registries.conf

W registries.conf ustawisz m.in. domyślne rejestry, mirror, short-name mode oraz „insecure” dla konkretnych hostów (tylko jeśli musisz).

---

## Sekrety (secrets)

Sekrety pozwalają bezpieczniej przekazywać hasła/klucze do kontenerów.

```bash
# Utwórz sekret z pliku lub STDIN
printf 's3cr3t' | podman secret create db_password -
podman secret ls
podman secret inspect db_password | jq '.'

# Użycie jako plik (domyślnie montowany w /run/secrets/<nazwa>)
podman run -d --name db \
  --secret id=db_password \
  -e POSTGRES_PASSWORD_FILE=/run/secrets/db_password \
  postgres:16

# Użycie jako zmienna środowiskowa
podman run --rm \
  --secret id=db_password,type=env,target=DB_PASSWORD \
  alpine:3.20 sh -c 'echo "$DB_PASSWORD" | sed "s/./*/g"'

# Usunięcie sekretu
podman secret rm db_password
```

Uwaga: Sekrety są dostępne tylko w czasie działania kontenera (nie trafiają do obrazu).

---

## Konfiguracja (containers.conf, storage.conf, policy.json)

Główne pliki i ścieżki:

- containers.conf: /etc/containers/containers.conf oraz ~/.config/containers/containers.conf
- storage.conf: /etc/containers/storage.conf oraz ~/.config/containers/storage.conf
- policy.json (podpisy/pozwolenia): /etc/containers/policy.json oraz ~/.config/containers/policy.json
- registries.conf: jak wyżej

Przykładowe ustawienia w containers.conf:

- domyślne limity zasobów
- domyślne opcje sieci (np. dns, add-host)
- domyślne capabilities i seccomp profile

Ścieżki storage (rootless):

- ~/.local/share/containers/storage (obrazy, warstwy)
- ~/.local/share/containers/cache

---

## Bezpieczeństwo i dobre praktyki

- Preferuj rootless, gdy to możliwe.
- Używaj --read-only i montuj potrzebne ścieżki z tmpfs (--tmpfs /run, --tmpfs /tmp).
- Ogranicz uprawnienia: --cap-drop ALL, dodawaj tylko potrzebne (--cap-add NET_BIND_SERVICE itp.).
- Ustaw no-new-privileges: --security-opt no-new-privileges.
- Uruchamiaj procesy jako nie-root: --user 1000:1000 lub userns=keep-id.
- Ogranicz zasoby: --memory, --cpus, --pids-limit.
- Na SELinux używaj :Z/:z dla bind mountów.
- Nie ustawiaj --privileged, chyba że naprawdę rozumiesz konsekwencje.
- Aktualizuj obrazy regularnie; używaj tagów wersji (nie zawsze :latest).

Przykład bezpieczniejszego uruchomienia:

```bash
podman run -d --name api \
  --user 1000:1000 --read-only \
  --tmpfs /run --tmpfs /tmp \
  --cap-drop ALL --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges \
  --memory 256m --cpus 1 \
  -p 8080:8080 ghcr.io/org/api:1.2.3
```

### Bezpieczeństwo – deep dive (seccomp, AppArmor)

Seccomp – własny profil:

1) Generowanie bazowego profilu i dostosowanie (albo użyj gotowego JSON):

```bash
podman run --rm --privileged ghcr.io/containers/podman-tools/seccomp-profile:latest > seccomp.json
# Edytuj seccomp.json, aby zablokować niepotrzebne syscall-e
```

1) Użycie profilu w kontenerze:

```bash
podman run -d --name api \
  --security-opt seccomp=$(pwd)/seccomp.json \
  ghcr.io/org/api:latest
```

1) Mapowanie w Quadlet (`SeccompProfile=`):

```ini
[Container]
Image=ghcr.io/org/api:latest
SeccompProfile=%h/security/seccomp.json
```

AppArmor – profil niestandardowy (na systemach z AppArmor):

```bash
# Przykładowo w Ubuntu
sudo aa-status
sudo aa-enforce /etc/apparmor.d/usr.bin.podman # globalnie (opcjonalne)

# Własny profil np. /etc/apparmor.d/container.myapp
sudo apparmor_parser -r -W /etc/apparmor.d/container.myapp

# Użycie profilu przy uruchomieniu:
podman run -d --name api \
  --security-opt apparmor=container.myapp \
  ghcr.io/org/api:latest
```

Quadlet – przypięcie profilu AppArmor:

```ini
[Container]
Image=ghcr.io/org/api:latest
Pod=app
PodmanArgs=--security-opt apparmor=container.myapp
```

Uwagi:

- Na SELinux używaj `SecurityLabel*` opcji w Quadlet (np. `SecurityLabelDisable=true`).
- `--cap-drop ALL` + `NoNewPrivileges=yes` znacząco ogranicza powierzchnię ataku.
- Rozważ `ReadOnly=true` + `ReadOnlyTmpfs=true` oraz jawne `Tmpfs=`.
- Używaj `Mount=` z `ro`, `nodev`, `nosuid`, `noexec` gdzie to możliwe.

---

## Systemd i autostart

Generowanie unitów systemd dla kontenerów i podów:

```bash
# Dla pojedynczego kontenera
podman generate systemd --new --name myapp --files --restart-policy=always
ls -1 *.service

# Dla poda (wszystkie kontenery w podzie)
podman generate systemd --new --name mypod --files --restart-policy=always --container-prefix=ctr --pod-prefix=pod
```

Instalacja unitów:

```bash
# System-wide (root)
sudo mv *.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now myapp.service

# User units (rootless)
mkdir -p ~/.config/systemd/user
mv *.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now myapp.service

# Aby user units działały po wylogowaniu:
loginctl enable-linger $(whoami)
```

### Quadlet (systemd .container/.pod)

Quadlet pozwala definiować kontenery/pody jako pliki unitów systemd bezpośrednio (bez generowania).

```ini
# ~/.config/containers/systemd/web.container
[Unit]
Description=Web via Quadlet

[Container]
Image=nginx:alpine
PublishPort=8080:80
Volume=%h/sites/demo:/usr/share/nginx/html:Z
Environment=NGINX_WORKER_PROCESSES=1
ReadOnly=true
Tmpfs=/run
Tmpfs=/tmp

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now web.service
```

#### Gdzie umieszczać pliki i nazewnictwo

- User (rootless): `~/.config/containers/systemd/`
- System-wide (root): `/etc/containers/systemd/`
- Nazwa zasobu bierze się z nazwy pliku (bez rozszerzenia). Przykłady:
  - `web.container` → unit `web.service`
  - `app.pod` → unit `app-pod.service` (tworzy infra + kontenery podłączone przez `Pod=`)
  - `mynet.network` → tworzy sieć `mynet`
  - `data.volume` → tworzy wolumen `data`

Po dodaniu/zmianie plików wykonaj:

```bash
systemctl --user daemon-reload
systemctl --user enable --now <nazwa>.service
```

#### Mapowanie opcji Podman → Quadlet ([Container])

- Image= → `--image`
- PublishPort= → `-p`
- Volume= → `-v` (obsługuje named volume i bind mount)
- Network= → `--network`
- Environment= / EnvFile= → `-e` / `--env-file`
- User= / Group= → `--user`
- WorkDir= → `--workdir`
- ReadOnly=true → `--read-only`
- Tmpfs=/run → `--tmpfs /run` (wiele wpisów dozwolone)
- AddCapability= / DropCapability= → `--cap-add` / `--cap-drop`
- NoNewPrivileges=yes → `--security-opt no-new-privileges`
- SeccompProfile= → `--security-opt seccomp=...`
- SecurityLabelDisable=true → `--security-opt label=disable` (SELinux)
- MemoryLimit=, CPUQuota=, PidsLimit= → limity zasobów
- HealthCmd=, HealthInterval=, HealthRetries=, HealthTimeout=, HealthStartPeriod= → HEALTHCHECK
- AutoUpdate=image|registry → etykiety auto-update

Uwaga: Dodatkowe sekcje [Unit]/[Service]/[Install] można umieszczać w tym samym pliku aby nadpisać zachowanie systemd, np. Restart=always.

#### Zaawansowane mapowania: EnvFile i Mount

EnvFile – wstrzykiwanie zmiennych środowiskowych z pliku:

```ini
# ~/.config/containers/systemd/api.container
[Unit]
Description=API with EnvFile

[Container]
Image=ghcr.io/org/api:latest
Pod=app
EnvFile=./api.env
Environment=JAVA_TOOL_OPTIONS=-XX:+UseContainerSupport

[Install]
WantedBy=default.target
```

Uwagi:

- Ścieżka w `EnvFile=` może być względna względem pliku `.container` (używaj `./` przed specifierami jak `%n`).
- Składnia pliku EnvFile jak w systemd: linie `KEY=VALUE`, komentarze `# ...`.

Mount – różne style montowania:

1) type=bind (odpowiednik `-v /host:/ctr:Z,ro`):

```ini
[Container]
Image=nginx:alpine
Mount=type=bind,source=%h/sites/demo,target=/usr/share/nginx/html,ro,z
```

1) type=tmpfs (odpowiednik `--tmpfs /run:rw,size=64m`):

```ini
[Container]
Image=ghcr.io/org/app:latest
Mount=type=tmpfs,target=/run,tmpfs-size=64m
```

1) type=volume (named volume) z Quadlet `.volume` zależnością:

```ini
[Unit]
Wants=data.volume
After=data.volume

[Container]
Image=postgres:16
Volume=data.volume:/var/lib/postgresql/data:Z
```

1) Prosty Volume= (skrócona forma za `--volume`):

```ini
[Container]
Image=redis:7
Volume=%h/redis:/data:Z
```

Tipy:

- Dla SELinux używaj sufiksu `:Z` (prywatne) lub `:z` (współdzielone) przy bind/volume.
- `Mount=` daje pełnię opcji `--mount` (np. `uid=`, `gid=`, `context=`). `Volume=` to krótsza forma ogólnego przypadku.
- Dla podów możesz użyć sekcji `[Pod]` i `Volume=` aby współdzielić mounty między kontenerami w podzie.

#### Kompletny przykład: Pod + sieć + wolumen + 2 kontenery

Plik `app.pod`:

```ini
[Unit]
Description=App Pod

[Pod]
PodName=app
PublishPort=8080:8080
Network=mynet

[Install]
WantedBy=default.target
```

Plik `mynet.network`:

```ini
[Unit]
Description=Custom bridge network

[Network]
NetworkName=mynet
Subnet=10.89.0.0/24
Gateway=10.89.0.1
```

Plik `data.volume`:

```ini
[Unit]
Description=App data volume

[Volume]
VolumeName=data
```

Kontener API `api.container` (w podzie, z healthcheck i autoupdate):

```ini
[Unit]
Description=API container
Wants=mynet.network data.volume app-pod.service
After=mynet.network data.volume app-pod.service

[Container]
Image=ghcr.io/org/api:1.2.3
Pod=app
Environment=JAVA_OPTS=-Xms128m -Xmx256m
Volume=data:/var/lib/app:Z
ReadOnly=true
Tmpfs=/run
Tmpfs=/tmp
AddCapability=NET_BIND_SERVICE
DropCapability=ALL
NoNewPrivileges=yes
HealthCmd=curl -fsS http://127.0.0.1:8080/health || exit 1
HealthInterval=30s
HealthRetries=3
HealthTimeout=3s
AutoUpdate=image

[Service]
Restart=always
RestartSec=5s

[Install]
WantedBy=default.target
```

Kontener Worker `worker.container` (ten sam pod, bez portów):

```ini
[Unit]
Description=Worker container
Wants=app-pod.service
After=app-pod.service

[Container]
Image=ghcr.io/org/worker:1.2.3
Pod=app
Environment=QUEUE=default
DropCapability=ALL
NoNewPrivileges=yes

[Service]
Restart=on-failure
RestartSec=2s

[Install]
WantedBy=default.target
```

Uruchomienie wszystkiego:

```bash
systemctl --user daemon-reload
systemctl --user enable --now mynet.service data.service app-pod.service api.service worker.service
```

Uwaga: nazwy service wynikają z bazowej nazwy plików (`*.network` → `*.service` itd.). Sprawdź `systemctl --user status ...` gdyby nazwy różniły się w Twojej dystrybucji.

#### Healthcheck i AutoUpdate w Quadlet

- Healthcheck: użyj `HealthCmd=` i powiązanych opcji w sekcji [Container]. Status można zobaczyć w `podman ps` i logach.
- AutoUpdate: `AutoUpdate=image|registry` spowoduje, że `podman auto-update` zrestartuje usługę z nową wersją obrazu.

#### Dobre praktyki i debugowanie

- Dodaj `Wants=`/`After=` aby zapewnić kolejność startu (np. sieć, wolumeny, pod).
- Używaj `Restart=` i `RestartSec=` w [Service] dla stabilności.
- Logi i stan:
  
  ```bash
  systemctl --user status api.service
  journalctl --user -u api.service -f
  ```

- Sprawdź powiązane zasoby:
  
  ```bash
  podman pod ps; podman network ls; podman volume ls
  ```

#### Quadlet: .kube (Kubernetes YAML jako usługa)

Możesz zarządzać YAML-em Kubernetes (podman kube play) przez Quadlet używając pliku `.kube`.

Plik `app.kube`:

```ini
[Unit]
Description=Kubernetes YAML via Quadlet

[Kube]
# Ścieżka (absolutna lub względna względem pliku .kube)
Yaml=%h/apps/app.yaml
# Opcjonalnie wymuś usunięcie zasobów przy stopie
KubeDownForce=true
# Możesz dodać sieć Quadlet
# Network=mynet.network
# Publikacje portów (uzupełniają to co w YAML)
PublishPort=8080:8080
# AutoUpdate dla poszczególnych kontenerów z YAML
AutoUpdate=registry

[Install]
WantedBy=default.target
```

Użycie:

```bash
systemctl --user daemon-reload
systemctl --user enable --now app.service
# Podgląd logów
journalctl --user -u app.service -f
# Zatrzymanie i cleanup (down --force)
systemctl --user stop app.service
```

Uwagi:

- `.kube` generuje usługę `podman kube play ...`; `Yaml=` jest wymagane.
- `PublishPort=` scala się z portami zdefiniowanymi w YAML i może je nadpisać.
- `Network=` może wskazywać nazwę sieci lub `mynet.network` Quadlet (tworzy zależność).
- `SetWorkingDirectory=yaml|unit` pomaga rozwiązać ścieżki względne.
- `AutoUpdate=` w `.kube` pozwala sterować auto‑update całości lub wybranych kontenerów po nazwie.

---

## Kubernetes: play i generate

```bash
# Wygeneruj szkic YAML (Kubernetes) z działającego kontenera/poda
podman generate kube mypod > mypod.yaml

# Uruchom na podstawie YAML (podman play kube)
podman play kube -f mypod.yaml

# Usuwanie zasobów z YAML
podman play kube --down -f mypod.yaml
```

Uwagi:

- YAML nie jest 1:1 z pełnym K8s, ale pozwala na przenośność definicji lokalnie.

---

## Compose i socket Docker API

Możesz wystawić Docker-compatible API i użyć docker-compose/compose v2.

```bash
# Socket jako user service (rootless)
systemctl --user enable --now podman.socket
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock

# W tle bez systemd
podman system service --time=0 &
```

Następnie użyj docker compose lub podman-compose.

```bash
# docker compose (jeśli zainstalowany)
docker compose up -d

# podman-compose (osobny projekt)
podman-compose up -d
```

---

## Auto-update i healthcheck

Auto-update działa na podstawie etykiet w obrazie/kontenerze.

```bash
# Etykieta w kontenerze: io.containers.autoupdate=registry|image
podman run -d --name web \
  --label "io.containers.autoupdate=image" \
  nginx:alpine

# Sprawdzenie/wykonanie auto-update
podman auto-update --dry-run
podman auto-update
```

Healthcheck:

- Zdefiniuj HEALTHCHECK w Dockerfile/Containerfile.
- Podman wykonuje healthcheck wg definicji obrazu.

```bash
podman ps --format '{{.Names}}\t{{.Health}}'
podman healthcheck run web
```

Auto-update jako timer systemd:

```bash
# System-wide (root)
sudo systemctl enable --now podman-auto-update.timer

# Dla użytkownika (rootless)
systemctl --user enable --now podman-auto-update.timer
```

---

## Sprzątanie i diagnostyka

```bash
# Globalne sprzątanie (ostrożnie)
podman system prune -a

# Informacje i zdarzenia
podman info
podman events --since 1h

# Inspekcja storage i przestrzeni
podman system df

# Reset (usuwa WSZYSTKO dla bieżącego użytkownika/roota)
podman system reset
```

Troubleshooting:

- Sprawdź logi jednostek systemd, jeśli używasz generate systemd: journalctl -u myapp.service -xe
- Sprawdź polityki sieci i porty: podman pod inspect, podman network inspect
- SELinux: audit.log / ausearch -m AVC; spróbuj dodać :Z lub :z

Zaawansowane:

- Checkpoint/restore (CRIU wymagane):

  ```bash
  sudo dnf install -y criu # lub apt/yum w zależności od dystrybucji
  podman container checkpoint myapp
  podman container restore myapp
  ```

- Różnice kontenera: podman diff myapp
- Formatowanie inspect bez jq:

  ```bash
  podman inspect --format '{{.Id}} {{range .NetworkSettings.Ports}}{{println .}}{{end}}' myapp
  ```

---

## Przydatne aliasy i różnice vs Docker

Alias zgodności z Dockerem:

```bash
alias docker=podman
```

Różnice:

- Podman nie ma demona; polecenia komunikują się bezpośrednio z libpod.
- Rootless to domyślny, bezpieczniejszy tryb; nie wszystkie funkcje kernelowe są dostępne bez roota (np. porty <1024).
- Sieć rootless opiera się o slirp4netns; rootful — natywne bridge/iptables/nat (netavark).
- Na macOS/Windows używa się „podman machine”; na Linux nie jest potrzebne.

Tipy:

- Bash completion:

  ```bash
  podman completion bash | sudo tee /etc/bash_completion.d/podman >/dev/null
  source /etc/bash_completion
  ```

- Rootless porty <1024: jako root ustaw sysctl lub przekieruj przez firewall:

  ```bash
  sudo sysctl -w net.ipv4.ip_unprivileged_port_start=0
  # lub przekierowanie np. 80 -> 8080
  sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080
  ```

---

## Przykłady „od A do Z”

### Prosty serwer WWW z danymi na hoście (SELinux)

```bash
mkdir -p ~/sites/demo
echo "Hello Podman" > ~/sites/demo/index.html
podman run -d --name web \
  -p 8080:80 \
  -v ~/sites/demo:/usr/share/nginx/html:Z \
  nginx:alpine
# Otwórz: http://localhost:8080
```

### Aplikacja + Worker w jednym podzie

```bash
podman pod create --name app --hostname app --publish 8080:8080
podman run -d --name api --pod app ghcr.io/org/api:1.2.3
podman run -d --name worker --pod app ghcr.io/org/worker:1.2.3
podman pod ps
podman pod port app
```

### Budowanie i uruchomienie obrazu własnego

```bash
cat > Containerfile <<'EOF'
FROM alpine:3.20
RUN apk add --no-cache busybox-extras
EXPOSE 8080
HEALTHCHECK CMD nc -z 127.0.0.1 8080 || exit 1
CMD ["sh", "-c", "while true; do printf 'OK\n' | nc -l -p 8080 -s 0.0.0.0; done"]
EOF

podman build -t demo:local .
podman run -d --name demo -p 8080:8080 demo:local
podman ps --format '{{.Names}}\t{{.Health}}\t{{.Ports}}'
```

### Minimalny real-world stack (Quadlet): pod + sieć + wolumeny + auto-update

Pliki w `~/.config/containers/systemd/` (rootless):

`mynet.network`:

```ini
[Unit]
Description=App network

[Network]
NetworkName=mynet
Subnet=10.91.0.0/24
Gateway=10.91.0.1
```

`data.volume`:

```ini
[Unit]
Description=Data volume

[Volume]
VolumeName=data
```

`app.pod`:

```ini
[Unit]
Description=App Pod
After=mynet.network data.volume
Wants=mynet.network data.volume

[Pod]
PodName=app
Network=mynet
PublishPort=8080:8080

[Install]
WantedBy=default.target
```

`api.container`:

```ini
[Unit]
Description=API
Wants=app-pod.service
After=app-pod.service

[Container]
Image=ghcr.io/example/api:latest
Pod=app
Volume=data:/var/lib/api:Z
Environment=JAVA_OPTS=-Xmx256m
AddCapability=NET_BIND_SERVICE
DropCapability=ALL
NoNewPrivileges=yes
ReadOnly=true
Tmpfs=/run
Tmpfs=/tmp
HealthCmd=curl -fsS http://127.0.0.1:8080/health || exit 1
HealthInterval=30s
AutoUpdate=registry

[Service]
Restart=always
RestartSec=3s

[Install]
WantedBy=default.target
```

`worker.container`:

```ini
[Unit]
Description=Worker
Wants=app-pod.service
After=app-pod.service

[Container]
Image=ghcr.io/example/worker:latest
Pod=app
Environment=QUEUE=default
DropCapability=ALL
NoNewPrivileges=yes
AutoUpdate=registry

[Service]
Restart=on-failure
RestartSec=2s

[Install]
WantedBy=default.target
```

Uruchomienie i zarządzanie:

```bash
systemctl --user daemon-reload
systemctl --user enable --now mynet.service data.service app-pod.service api.service worker.service

# Auto-update jako timer (rootless)
systemctl --user enable --now podman-auto-update.timer

# Sprawdzenie
podman pod ps
podman ps --format '{{.Names}}\t{{.Status}}\t{{.Health}}'
```

---

## Szybkie ściągi opcji

- -d: detached
- --rm: usuń po zakończeniu
- -p H:C[/proto]: mapowanie portów (host:container)
- -v SRC:DST[:Z|:z|:ro|:rw]: wolumen bind/named
- --tmpfs PATH: mount tmpfs
- --network NAME|host|none: sieć
- --user UID:GID: uruchom jako użytkownik
- --cap-drop/--cap-add: zdolności kernela
- --read-only: read-only rootfs
- --env NAME=VAL, --env-file: zmienne środowiskowe
- --restart=always,on-failure: restart polityka (systemd lub podman run --restart)

---

## Mini-FAQ

### Jak uruchomić kontener na porcie <1024 bez roota?

- Ustaw sysctl: `sudo sysctl -w net.ipv4.ip_unprivileged_port_start=0` (trwałe w /etc/sysctl.conf).
- Lub przekieruj port przez firewall: `sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080`.

### Jak uzyskać dostęp do hosta z kontenera (host.containers.internal)?

- W sieci `host`: `--network host` (rootful).
- W innych sieciach: użyj `--add-host host.containers.internal:host-gateway` (od Podman 4.0+).

### Jak ustawić stałe DNS dla kontenerów?

- W containers.conf: `dns = ["8.8.8.8", "1.1.1.1"]`.
- Lub per-kontener: `--dns 8.8.8.8 --dns-search example.com`.

### Jak zmienić domyślny storage driver?

- W storage.conf: `driver = "overlay"` (lub "vfs" dla prostoty, ale wolniejszy).

### Jak debugować problemy z siecią rootless?

- Sprawdź `podman network inspect podman`.
- Użyj `slirp4netns` logs: `podman run --rm -it --network host alpine ip route`.

### Jak używać GPU w kontenerach?

- `--device /dev/dri:/dev/dri` dla Intel/AMD.
- Dla NVIDIA: `--device /dev/nvidia0:/dev/nvidia0` + `--security-opt label=disable`.

---

## Rootless (szczegóły)

Tryb rootless pozwala uruchamiać kontenery bez uprawnień roota, co zwiększa bezpieczeństwo.

### Mapowania UID/GID

- Podman mapuje UID użytkownika hosta na UID 0 w kontenerze (domyślnie).
- Konfiguracja w `/etc/subuid` i `/etc/subgid` (np. `user:100000:65536`).
- Sprawdź: `podman unshare cat /proc/self/uid_map`.

### Opcja --userns=keep-id

- Zachowuje oryginalne UID/GID użytkownika w kontenerze (bez mapowania na root).
- Przydatne dla aplikacji, które wymagają konkretnych UID.
- Przykład: `podman run --userns=keep-id -v /home/user:/home/user:Z alpine whoami`.

### Ograniczenia rootless

- Brak dostępu do portów <1024 (rozwiązanie wyżej).
- Ograniczona obsługa urządzeń (np. GPU wymaga dodatkowych ustawień).
- Sieć przez slirp4netns (wolniejsza niż natywna).

### Włączenie rootless dla użytkownika

- Upewnij się, że użytkownik ma zakres UID w subuid/subgid.
- Jeśli nie: `sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 $USER`.

---

## Multi-arch i buildx

Podman wspiera budowanie obrazów dla różnych architektur (ARM64, x86_64, etc.).

### Budowanie dla wielu platform

```bash
# Lista dostępnych platform
podman info --format='{{.Host.RemoteSocket.Exists}}'

# Budowanie dla ARM64 na x86_64 (wymaga QEMU)
podman build --platform linux/arm64 -t myapp:arm64 .

# Budowanie dla wielu architektur jednocześnie
podman build --platform linux/amd64,linux/arm64 -t myapp:multi .

# Manifest list (multi-arch)
podman manifest create myapp:latest
podman manifest add myapp:latest myapp:amd64
podman manifest add myapp:latest myapp:arm64
podman manifest push myapp:latest registry.example.com/myapp:latest
```

### Emulacja architektur (QEMU)

```bash
# Instalacja QEMU (Fedora/RHEL)
sudo dnf install qemu-user-static

# Rejestracja formatów binfmt
sudo systemctl restart systemd-binfmt

# Test emulacji
podman run --rm --platform linux/arm64 alpine:latest uname -m
```

---

## Monitorowanie i logi

### Zaawansowane logowanie

```bash
# Różne sterowniki logów
podman run --log-driver journald nginx:alpine  # systemd journal
podman run --log-driver k8s-file nginx:alpine  # kubernetes format
podman run --log-driver json-file nginx:alpine # JSON (domyślny)

# Ograniczenie rozmiaru logów
podman run --log-opt max-size=10m --log-opt max-file=3 nginx:alpine

# Logi z timestampami i filtrowanie
podman logs --since="2h" --until="1h" myapp
podman logs --tail=50 --follow myapp
```

### Monitoring zasobów

```bash
# Stats w czasie rzeczywistym
podman stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Export metryk do pliku
podman stats --format json > metrics.json

# Pojedynczy pomiar
podman stats --no-stream myapp
```

### Integracja z systemd journal

```bash
# Logi kontenerów w journal
journalctl CONTAINER_NAME=myapp -f

# Wszystkie logi kontenerów
journalctl -t podman -f
```

---

## CI/CD i automatyzacja

### Budowanie w CI/CD

```bash
# Rootless w CI (GitLab CI, GitHub Actions)
podman build --layers=false -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
echo $CI_REGISTRY_PASSWORD | podman login -u $CI_REGISTRY_USER --password-stdin $CI_REGISTRY

# Push z retry
for i in {1..3}; do podman push $IMAGE && break || sleep 5; done
```

### Testowanie obrazów

```bash
# Skanowanie podatności (jeśli masz skopeo/trivy)
podman save myapp:latest | trivy image --input /dev/stdin

# Test kontenera
podman run --rm --name test myapp:latest /app/healthcheck.sh
test_exit_code=$?
podman run --rm myapp:latest /app/run-tests.sh

# Szybkie testy smoke
timeout 30 podman run --rm -p 8080:8080 myapp:latest &
sleep 5 && curl -f http://localhost:8080/health
```

### Automatyzacja z systemd timers

```bash
# Timer dla backup kontenerów
# ~/.config/systemd/user/backup-containers.timer
[Unit]
Description=Backup containers daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

### Skrypty utility

```bash
# Czyszczenie starych obrazów (skrypt)
#!/bin/bash
# cleanup-old-images.sh
DAYS=${1:-7}
podman image ls --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" | \
  while read image date; do
    if [[ $(date -d "$date" +%s) -lt $(date -d "$DAYS days ago" +%s) ]]; then
      echo "Removing old image: $image"
      podman rmi "$image" 2>/dev/null || true
    fi
  done
```

---

Masz inne przypadki użycia? Dodaj notatki i przykłady poniżej.
