#!/usr/bin/env python3
"""
Project Archiver - Eksport i import projektu do/z jednego pliku tekstowego.

Użycie:
  ./project_archiver.py export <katalog_projektu> <plik_wyjściowy> [opcje]
  ./project_archiver.py import <plik_archiwum> <katalog_docelowy> [opcje]
"""

import argparse
import base64
import fnmatch
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"

MARKER_START = "<<<FILE_START>>>"
MARKER_END = "<<<FILE_END>>>"
MARKER_BINARY = "<<<BINARY_BASE64>>>"
MARKER_EMPTY_DIR = "<<<EMPTY_DIR>>>"

# ANSI colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

DEFAULT_IGNORE_PATTERNS = [
    ".git",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    ".idea",
    ".vscode",
    "*.egg-info",
    "dist",
    "build",
    ".tox",
    ".coverage",
    "htmlcov",
    "*.so",
    "*.dylib",
    "*.dll",
]


def log_info(msg: str) -> None:
    print(f"{BLUE}[INFO]{NC} {msg}")


def log_success(msg: str) -> None:
    print(f"{GREEN}[OK]{NC} {msg}")


def log_warning(msg: str) -> None:
    print(f"{YELLOW}[UWAGA]{NC} {msg}")


def log_error(msg: str) -> None:
    print(f"{RED}[BŁĄD]{NC} {msg}", file=sys.stderr)


def is_binary(file_path: Path) -> bool:
    """Sprawdza czy plik jest binarny (zawiera bajty null)."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except (OSError, IOError):
        return True


def is_safe_path(path: str) -> bool:
    """Sprawdza czy ścieżka jest bezpieczna (brak path traversal)."""
    if not path:
        return False
    if path.startswith("/"):
        return False
    if path.startswith("../") or "/../" in path or path.endswith("/..") or path == "..":
        return False
    return True


def should_ignore(rel_path: str, ignore_patterns: list[str], full_path: str = "") -> bool:
    """Sprawdza czy plik pasuje do wzorców ignorowania."""
    basename = os.path.basename(rel_path)
    path_parts = rel_path.replace("\\", "/").split("/")

    for pattern in ignore_patterns:
        if full_path and full_path == pattern:
            return True
        if fnmatch.fnmatch(basename, pattern):
            return True
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Pobiera względną ścieżkę względem katalogu bazowego."""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)


def escape_content_line(line: str) -> str:
    """Escapuje linie zaczynające się od markerów protokołu."""
    prefixes = ("<<<", "PATH:", "TYPE:", "TRAILING_NEWLINE", "CONTENT_LENGTH:", "CONTENT:")
    if line.startswith(prefixes):
        return f">>>ESC<<<{line}"
    return line


def unescape_content_line(line: str) -> str:
    """De-escapuje linie które były escapowane przy eksporcie."""
    escape_prefixes = (
        ">>>ESC<<<<<<",
        ">>>ESC<<<PATH:",
        ">>>ESC<<<TYPE:",
        ">>>ESC<<<TRAILING_NEWLINE",
        ">>>ESC<<<CONTENT_LENGTH:",
        ">>>ESC<<<CONTENT:",
    )
    for prefix in escape_prefixes:
        if line.startswith(prefix):
            return line[len(">>>ESC<<<") :]
    return line


