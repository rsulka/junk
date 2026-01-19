"""Moduł wykonywania komend - lokalne i przez SSH."""

import shlex
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dsmonitor.utils import normalize_path

if TYPE_CHECKING:
    from dsmonitor.config import Config, HostProfile


@dataclass
class CommandResult:
    """Wynik wykonania komendy."""

    command: str
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False
    dry_run: bool = False

    @property
    def success(self) -> bool:
        """Czy komenda zakończyła się sukcesem."""
        return self.return_code == 0 and not self.timed_out


def build_du_command_args(
    path: str, depth: int, excludes: list[str], one_filesystem: bool = True, du_command: str = "du"
) -> list[str]:
    """
    Buduje komendę du jako listę argumentów (dla shell=False).

    Args:
        path: Ścieżka do skanowania.
        depth: Maksymalna głębokość.
        excludes: Lista wzorców do wykluczenia.
        one_filesystem: Czy ograniczyć do jednego systemu plików.
        du_command: Ścieżka do komendy du (np. /opt/freeware/bin/du dla AIX).

    Returns:
        Lista argumentów komendy du.
    """
    cmd_args = [du_command, "-B1"]

    if one_filesystem:
        cmd_args.append("-x")

    cmd_args.append(f"--max-depth={depth}")

    for pattern in excludes:
        cmd_args.append(f"--exclude={pattern}")

    cmd_args.append(path)

    return cmd_args


def build_ssh_command_args(host: "HostProfile", remote_cmd: str, config: "Config") -> list[str]:
    """
    Buduje komendę SSH jako listę argumentów.

    Args:
        host: Profil hosta.
        remote_cmd: Komenda do wykonania na zdalnym hoście.
        config: Konfiguracja globalna.

    Returns:
        Lista argumentów komendy SSH.
    """
    ssh_args = ["ssh"]

    ssh_user = host.get_ssh_user(config.ssh_user)
    ssh_port = host.get_ssh_port(config.ssh_port)
    ssh_host = host.get_ssh_host()

    if config.ssh_options:
        ssh_args.extend(shlex.split(config.ssh_options))

    ssh_args.extend(["-p", str(ssh_port)])

    if ssh_user:
        ssh_args.append(f"{ssh_user}@{ssh_host}")
    else:
        ssh_args.append(ssh_host)

    ssh_args.append(remote_cmd)

    return ssh_args


def build_ssh_command(host: "HostProfile", remote_cmd: str, config: "Config") -> str:
    """
    Buduje komendę SSH jako string (do wyświetlania).

    Args:
        host: Profil hosta.
        remote_cmd: Komenda do wykonania na zdalnym hoście.
        config: Konfiguracja globalna.

    Returns:
        Pełna komenda SSH jako string.
    """
    args = build_ssh_command_args(host, remote_cmd, config)
    args_quoted = [*args[:-1], shlex.quote(args[-1])]
    return " ".join(args_quoted)


