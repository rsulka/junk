#!/bin/bash

# =============================================================================
# Project Archiver - Eksport i import projektu do/z jednego pliku tekstowego
# =============================================================================
# Użycie:
#   ./project_archiver.sh export <katalog_projektu> <plik_wyjściowy>
#   ./project_archiver.sh import <plik_archiwum> <katalog_docelowy>
# =============================================================================

set -e
set -o pipefail

# Sprawdź wymagane zależności
check_dependencies() {
    local missing=()
    for cmd in file base64 perl find stat; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Błąd: Brakujące zależności: ${missing[*]}" >&2
        exit 1
    fi
}
check_dependencies

VERSION="1.0.0"
MARKER_START="<<<FILE_START>>>"
MARKER_END="<<<FILE_END>>>"
MARKER_BINARY="<<<BINARY_BASE64>>>"
MARKER_EMPTY_DIR="<<<EMPTY_DIR>>>"

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Domyślne wzorce do ignorowania
DEFAULT_IGNORE_PATTERNS=(
    ".git"
    "__pycache__"
    "*.pyc"
    "*.pyo"
    ".pytest_cache"
    ".mypy_cache"
    ".venv"
    "venv"
    "env"
    ".env"
    "node_modules"
    ".idea"
    ".vscode"
    "*.egg-info"
    "dist"
    "build"
    ".tox"
    ".coverage"
    "htmlcov"
    "*.so"
    "*.dylib"
    "*.dll"
)

# ============================================================================
# Funkcje pomocnicze
# ============================================================================

print_usage() {
    echo -e "${GREEN}Project Archiver v${VERSION}${NC}"
    echo "Narzędzie do eksportu i importu projektów do/z jednego pliku tekstowego."
    echo ""
    echo -e "${YELLOW}Użycie:${NC}"
    echo "  $0 export <katalog_projektu> <plik_wyjściowy> [opcje]"
    echo "  $0 import <plik_archiwum> <katalog_docelowy> [opcje]"
    echo ""
    echo -e "${YELLOW}Komendy:${NC}"
    echo "  export    Eksportuj projekt do pliku tekstowego"
    echo "  import    Odtwórz projekt z pliku tekstowego"
    echo ""
    echo -e "${YELLOW}Opcje eksportu:${NC}"
    echo "  --no-ignore         Nie ignoruj domyślnych wzorców (.git, __pycache__, etc.)"
    echo "  --include-hidden    Dołącz ukryte pliki (domyślnie ignorowane)"
    echo "  --ignore <wzorzec>  Dodaj własny wzorzec do ignorowania"
    echo "  --max-size <MB>     Maksymalny rozmiar pliku do eksportu (domyślnie: 10MB)"
    echo ""
    echo -e "${YELLOW}Opcje importu:${NC}"
    echo "  --dry-run           Pokaż co zostanie utworzone bez faktycznego tworzenia"
    echo "  --force             Nadpisz istniejące pliki bez pytania"
    echo ""
    echo -e "${YELLOW}Przykłady:${NC}"
    echo "  $0 export ./moj_projekt ./backup.txt"
    echo "  $0 export ./moj_projekt ./backup.txt --include-hidden"
    echo "  $0 import ./backup.txt ./odtworzony_projekt"
    echo "  $0 import ./backup.txt ./odtworzony_projekt --dry-run"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[UWAGA]${NC} $1"
}

log_error() {
    echo -e "${RED}[BŁĄD]${NC} $1" >&2
}

