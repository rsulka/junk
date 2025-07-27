#!/bin/bash
set -e -o pipefail -u

# ==============================================================================
# Funkcje pomocnicze
# ==============================================================================

# Wyświetla komunikat o błędzie i kończy działanie skryptu.
# Użycie: die "Komunikat o błędzie"
die() {
    echo >&2 "BŁĄD: $1"
    exit 1
}

# Sprawdza, czy wymagane narzędzia są zainstalowane.
check_dependencies() {
    command -v jq &>/dev/null || die "Narzędzie 'jq' nie jest zainstalowane. Proszę je zainstalować."
    command -v git &>/dev/null || die "Narzędzie 'git' nie jest zainstalowane. Proszę je zainstalować."
}

# Wyświetla instrukcję użycia skryptu.
usage() {
    cat <<EOF
Użycie: $(basename "$0") -r <nazwa-repozytorium> [-a] [-d /sciezka/do/katalogu]

Skrypt do pobierania i łączenia zmian z otwartych pull requestów w Bitbucket.

Parametry:
  -r <nazwa-repo>   (Wymagany) Nazwa repozytorium w Bitbucket.
  -a                (Opcjonalny) Pobieraj zmiany tylko z zatwierdzonych (approved) PR.
  -d <katalog>      (Opcjonalny) Ścieżka do katalogu wynikowego.
                    Domyślnie: ~/<nazwa-repo>_merged
EOF
    exit 1
}

# ==============================================================================
# Główna logika skryptu
# ==============================================================================

