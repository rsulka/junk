"""Moduł raportowania - formatowanie wyników."""

import csv
import io
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dsmonitor import __version__
from dsmonitor.utils import human_size

if TYPE_CHECKING:
    from dsmonitor.analyzer import HostResult, RootSummary
    from dsmonitor.config import Config


def generate_report(results: list["HostResult"], config: "Config") -> str:
    """
    Generuje raport w wybranym formacie.

    Args:
        results: Lista wyników dla hostów.
        config: Konfiguracja.

    Returns:
        Sformatowany raport.
    """
    if config.output_format == "json":
        return format_json_report(results, config)
    elif config.output_format == "csv":
        return format_csv_report(results)
    else:
        return format_text_report(results, config)


def get_metadata(config: "Config") -> dict[str, Any]:
    """
    Generuje metadane raportu.

    Args:
        config: Konfiguracja.

    Returns:
        Słownik z metadanymi.
    """
    return {
        "version": __version__,
        "timestamp": datetime.now(UTC).isoformat(),
        "parameters": {
            "top_n": config.top_n,
            "file_heavy_threshold": config.file_heavy_threshold,
            "scan_depth": config.scan_depth,
            "stale_days": config.stale_days,
            "stale_kind": config.stale_kind,
            "excludes": config.excludes,
        },
    }


def _format_report_header(config: "Config") -> list[str]:
    """Buduje nagłówek raportu tekstowego."""
    return [
        "=" * 70,
        "DISK SPACE MONITOR - RAPORT",
        "=" * 70,
        f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Wersja: {__version__}",
        f"Top N: {config.top_n} | Próg file-heavy: {config.file_heavy_threshold}",
        f"Stare: {config.stale_days} dni ({config.stale_kind})",
        "",
    ]


def _format_report_footer() -> list[str]:
    """Buduje stopkę raportu tekstowego."""
    return [
        "",
        "=" * 70,
        "KONIEC RAPORTU",
        "=" * 70,
    ]


def format_text_report(results: list["HostResult"], config: "Config") -> str:
    """
    Formatuje raport tekstowy.

    Args:
        results: Lista wyników dla hostów.
        config: Konfiguracja.

    Returns:
        Raport tekstowy.
    """
    lines: list[str] = _format_report_header(config)

    for host_result in results:
        lines.append("")
        lines.append("=" * 70)
        host_label = "LOCALHOST" if config.local else host_result.host_name
        lines.append(f"HOST: {host_label}")
        lines.append("=" * 70)

        if host_result.errors:
            lines.append("")
            lines.append("BŁĘDY:")
            for error in host_result.errors:
                lines.append(f"  ✗ {error}")

        for root in host_result.roots:
            lines.append("")
            lines.append(_format_root_summary(root, config.stale_days))

    lines.extend(_format_report_footer())

    return "\n".join(lines)


def _format_root_summary(root: "RootSummary", stale_days: int) -> str:
    """Formatuje podsumowanie dla roota."""
    lines: list[str] = []

    stale_info = ""
    if root.stale_size is not None:
        stale_info = f", Stare > {stale_days} dni: {human_size(root.stale_size)}"

    approx_marker = " [APPROX]" if root.approx else ""

    lines.append(f"ROOT: {root.path}")
    lines.append(f"  Rozmiar: {human_size(root.total_size)}{stale_info}{approx_marker}")
    lines.append("─" * 60)

    if root.warnings:
        lines.append("  Ostrzeżenia:")
        for warning in root.warnings[:5]:
            lines.append(f"    ⚠ {warning}")
        lines.append("")

    if not root.top_directories:
        lines.append("  Brak katalogów spełniających kryteria file-heavy.")
    else:
        for i, dir_info in enumerate(root.top_directories, 1):
            stale_str = ""
            if dir_info.stale_size is not None:
                stale_str = f" (Stare > {stale_days} dni: {human_size(dir_info.stale_size)})"

            ratio_pct = f"{dir_info.file_heavy_ratio * 100:.0f}%"

            lines.append(f"  {i:3}. {dir_info.path}")
            lines.append(f"       Rozmiar: {human_size(dir_info.total_size)}{stale_str}")
            lines.append(f"       Pliki bezpośrednio: {human_size(dir_info.direct_files_size)} ({ratio_pct})")

            if dir_info.parent_path and dir_info.parent_total_size is not None:
                lines.append(f"       Rodzic: {dir_info.parent_path} — {human_size(dir_info.parent_total_size)}")

            lines.append("")

    return "\n".join(lines)


