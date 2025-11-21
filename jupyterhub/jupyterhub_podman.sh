#!/usr/bin/env bash
set -euo pipefail

CMD="${1:-install}"

HOST_USER="${USER}"                           # systemowy użytkownik, np. rafal
HOST_HOME="${HOME}"
HUB_DATA_DIR="${HOST_HOME}/jupyterhub-data"
BUILD_DIR="${HOST_HOME}/jupyter-build"
NETWORK_NAME="jupyterhub-network"
HUB_IMAGE="my-jupyterhub"
USER_IMAGE="my-jupyter-notebook"
CONTAINER_NAME="jupyterhub-container"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Nie uruchamiaj tego skryptu jako root. Użyj zwykłego użytkownika z sudo."
  exit 1
fi

### FUNKCJE POMOCNICZE ###

clean_all() {
  echo "=== CZYSZCZENIE INSTALACJI JUPYTERHUBA ==="
  echo "Zostaną usunięte:"
  echo "  - kontener Huba: ${CONTAINER_NAME}"
  echo "  - wszystkie kontenery użytkowników jupyter-*"
  echo "  - sieć Podmana: ${NETWORK_NAME}"
  echo "  - katalogi: ${HUB_DATA_DIR} oraz ${BUILD_DIR}"
  echo

  read -r -p "Na pewno chcesz to zrobić? (wpisz 'TAK' żeby kontynuować): " ANSWER
  if [[ "${ANSWER:-}" != "TAK" && "${ANSWER:-}" != "Tak" && "${ANSWER:-}" != "tak" ]]; then
    echo "Przerwano czyszczenie."
    exit 0
  fi

  echo
  echo "== 1. Zatrzymanie i usunięcie kontenera Huba =="

  podman stop "${CONTAINER_NAME}" 2>/dev/null || true
  podman rm "${CONTAINER_NAME}" 2>/dev/null || true

  echo
  echo "== 2. Usunięcie kontenerów użytkowników (jupyter-*) =="

  # Usuwamy wszystkie kontenery, których nazwa zaczyna się od 'jupyter-'
  mapfile -t JUPYTER_CONTAINERS < <(podman ps -a --format '{{.ID}} {{.Names}}' | awk '$2 ~ /^jupyter-/ {print $1}')
  if [[ "${#JUPYTER_CONTAINERS[@]}" -gt 0 ]]; then
    echo "Usuwam kontenery:"
    printf '  %s\n' "${JUPYTER_CONTAINERS[@]}"
    podman rm -f "${JUPYTER_CONTAINERS[@]}" || true
  else
    echo "Brak kontenerów jupyter-* do usunięcia."
  fi

  echo
  echo "== 3. Usunięcie sieci Podmana =="

  podman network rm "${NETWORK_NAME}" 2>/dev/null || true

  echo
  echo "== 4. Usunięcie katalogów z danymi i buildem =="

  sudo rm -rf "${HUB_DATA_DIR}" "${BUILD_DIR}"

  echo
  echo "=== CZYSZCZENIE ZAKOŃCZONE ==="
  exit 0
}

install_all() {
  echo "=== Instalacja / aktualizacja JupyterHub + Podman (użytkownik: ${HOST_USER}) ==="

  echo
  echo "== KROK 1: Sieć Podmana =="
  if podman network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
    echo "Sieć ${NETWORK_NAME} już istnieje – pomijam tworzenie."
  else
    podman network create "${NETWORK_NAME}"
    echo "Utworzyłem sieć ${NETWORK_NAME}."
  fi

  echo
  echo "== KROK 2: Katalogi na dane JupyterHuba =="
  mkdir -p "${HUB_DATA_DIR}/hub_data"
  mkdir -p "${HUB_DATA_DIR}/user_home"
  echo "Katalogi:"
  echo "  - ${HUB_DATA_DIR}/hub_data"
  echo "  - ${HUB_DATA_DIR}/user_home"

  echo
  echo "== KROK 3: Klucz JUPYTERHUB_CRYPT_KEY =="
  if [[ -f "${HUB_DATA_DIR}/jupyterhub.env" ]]; then
    echo "Plik ${HUB_DATA_DIR}/jupyterhub.env już istnieje – nie nadpisuję."
  else
    echo "JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)" > "${HUB_DATA_DIR}/jupyterhub.env"
    echo "Utworzyłem ${HUB_DATA_DIR}/jupyterhub.env."
  fi

  echo
  echo "== KROK 4: Katalog build i Dockerfile.hub =="
  mkdir -p "${BUILD_DIR}"
  cd "${BUILD_DIR}"

  cat > Dockerfile.hub << 'EOF'
FROM quay.io/jupyterhub/jupyterhub:latest

# JupyterHub + DockerSpawner + idle-culler + Paramiko (SSH)
RUN pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-idle-culler \
    paramiko
EOF

  echo "Zbuduję obraz Huba: ${HUB_IMAGE}"
  podman build -t "${HUB_IMAGE}" -f Dockerfile.hub .

  echo
  echo "== KROK 5: Dockerfile.user (obraz użytkownika) =="

  cat > Dockerfile.user << 'EOF'
FROM quay.io/jupyter/base-notebook:latest

USER root
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Instalujemy pakiety globalnie jako root, żeby nie były przykryte przez wolumen
RUN pip install --no-cache-dir \
    pandas \
    fabric

# Wracamy do domyślnego użytkownika jovyan
USER ${NB_UID}

# Ustawiamy domyślny katalog notebooków i pip do ~/.local
ENV DOCKER_NOTEBOOK_DIR=/home/jovyan \
    PIP_USER=true

WORKDIR /home/jovyan
EOF

  echo "Zbuduję obraz użytkownika: ${USER_IMAGE}"
  podman build -t "${USER_IMAGE}" -f Dockerfile.user .

  echo
  echo "== KROK 6: Konfiguracja JupyterHuba (jupyterhub_config.py) =="
  cd "${HUB_DATA_DIR}/hub_data"

  cat > jupyterhub_config.py << EOF
import os
import asyncio
import paramiko
from jupyterhub.auth import Authenticator

c = get_config()

# --- Własny Authenticator: logowanie przez SSH na hosta ---
class MySSHAuthenticator(Authenticator):
    # host widziany z kontenera rootless Podmana
    ssh_host = os.environ.get("SSH_AUTH_HOST", "host.containers.internal")
    ssh_port = int(os.environ.get("SSH_AUTH_PORT", "22"))

    async def authenticate(self, handler, data):
        username = data["username"]
        password = data["password"]

        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(
            None, self._check_ssh, username, password
        )
        return username if ok else None

    def _check_ssh(self, username, password):
        client = paramiko.SSHClient()
        # Akceptujemy host przy pierwszym połączeniu (ruch lokalny kontener -> host)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                self.ssh_host,
                port=self.ssh_port,
                username=username,
                password=password,
                timeout=10,
                look_for_keys=False,
                allow_agent=False,
            )
            client.close()
            return True
        except Exception as e:
            self.log.warning(
                f"SSH Auth failed for {username}@{self.ssh_host}:{self.ssh_port}: {e}"
            )
            return False