def run_command(
    cmd: str | list[str],
    host: "HostProfile | None",
    config: "Config",
    timeout: int | None = None,
) -> CommandResult:
    """
    Uruchamia komendę lokalnie lub przez SSH.

    Dla SSH zawsze używa shell=False. Dla lokalnych komend:
    - jeśli cmd jest listą - shell=False (bezpieczniejsze)
    - jeśli cmd jest stringiem - shell=True (dla pipe'ów)

    Args:
        cmd: Komenda do wykonania (string lub lista argumentów).
        host: Profil hosta (None dla trybu lokalnego).
        config: Konfiguracja globalna.
        timeout: Timeout w sekundach (None = użyj config.timeout).

    Returns:
        Wynik wykonania komendy.
    """
    if timeout is None:
        timeout = config.timeout

    is_ssh = host is not None and not config.local
    cmd_str = shlex.join(cmd) if isinstance(cmd, list) else cmd
    display_cmd = build_ssh_command(host, cmd_str, config) if is_ssh and host else cmd_str

    if config.dry_run:
        return CommandResult(
            command=display_cmd,
            stdout="",
            stderr="",
            return_code=0,
            dry_run=True,
        )

    try:
        if is_ssh:
            assert host is not None
            ssh_args = build_ssh_command_args(host, cmd_str, config)
            result = subprocess.run(
                ssh_args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            use_shell = isinstance(cmd, str)
            result = subprocess.run(
                cmd,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        return CommandResult(
            command=display_cmd,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )

    except subprocess.TimeoutExpired:
        return CommandResult(
            command=display_cmd,
            stdout="",
            stderr=f"Timeout po {timeout} sekundach",
            return_code=-1,
            timed_out=True,
        )


def run_du(
    path: str,
    host: "HostProfile | None",
    config: "Config",
    depth: int | None = None,
    excludes: list[str] | None = None,
) -> CommandResult:
    """
    Uruchamia komendę du dla podanej ścieżki.

    Args:
        path: Ścieżka do skanowania.
        host: Profil hosta (None dla trybu lokalnego).
        config: Konfiguracja globalna.
        depth: Głębokość skanowania (None = użyj config).
        excludes: Wykluczenia (None = użyj config).

    Returns:
        Wynik wykonania komendy du.
    """
    if depth is None:
        depth = host.get_scan_depth(config.scan_depth) if host else config.scan_depth

    if excludes is None:
        all_excludes = list(config.excludes)
        if host:
            all_excludes.extend(host.excludes)
        excludes = all_excludes

    du_command = host.get_du_command(config.du_command) if host else config.du_command
    du_cmd = build_du_command_args(path, depth, excludes, du_command=du_command)
    return run_command(du_cmd, host, config)


def build_find_stale_batch_command(root_path: str, days: int, kind: str = "mtime", find_command: str = "find") -> str:
    """
    Buduje komendę find do wyliczenia stale_size dla wielu ścieżek naraz.

    Zwraca rozmiar per katalog w formacie: ścieżka<tab>rozmiar.

    Args:
        root_path: Główna ścieżka (root).
        days: Liczba dni (pliki starsze niż).
        kind: Typ czasu (mtime, atime, ctime).
        find_command: Ścieżka do komendy find.

    Returns:
        Komenda find jako string.
    """
    time_flag = f"-{kind}"
    quoted_root = shlex.quote(root_path)

    cmd = (
        f"{shlex.quote(find_command)} {quoted_root} -xdev -type f {time_flag} +{days} -printf '%h\\t%s\\n' | "
        "awk -F'\\t' '{sums[$1]+=$2} END{for(d in sums) print d\"\\t\"sums[d]}'"
    )

    return cmd


def run_find_stale_batch(
    root_path: str,
    host: "HostProfile | None",
    config: "Config",
    days: int | None = None,
    kind: str | None = None,
) -> CommandResult:
    """
    Uruchamia komendę find do obliczenia stale_size dla całego roota.

    Skanuje cały root_path i grupuje wyniki per katalog.
    Filtrowanie do konkretnych ścieżek odbywa się po stronie wywołującego.

    Args:
        root_path: Główna ścieżka (root) do skanowania.
        host: Profil hosta (None dla trybu lokalnego).
        config: Konfiguracja globalna.
        days: Liczba dni (None = użyj config).
        kind: Typ czasu (None = użyj config).

    Returns:
        Wynik wykonania komendy find.
    """
    if days is None:
        days = config.stale_days

    if kind is None:
        kind = config.stale_kind

    find_command = host.get_find_command(config.find_command) if host else config.find_command
    find_cmd = build_find_stale_batch_command(root_path, days, kind, find_command)
    return run_command(find_cmd, host, config)


def parse_stale_batch_output(output: str) -> dict[str, int]:
    """
    Parsuje wyjście komendy find batch do słownika path -> stale_size.

    Args:
        output: Wyjście komendy (ścieżka<tab>rozmiar na linię).

    Returns:
        Słownik: ścieżka -> rozmiar stale w bajtach.
    """
    results: dict[str, int] = {}

    for line in output.strip().split("\n"):
        if not line:
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        try:
            path = normalize_path(parts[0])
            size = int(parts[1])
            results[path] = size
        except ValueError:
            continue

    return results