# Sprawdź czy plik jest binarny (używa MIME type)
is_binary() {
    local file="$1"
    local mime_type
    
    # Sprawdź czy plik jest czytelny
    if [[ ! -r "$file" ]]; then
        log_warning "Nie można odczytać pliku: $file"
        return 0  # Traktuj jako binarny dla bezpieczeństwa
    fi
    
    # Użyj file z MIME type - najbardziej niezawodna metoda
    mime_type=$(file -b --mime-type "$file" 2>/dev/null)
    
    # Jeśli nie udało się określić MIME type, sprawdź null bytes
    if [[ -z "$mime_type" ]]; then
        # Fallback do testu null bytes
        if LC_ALL=C tr -d '\0' <"$file" 2>/dev/null | cmp -s - "$file" 2>/dev/null; then
            return 1  # Brak null bytes - tekst
        else
            return 0  # Ma null bytes lub błąd - binarny
        fi
    fi
    
    # Jeśli MIME type zaczyna się od "text/" to plik tekstowy
    if [[ "$mime_type" == text/* ]]; then
        return 1  # Plik tekstowy
    fi
    
    # Specjalne przypadki które są tekstowe mimo innego MIME
    case "$mime_type" in
        application/json|application/xml|application/javascript|\
        application/x-shellscript|application/x-perl|application/x-python|\
        application/x-ruby|application/x-php|application/sql|\
        application/x-empty|inode/x-empty)
            return 1  # Plik tekstowy
            ;;
    esac
    
    # Dodatkowe sprawdzenie: czy zawiera bajty null (pewny test binarności)
    # Używamy tr zamiast grep -P dla kompatybilności
    local tr_result
    if ! tr_result=$(LC_ALL=C tr -d '\0' <"$file" 2>/dev/null); then
        return 0  # Błąd odczytu - traktuj jako binarny
    fi
    
    if printf '%s' "$tr_result" | cmp -s - "$file" 2>/dev/null; then
        :  # Brak null bytes - kontynuuj
    else
        # Sprawdź czy cmp faktycznie wykrył różnicę czy był błąd
        if [[ -s "$file" ]] && [[ -z "$tr_result" ]]; then
            return 0  # Plik ma zawartość ale tr ją usunął - same null bytes
        fi
        return 0  # Plik binarny (zawiera null bytes)
    fi
    
    # Jeśli MIME nie jest text/* ale nie ma null bytes, traktuj jako tekst
    # (np. pliki .md, .rst bez rozpoznanego typu)
    return 1
}

# Sprawdź czy ścieżka jest bezpieczna (brak path traversal)
is_safe_path() {
    local path="$1"
    
    # Odrzuć puste ścieżki
    if [[ -z "$path" ]]; then
        return 1
    fi
    
    # Odrzuć ścieżki zaczynające się od /
    if [[ "$path" == /* ]]; then
        return 1
    fi
    
    # Odrzuć ścieżki zawierające path traversal (../ lub /../ lub ..)
    # Ale pozwól na nazwy plików typu foo..bar.txt
    if [[ "$path" == ../* || "$path" == */../* || "$path" == */.. || "$path" == ".." ]]; then
        return 1
    fi
    
    return 0
}

