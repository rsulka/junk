#!/bin/bash

# Wczytanie konfiguracji
CONFIG_FILE=".mb_config"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "BŁĄD: Plik konfiguracyjny '${CONFIG_FILE}' nie został znaleziony."
    exit 1
fi

# Sprawdzenie, czy zainstalowane są wymagane narzędzia
if ! command -v jq &> /dev/null; then
    echo "BŁĄD: Narzędzie 'jq' nie jest zainstalowane."
    exit 1
fi
if ! command -v git &> /dev/null; then
    echo "BŁĄD: Narzędzie 'git' nie jest zainstalowane."
    exit 1
fi

REPO=""
APPROVED_ONLY=false
MERGE_DIR=""
while getopts ":ar:d:" opt; do
  case ${opt} in
    a ) APPROVED_ONLY=true ;;
    r ) REPO=$OPTARG ;;
    d ) MERGE_DIR=$OPTARG ;;
    \? ) echo "Nieprawidłowa opcja: -$OPTARG" 1>&2; exit 1 ;;
    : ) echo "Opcja -$OPTARG wymaga argumentu." 1>&2; exit 1;;
  esac
done

# Sprawdzenie, czy nazwa repozytorium została podana
if [ -z "$REPO" ]; then
    echo "BŁĄD: Nazwa repozytorium nie została podana. Użyj opcji -r <nazwa_repozytorium>."
    exit 1
fi

# Ustawienie katalogu docelowego
if [ -z "$MERGE_DIR" ]; then
    MERGE_DIR="$HOME/${REPO}_merged"
    echo "Informacja: Katalog docelowy nie został podany. Używam domyślnego: ${MERGE_DIR}"
fi

# --- Logika specyficzna dla platformy ---
if [ "$IS_BITBUCKET_SERVER" = true ]; then
    # Ustawienia dla Bitbucket Server/Data Center
    API_URL="https://${BITBUCKET_HOST}/rest/api/1.0/projects/${BITBUCKET_PROJECT_OR_WORKSPACE}/repos/${REPO}/pull-requests?state=OPEN&order=NEWEST"
    REPO_URL="ssh://git@${BITBUCKET_HOST}/${BITBUCKET_PROJECT_OR_WORKSPACE}/${REPO}.git"
    JQ_BRANCH_PATH='.fromRef.displayId'
    JQ_APPROVED_FILTER='select(.reviewers[] | .approved == true)'
else
    # Ustawienia dla Bitbucket Cloud
    API_URL="https://api.bitbucket.org/2.0/repositories/${BITBUCKET_PROJECT_OR_WORKSPACE}/${REPO}/pullrequests?state=OPEN&fields=%2Bvalues.participants"
    REPO_URL="git@bitbucket.org:${BITBUCKET_PROJECT_OR_WORKSPACE}/${REPO}.git"
    JQ_BRANCH_PATH='.source.branch.name'
    JQ_APPROVED_FILTER='select(.participants[] | .approved == true)'
fi
# --- Koniec logiki specyficznej dla platformy ---

echo "Krok 1: Pobieranie informacji o aktywnych pull requestach..."

api_response=$(curl -s -H "Authorization: Bearer ${BITBUCKET_API_TOKEN}" "${API_URL}")

if [ "$APPROVED_ONLY" = true ]; then
    echo "Informacja: Filtruję tylko zatwierdzone (approved) pull requesty."
    branches=($(echo "$api_response" | jq -r ".values[] | ${JQ_APPROVED_FILTER} | ${JQ_BRANCH_PATH}"))
else
    branches=($(echo "$api_response" | jq -r ".values[] | ${JQ_BRANCH_PATH}"))
fi

if [ ${#branches[@]} -eq 0 ]; then
    if [ "$APPROVED_ONLY" = true ]; then
        echo "Nie znaleziono żadnych ZATWIERDZONYCH, otwartych pull requestów."
    else
        echo "Nie znaleziono żadnych otwartych pull requestów."
    fi
    exit 0
fi

echo "Znaleziono następujące gałęzie z otwartymi PR:"
printf " - %s\n" "${branches[@]}"
echo ""

# Klonowanie repozytorium i przygotowanie katalogu roboczego
echo "Krok 2: Przygotowywanie katalogu roboczego..."
rm -rf "${MERGE_DIR}"
git clone --quiet -b master "${REPO_URL}" "${MERGE_DIR}"
cd "${MERGE_DIR}"

echo "Krok 3: Analiza zmienionych plików w każdej gałęzi..."
declare -A file_branch_map
for branch in "${branches[@]}"; do
    echo " - Przetwarzanie gałęzi: ${branch}"
    git fetch --quiet origin "${branch}"
    
    # Użycie pętli while read dla poprawnego i bezpiecznego parsowania nazw plików
    while IFS= read -r file; do
        if [ -n "$file" ]; then # Zabezpieczenie przed pustymi liniami
            file_branch_map["$file"]+="${branch} "
        fi
    done < <(git diff --name-only master "origin/${branch}")
done

echo ""
echo "Krok 4: Scalanie plików i rozwiązywanie konfliktów..."
for file in "${!file_branch_map[@]}"; do
    sources=(${file_branch_map[$file]})
    branch_name=""

    if [[ ${#sources[@]} -eq 1 ]]; then
        branch_name=${sources[0]}
        echo " > Zmiany w pliku '${file}' pochodzą tylko z gałęzi '${branch_name}'."
    else
        echo " ! KONFLIKT: Plik '${file}' został zmodyfikowany w kilku gałęziach: ${sources[@]}"
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

    # Sprawdzenie, czy plik istnieje w wybranej gałęzi (mógł zostać usunięty)
    if git cat-file -e "origin/${branch_name}:${file}" 2>/dev/null; then
        # Plik istnieje w gałęzi źródłowej - pobieramy go
        echo "   -> Stosuję zmiany dla '${file}' z gałęzi '${branch_name}'."
        # Upewnij się, że katalog dla pliku istnieje
        mkdir -p "$(dirname "${file}")"
        git show "origin/${branch_name}:${file}" > "${file}"
    else
        # Plik nie istnieje w gałęzi źródłowej - został usunięty
        echo "   -> Plik '${file}' został usunięty w '${branch_name}'. Usuwam go z katalogu wynikowego."
        rm -f "${file}"
    fi
done

rm -rf .git
cd ..
echo ""
echo "====================================================================="
echo "Zakończono! Połączone pliki znajdują się w katalogu: '${MERGE_DIR}'"
echo "====================================================================="
