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


def parse_size_to_bytes(size_str: str) -> int:
    """
    Parsuje rozmiar z jednostką do bajtów.

    Args:
        size_str: Rozmiar z jednostką (np. "1.5GB", "100 MB").

    Returns:
        Rozmiar w bajtach.

    Raises:
        ValueError: Gdy format jest nieprawidłowy.
    """
    size_str = size_str.strip().upper().replace(" ", "")

    units = {
        "B": 1,
        "KB": 1024,
        "K": 1024,
        "MB": 1024**2,
        "M": 1024**2,
        "GB": 1024**3,
        "G": 1024**3,
        "TB": 1024**4,
        "T": 1024**4,
        "PB": 1024**5,
        "P": 1024**5,
    }

    for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            number_part = size_str[: -len(unit)]
            try:
                return int(float(number_part) * multiplier)
            except ValueError as e:
                raise ValueError(f"Nieprawidłowy format rozmiaru: {size_str}") from e

    try:
        return int(size_str)
    except ValueError as e:
        raise ValueError(f"Nieprawidłowy format rozmiaru: {size_str}") from e


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