main() {
    # --- Domyślne wartości ---
    local REPO=""
    local APPROVED_ONLY=false
    local MERGE_DIR=""
    local CONFIG_FILE=".mb_config"

    # --- Parsowanie opcji ---
    while getopts ":ar:d:" opt; do
      case ${opt} in
        a ) APPROVED_ONLY=true ;;
        r ) REPO=$OPTARG ;;
        d ) MERGE_DIR=$OPTARG ;;
        \? ) echo "Nieprawidłowa opcja: -$OPTARG" >&2; usage ;;
        : ) echo "Opcja -$OPTARG wymaga argumentu." >&2; usage ;;
      esac
    done

    # --- Walidacja i konfiguracja ---
    [ -z "$REPO" ] && die "Nazwa repozytorium jest wymagana. Użyj opcji -r."

    [ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE" || die "Plik konfiguracyjny '${CONFIG_FILE}' nie został znaleziony."
    
    # Sprawdzenie, czy kluczowe zmienne konfiguracyjne są ustawione
    : "${BITBUCKET_HOST?Zmienna BITBUCKET_HOST nie jest ustawiona w $CONFIG_FILE}"
    : "${IS_BITBUCKET_SERVER?Zmienna IS_BITBUCKET_SERVER nie jest ustawiona w $CONFIG_FILE}"
    : "${BITBUCKET_PROJECT_OR_WORKSPACE?Zmienna BITBUCKET_PROJECT_OR_WORKSPACE nie jest ustawiona w $CONFIG_FILE}"
    : "${BITBUCKET_API_TOKEN?Zmienna BITBUCKET_API_TOKEN nie jest ustawiona w $CONFIG_FILE}"

    if [ -z "$MERGE_DIR" ]; then
        MERGE_DIR="$HOME/${REPO}_merged"
        echo "Informacja: Katalog docelowy nie został podany. Używam domyślnego: ${MERGE_DIR}"
    fi

    # --- Ustawienia specyficzne dla platformy ---
    local API_URL REPO_URL JQ_BRANCH_PATH JQ_APPROVED_FILTER
    if [ "$IS_BITBUCKET_SERVER" = true ]; then
        API_URL="https://${BITBUCKET_HOST}/rest/api/1.0/projects/${BITBUCKET_PROJECT_OR_WORKSPACE}/repos/${REPO}/pull-requests?state=OPEN&order=NEWEST&limit=100"
        REPO_URL="ssh://git@${BITBUCKET_HOST}/${BITBUCKET_PROJECT_OR_WORKSPACE}/${REPO}.git"
        JQ_BRANCH_PATH='.fromRef.displayId'
        JQ_APPROVED_FILTER='select(.reviewers[] | .approved == true)'
    else
        API_URL="https://api.bitbucket.org/2.0/repositories/${BITBUCKET_PROJECT_OR_WORKSPACE}/${REPO}/pullrequests?state=OPEN&fields=%2Bvalues.participants"
        REPO_URL="git@bitbucket.org:${BITBUCKET_PROJECT_OR_WORKSPACE}/${REPO}.git"
        JQ_BRANCH_PATH='.source.branch.name'
        JQ_APPROVED_FILTER='select(.participants[] | .approved == true)'
    fi

    # --- Krok 1: Pobieranie informacji o PR ---
    echo "Krok 1: Pobieranie informacji o aktywnych pull requestach..."
    local api_response
    api_response=$(curl -s -H "Authorization: Bearer ${BITBUCKET_API_TOKEN}" "${API_URL}")

    local jq_query=".values[]"
    if [ "$APPROVED_ONLY" = true ]; then
        echo "Informacja: Filtruję tylko zatwierdzone (approved) pull requesty."
        jq_query+=" | ${JQ_APPROVED_FILTER}"
    fi
    jq_query+=" | ${JQ_BRANCH_PATH}"

    readarray -t branches < <(echo "$api_response" | jq -r "$jq_query")

    if [ ${#branches[@]} -eq 0 ]; then
        echo "Nie znaleziono żadnych pasujących otwartych pull requestów."
        exit 0
    fi

    echo "Znaleziono następujące gałęzie z otwartymi PR:"
    printf " - %s\n" "${branches[@]}"
    echo ""

    # --- Krok 2: Przygotowanie katalogu roboczego ---
    echo "Krok 2: Przygotowywanie katalogu roboczego..."
    rm -rf "${MERGE_DIR}"
    git clone --quiet -b master "${REPO_URL}" "${MERGE_DIR}"
    
    # Użycie subshell do zmiany katalogu, aby uniknąć `cd ..`
    (
        cd "${MERGE_DIR}"

        # --- Krok 3: Analiza zmienionych plików ---
        echo "Krok 3: Analiza zmienionych plików w każdej gałęzi..."
        echo "Pobieram wszystkie potrzebne gałęzie..."
        git fetch --quiet origin "${branches[@]}"

        declare -A file_branch_map
        for branch in "${branches[@]}"; do
            echo " - Przetwarzanie gałęzi: ${branch}"
            while IFS= read -r file; do
                [ -n "$file" ] && file_branch_map["$file"]+="${branch} "
            done < <(git diff --name-only master "origin/${branch}")
        done
        echo ""

        # --- Krok 4: Scalanie plików i rozwiązywanie konfliktów ---
        echo "Krok 4: Scalanie plików i rozwiązywanie konfliktów..."
        for file in "${!file_branch_map[@]}"; do
            local sources=(${file_branch_map[$file]})
            local branch_name=""

            if [[ ${#sources[@]} -eq 1 ]]; then
                branch_name=${sources[0]}
                echo " > Zmiany w pliku '${file}' pochodzą tylko z gałęzi '${branch_name}'."
            else
                echo " ! KONFLIKT: Plik '${file}' został zmodyfikowany w kilku gałęziach: ${sources[*]}"
                PS3="Wybierz, z której gałęzi pobrać wersję pliku '${file}': "
                select choice in "${sources[@]}"; do
                    if [[ -n "$choice" ]]; then
                        branch_name=$choice
                        break
                    else
                        echo "Nieprawidłowy wybór. Spróbuj ponownie."
                    fi
                done
            fi

            if git cat-file -e "origin/${branch_name}:${file}" 2>/dev/null; then
                echo "   -> Stosuję zmiany dla '${file}' z gałęzi '${branch_name}'."
                mkdir -p "$(dirname "${file}")"
                git show "origin/${branch_name}:${file}" > "${file}"
            else
                echo "   -> Plik '${file}' został usunięty w '${branch_name}'. Usuwam go."
                rm -f "${file}"
            fi
        done

        rm -rf .git
    )

    echo ""
    echo "====================================================================="
    echo "Zakończono! Połączone pliki znajdują się w katalogu: '${MERGE_DIR}'"
    echo "====================================================================="
}


# ==============================================================================
# Uruchomienie skryptu
# ==============================================================================
check_dependencies
main "$@"