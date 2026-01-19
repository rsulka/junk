"""Testy dla modułu config."""

import tempfile
from pathlib import Path

import pytest

from dsmonitor.config import (
    Config,
    HostProfile,
    build_config,
    load_yaml_config,
)


class TestHostProfile:
    """Testy dla HostProfile."""

    def test_get_scan_depth_with_value(self) -> None:
        """Test zwracania własnej głębokości."""
        host = HostProfile(name="test", paths=["/data"], scan_depth=10)
        assert host.get_scan_depth(20) == 10

    def test_get_scan_depth_default(self) -> None:
        """Test zwracania domyślnej głębokości."""
        host = HostProfile(name="test", paths=["/data"])
        assert host.get_scan_depth(20) == 20

    def test_get_ssh_user_with_value(self) -> None:
        """Test zwracania własnego użytkownika SSH."""
        host = HostProfile(name="test", paths=["/data"], ssh_user="admin")
        assert host.get_ssh_user("default") == "admin"

    def test_get_ssh_user_default(self) -> None:
        """Test zwracania domyślnego użytkownika SSH."""
        host = HostProfile(name="test", paths=["/data"])
        assert host.get_ssh_user("default") == "default"


class TestConfigValidation:
    """Testy walidacji konfiguracji."""

    def test_valid_local_config(self) -> None:
        """Test poprawnej konfiguracji lokalnej."""
        config = Config(local=True, paths=["/data"])
        errors = config.validate()
        assert errors == []

    def test_missing_hosts_remote(self) -> None:
        """Test braku hostów w trybie zdalnym."""
        config = Config(local=False, hosts=[])
        errors = config.validate()
        assert any("Brak hostów" in e for e in errors)

    def test_missing_paths_local(self) -> None:
        """Test braku ścieżek w trybie lokalnym."""
        config = Config(local=True, paths=[])
        errors = config.validate()
        assert any("Brak ścieżek" in e for e in errors)

    def test_invalid_top_n(self) -> None:
        """Test nieprawidłowego top_n."""
        config = Config(local=True, paths=["/data"], top_n=0)
        errors = config.validate()
        assert any("top-n" in e for e in errors)

    def test_invalid_threshold(self) -> None:
        """Test nieprawidłowego progu."""
        config = Config(local=True, paths=["/data"], file_heavy_threshold=1.5)
        errors = config.validate()
        assert any("threshold" in e for e in errors)

    def test_invalid_stale_kind(self) -> None:
        """Test nieprawidłowego stale_kind."""
        config = Config(local=True, paths=["/data"], stale_kind="invalid")
        errors = config.validate()
        assert any("stale-kind" in e for e in errors)


class TestLoadYamlConfig:
    """Testy ładowania konfiguracji YAML."""

    def test_load_valid_yaml(self) -> None:
        """Test ładowania poprawnego YAML."""
        yaml_content = """
defaults:
  top_n: 10
  scan_depth: 15

hosts:
  - name: server1
    paths:
      - /data
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = load_yaml_config(f.name)

            assert config["defaults"]["top_n"] == 10
            assert config["defaults"]["scan_depth"] == 15
            assert len(config["hosts"]) == 1
            assert config["hosts"][0]["name"] == "server1"

        Path(f.name).unlink()

    def test_load_nonexistent_file(self) -> None:
        """Test ładowania nieistniejącego pliku."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config("/nonexistent/config.yaml")


class TestMergeConfig:
    """Testy łączenia konfiguracji YAML z CLI."""

    def test_cli_overrides_yaml(self) -> None:
        """Test nadpisywania wartości YAML przez CLI."""
        yaml_config = {
            "defaults": {"top_n": 10, "scan_depth": 15},
            "hosts": [{"name": "server1", "paths": ["/data"]}],
        }
        cli_args = {"top_n": 5, "local": False}

        config = build_config(yaml_config, cli_args)

        assert config.top_n == 5
        assert config.scan_depth == 15

    def test_merge_excludes(self) -> None:
        """Test łączenia wykluczeń z YAML i CLI."""
        yaml_config = {
            "defaults": {"excludes": ["*.log"]},
            "hosts": [],
        }
        cli_args = {"excludes": ["*.tmp"], "local": True, "paths": ["/data"]}

        config = build_config(yaml_config, cli_args)

        assert "*.log" in config.excludes
        assert "*.tmp" in config.excludes


class TestCreateConfigFromCli:
    """Testy tworzenia konfiguracji tylko z CLI."""

    def test_create_local_config(self) -> None:
        """Test tworzenia konfiguracji lokalnej."""
        cli_args = {
            "local": True,
            "paths": ["/data", "/home"],
            "top_n": 5,
            "hosts": [],
        }

        config = build_config(None, cli_args)

        assert config.local is True
        assert config.paths == ["/data", "/home"]
        assert config.top_n == 5

    def test_create_remote_config(self) -> None:
        """Test tworzenia konfiguracji zdalnej."""
        cli_args = {
            "local": False,
            "hosts": ["server1", "server2"],
            "paths": ["/data"],
            "ssh_user": "admin",
        }

        config = build_config(None, cli_args)

        assert config.local is False
        assert len(config.hosts) == 2
        assert config.hosts[0].name == "server1"
        assert config.ssh_user == "admin"


class TestYamlBooleanDefaults:
    """Testy dla booleanów z YAML defaults."""

    def test_yaml_dry_run_true_respected(self) -> None:
        """Test że dry_run=true z YAML jest respektowane."""
        yaml_config = {
            "defaults": {"dry_run": True, "verbose": True},
            "hosts": [{"name": "server1", "paths": ["/data"]}],
        }
        cli_args: dict[str, object] = {}

        config = build_config(yaml_config, cli_args)

        assert config.dry_run is True
        assert config.verbose is True

    def test_cli_false_overrides_yaml_true(self) -> None:
        """Test że CLI False nadpisuje YAML True."""
        yaml_config = {
            "defaults": {"dry_run": True},
            "hosts": [{"name": "server1", "paths": ["/data"]}],
        }
        cli_args = {"dry_run": False}

        config = build_config(yaml_config, cli_args)

        assert config.dry_run is False


class TestSshOptionsValidation:
    """Testy walidacji ssh_options."""

    def test_dangerous_ssh_options_rejected(self) -> None:
        """Test że niebezpieczne ssh_options są odrzucane."""
        config = Config(local=True, paths=["/data"], ssh_options="-o ProxyCommand=`whoami`")
        errors = config.validate()
        assert any("ssh_options" in e for e in errors)

    def test_valid_ssh_options_accepted(self) -> None:
        """Test że poprawne ssh_options są akceptowane."""
        config = Config(local=True, paths=["/data"], ssh_options="-o BatchMode=yes -o ConnectTimeout=10")
        errors = config.validate()
        assert not any("ssh_options" in e for e in errors)