# Sprawdź czy plik pasuje do wzorców ignorowania
should_ignore() {
    local path="$1"
    local full_path="$2"  # Opcjonalna pełna ścieżka do porównania
    local basename
    basename=$(basename "$path")
    
    for pattern in "${IGNORE_PATTERNS[@]}"; do
        # Sprawdź dokładne dopasowanie pełnej ścieżki (dla pliku wyjściowego)
        if [[ -n "$full_path" ]] && [[ "$full_path" == "$pattern" ]]; then
            return 0
        fi
        
        # Sprawdź dopasowanie wzorca używając globów:
        # 1. Basename pasuje do wzorca (np. "*.pyc", ".git", "node_modules")
        # 2. Pełna ścieżka pasuje do wzorca
        # 3. Wzorzec jest komponentem ścieżki (np. ".git" w "projekt/.git/config")
        case "$basename" in
            $pattern) return 0 ;;
        esac
        case "$path" in
            $pattern) return 0 ;;
            $pattern/*) return 0 ;;      # wzorzec na początku ścieżki
            */$pattern) return 0 ;;      # wzorzec na końcu ścieżki
            */$pattern/*) return 0 ;;    # wzorzec w środku ścieżki
        esac
    done
    return 1
}

# Pobierz względną ścieżkę
get_relative_path() {
    local file="$1"
    local base="$2"
    
    # Obsłuż przypadek gdy file == base
    if [[ "$file" == "$base" ]]; then
        echo ""
        return
    fi
    
    # Upewnij się że base kończy się bez /
    base="${base%/}"
    
    # Sprawdź czy file jest podścieżką base
    if [[ "$file" == "$base/"* ]]; then
        echo "${file#$base/}"
    else
        # Ścieżka nie jest podścieżką base - zwróć oryginalną
        echo "$file"
    fi
}

# ============================================================================
# Funkcja eksportu
# ============================================================================

do_export() {
    local project_dir="$1"
    local output_file="$2"
    shift 2
    
    # Domyślne ustawienia
    local use_ignore=true
    local include_hidden=false
    local max_size_mb=10
    IGNORE_PATTERNS=("${DEFAULT_IGNORE_PATTERNS[@]}")
    
    # Parsuj opcje
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-ignore)
                use_ignore=false
                IGNORE_PATTERNS=()
                shift
                ;;
            --include-hidden)
                include_hidden=true
                shift
                ;;
            --ignore)
                IGNORE_PATTERNS+=("$2")
                shift 2
                ;;
            --max-size)
                if [[ ! "$2" =~ ^[0-9]+$ ]]; then
                    log_error "--max-size wymaga liczby całkowitej (podano: '$2')"
                    exit 1
                fi
                max_size_mb="$2"
                shift 2
                ;;
            *)
                log_error "Nieznana opcja: $1"
                exit 1
                ;;
        esac
    done
    
    # Walidacja
    if [[ ! -d "$project_dir" ]]; then
        log_error "Katalog '$project_dir' nie istnieje!"
        exit 1
    fi
    
    # Konwertuj na ścieżkę absolutną
    project_dir=$(cd "$project_dir" && pwd)
    local project_name=$(basename "$project_dir")
    
    # Konwertuj output_file na ścieżkę absolutną
    local output_dir=$(dirname "$output_file")
    if ! mkdir -p "$output_dir" 2>/dev/null; then
        log_error "Nie można utworzyć katalogu wyjściowego: $output_dir"
        exit 1
    fi
    if ! cd "$output_dir" 2>/dev/null; then
        log_error "Nie można uzyskać dostępu do katalogu: $output_dir"
        exit 1
    fi
    output_file="$(pwd)/$(basename "$output_file")"
    cd - >/dev/null
    
    # Dodaj plik wyjściowy do wzorców ignorowania (zapobiegaj samozjadaniu)
    IGNORE_PATTERNS+=("$output_file")
    
    log_info "Eksportuję projekt: $project_dir"
    log_info "Plik wyjściowy: $output_file"
    
    # Rozpocznij eksport
    local file_count=0
    local dir_count=0
    local skipped_count=0
    local binary_count=0
    
    # Nagłówek pliku
    if ! cat > "$output_file" << EOF
# =============================================================================
# PROJECT ARCHIVE - Wygenerowano przez Project Archiver v${VERSION}
# =============================================================================
# Projekt: ${project_name}
# Data: $(date '+%Y-%m-%d %H:%M:%S')
# System: $(uname -s) $(uname -r)
# =============================================================================
# 
# Aby odtworzyć ten projekt, użyj:
#   ./project_archiver.sh import <ten_plik> <katalog_docelowy>
#
# =============================================================================

<<<PROJECT_NAME>>>
${project_name}
<<<PROJECT_NAME_END>>>

<<<FILES_START>>>
EOF
    then
        log_error "Nie można utworzyć pliku wyjściowego: $output_file"
        exit 1
    fi
    
    # Sprawdź czy plik został utworzony
    if [[ ! -f "$output_file" ]]; then
        log_error "Plik wyjściowy nie został utworzony: $output_file"
        exit 1
    fi

    # Znajdź wszystkie pliki i katalogi
    local find_opts=()
    if [[ "$include_hidden" == false ]]; then
        find_opts+=(-not -path '*/\.*')
    fi
    
    # Znajdź puste katalogi
    while IFS= read -r -d '' dir; do
        local rel_path=$(get_relative_path "$dir" "$project_dir")
        
        # Pomiń katalog główny projektu (pusta ścieżka względna)
        if [[ -z "$rel_path" || "$rel_path" == "." ]]; then
            continue
        fi
        
        if [[ "$use_ignore" == true ]] && should_ignore "$rel_path" "$dir"; then
            continue
        fi
        
        # Sprawdź czy katalog jest pusty
        if [[ -z "$(ls -A "$dir" 2>/dev/null)" ]]; then
            echo "" >> "$output_file"
            echo "${MARKER_EMPTY_DIR}" >> "$output_file"
            echo "${rel_path}" >> "$output_file"
            dir_count=$((dir_count + 1))
            log_info "Pusty katalog: $rel_path"
        fi
    done < <(find "$project_dir" -type d "${find_opts[@]}" -print0 2>/dev/null)
    
    # Znajdź wszystkie pliki
    while IFS= read -r -d '' file; do
        local rel_path=$(get_relative_path "$file" "$project_dir")
        
        # Sprawdź czy ignorować
        if [[ "$use_ignore" == true ]] && should_ignore "$rel_path" "$file"; then
            skipped_count=$((skipped_count + 1))
            continue
        fi
        
        # Sprawdź rozmiar pliku
        local file_size
        # Próbuj format Linux, potem macOS/BSD
        file_size=$(stat -c%s "$file" 2>/dev/null) || file_size=$(stat -f%z "$file" 2>/dev/null) || file_size=""
        local max_size_bytes=$((max_size_mb * 1024 * 1024))
        
        if [[ -z "$file_size" ]] || ! [[ "$file_size" =~ ^[0-9]+$ ]]; then
            log_warning "Nie można określić rozmiaru: $rel_path"
            skipped_count=$((skipped_count + 1))
            continue
        fi
        
        if [[ "$file_size" -gt "$max_size_bytes" ]]; then
            log_warning "Pominięto (za duży): $rel_path ($(($file_size / 1024 / 1024))MB)"
            skipped_count=$((skipped_count + 1))
            continue
        fi
        
        echo "" >> "$output_file"
        echo "${MARKER_START}" >> "$output_file"
        echo "PATH: ${rel_path}" >> "$output_file"
        
        # Sprawdź czy plik jest binarny
        if is_binary "$file"; then
            echo "TYPE: binary" >> "$output_file"
            echo "${MARKER_BINARY}" >> "$output_file"
            base64 "$file" >> "$output_file"
            echo "" >> "$output_file"
            echo "${MARKER_BINARY}" >> "$output_file"
            binary_count=$((binary_count + 1))
            log_info "Plik binarny: $rel_path"
        else
            # Oblicz długość pliku w bajtach (przed command substitution)
            local content_length
            content_length=$(wc -c < "$file")
            
            # Policz ile trailing newlines ma plik
            local trailing_newline_count=0
            if [[ -s "$file" ]]; then
                # Policz trailing newlines od końca pliku
                # Używamy perl do usunięcia trailing newlines i porównujemy długości
                local trimmed_length
                trimmed_length=$(perl -0777 -pe 's/\n+$//' "$file" 2>/dev/null | wc -c)
                trailing_newline_count=$((content_length - trimmed_length))
            fi
            
            echo "TYPE: text" >> "$output_file"
            echo "TRAILING_NEWLINE_COUNT: $trailing_newline_count" >> "$output_file"
            echo "CONTENT_LENGTH: $content_length" >> "$output_file"
            echo "CONTENT:" >> "$output_file"
            # Escapuj linie zaczynające się od markerów protokołu
            # Zapisz zawartość BEZ trailing newlines (zostaną odtworzone przy imporcie na podstawie TRAILING_NEWLINE_COUNT)
            perl -0777 -pe 's/\n+$//' "$file" 2>/dev/null | sed 's/^\(<<<\|PATH:\|TYPE:\|TRAILING_NEWLINE\|CONTENT_LENGTH:\|CONTENT:\)/>>>ESC<<<\1/' >> "$output_file"
            # Zawsze dodaj nową linię jako separator (zawartość nie kończy się już \n)
            echo "" >> "$output_file"
        fi
        
        echo "${MARKER_END}" >> "$output_file"
        file_count=$((file_count + 1))
        
    done < <(find "$project_dir" -type f "${find_opts[@]}" -print0 2>/dev/null)
    
    # Stopka
    cat >> "$output_file" << EOF