def format_json_report(results: list["HostResult"], config: "Config") -> str:
    """
    Formatuje raport JSON.

    Args:
        results: Lista wyników dla hostów.
        config: Konfiguracja.

    Returns:
        Raport JSON.
    """
    data: dict[str, Any] = {
        "metadata": get_metadata(config),
        "hosts": [],
    }

    for host_result in results:
        host_data: dict[str, Any] = {
            "name": host_result.host_name,
            "success": host_result.success,
            "errors": host_result.errors,
            "roots": [],
        }

        for root in host_result.roots:
            root_data: dict[str, Any] = {
                "path": root.path,
                "total_size_bytes": root.total_size,
                "total_size_human": human_size(root.total_size),
                "stale_size_bytes": root.stale_size,
                "stale_size_human": human_size(root.stale_size) if root.stale_size is not None else None,
                "approx": root.approx,
                "warnings": root.warnings,
                "directories": [],
            }

            for dir_info in root.top_directories:
                dir_data = {
                    "path": dir_info.path,
                    "total_size_bytes": dir_info.total_size,
                    "total_size_human": human_size(dir_info.total_size),
                    "direct_files_size_bytes": dir_info.direct_files_size,
                    "direct_files_size_human": human_size(dir_info.direct_files_size),
                    "file_heavy_ratio": round(dir_info.file_heavy_ratio, 3),
                    "stale_size_bytes": dir_info.stale_size,
                    "stale_size_human": human_size(dir_info.stale_size) if dir_info.stale_size is not None else None,
                    "parent_path": dir_info.parent_path,
                    "parent_total_size_bytes": dir_info.parent_total_size,
                    "parent_total_size_human": (
                        human_size(dir_info.parent_total_size) if dir_info.parent_total_size else None
                    ),
                    "depth": dir_info.depth,
                }
                root_data["directories"].append(dir_data)

            host_data["roots"].append(root_data)

        data["hosts"].append(host_data)

    return json.dumps(data, indent=2, ensure_ascii=False)


def format_csv_report(results: list["HostResult"]) -> str:
    """
    Formatuje raport CSV.

    Args:
        results: Lista wyników dla hostów.

    Returns:
        Raport CSV.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "host",
            "root",
            "path",
            "total_size_bytes",
            "total_size_human",
            "direct_files_size_bytes",
            "file_heavy_ratio",
            "stale_size_bytes",
            "parent_path",
            "parent_total_size_bytes",
            "depth",
        ]
    )

    for host_result in results:
        for root in host_result.roots:
            for dir_info in root.top_directories:
                writer.writerow(
                    [
                        host_result.host_name,
                        root.path,
                        dir_info.path,
                        dir_info.total_size,
                        human_size(dir_info.total_size),
                        dir_info.direct_files_size,
                        round(dir_info.file_heavy_ratio, 3),
                        dir_info.stale_size if dir_info.stale_size is not None else "",
                        dir_info.parent_path,
                        dir_info.parent_total_size if dir_info.parent_total_size else "",
                        dir_info.depth,
                    ]
                )

    return output.getvalue()


def write_report(report: str, config: "Config") -> None:
    """
    Zapisuje raport do pliku lub wyświetla na stdout.

    Args:
        report: Treść raportu.
        config: Konfiguracja.
    """
    if config.output_file:
        with open(config.output_file, "w", encoding="utf-8") as f:
            f.write(report)
        if config.verbose:
            print(f"Raport zapisano do: {config.output_file}")
    else:
        print(report)
