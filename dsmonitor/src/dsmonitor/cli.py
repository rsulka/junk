"""Interfejs CLI - główny punkt wejścia."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

from dsmonitor import __version__
from dsmonitor.analyzer import HostResult, RootSummary, analyze_root, enrich_with_stale
from dsmonitor.config import Config, HostProfile, build_config, load_yaml_config
from dsmonitor.executor import parse_stale_batch_output, run_du, run_find_stale_batch
from dsmonitor.reporter import generate_report, write_report
from dsmonitor.utils import is_child_of

if TYPE_CHECKING:
    pass


def create_parser() -> argparse.ArgumentParser:
    """Tworzy parser argumentów CLI."""
    parser = argparse.ArgumentParser(
        prog="dsmonitor",
        description="Narzędzie do monitorowania zajętości dysku na serwerach RHEL i AIX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:
  # Skan lokalny
  dsmonitor --local --paths /data /home --top-n 5

  # Skan z pliku konfiguracyjnego
  dsmonitor --config config.yaml

  # Dry-run - podgląd komend SSH
  dsmonitor --config config.yaml --dry-run --verbose

  # Skan jednego hosta
  dsmonitor --host server1 --paths /data --ssh-user admin
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    config_group = parser.add_argument_group("Konfiguracja")
    config_group.add_argument("--config", "-c", metavar="PLIK", help="Plik konfiguracyjny YAML")
    config_group.add_argument("--local", "-l", action="store_true", help="Tryb lokalny (bez SSH)")
    config_group.add_argument("--host", dest="hosts", action="append", metavar="HOST", help="Host do skanowania")
    config_group.add_argument("--paths", "-p", nargs="+", metavar="ŚCIEŻKA", help="Ścieżki do skanowania")

    scan_group = parser.add_argument_group("Parametry skanowania")
    scan_group.add_argument("--top-n", "-n", type=int, metavar="N", help="Liczba wyników Top N (domyślnie: 20)")
    scan_group.add_argument(
        "--file-heavy-threshold", "-t", type=float, metavar="PRÓG", help="Próg file-heavy ratio (domyślnie: 0.8)"
    )
    scan_group.add_argument("--scan-depth", "-d", type=int, metavar="GŁĘBOKOŚĆ", help="Głębokość skanowania")
    scan_group.add_argument("--exclude", "-e", dest="excludes", action="append", metavar="WZORZEC", help="Wykluczenia")

    stale_group = parser.add_argument_group("Analiza stale")
    stale_group.add_argument("--stale-days", type=int, metavar="DNI", help="Wiek plików stale (domyślnie: 365)")
    stale_group.add_argument(
        "--stale-kind", choices=["mtime", "atime", "ctime"], metavar="TYP", help="Typ czasu (domyślnie: mtime)"
    )

    output_group = parser.add_argument_group("Wyjście")
    output_group.add_argument("--format", "-f", choices=["text", "json", "csv"], help="Format wyjścia")
    output_group.add_argument("--output", "-o", metavar="PLIK", help="Plik wyjściowy (domyślnie: stdout)")

    ssh_group = parser.add_argument_group("Opcje SSH")
    ssh_group.add_argument("--ssh-user", metavar="USER", help="Użytkownik SSH")
    ssh_group.add_argument("--ssh-port", type=int, metavar="PORT", help="Port SSH (domyślnie: 22)")
    ssh_group.add_argument("--ssh-options", metavar="OPCJE", help="Dodatkowe opcje SSH")

    exec_group = parser.add_argument_group("Wykonanie")
    exec_group.add_argument("--parallel", type=int, metavar="K", help="Równoległość hostów (domyślnie: 10)")
    exec_group.add_argument("--timeout", type=int, metavar="SEK", help="Timeout per host (domyślnie: 1800)")
    exec_group.add_argument("--dry-run", action="store_true", help="Tylko wyświetl komendy (bez wykonania)")
    exec_group.add_argument("--verbose", "-v", action="store_true", help="Szczegółowe logi")

    return parser


def parse_args(args: list[str] | None = None) -> dict[str, Any]:
    """Parsuje argumenty CLI do słownika."""
    parser = create_parser()
    parsed = parser.parse_args(args)
    return vars(parsed)


def load_config(cli_args: dict[str, Any]) -> Config:
    """
    Ładuje konfigurację z YAML i/lub CLI.

    Args:
        cli_args: Argumenty z linii poleceń.

    Returns:
        Konfiguracja.

    Raises:
        SystemExit: Gdy konfiguracja jest nieprawidłowa.
    """
    config_file = cli_args.get("config")

    if config_file:
        try:
            yaml_config = load_yaml_config(config_file)
            config = build_config(yaml_config, cli_args)
        except FileNotFoundError as e:
            print(f"Błąd: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Błąd parsowania konfiguracji: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        config = build_config(None, cli_args)

    errors = config.validate()
    if errors:
        print("Błędy konfiguracji:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    return config


def _scan_path(
    path: str,
    host: HostProfile | None,
    config: Config,
    host_name: str,
) -> tuple[RootSummary, str | None]:
    """
    Skanuje pojedynczą ścieżkę: du → analyze → stale.

    Args:
        path: Ścieżka do skanowania.
        host: Profil hosta (None dla trybu lokalnego).
        config: Konfiguracja.
        host_name: Nazwa hosta (do logowania).

    Returns:
        (RootSummary, None) - sukces
        (RootSummary z ostrzeżeniem, error_message) - błąd
    """
    du_result = run_du(path, host, config)

    if config.dry_run:
        print(f"[DRY-RUN] {du_result.command}")
        return (
            RootSummary(path=path, total_size=0, warnings=["Tryb dry-run"]),
            None,
        )

    if not du_result.success:
        return (
            RootSummary(
                path=path,
                total_size=0,
                warnings=[f"Błąd du: {du_result.stderr}"],
            ),
            f"Błąd du dla {path}: {du_result.stderr}",
        )

    root_summary = analyze_root(du_result, path, config)

    if config.stale_days > 0 and root_summary.top_directories:
        if config.verbose:
            print(f"[{host_name}] Obliczam stale dla {path}...")

        stale_batch_result = run_find_stale_batch(path, host, config)

        if config.dry_run:
            print(f"[DRY-RUN] {stale_batch_result.command}")
        elif stale_batch_result.success:
            all_stale = parse_stale_batch_output(stale_batch_result.stdout)

            top_paths = {d.path for d in root_summary.top_directories}
            stale_results: dict[str, int] = dict.fromkeys(top_paths, 0)
            for stale_path, stale_size in all_stale.items():
                for dir_path in top_paths:
                    if is_child_of(stale_path, dir_path):
                        stale_results[dir_path] += stale_size
                        break

            root_stale = sum(all_stale.values())
            enrich_with_stale(root_summary, stale_results, root_stale)
        elif stale_batch_result.stderr:
            root_summary.warnings.append(f"Błąd stale: {stale_batch_result.stderr[:100]}")

    return root_summary, None


def scan_host(host: HostProfile | None, config: Config) -> HostResult:
    """
    Skanuje pojedynczy host.

    Args:
        host: Profil hosta (None dla trybu lokalnego).
        config: Konfiguracja.

    Returns:
        Wynik skanowania.
    """
    host_name = "localhost" if host is None else host.name
    paths = config.paths if host is None else host.paths

    result = HostResult(host_name=host_name)

    if config.verbose:
        print(f"[{host_name}] Rozpoczynam skanowanie...")

    for path in paths:
        if config.verbose:
            print(f"[{host_name}] Skanuję: {path}")

        root_summary, error = _scan_path(path, host, config, host_name)

        if error:
            result.success = False
            result.errors.append(error)

        result.roots.append(root_summary)

    if config.verbose:
        print(f"[{host_name}] Zakończono skanowanie.")

    return result


def scan_all_hosts(config: Config) -> list[HostResult]:
    """
    Skanuje wszystkie hosty.

    Args:
        config: Konfiguracja.

    Returns:
        Lista wyników dla wszystkich hostów.
    """
    results: list[HostResult] = []

    if config.local:
        result = scan_host(None, config)
        results.append(result)
    else:
        with ThreadPoolExecutor(max_workers=config.parallel) as executor:
            futures = {executor.submit(scan_host, host, config): host for host in config.hosts}

            for future in as_completed(futures):
                host = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_result = HostResult(
                        host_name=host.name,
                        success=False,
                        errors=[str(e)],
                    )
                    results.append(error_result)

    return results


def main(args: list[str] | None = None) -> int:
    """
    Główna funkcja programu.

    Args:
        args: Argumenty CLI (None = sys.argv).

    Returns:
        Kod wyjścia (0 = sukces).
    """
    cli_args = parse_args(args)
    config = load_config(cli_args)

    if config.verbose:
        print(f"Konfiguracja załadowana. Hostów: {len(config.hosts)}, Tryb lokalny: {config.local}")

    results = scan_all_hosts(config)

    report = generate_report(results, config)
    write_report(report, config)

    has_errors = any(not r.success for r in results)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
