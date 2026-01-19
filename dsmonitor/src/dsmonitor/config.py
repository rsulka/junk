"""Moduł konfiguracji - ładowanie YAML i merge z CLI."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class HostProfile:
    """Profil hosta z dedykowanymi ustawieniami."""

    name: str
    paths: list[str]
    excludes: list[str] = field(default_factory=list)
    scan_depth: int | None = None
    ssh_user: str | None = None
    ssh_port: int | None = None
    ssh_host: str | None = None
    du_command: str | None = None
    find_command: str | None = None

    def get_scan_depth(self, default: int) -> int:
        """Zwraca głębokość skanowania dla hosta lub wartość domyślną."""
        return self.scan_depth if self.scan_depth is not None else default

    def get_ssh_user(self, default: str | None) -> str | None:
        """Zwraca użytkownika SSH dla hosta lub wartość domyślną."""
        return self.ssh_user if self.ssh_user is not None else default

    def get_ssh_port(self, default: int) -> int:
        """Zwraca port SSH dla hosta lub wartość domyślną."""
        return self.ssh_port if self.ssh_port is not None else default

    def get_ssh_host(self) -> str:
        """Zwraca hosta SSH (domyślnie name)."""
        return self.ssh_host if self.ssh_host is not None else self.name

    def get_du_command(self, default: str) -> str:
        """Zwraca ścieżkę do komendy du dla hosta lub wartość domyślną."""
        return self.du_command if self.du_command is not None else default

    def get_find_command(self, default: str) -> str:
        """Zwraca ścieżkę do komendy find dla hosta lub wartość domyślną."""
        return self.find_command if self.find_command is not None else default


@dataclass
class Config:
    """Główna konfiguracja aplikacji."""

    hosts: list[HostProfile] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    top_n: int = 20
    report_mode: str = "size"
    file_heavy_threshold: float = 0.8
    scan_depth: int = 20
    stale_days: int = 365
    stale_kind: str = "mtime"
    excludes: list[str] = field(default_factory=list)
    parallel: int = 10
    timeout: int = 1800
    output_format: str = "text"
    output_file: str | None = None
    dry_run: bool = False
    verbose: bool = False
    local: bool = False
    ssh_user: str | None = None
    ssh_port: int = 22
    du_command: str = "du"
    find_command: str = "find"
    ssh_options: str = "-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new"

    def validate(self) -> list[str]:
        """
        Waliduje konfigurację.

        Returns:
            Lista błędów walidacji (pusta jeśli OK).
        """
        errors: list[str] = []

        if not self.local and not self.hosts:
            errors.append("Brak hostów do skanowania. Użyj --host lub --local.")

        if self.local and not self.paths:
            errors.append("Brak ścieżek do skanowania. Użyj --paths.")

        if not self.local:
            for host in self.hosts:
                if not host.paths:
                    errors.append(f"Host {host.name} nie ma zdefiniowanych ścieżek.")

        if self.top_n < 1:
            errors.append("--top-n musi być >= 1.")

        if not 0.0 <= self.file_heavy_threshold <= 1.0:
            errors.append("--file-heavy-threshold musi być w zakresie 0.0-1.0.")

        if self.scan_depth < 1:
            errors.append("--scan-depth musi być >= 1.")

        if self.stale_days < 0:
            errors.append("--stale-days musi być >= 0.")

        if self.stale_kind not in ("mtime", "atime", "ctime"):
            errors.append("--stale-kind musi być: mtime, atime lub ctime.")

        if self.report_mode not in ("size", "stale"):
            errors.append("--report-mode musi być: size lub stale.")

        if self.output_format not in ("text", "json", "csv"):
            errors.append("--format musi być: text, json lub csv.")

        if self.parallel < 1:
            errors.append("--parallel musi być >= 1.")

        if self.timeout < 1:
            errors.append("--timeout musi być >= 1.")

        dangerous_patterns = ["`", "$", "&&", "||", ";", "|", ">", "<"]
        for pattern in dangerous_patterns:
            if pattern in self.ssh_options:
                errors.append(f"ssh_options zawiera niebezpieczny znak: {pattern}")
                break

        return errors


def load_yaml_config(config_path: str) -> dict[str, Any]:
    """
    Ładuje konfigurację z pliku YAML.

    Args:
        config_path: Ścieżka do pliku konfiguracyjnego.

    Returns:
        Słownik z konfiguracją.

    Raises:
        FileNotFoundError: Gdy plik nie istnieje.
        yaml.YAMLError: Gdy plik ma nieprawidłowy format.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Plik konfiguracyjny nie istnieje: {config_path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data if data else {}


def build_config(yaml_config: dict[str, Any] | None, cli_args: dict[str, Any]) -> Config:
    """
    Buduje konfigurację z opcjonalnego YAML i argumentów CLI.

    CLI nadpisuje wartości z YAML. Gdy yaml_config jest None, buduje
    konfigurację tylko z CLI.

    Args:
        yaml_config: Opcjonalna konfiguracja z pliku YAML.
        cli_args: Argumenty z linii poleceń.

    Returns:
        Skonfigurowany obiekt Config.
    """
    yaml_config = yaml_config or {}
    defaults = yaml_config.get("defaults", {})
    ssh_config = yaml_config.get("ssh", {})
    yaml_hosts = yaml_config.get("hosts", [])

    hosts: list[HostProfile] = []
    for host_data in yaml_hosts:
        host = HostProfile(
            name=host_data.get("name", ""),
            paths=host_data.get("paths", []),
            excludes=host_data.get("excludes", []),
            scan_depth=host_data.get("scan_depth"),
            ssh_user=host_data.get("ssh_user"),
            ssh_port=host_data.get("ssh_port"),
            ssh_host=host_data.get("ssh_host"),
            du_command=host_data.get("du_command"),
            find_command=host_data.get("find_command"),
        )
        hosts.append(host)

    cli_hosts = cli_args.get("hosts") or []
    cli_paths = cli_args.get("paths") or []
    if cli_hosts:
        for host_name in cli_hosts:
            existing = next((h for h in hosts if h.name == host_name), None)
            if not existing:
                hosts.append(
                    HostProfile(
                        name=host_name,
                        paths=cli_paths if cli_paths else defaults.get("paths", []),
                    )
                )
            elif cli_paths:
                existing.paths = cli_paths

    global_excludes = list(defaults.get("excludes", []))
    cli_excludes = cli_args.get("excludes") or []
    if cli_excludes:
        global_excludes = list(set(global_excludes + cli_excludes))

    paths = cli_paths if cli_paths else defaults.get("paths", [])

    def get_value(key: str, default: Any) -> Any:
        """Pobiera wartość: CLI > YAML defaults > default."""
        if key in cli_args and cli_args[key] is not None:
            return cli_args[key]
        return defaults.get(key, default)

    return Config(
        hosts=hosts,
        paths=paths,
        top_n=get_value("top_n", 20),
        report_mode=get_value("report_mode", "size"),
        file_heavy_threshold=get_value("file_heavy_threshold", 0.8),
        scan_depth=get_value("scan_depth", 20),
        stale_days=get_value("stale_days", 365),
        stale_kind=get_value("stale_kind", "mtime"),
        excludes=global_excludes,
        parallel=get_value("parallel", 10),
        timeout=get_value("timeout", 1800),
        output_format=cli_args.get("format") or defaults.get("format") or "text",
        output_file=cli_args.get("output"),
        dry_run=get_value("dry_run", False),
        verbose=get_value("verbose", False),
        local=get_value("local", False),
        ssh_user=cli_args.get("ssh_user") or ssh_config.get("user"),
        ssh_port=cli_args.get("ssh_port") or ssh_config.get("port", 22),
        ssh_options=cli_args.get("ssh_options") or ssh_config.get("options", Config.ssh_options),
        du_command=get_value("du_command", "du"),
        find_command=get_value("find_command", "find"),
    )
