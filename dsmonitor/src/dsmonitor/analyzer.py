"""Moduł analizy - parsowanie du, wyliczanie Top N, ratio, stale."""

from dataclasses import dataclass, field
from pathlib import Path

from dsmonitor.utils import get_parent_path, is_child_of, normalize_path


@dataclass
class DirectoryInfo:
    """Informacje o katalogu."""

    path: str
    total_size: int
    direct_files_size: int
    file_heavy_ratio: float
    stale_size: int | None = None
    parent_path: str | None = None
    parent_total_size: int | None = None
    depth: int = 0


@dataclass
class RootSummary:
    """Podsumowanie dla katalogu głównego (root/mountpoint)."""

    path: str
    total_size: int
    stale_size: int | None = None
    top_directories: list[DirectoryInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    approx: bool = False


@dataclass
class HostResult:
    """Wynik skanowania dla hosta."""

    host_name: str
    roots: list[RootSummary] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = True


def parse_du_output(output: str) -> dict[str, int]:
    """
    Parsuje wyjście komendy du do słownika path -> size.

    Args:
        output: Wyjście komendy du.

    Returns:
        Słownik: ścieżka -> rozmiar w bajtach.
    """
    sizes: dict[str, int] = {}

    for line in output.strip().split("\n"):
        if not line:
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        try:
            size = int(parts[0])
            path = normalize_path(parts[1])
            sizes[path] = size
        except ValueError:
            continue

    return sizes


def _compute_children_sums(sizes: dict[str, int]) -> dict[str, int]:
    """
    Oblicza sumę rozmiarów bezpośrednich dzieci dla każdego katalogu.

    Args:
        sizes: Słownik wszystkich rozmiarów.

    Returns:
        Słownik: ścieżka rodzica -> suma rozmiarów dzieci.
    """
    children_sums: dict[str, int] = {}
    for path, size in sizes.items():
        parent = str(Path(path).parent)
        if parent != path:
            children_sums[parent] = children_sums.get(parent, 0) + size
    return children_sums


def calculate_direct_files_size(path: str, sizes: dict[str, int], children_sums: dict[str, int] | None = None) -> int:
    """
    Wylicza rozmiar plików bezpośrednio w katalogu.

    direct_files_size = total_size - sum(child_sizes)

    Args:
        path: Ścieżka do katalogu.
        sizes: Słownik wszystkich rozmiarów.
        children_sums: Opcjonalna mapa sum dzieci (jeśli None, zostanie wyliczona).

    Returns:
        Rozmiar plików bezpośrednio w katalogu.
    """
    total_size = sizes.get(path, 0)
    if total_size == 0:
        return 0

    if children_sums is None:
        children_sums = _compute_children_sums(sizes)
    direct_files_size = max(0, total_size - children_sums.get(path, 0))
    return direct_files_size


def get_path_depth(path: str, root: str) -> int:
    """
    Oblicza głębokość ścieżki względem roota.

    Args:
        path: Ścieżka do katalogu.
        root: Ścieżka do katalogu głównego.

    Returns:
        Głębokość (0 dla roota).
    """
    path = normalize_path(path)
    root = normalize_path(root)

    if path == root:
        return 0

    relative = path.removeprefix(root).strip("/")
    if not relative:
        return 0

    return len(relative.split("/"))


def find_top_n_file_heavy(
    sizes: dict[str, int],
    root: str,
    n: int,
    threshold: float,
) -> list[DirectoryInfo]:
    """
    Znajduje Top N katalogów file-heavy.

    Args:
        sizes: Słownik wszystkich rozmiarów.
        root: Ścieżka do katalogu głównego.
        n: Liczba wyników.
        threshold: Próg file_heavy_ratio.

    Returns:
        Lista Top N katalogów spełniających warunek.
    """
    root = normalize_path(root)

    children_sums = _compute_children_sums(sizes)

    candidates: list[DirectoryInfo] = []

    for path, total_size in sizes.items():
        if total_size == 0:
            continue

        if not is_child_of(path, root):
            continue

        direct_files_size = max(0, total_size - children_sums.get(path, 0))
        ratio = direct_files_size / total_size

        if ratio >= threshold:
            parent_path = get_parent_path(path)
            parent_total_size = sizes.get(parent_path)

            candidates.append(
                DirectoryInfo(
                    path=path,
                    total_size=total_size,
                    direct_files_size=direct_files_size,
                    file_heavy_ratio=ratio,
                    parent_path=parent_path,
                    parent_total_size=parent_total_size,
                    depth=get_path_depth(path, root),
                )
            )

    candidates.sort(key=lambda d: d.total_size, reverse=True)

    return candidates[:n]


def find_top_n_by_stale(
    stale_data: dict[str, int],
    sizes: dict[str, int],
    root: str,
    n: int,
) -> list[DirectoryInfo]:
    """
    Znajduje Top N katalogów z największą ilością stale plików.

    Args:
        stale_data: Słownik ścieżka -> rozmiar stale (z find output).
        sizes: Słownik wszystkich rozmiarów (z du output).
        root: Ścieżka do katalogu głównego.
        n: Liczba wyników.

    Returns:
        Lista Top N katalogów posortowanych po stale_size.
    """
    root = normalize_path(root)
    children_sums = _compute_children_sums(sizes)
    candidates: list[DirectoryInfo] = []

    for path, stale_size in stale_data.items():
        if stale_size == 0:
            continue

        if not is_child_of(path, root):
            continue

        total_size = sizes.get(path, 0)
        direct_files_size = max(0, total_size - children_sums.get(path, 0)) if total_size > 0 else 0
        ratio = direct_files_size / total_size if total_size > 0 else 0.0

        parent_path = get_parent_path(path)
        parent_total_size = sizes.get(parent_path)

        candidates.append(
            DirectoryInfo(
                path=path,
                total_size=total_size,
                direct_files_size=direct_files_size,
                file_heavy_ratio=ratio,
                stale_size=stale_size,
                parent_path=parent_path,
                parent_total_size=parent_total_size,
                depth=get_path_depth(path, root),
            )
        )

    candidates.sort(key=lambda d: d.stale_size or 0, reverse=True)

    return candidates[:n]


def enrich_with_stale(
    summary: RootSummary,
    stale_results: dict[str, int],
    root_stale: int | None = None,
) -> None:
    """
    Wzbogaca podsumowanie o informacje o stale.

    Args:
        summary: Podsumowanie do wzbogacenia.
        stale_results: Słownik path -> stale_size.
        root_stale: Stale size dla roota.
    """
    summary.stale_size = root_stale

    for dir_info in summary.top_directories:
        if dir_info.path in stale_results:
            dir_info.stale_size = stale_results[dir_info.path]
