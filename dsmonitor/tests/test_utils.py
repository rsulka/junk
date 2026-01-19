"""Testy dla modułu utils."""

from dsmonitor.utils import (
    count_access_denied_errors,
    get_parent_path,
    human_size,
    is_child_of,
    normalize_path,
)


class TestHumanSize:
    """Testy konwersji rozmiaru na czytelny format."""

    def test_bytes(self) -> None:
        """Test bajtów."""
        assert human_size(0) == "0 B"
        assert human_size(100) == "100 B"
        assert human_size(1023) == "1023 B"

    def test_kilobytes(self) -> None:
        """Test kilobajtów."""
        assert human_size(1024) == "1.0 KB"
        assert human_size(1536) == "1.5 KB"

    def test_megabytes(self) -> None:
        """Test megabajtów."""
        assert human_size(1024 * 1024) == "1.0 MB"
        assert human_size(1024 * 1024 * 1.5) == "1.5 MB"

    def test_gigabytes(self) -> None:
        """Test gigabajtów."""
        assert human_size(1024**3) == "1.0 GB"

    def test_terabytes(self) -> None:
        """Test terabajtów."""
        assert human_size(1024**4) == "1.0 TB"

    def test_negative(self) -> None:
        """Test ujemnych wartości."""
        assert human_size(-100) == "0 B"


class TestGetParentPath:
    """Testy pobierania ścieżki rodzica."""

    def test_simple_path(self) -> None:
        """Test prostej ścieżki."""
        assert get_parent_path("/data/dir") == "/data"

    def test_nested_path(self) -> None:
        """Test zagnieżdżonej ścieżki."""
        assert get_parent_path("/a/b/c/d") == "/a/b/c"

    def test_root(self) -> None:
        """Test roota."""
        assert get_parent_path("/") == "/"


class TestNormalizePath:
    """Testy normalizacji ścieżki."""

    def test_trailing_slash(self) -> None:
        """Test usuwania trailing slash."""
        assert normalize_path("/data/") == "/data"

    def test_double_slash(self) -> None:
        """Test podwójnych slashy."""
        result = normalize_path("/data//dir")
        assert "//" not in result

    def test_root(self) -> None:
        """Test roota."""
        assert normalize_path("/") == "/"


class TestIsChildOf:
    """Testy sprawdzania czy ścieżka jest podścieżką."""

    def test_exact_match(self) -> None:
        """Test równości ścieżek."""
        assert is_child_of("/data/app", "/data/app") is True

    def test_child_path(self) -> None:
        """Test ścieżki dziecka."""
        assert is_child_of("/data/app/subdir", "/data/app") is True
        assert is_child_of("/data/app/sub/deep", "/data/app") is True

    def test_not_child_similar_prefix(self) -> None:
        """Test że /data/app2 NIE jest dzieckiem /data/app."""
        assert is_child_of("/data/app2", "/data/app") is False
        assert is_child_of("/data/application", "/data/app") is False

    def test_root_is_parent_of_all(self) -> None:
        """Test że / jest rodzicem wszystkiego."""
        assert is_child_of("/data/app", "/") is True
        assert is_child_of("/", "/") is True

    def test_trailing_slash_handling(self) -> None:
        """Test obsługi trailing slash."""
        assert is_child_of("/data/app/", "/data/app") is True
        assert is_child_of("/data/app", "/data/app/") is True


class TestCountAccessDeniedErrors:
    """Testy zliczania błędów dostępu."""

    def test_no_errors(self) -> None:
        """Test braku błędów."""
        assert count_access_denied_errors("") == 0
        assert count_access_denied_errors("some other error\n") == 0

    def test_permission_denied(self) -> None:
        """Test błędów Permission denied."""
        stderr = "du: cannot read directory '/root': Permission denied\n"
        assert count_access_denied_errors(stderr) == 1

    def test_multiple_errors(self) -> None:
        """Test wielu błędów."""
        stderr = """du: cannot read directory '/root': Permission denied
du: cannot read directory '/etc/private': Permission denied
du: cannot access '/lost+found': cannot read directory"""
        assert count_access_denied_errors(stderr) == 3

    def test_polish_error(self) -> None:
        """Test błędu po polsku."""
        stderr = "du: Brak dostępu do '/root'\n"
        assert count_access_denied_errors(stderr) == 1