# --- Sieć / Hub ---
c.JupyterHub.bind_url = "http://:8000"
c.JupyterHub.hub_connect_ip = "jupyterhub-container"  # nazwa kontenera Huba w sieci Podmana

# --- Auth przez SSH ---
c.JupyterHub.authenticator_class = MySSHAuthenticator

# Jedyny użytkownik i admin Huba: ${HOST_USER}
c.Authenticator.admin_users = {"${HOST_USER}"}
c.Authenticator.allowed_users = {"${HOST_USER}"}

# --- DockerSpawner ---
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = "${USER_IMAGE}"
c.DockerSpawner.network_name = "${NETWORK_NAME}"
c.DockerSpawner.use_internal_ip = True

# Katalog roboczy w kontenerze usera (domyślnie w base-notebook)
notebook_dir = "/home/jovyan"
c.DockerSpawner.notebook_dir = notebook_dir

# Hostowy katalog na dane użytkownika
host_data_root = "${HUB_DATA_DIR}/user_home"

c.DockerSpawner.volumes = {
    f"{host_data_root}/{{username}}": notebook_dir
}

# Usuwaj kontener po wylogowaniu (dane zostają na wolumenie)
c.DockerSpawner.remove = True

# Domyślnie JupyterLab
c.Spawner.default_url = "/lab"

# --- Idle culler: sprzątanie nieaktywnych serwerów ---
c.JupyterHub.services = [
    {
        "name": "idle-culler",
        "admin": True,
        "command": [
            "python",
            "-m", "jupyterhub_idle_culler",
            "--timeout=3600",
            "--cull-every=600",
        ],
    }
]
EOF

  echo "Plik konfiguracyjny Huba zapisany w: ${HUB_DATA_DIR}/hub_data/jupyterhub_config.py"

  echo
  echo "== KROK 7: Katalog użytkownika ${HOST_USER} + podman unshare =="

  mkdir -p "${HUB_DATA_DIR}/user_home/${HOST_USER}"

  echo "Ustawiam właściciela (z perspektywy kontenera: jovyan = UID 1000, GID 100)..."
  podman unshare chown -R 1000:100 "${HUB_DATA_DIR}/user_home"

  sudo chmod 755 "${HUB_DATA_DIR}/user_home/${HOST_USER}"

  echo
  echo "== KROK 8: Uruchomienie kontenera JupyterHuba =="

  cd "${HUB_DATA_DIR}"

  echo "Zatrzymuję poprzedni kontener (jeśli istnieje)..."
  podman stop "${CONTAINER_NAME}" 2>/dev/null || true
  podman rm "${CONTAINER_NAME}" 2>/dev/null || true

  USER_UID="$(id -u)"

  podman run -d \
    --name "${CONTAINER_NAME}" \
    --network "${NETWORK_NAME}" \
    --security-opt label=disable \
    --env-file "${HUB_DATA_DIR}/jupyterhub.env" \
    -p 8000:8000 \
    -v "/run/user/${USER_UID}/podman/podman.sock:/var/run/docker.sock:z" \
    -v "${HUB_DATA_DIR}/hub_data:/srv/jupyterhub:z" \
    -e DOCKER_HOST="unix:///var/run/docker.sock" \
    -e SSH_AUTH_HOST="host.containers.internal" \
    -e SSH_AUTH_PORT="22" \
    "${HUB_IMAGE}"

  echo
  echo "=== INSTALACJA ZAKOŃCZONA ==="
  echo "JupyterHub powinien być dostępny pod adresem: http://localhost:8000"
  echo
  echo "Logowanie do Huba:"
  echo "  użytkownik: ${HOST_USER}"
  echo "  hasło:      takie jak do 'ssh ${HOST_USER}@<host>' (hasło systemowe)"
}

### GŁÓWNA LOGIKA ###

case "${CMD}" in
  install|"")
    install_all
    ;;
  clean)
    clean_all
    ;;
  *)
    echo "Użycie: $0 [install|clean]"
    exit 1
    ;;
esac
