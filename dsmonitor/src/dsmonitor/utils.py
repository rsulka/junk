"""Funkcje pomocnicze."""

from pathlib import Path, PurePosixPath


def human_size(size_bytes: int) -> str:
    """
    Konwertuje rozmiar w bajtach na czytelny format.

    Args:
        size_bytes: Rozmiar w bajtach.

    Returns:
        Czytelny rozmiar z jednostką (np. "1.5 GB").
    """
    if size_bytes < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)

    for unit in units[:-1]:
        if abs(size) < 1024.0:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} {units[-1]}"


def get_parent_path(path: str) -> str:
    """
    Zwraca ścieżkę do katalogu nadrzędnego.

    Args:
        path: Ścieżka do katalogu.

    Returns:
        Ścieżka do rodzica lub "/" dla roota.
    """
    parent = str(Path(path).parent)
    return parent if parent != path else "/"


def normalize_path(path: str) -> str:
    """
    Normalizuje ścieżkę (usuwa trailing slash, rozwiązuje ./).

    Używa PurePosixPath zamiast Path.resolve(), co:
    - Nie dotyka lokalnego systemu plików
    - Nie rozwiązuje symlinków
    - Bezpiecznie działa dla ścieżek zdalnych (du/find output)

    Args:
        path: Ścieżka do normalizacji.

    Returns:
        Znormalizowana ścieżka.
    """
    normalized = str(PurePosixPath(path))
    return normalized.rstrip("/") if normalized != "/" else "/"


def is_child_of(child_path: str, parent_path: str) -> bool:
    """
    Sprawdza czy child_path jest podścieżką parent_path.

    Unika fałszywych dopasowań typu /data/app2 do /data/app,
    używając testu z separatorem zamiast startswith().

    Args:
        child_path: Potencjalna ścieżka dziecka.
        parent_path: Ścieżka rodzica.

    Returns:
        True jeśli child_path jest w parent_path lub równy.
    """
    child = normalize_path(child_path)
    parent = normalize_path(parent_path)

    if child == parent:
        return True

    if parent == "/":
        return True

    return child.startswith(parent + "/")


def count_access_denied_errors(stderr: str) -> int:
    """
    Zlicza błędy braku dostępu ze stderr.

    Args:
        stderr: Wyjście błędów komendy.

    Returns:
        Liczba błędów typu "Permission denied".
    """
    if not stderr:
        return 0
    return sum(
        1
        for line in stderr.strip().split("\n")
        if "Permission denied" in line or "Brak dostępu" in line or "cannot read" in line.lower()
    )