def do_export(
    project_dir: Path,
    output_file: Path,
    use_ignore: bool = True,
    include_hidden: bool = False,
    max_size_mb: int = 10,
    extra_ignore: list[str] | None = None,
) -> None:
    """Eksportuje projekt do pliku tekstowego."""
    if not project_dir.is_dir():
        log_error(f"Katalog '{project_dir}' nie istnieje!")
        sys.exit(1)

    project_dir = project_dir.resolve()
    project_name = project_dir.name

    output_file = output_file.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    ignore_patterns = list(DEFAULT_IGNORE_PATTERNS) if use_ignore else []
    if extra_ignore:
        ignore_patterns.extend(extra_ignore)
    ignore_patterns.append(str(output_file))

    log_info(f"Eksportuję projekt: {project_dir}")
    log_info(f"Plik wyjściowy: {output_file}")

    file_count = 0
    dir_count = 0
    skipped_count = 0
    binary_count = 0
    max_size_bytes = max_size_mb * 1024 * 1024

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"""\
# =============================================================================
# PROJECT ARCHIVE - Wygenerowano przez Project Archiver v{VERSION}
# =============================================================================
# Projekt: {project_name}
# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# System: {platform.system()} {platform.release()}
# =============================================================================
# 
# Aby odtworzyć ten projekt, użyj:
#   ./project_archiver.py import <ten_plik> <katalog_docelowy>
#
# =============================================================================

<<<PROJECT_NAME>>>
{project_name}
<<<PROJECT_NAME_END>>>

<<<FILES_START>>>
""")

        for root, dirs, files in os.walk(project_dir):
            root_path = Path(root)

            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files = [f for f in files if not f.startswith(".")]

            rel_root = get_relative_path(root_path, project_dir)

            if rel_root and rel_root != ".":
                if should_ignore(rel_root, ignore_patterns, str(root_path)):
                    dirs[:] = []
                    continue

            filtered_dirs = []
            for d in dirs:
                dir_rel = os.path.join(rel_root, d) if rel_root and rel_root != "." else d
                if should_ignore(dir_rel, ignore_patterns):
                    continue
                filtered_dirs.append(d)
            dirs[:] = filtered_dirs

            for d in dirs:
                dir_path = root_path / d
                dir_rel = get_relative_path(dir_path, project_dir)
                if not any(dir_path.iterdir()):
                    out.write(f"\n{MARKER_EMPTY_DIR}\n")
                    out.write(f"{dir_rel}\n")
                    dir_count += 1
                    log_info(f"Pusty katalog: {dir_rel}")

            for file_name in files:
                file_path = root_path / file_name
                rel_path = get_relative_path(file_path, project_dir)

                if should_ignore(rel_path, ignore_patterns, str(file_path)):
                    skipped_count += 1
                    continue

                try:
                    file_size = file_path.stat().st_size
                except OSError:
                    log_warning(f"Nie można określić rozmiaru: {rel_path}")
                    skipped_count += 1
                    continue

                if file_size > max_size_bytes:
                    log_warning(f"Pominięto (za duży): {rel_path} ({file_size // 1024 // 1024}MB)")
                    skipped_count += 1
                    continue

                out.write(f"\n{MARKER_START}\n")
                out.write(f"PATH: {rel_path}\n")

                if is_binary(file_path):
                    out.write("TYPE: binary\n")
                    out.write(f"{MARKER_BINARY}\n")
                    try:
                        with open(file_path, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("ascii")
                            out.write(encoded)
                            out.write("\n")
                    except OSError as e:
                        log_warning(f"Błąd odczytu pliku binarnego: {rel_path} - {e}")
                        skipped_count += 1
                        continue
                    out.write(f"{MARKER_BINARY}\n")
                    binary_count += 1
                    log_info(f"Plik binarny: {rel_path}")
                else:
                    try:
                        with open(file_path, "rb") as f:
                            raw_content = f.read()
                        content_length = len(raw_content)
                        content = raw_content.decode("utf-8")
                    except UnicodeDecodeError:
                        out.write("TYPE: binary\n")
                        out.write(f"{MARKER_BINARY}\n")
                        with open(file_path, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("ascii")
                            out.write(encoded)
                            out.write("\n")
                        out.write(f"{MARKER_BINARY}\n")
                        binary_count += 1
                        log_info(f"Plik binarny (encoding): {rel_path}")
                        file_count += 1
                        continue
                    except OSError as e:
                        log_warning(f"Błąd odczytu pliku: {rel_path} - {e}")
                        skipped_count += 1
                        continue

                    trailing_newline_count = 0
                    if content.endswith("\n"):
                        stripped = content.rstrip("\n")
                        trailing_newline_count = len(content) - len(stripped)
                        content = stripped

                    out.write("TYPE: text\n")
                    out.write(f"TRAILING_NEWLINE_COUNT: {trailing_newline_count}\n")
                    out.write(f"CONTENT_LENGTH: {content_length}\n")
                    out.write("CONTENT:\n")

                    for line in content.split("\n"):
                        out.write(escape_content_line(line) + "\n")

                out.write(f"{MARKER_END}\n")
                file_count += 1

        out.write(f"""
<<<FILES_END>>>

# =============================================================================
# PODSUMOWANIE ARCHIWUM
# =============================================================================
# Plików tekstowych: {file_count - binary_count}
# Plików binarnych: {binary_count}
# Pustych katalogów: {dir_count}
# Pominiętych: {skipped_count}
# =============================================================================
""")

    log_success("Eksport zakończony!")
    print()
    print("Podsumowanie:")
    print(f"  - Plików wyeksportowanych: {file_count}")
    print(f"  - W tym binarnych: {binary_count}")
    print(f"  - Pustych katalogów: {dir_count}")
    print(f"  - Pominiętych: {skipped_count}")
    archive_size = output_file.stat().st_size
    if archive_size >= 1024 * 1024:
        size_str = f"{archive_size / 1024 / 1024:.1f}MB"
    elif archive_size >= 1024:
        size_str = f"{archive_size / 1024:.1f}KB"
    else:
        size_str = f"{archive_size}B"
    print(f"  - Rozmiar archiwum: {size_str}")


def do_import(
    archive_file: Path,
    target_dir: Path,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """Importuje projekt z pliku archiwum."""
    if not archive_file.is_file():
        log_error(f"Plik archiwum '{archive_file}' nie istnieje!")
        sys.exit(1)

    try:
        with open(archive_file, "r", encoding="utf-8") as f:
            archive_content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        log_error(f"Błąd odczytu archiwum: {e}")
        sys.exit(1)

    if "<<<PROJECT_NAME>>>" not in archive_content:
        log_error("Plik nie jest prawidłowym archiwum projektu!")
        sys.exit(1)

    lines = archive_content.split("\n")

    project_name = ""
    in_project_name = False
    for line in lines:
        if line == "<<<PROJECT_NAME>>>":
            in_project_name = True
            continue
        if line == "<<<PROJECT_NAME_END>>>":
            break
        if in_project_name:
            project_name = line
            break

    log_info(f"Importuję projekt: {project_name}")
    log_info(f"Katalog docelowy: {target_dir}")

    if dry_run:
        log_warning("Tryb testowy - żadne pliki nie zostaną utworzone")
    else:
        target_dir.mkdir(parents=True, exist_ok=True)

    file_count = 0
    dir_count = 0
    skipped_count = 0
    dirs_created: set[str] = set()

    current_file = ""
    current_type = ""
    trailing_newline_count = 0
    content_length = -1
    in_content = False
    in_binary = False
    content_lines: list[str] = []
    binary_content = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        if line == MARKER_EMPTY_DIR:
            i += 1
            if i < len(lines):
                dir_path = lines[i]
                if not dir_path:
                    log_error(f"Brak ścieżki katalogu po markerze {MARKER_EMPTY_DIR}, pomijam")
                    skipped_count += 1
                elif not is_safe_path(dir_path):
                    log_error(f"Niebezpieczna ścieżka, pomijam: {dir_path}")
                    skipped_count += 1
                else:
                    full_path = target_dir / dir_path
                    if dry_run:
                        print(f"  [DIR] {dir_path}")
                    else:
                        full_path.mkdir(parents=True, exist_ok=True)
                        log_info(f"Utworzono katalog: {dir_path}")
                    if str(full_path) not in dirs_created:
                        dirs_created.add(str(full_path))
                        dir_count += 1
            i += 1
            continue

        if line == MARKER_START:
            current_file = ""
            current_type = ""
            trailing_newline_count = 0
            content_length = -1
            in_content = False
            in_binary = False
            content_lines = []
            binary_content = ""
            i += 1
            continue

        if line.startswith("PATH: "):
            current_file = line[6:]
            if not is_safe_path(current_file):
                log_error(f"Niebezpieczna ścieżka, pomijam: {current_file}")
                current_file = ""
                skipped_count += 1
            i += 1
            continue

        if line.startswith("TYPE: "):
            current_type = line[6:]
            i += 1
            continue

        if line.startswith("TRAILING_NEWLINE_COUNT: "):
            try:
                trailing_newline_count = int(line[24:])
            except ValueError:
                trailing_newline_count = 0
                log_warning(f"Nieprawidłowa wartość TRAILING_NEWLINE_COUNT: '{line[24:]}', używam 0")
            i += 1
            continue

        if line.startswith("TRAILING_NEWLINE: "):
            tn_value = line[18:]
            trailing_newline_count = 1 if tn_value == "yes" else 0
            i += 1
            continue

        if line.startswith("CONTENT_LENGTH: "):
            try:
                content_length = int(line[16:])
            except ValueError:
                content_length = -1
                log_warning(f"Nieprawidłowa wartość CONTENT_LENGTH: '{line[16:]}', pomijam walidację")
            i += 1
            continue

        if line == "CONTENT:":
            in_content = True
            content_lines = []
            i += 1
            continue

        if line == MARKER_BINARY:
            if not in_binary:
                in_binary = True
                binary_content = ""
            else:
                in_binary = False
            i += 1
            continue

        if line == MARKER_END:
            if current_file:
                full_path = target_dir / current_file
                dir_path = full_path.parent

                if dry_run:
                    print(f"  [FILE] {current_file} ({current_type})")
                    file_count += 1
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    if str(dir_path) not in dirs_created:
                        dirs_created.add(str(dir_path))
                        dir_count += 1

                    if full_path.exists() and not force:
                        log_warning(f"Plik istnieje, pomijam: {current_file} (użyj --force aby nadpisać)")
                        skipped_count += 1
                        i += 1
                        continue

                    if not current_type:
                        log_warning(f"Brak typu pliku dla: {current_file}, traktuję jako tekstowy")
                        current_type = "text"

                    if current_type == "binary":
                        try:
                            decoded = base64.b64decode(binary_content)
                            with open(full_path, "wb") as f:
                                f.write(decoded)
                        except Exception as e:
                            log_error(f"Błąd dekodowania base64 dla: {current_file} - {e}")
                            if full_path.exists():
                                full_path.unlink()
                            skipped_count += 1
                            i += 1
                            continue
                    else:
                        content = "\n".join(unescape_content_line(ln) for ln in content_lines)
                        content += "\n" * trailing_newline_count

                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        if content_length >= 0:
                            actual_length = full_path.stat().st_size
                            if actual_length != content_length:
                                log_warning(
                                    f"Ostrzeżenie: {current_file} - oczekiwano {content_length} bajtów, "
                                    f"otrzymano {actual_length}"
                                )

                    log_info(f"Utworzono: {current_file}")
                    file_count += 1

            in_content = False
            in_binary = False
            i += 1
            continue

        if in_content:
            content_lines.append(line)
        elif in_binary:
            if binary_content:
                binary_content += "\n"
            binary_content += line

        i += 1

    log_success("Import zakończony!")
    print()
    print("Podsumowanie:")
    print(f"  - Plików utworzonych: {file_count}")
    print(f"  - Katalogów utworzonych: {dir_count}")
    if skipped_count > 0:
        print(f"  - Pominiętych (niebezpieczne ścieżki): {skipped_count}")


def print_usage() -> None:
    print(f"{GREEN}Project Archiver v{VERSION}{NC}")
    print("Narzędzie do eksportu i importu projektów do/z jednego pliku tekstowego.")
    print()
    print(f"{YELLOW}Użycie:{NC}")
    print("  project_archiver.py export <katalog_projektu> <plik_wyjściowy> [opcje]")
    print("  project_archiver.py import <plik_archiwum> <katalog_docelowy> [opcje]")
    print()
    print(f"{YELLOW}Komendy:{NC}")
    print("  export    Eksportuj projekt do pliku tekstowego")
    print("  import    Odtwórz projekt z pliku tekstowego")
    print()
    print(f"{YELLOW}Opcje eksportu:{NC}")
    print("  --no-ignore         Nie ignoruj domyślnych wzorców (.git, __pycache__, etc.)")
    print("  --include-hidden    Dołącz ukryte pliki (domyślnie ignorowane)")
    print("  --ignore <wzorzec>  Dodaj własny wzorzec do ignorowania")
    print("  --max-size <MB>     Maksymalny rozmiar pliku do eksportu (domyślnie: 10MB)")
    print()
    print(f"{YELLOW}Opcje importu:{NC}")
    print("  --dry-run           Pokaż co zostanie utworzone bez faktycznego tworzenia")
    print("  --force             Nadpisz istniejące pliki bez pytania")
    print()
    print(f"{YELLOW}Przykłady:{NC}")
    print("  project_archiver.py export ./moj_projekt ./backup.txt")
    print("  project_archiver.py export ./moj_projekt ./backup.txt --include-hidden")
    print("  project_archiver.py import ./backup.txt ./odtworzony_projekt")
    print("  project_archiver.py import ./backup.txt ./odtworzony_projekt --dry-run")


def main() -> None:
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command in ("--help", "-h"):
        print_usage()
        sys.exit(0)

    if command in ("--version", "-v"):
        print(f"Project Archiver v{VERSION}")
        sys.exit(0)

    if command == "export":
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("command")
        parser.add_argument("project_dir", type=Path)
        parser.add_argument("output_file", type=Path)
        parser.add_argument("--no-ignore", action="store_true")
        parser.add_argument("--include-hidden", action="store_true")
        parser.add_argument("--ignore", action="append", default=[])
        parser.add_argument("--max-size", type=int, default=10)
        args = parser.parse_args()

        do_export(
            project_dir=args.project_dir,
            output_file=args.output_file,
            use_ignore=not args.no_ignore,
            include_hidden=args.include_hidden,
            max_size_mb=args.max_size,
            extra_ignore=args.ignore,
        )

    elif command == "import":
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("command")
        parser.add_argument("archive_file", type=Path)
        parser.add_argument("target_dir", type=Path)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--force", action="store_true")
        args = parser.parse_args()

        do_import(
            archive_file=args.archive_file,
            target_dir=args.target_dir,
            dry_run=args.dry_run,
            force=args.force,
        )

    else:
        log_error(f"Nieznana komenda: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