<<<FILES_END>>>

# =============================================================================
# PODSUMOWANIE ARCHIWUM
# =============================================================================
# Plików tekstowych: $((file_count - binary_count))
# Plików binarnych: ${binary_count}
# Pustych katalogów: ${dir_count}
# Pominiętych: ${skipped_count}
# =============================================================================
EOF

    log_success "Eksport zakończony!"
    echo ""
    echo "Podsumowanie:"
    echo "  - Plików wyeksportowanych: $file_count"
    echo "  - W tym binarnych: $binary_count"
    echo "  - Pustych katalogów: $dir_count"
    echo "  - Pominiętych: $skipped_count"
    echo "  - Rozmiar archiwum: $(du -h "$output_file" | cut -f1)"
}

# ============================================================================
# Funkcja importu
# ============================================================================

do_import() {
    local archive_file="$1"
    local target_dir="$2"
    shift 2
    
    local dry_run=false
    local force=false
    
    # Parsuj opcje
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                dry_run=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            *)
                log_error "Nieznana opcja: $1"
                exit 1
                ;;
        esac
    done
    
    # Walidacja
    if [[ ! -f "$archive_file" ]]; then
        log_error "Plik archiwum '$archive_file' nie istnieje!"
        exit 1
    fi
    
    # Sprawdź czy to prawidłowe archiwum
    if ! grep -q "<<<PROJECT_NAME>>>" "$archive_file"; then
        log_error "Plik nie jest prawidłowym archiwum projektu!"
        exit 1
    fi
    
    # Pobierz nazwę projektu
    local project_name=$(sed -n '/<<<PROJECT_NAME>>>/,/<<<PROJECT_NAME_END>>>/p' "$archive_file" | sed '1d;$d')
    
    log_info "Importuję projekt: $project_name"
    log_info "Katalog docelowy: $target_dir"
    
    if [[ "$dry_run" == true ]]; then
        log_warning "Tryb testowy - żadne pliki nie zostaną utworzone"
    fi
    
    # Utwórz katalog docelowy
    if [[ "$dry_run" == false ]]; then
        mkdir -p "$target_dir"
    fi
    
    local file_count=0
    local dir_count=0
    local skipped_count=0
    local dirs_created=""  # Track created directories to avoid double counting
    local current_file=""
    local current_type=""
    local trailing_newline_count=0
    local content_length=-1
    local in_content=false
    local in_binary=false
    local content=""
    local binary_content=""
    
    # Parsuj plik archiwum
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Pusty katalog
        if [[ "$line" == "${MARKER_EMPTY_DIR}" ]]; then
            IFS= read -r dir_path || dir_path=""
            
            # Walidacja ścieżki - zabezpieczenie przed path traversal
            if [[ -z "$dir_path" ]]; then
                log_error "Brak ścieżki katalogu po markerze ${MARKER_EMPTY_DIR}, pomijam"
                skipped_count=$((skipped_count + 1))
                continue
            fi
            if ! is_safe_path "$dir_path"; then
                log_error "Niebezpieczna ścieżka, pomijam: $dir_path"
                skipped_count=$((skipped_count + 1))
                continue
            fi
            
            local full_path="${target_dir}/${dir_path}"
            
            if [[ "$dry_run" == true ]]; then
                echo "  [DIR] $dir_path"
            else
                mkdir -p "$full_path"
                log_info "Utworzono katalog: $dir_path"
            fi
            # Track this directory
            if [[ ! "$dirs_created" == *"|$full_path|"* ]]; then
                dirs_created+="|$full_path|"
                dir_count=$((dir_count + 1))
            fi
            continue
        fi
        
        # Początek pliku
        if [[ "$line" == "${MARKER_START}" ]]; then
            current_file=""
            current_type=""
            trailing_newline_count=0
            content_length=-1
            in_content=false
            in_binary=false
            content=""
            binary_content=""
            continue
        fi
        
        # Ścieżka pliku
        if [[ "$line" == PATH:* ]]; then
            current_file="${line#PATH: }"
            # Walidacja ścieżki - zabezpieczenie przed path traversal
            if ! is_safe_path "$current_file"; then
                log_error "Niebezpieczna ścieżka, pomijam: $current_file"
                current_file=""  # Clear to skip this file
                skipped_count=$((skipped_count + 1))
            fi
            continue
        fi
        
        # Typ pliku
        if [[ "$line" == TYPE:* ]]; then
            current_type="${line#TYPE: }"
            continue
        fi
        
        # Informacja o trailing newline (nowy format z liczbą)
        if [[ "$line" == TRAILING_NEWLINE_COUNT:* ]]; then
            local tn_count="${line#TRAILING_NEWLINE_COUNT: }"
            if [[ "$tn_count" =~ ^[0-9]+$ ]]; then
                trailing_newline_count="$tn_count"
            else
                trailing_newline_count=0
                log_warning "Nieprawidłowa wartość TRAILING_NEWLINE_COUNT: '$tn_count', używam 0"
            fi
            continue
        fi
        
        # Informacja o trailing newline (stary format yes/no - kompatybilność wsteczna)
        if [[ "$line" == TRAILING_NEWLINE:* ]]; then
            local tn_value="${line#TRAILING_NEWLINE: }"
            if [[ "$tn_value" == "yes" ]]; then
                trailing_newline_count=1
            else
                trailing_newline_count=0
            fi
            continue
        fi
        
        # Długość zawartości
        if [[ "$line" == CONTENT_LENGTH:* ]]; then
            local cl_value="${line#CONTENT_LENGTH: }"
            if [[ "$cl_value" =~ ^[0-9]+$ ]]; then
                content_length="$cl_value"
            else
                content_length=-1
                log_warning "Nieprawidłowa wartość CONTENT_LENGTH: '$cl_value', pomijam walidację"
            fi
            continue
        fi
        
        # Początek zawartości tekstowej
        if [[ "$line" == "CONTENT:" ]]; then
            in_content=true
            content=""
            continue
        fi
        
        # Początek/koniec zawartości binarnej
        if [[ "$line" == "${MARKER_BINARY}" ]]; then
            if [[ "$in_binary" == false ]]; then
                in_binary=true
                binary_content=""
            else
                in_binary=false
            fi
            continue
        fi
        
        # Koniec pliku - zapisz
        if [[ "$line" == "${MARKER_END}" ]]; then
            if [[ -n "$current_file" ]]; then
                local full_path="${target_dir}/${current_file}"
                local dir_path=$(dirname "$full_path")
                
                if [[ "$dry_run" == true ]]; then
                    echo "  [FILE] $current_file ($current_type)"
                    file_count=$((file_count + 1))
                else
                    mkdir -p "$dir_path"
                    # Track directory creation
                    if [[ ! "$dirs_created" == *"|$dir_path|"* ]]; then
                        dirs_created+="|$dir_path|"
                        dir_count=$((dir_count + 1))
                    fi
                    
                    # Sprawdź czy plik istnieje
                    if [[ -f "$full_path" ]] && [[ "$force" == false ]]; then
                        log_warning "Plik istnieje, pomijam: $current_file (użyj --force aby nadpisać)"
                        skipped_count=$((skipped_count + 1))
                        continue
                    fi
                    
                    # Sprawdź czy typ pliku jest ustawiony
                    if [[ -z "$current_type" ]]; then
                        log_warning "Brak typu pliku dla: $current_file, traktuję jako tekstowy"
                        current_type="text"
                    fi
                    
                    if [[ "$current_type" == "binary" ]]; then
                        if ! printf '%s' "$binary_content" | base64 -d > "$full_path" 2>/dev/null; then
                            log_error "Błąd dekodowania base64 dla: $current_file"
                            rm -f "$full_path"  # Usuń uszkodzony plik
                            skipped_count=$((skipped_count + 1))
                            continue
                        fi
                    else
                        # Zapisz zawartość bez trailing newlines
                        printf '%s' "$content" > "$full_path"
                        # Dodaj dokładną liczbę trailing newlines
                        local i
                        for ((i=0; i<trailing_newline_count; i++)); do
                            printf '\n' >> "$full_path"
                        done
                        
                        # Walidacja długości zawartości
                        if [[ $content_length -ge 0 ]]; then
                            local actual_length
                            actual_length=$(wc -c < "$full_path")
                            if [[ $actual_length -ne $content_length ]]; then
                                log_warning "Ostrzeżenie: $current_file - oczekiwano $content_length bajtów, otrzymano $actual_length"
                            fi
                        fi
                    fi
                    
                    log_info "Utworzono: $current_file"
                    file_count=$((file_count + 1))
                fi
            fi
            in_content=false
            in_binary=false
            continue
        fi
        
        # Zbieraj zawartość
        if [[ "$in_content" == true ]]; then
            # De-escapuj linie które były escapowane przy eksporcie
            # Tylko gdy po >>>ESC<<< następuje marker protokołu
            local unescaped_line="$line"
            if [[ "$line" == ">>>ESC<<<<<<"* || "$line" == ">>>ESC<<<PATH:"* || \
                  "$line" == ">>>ESC<<<TYPE:"* || "$line" == ">>>ESC<<<TRAILING_NEWLINE"* || \
                  "$line" == ">>>ESC<<<CONTENT_LENGTH:"* || "$line" == ">>>ESC<<<CONTENT:"* ]]; then
                unescaped_line="${line#>>>ESC<<<}"
            fi
            if [[ -n "$content" ]]; then
                content+=$'\n'
            fi
            content+="$unescaped_line"
        elif [[ "$in_binary" == true ]]; then
            if [[ -n "$binary_content" ]]; then
                binary_content+=$'\n'
            fi
            binary_content+="$line"
        fi
        
    done < "$archive_file"
    
    log_success "Import zakończony!"
    echo ""
    echo "Podsumowanie:"
    echo "  - Plików utworzonych: $file_count"
    echo "  - Katalogów utworzonych: $dir_count"
    if [[ $skipped_count -gt 0 ]]; then
        echo "  - Pominiętych (niebezpieczne ścieżki): $skipped_count"
    fi
}

# ============================================================================
# Główna logika
# ============================================================================

main() {
    if [[ $# -lt 1 ]]; then
        print_usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        export)
            if [[ $# -lt 2 ]]; then
                log_error "Wymagane argumenty: <katalog_projektu> <plik_wyjściowy>"
                print_usage
                exit 1
            fi
            do_export "$@"
            ;;
        import)
            if [[ $# -lt 2 ]]; then
                log_error "Wymagane argumenty: <plik_archiwum> <katalog_docelowy>"
                print_usage
                exit 1
            fi
            do_import "$@"
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        --version|-v)
            echo "Project Archiver v${VERSION}"
            exit 0
            ;;
        *)
            log_error "Nieznana komenda: $command"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
