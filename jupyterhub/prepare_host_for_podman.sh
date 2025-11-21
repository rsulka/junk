#!/usr/bin/env bash
set -euo pipefail

HOST_USER="${USER}"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Nie uruchamiaj tego skryptu jako root. Użyj zwykłego użytkownika z sudo."
  exit 1
fi

echo "=== Przygotowanie hosta dla rootless Podmana (użytkownik: ${HOST_USER}) ==="

echo
echo "== KROK 1: subuid/subgid dla rootless Podmana =="

if ! grep -q "^${HOST_USER}:" /etc/subuid 2>/dev/null || ! grep -q "^${HOST_USER}:" /etc/subgid 2>/dev/null; then
  echo "Brak wpisów w /etc/subuid / /etc/subgid dla ${HOST_USER} – dodaję zakres 100000-165535..."
  sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "${HOST_USER}"
  echo "UWAGA: po tym kroku dobrze jest się wylogować i zalogować ponownie."
else
  echo "subuid/subgid dla ${HOST_USER} już istnieją – OK."
fi

echo
echo "== KROK 2: Instalacja pakietów (Podman, Python, narzędzia) =="

sudo apt update
sudo apt install -y \
  podman podman-plugins \
  slirp4netns fuse-overlayfs uidmap \
  git python3-pip openssl

echo
echo "== KROK 3: Włączenie linger + podman.socket dla użytkownika =="

loginctl enable-linger "${HOST_USER}" || true

systemctl --user daemon-reload || true
systemctl --user enable --now podman.socket

echo
echo "Podman socket powinien być dostępny pod:"
echo "  unix:///run/user/$(id -u)/podman/podman.sock"

echo
echo "=== Przygotowanie hosta zakończone. ==="
echo "Jeśli subuid/subgid były dopiero co dodane, warto się raz wylogować i zalogować ponownie."
