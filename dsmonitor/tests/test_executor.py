"""Testy dla modułu executor."""

from dsmonitor.config import Config, HostProfile
from dsmonitor.executor import (
    build_du_command,
    build_du_command_args,
    build_find_stale_command,
    build_ssh_command,
    run_command,
)


class TestBuildDuCommand:
    """Testy budowania komendy du."""

    def test_basic_command(self) -> None:
        """Test podstawowej komendy."""
        cmd = build_du_command("/data", depth=10, excludes=[])

        assert "du" in cmd
        assert "-B1" in cmd
        assert "-x" in cmd
        assert "--max-depth=10" in cmd
        assert "/data" in cmd

    def test_command_with_excludes(self) -> None:
        """Test komendy z wykluczeniami."""
        cmd = build_du_command("/data", depth=10, excludes=["*.log", "*.tmp"])

        assert "--exclude=*.log" in cmd or "'--exclude=*.log'" in cmd
        assert "--exclude=*.tmp" in cmd or "'--exclude=*.tmp'" in cmd

    def test_command_args_returns_list(self) -> None:
        """Test że build_du_command_args zwraca listę."""
        args = build_du_command_args("/data", depth=10, excludes=["*.log"])

        assert isinstance(args, list)
        assert "--exclude=*.log" in args
        assert "/data" in args

    def test_command_without_one_filesystem(self) -> None:
        """Test komendy bez ograniczenia do jednego FS."""
        cmd = build_du_command("/data", depth=10, excludes=[], one_filesystem=False)

        assert "-x" not in cmd

    def test_custom_du_command_path(self) -> None:
        """Test komendy z niestandardową ścieżką du (np. AIX)."""
        cmd = build_du_command("/data", depth=10, excludes=[], du_command="/opt/freeware/bin/du")

        assert "/opt/freeware/bin/du" in cmd
        assert cmd.startswith("/opt/freeware/bin/du")

    def test_custom_du_command_args(self) -> None:
        """Test że build_du_command_args respektuje du_command."""
        args = build_du_command_args("/data", depth=10, excludes=[], du_command="/usr/bin/du")

        assert args[0] == "/usr/bin/du"


class TestBuildFindStaleCommand:
    """Testy budowania komendy find stale."""

    def test_basic_command(self) -> None:
        """Test podstawowej komendy."""
        cmd = build_find_stale_command("/data", days=365, kind="mtime")

        assert "find" in cmd
        assert "/data" in cmd
        assert "-xdev" in cmd
        assert "-type f" in cmd
        assert "-mtime +365" in cmd
        assert "-printf '%s\\n'" in cmd
        assert "awk" in cmd

    def test_command_with_atime(self) -> None:
        """Test komendy z atime."""
        cmd = build_find_stale_command("/data", days=30, kind="atime")

        assert "-atime +30" in cmd

    def test_custom_find_command(self) -> None:
        """Test komendy z niestandardową ścieżką find."""
        cmd = build_find_stale_command("/data", days=365, kind="mtime", find_command="/opt/freeware/bin/find")

        assert "/opt/freeware/bin/find" in cmd
        assert "/data" in cmd


class TestBuildSshCommand:
    """Testy budowania komendy SSH."""

    def test_basic_ssh_command(self) -> None:
        """Test podstawowej komendy SSH."""
        host = HostProfile(name="server1", paths=["/data"])
        config = Config(ssh_port=22, ssh_options="-o BatchMode=yes")

        cmd = build_ssh_command(host, "echo test", config)

        assert "ssh" in cmd
        assert "-o BatchMode=yes" in cmd
        assert "-p 22" in cmd
        assert "server1" in cmd

    def test_ssh_command_with_user(self) -> None:
        """Test komendy SSH z użytkownikiem."""
        host = HostProfile(name="server1", paths=["/data"], ssh_user="admin")
        config = Config(ssh_port=22, ssh_options="")

        cmd = build_ssh_command(host, "echo test", config)

        assert "admin@server1" in cmd

    def test_ssh_command_with_custom_port(self) -> None:
        """Test komendy SSH z własnym portem."""
        host = HostProfile(name="server1", paths=["/data"], ssh_port=2222)
        config = Config(ssh_port=22, ssh_options="")

        cmd = build_ssh_command(host, "echo test", config)

        assert "-p 2222" in cmd


class TestRunCommand:
    """Testy wykonywania komend."""

    def test_dry_run_mode(self) -> None:
        """Test trybu dry-run."""
        config = Config(dry_run=True, local=True, paths=["/data"])

        result = run_command("echo test", None, config)

        assert result.dry_run is True
        assert result.command == "echo test"
        assert result.return_code == 0

    def test_local_command(self) -> None:
        """Test lokalnej komendy."""
        config = Config(dry_run=False, local=True, paths=["/data"], timeout=10)

        result = run_command("echo 'hello'", None, config)

        assert result.success is True
        assert "hello" in result.stdout

    def test_command_with_error(self) -> None:
        """Test komendy z błędem."""
        config = Config(dry_run=False, local=True, paths=["/data"], timeout=10)

        result = run_command("ls /nonexistent/path/12345", None, config)

        assert result.success is False
        assert result.return_code != 0


class TestBuildFindStaleBatchCommand:
    """Testy budowania komendy find batch."""

    def test_basic_batch_command(self) -> None:
        """Test podstawowej komendy batch."""
        from dsmonitor.executor import build_find_stale_batch_command

        cmd = build_find_stale_batch_command("/data", days=365, kind="mtime")

        assert "find" in cmd
        assert "/data" in cmd
        assert "-mtime +365" in cmd
        assert "-printf '%h\\t%s\\n'" in cmd
        assert "awk" in cmd
        assert "sums[$1]+=$2" in cmd

    def test_batch_command_awk_syntax(self) -> None:
        """Test składni AWK - wykonanie komendy nie powinno zwracać błędu składni."""
        from dsmonitor.executor import build_find_stale_batch_command

        cmd = build_find_stale_batch_command("/tmp", days=1, kind="mtime")

        import subprocess

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        assert "syntax error" not in result.stderr.lower()


class TestParseStaleBatchOutput:
    """Testy parsowania wyjścia batch find."""

    def test_parse_valid_output(self) -> None:
        """Test parsowania poprawnego wyjścia."""
        from dsmonitor.executor import parse_stale_batch_output

        output = "/data/logs\t1000\n/data/tmp\t2000\n"
        result = parse_stale_batch_output(output)

        assert result == {"/data/logs": 1000, "/data/tmp": 2000}

    def test_parse_empty_output(self) -> None:
        """Test parsowania pustego wyjścia."""
        from dsmonitor.executor import parse_stale_batch_output

        result = parse_stale_batch_output("")
        assert result == {}

    def test_parse_invalid_lines(self) -> None:
        """Test parsowania z nieprawidłowymi liniami."""
        from dsmonitor.executor import parse_stale_batch_output

        output = "/data/logs\t1000\ninvalid_line\n/data/tmp\t2000\n"
        result = parse_stale_batch_output(output)

        assert result == {"/data/logs": 1000, "/data/tmp": 2000}

    def test_parse_output_normalizes_paths(self) -> None:
        """Test że ścieżki są normalizowane."""
        from dsmonitor.executor import parse_stale_batch_output

        output = "/data/logs/./subdir\t1000\n"
        result = parse_stale_batch_output(output)

        assert "/data/logs/subdir" in result
