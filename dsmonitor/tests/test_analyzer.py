"""Testy dla modułu analyzer."""

from dsmonitor.analyzer import (
    calculate_direct_files_size,
    find_top_n_file_heavy,
    get_path_depth,
    parse_du_output,
)


class TestParseDuOutput:
    """Testy parsowania wyjścia du."""

    def test_parse_simple_output(self) -> None:
        """Test parsowania prostego wyjścia."""
        output = """1024\t/data/dir1
2048\t/data/dir2
4096\t/data"""

        sizes = parse_du_output(output)

        assert sizes["/data/dir1"] == 1024
        assert sizes["/data/dir2"] == 2048
        assert sizes["/data"] == 4096

    def test_parse_empty_output(self) -> None:
        """Test parsowania pustego wyjścia."""
        sizes = parse_du_output("")
        assert sizes == {}

    def test_parse_with_invalid_lines(self) -> None:
        """Test parsowania z nieprawidłowymi liniami."""
        output = """1024\t/data/dir1
invalid line
2048\t/data/dir2"""

        sizes = parse_du_output(output)

        assert len(sizes) == 2
        assert "/data/dir1" in sizes
        assert "/data/dir2" in sizes


class TestCalculateDirectFilesSize:
    """Testy wyliczania direct_files_size."""

    def test_directory_with_only_files(self) -> None:
        """Test katalogu zawierającego tylko pliki."""
        sizes = {
            "/data": 1000,
        }

        direct = calculate_direct_files_size("/data", sizes)
        assert direct == 1000

    def test_directory_with_subdirs(self) -> None:
        """Test katalogu z podkatalogami."""
        sizes = {
            "/data": 1000,
            "/data/sub1": 300,
            "/data/sub2": 200,
        }

        direct = calculate_direct_files_size("/data", sizes)
        assert direct == 500

    def test_directory_with_nested_subdirs(self) -> None:
        """Test katalogu z zagnieżdżonymi podkatalogami."""
        sizes = {
            "/data": 1000,
            "/data/sub1": 500,
            "/data/sub1/nested": 200,
        }

        direct = calculate_direct_files_size("/data", sizes)
        assert direct == 500


class TestGetPathDepth:
    """Testy obliczania głębokości ścieżki."""

    def test_root_depth(self) -> None:
        """Test głębokości dla roota."""
        assert get_path_depth("/data", "/data") == 0

    def test_one_level_depth(self) -> None:
        """Test głębokości jednego poziomu."""
        assert get_path_depth("/data/sub", "/data") == 1

    def test_multi_level_depth(self) -> None:
        """Test głębokości wielu poziomów."""
        assert get_path_depth("/data/a/b/c", "/data") == 3


class TestFindTopNFileHeavy:
    """Testy znajdowania Top N katalogów file-heavy."""

    def test_find_top_n(self) -> None:
        """Test znajdowania Top N."""
        sizes = {
            "/data": 10000,
            "/data/big": 5000,
            "/data/medium": 3000,
            "/data/medium/sub": 500,
            "/data/small": 1000,
        }

        top = find_top_n_file_heavy(sizes, "/data", n=2, threshold=0.8)

        assert len(top) == 2
        assert top[0].path == "/data/big"
        assert top[1].path == "/data/medium"

    def test_filter_by_threshold(self) -> None:
        """Test filtrowania po progu."""
        sizes = {
            "/data": 1000,
            "/data/heavy": 500,
            "/data/light": 500,
            "/data/light/sub": 400,
        }

        top = find_top_n_file_heavy(sizes, "/data", n=10, threshold=0.9)

        assert len(top) == 2
        assert top[0].path == "/data/heavy"

    def test_empty_result(self) -> None:
        """Test pustego wyniku gdy katalog ma tylko podkatalogi bez plików."""
        sizes = {
            "/data": 1000,
            "/data/sub1": 500,
            "/data/sub2": 500,
        }

        top = find_top_n_file_heavy(sizes, "/data", n=10, threshold=0.5)
        assert all(d.file_heavy_ratio >= 0.5 for d in top)


class TestFindTopNByStale:
    """Testy znajdowania Top N katalogów po stale_size."""

    def test_find_top_n_by_stale(self) -> None:
        """Test znajdowania Top N po stale_size."""
        from dsmonitor.analyzer import find_top_n_by_stale

        stale_data = {
            "/data/dir1": 5000,
            "/data/dir2": 1000,
            "/data/dir3": 3000,
        }
        sizes = {
            "/data": 10000,
            "/data/dir1": 6000,
            "/data/dir2": 3000,
            "/data/dir3": 4000,
        }

        top = find_top_n_by_stale(stale_data, sizes, "/data", n=2)

        assert len(top) == 2
        assert top[0].path == "/data/dir1"
        assert top[0].stale_size == 5000
        assert top[1].path == "/data/dir3"
        assert top[1].stale_size == 3000

    def test_find_top_n_by_stale_with_zero(self) -> None:
        """Test pomijania katalogów z zerowym stale."""
        from dsmonitor.analyzer import find_top_n_by_stale

        stale_data = {
            "/data/dir1": 1000,
            "/data/dir2": 0,
        }
        sizes = {
            "/data": 5000,
            "/data/dir1": 2000,
            "/data/dir2": 3000,
        }

        top = find_top_n_by_stale(stale_data, sizes, "/data", n=10)

        assert len(top) == 1
        assert top[0].path == "/data/dir1"
