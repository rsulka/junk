#!/bin/bash

# branch_cleaner.sh - Skrypt do klonowania repozytorium Bitbucket i usuwania
# gałęzi, które zostały zmergowane do master lub są starsze niż 90 dni.

set -e
set -o pipefail

# --- Domyślne ustawienia ---
REPO_NAME=""
BITBUCKET_USER=""
DAYS_OLD=90
DRY_RUN=false
INTERACTIVE=false
# Główne gałęzie, które nigdy nie powinny być usunięte
PROTECTED_BRANCHES=("master" "main" "develop")

# --- Funkcje ---

# Funkcja wyświetlająca pomoc
usage() {
  echo "Użycie: $0 -u <użytkownik> -r <nazwa_repo> [opcje]"
  echo ""
  echo "Opcje:"
  echo "  -r <nazwa_repo>     (Wymagane) Nazwa repozytorium na Bitbucket (np. 'my-awesome-project')."
  echo "  --dry-run           Tryb symulacji. Wyświetla gałęzie do usunięcia, ale ich nie usuwa."
  echo "  -i                  Tryb interaktywny. Pyta o potwierdzenie przed usunięciem każdej gałęzi."
  echo "  -h,--help          Wyświetla tę pomoc."
  echo ""
  echo "Przykład:"
  echo "  $0 -r my-repo --dry-run"
  echo "  $0 -r my-repo -i"
}

# --- Parsowanie argumentów ---
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -r) REPO_NAME="$2"; shift ;;
    --dry-run) DRY_RUN=true ;;
    -i) INTERACTIVE=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Nieznana opcja: $1"; usage; exit 1 ;;
  esac
  shift
done

# --- Walidacja argumentów ---
if [ -z "$REPO_NAME" ]; then
  echo "Błąd: Opcja -r (nazwa repozytorium) jest wymagana."
  usage
  exit 1
fi

# --- Przygotowanie środowiska ---
TEMP_DIR=$(mktemp -d)
# Ustawienie pułapki, aby posprzątać katalog tymczasowy po zakończeniu skryptu
trap 'cd / && echo "Sprzątanie katalogu tymczasowego..." && rm -rf "$TEMP_DIR"' EXIT

REPO_URL="ssh://git@bitbucket:7999/cri/${REPO_NAME}.git"

echo "Klonowanie repozytorium z $REPO_URL..."
git clone --quiet "$REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"

echo "Aktualizowanie stanu z repozytorium zdalnego 'origin'..."
git fetch "origin" --prune

# --- Zbieranie gałęzi do usunięcia ---

echo "Wyszukiwanie gałęzi do usunięcia..."

# 1. Gałęzie zmergowane do master
MERGED_BRANCHES=$(git branch -r --merged origin/master | sed 's/ *origin\///' | tr -d ' *')

# 2. Gałęzie starsze niż 90 dni
CUTOFF_DATE=$(date -d "$DAYS_OLD days ago" +%s)
OLD_BRANCHES=""

# Używamy formatu iso8601 dla daty (bez spacji) i tabulatora jako separatora.
while IFS=$'\t' read -r commit_date_iso branch_name; do
    commit_date_s=$(date -d "$commit_date_iso" +%s)

    if (( commit_date_s < CUTOFF_DATE )); then
        # `refname:short` dla gałęzi zdalnych to 'origin/nazwa', więc usuwamy prefix.
        OLD_BRANCHES+="$(echo "$branch_name" | sed 's/^origin\///')\n"
    fi
done < <(git for-each-ref --sort=committerdate refs/remotes/origin/ --format='%(committerdate:iso8601)	%(refname:short)')


# --- Łączenie, filtrowanie i usuwanie ---

# Łączenie list, sortowanie, usuwanie duplikatów i pustych linii
ALL_CANDIDATES=$(echo -e "$MERGED_BRANCHES\n$OLD_BRANCHES" | sed '/^$/d' | sort -u)

FINAL_BRANCHES_TO_DELETE=""
for branch in $ALL_CANDIDATES; do
  # Pomijamy wskaźnik HEAD, który może się pojawić
  if [[ "$branch" == "HEAD" || "$branch" == "HEAD->" ]]; then
    continue
  fi

  is_protected=false
  # Sprawdzanie, czy gałąź jest na liście chronionych
  for protected in "${PROTECTED_BRANCHES[@]}"; do
    if [[ "$branch" == "$protected" ]]; then
      is_protected=true
      break
    fi
  done

  if ! $is_protected; then
    FINAL_BRANCHES_TO_DELETE+="$branch\n"
  fi
done

# Usuwanie ostatniej nowej linii, jeśli istnieje
FINAL_BRANCHES_TO_DELETE=$(echo -e "$FINAL_BRANCHES_TO_DELETE" | sed '/^$/d')

if [ -z "$FINAL_BRANCHES_TO_DELETE" ]; then
  echo "Brak gałęzi do usunięcia. Twoje repozytorium jest czyste!"
  exit 0
fi

echo ""
echo "Znaleziono następujące gałęzie do usunięcia na zdalnym 'origin':"
echo "---"
echo "$FINAL_BRANCHES_TO_DELETE"
echo "---"

# --- Wykonanie akcji ---

if [ "$DRY_RUN" = true ]; then
  echo "Tryb --dry-run jest włączony. Żadne gałęzie nie zostaną usunięte."
  exit 0
fi

echo ""

# Używamy `while read` do iteracji po nazwach gałęzi
echo "$FINAL_BRANCHES_TO_DELETE" | while IFS= read -r branch; do
  if [ -z "$branch" ]; then continue; fi

  if [ "$INTERACTIVE" = true ]; then
    read -p "Czy na pewno usunąć zdalną gałąź 'origin/$branch'? [y/N] " -n 1 -r < /dev/tty
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "Usuwanie gałęzi: origin/$branch"
      git push origin --delete "$branch"
    else
      echo "Pominięto: origin/$branch"
    fi
  else
    echo "Usuwanie gałęzi: origin/$branch"
    git push origin --delete "$branch"
  fi
done

echo ""
echo "Czyszczenie gałęzi zakończone."
