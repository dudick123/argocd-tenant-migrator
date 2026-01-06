"""Tests for the scanner module."""

from pathlib import Path

import pytest

from argocd_scanner.scanner import is_preview_file, is_valid_yaml, scan_directory


class TestIsPreviewFile:
    """Tests for preview detection."""

    def test_preview_in_filename_lowercase(self):
        """Lowercase 'preview' should be detected."""
        path = Path("/test/app-preview.yaml")
        assert is_preview_file(path) is True

    def test_preview_in_filename_uppercase(self):
        """Uppercase 'PREVIEW' should be detected."""
        path = Path("/test/app-PREVIEW.yaml")
        assert is_preview_file(path) is True

    def test_preview_in_filename_mixedcase(self):
        """Mixed case 'Preview' should be detected."""
        path = Path("/test/app-Preview.yml")
        assert is_preview_file(path) is True

    def test_no_preview_in_filename(self):
        """Files without 'preview' should not be detected."""
        path = Path("/test/app-main.yaml")
        assert is_preview_file(path) is False

    def test_preview_as_word_part(self):
        """'preview' as part of another word should be detected."""
        path = Path("/test/previewer.yaml")
        assert is_preview_file(path) is True


class TestIsValidYaml:
    """Tests for the is_valid_yaml function."""

    def test_empty_file_is_valid(self, tmp_path):
        """Empty files should be considered valid YAML."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        is_valid, error_msg = is_valid_yaml(yaml_file)

        assert is_valid is True
        assert error_msg is None

    def test_valid_yaml_file(self, tmp_path):
        """Valid YAML should pass validation."""
        yaml_file = tmp_path / "valid.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2\n")

        is_valid, error_msg = is_valid_yaml(yaml_file)

        assert is_valid is True
        assert error_msg is None

    def test_invalid_yaml_file(self, tmp_path):
        """Invalid YAML should fail validation with error message."""
        yaml_file = tmp_path / "invalid.yaml"
        # Use actually invalid YAML syntax (unclosed bracket)
        yaml_file.write_text("key: value\nlist: [item1, item2\n")

        is_valid, error_msg = is_valid_yaml(yaml_file)

        assert is_valid is False
        assert error_msg is not None
        assert "YAML syntax error" in error_msg


class TestScanDirectory:
    """Tests for the scan_directory function."""

    @pytest.fixture
    def test_data_dir(self):
        """Fixture providing path to test data directory."""
        return Path(__file__).parent.parent / "io-artifact-examples" / "input"

    def test_non_recursive_scan_finds_files(self, test_data_dir):
        """Non-recursive scan should find files in immediate directory."""
        team_a_dir = test_data_dir / "team-a"

        result = scan_directory(team_a_dir, recursive=False, verbose=False)

        assert result.input_path == team_a_dir
        assert result.recursive is False
        assert result.directories_scanned == 1
        assert result.total_yaml_files == 2  # team-a has 2 YAML files
        assert result.valid_yaml_files == 2  # Both are empty (valid)
        assert result.invalid_yaml_files == 0
        assert len(result.files) == 2
        assert result.scan_duration_seconds >= 0

    def test_recursive_scan_finds_nested_files(self, test_data_dir):
        """Recursive scan should find files in subdirectories."""
        result = scan_directory(test_data_dir, recursive=True, verbose=False)

        assert result.input_path == test_data_dir
        assert result.recursive is True
        assert result.total_yaml_files == 2  # team-a directory has 2 files
        assert result.valid_yaml_files == 2
        assert len(result.files) == 2

    def test_empty_directory_scan(self, tmp_path):
        """Scanning empty directory should return zero files."""
        result = scan_directory(tmp_path, recursive=False, verbose=False)

        assert result.total_yaml_files == 0
        assert result.valid_yaml_files == 0
        assert result.invalid_yaml_files == 0
        assert len(result.files) == 0

    def test_scan_with_valid_and_invalid_files(self, tmp_path):
        """Scan should correctly categorize valid and invalid YAML files."""
        # Create valid YAML file
        valid_file = tmp_path / "valid.yaml"
        valid_file.write_text("key: value\n")

        # Create invalid YAML file
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("key: value\n  bad: indentation\n")

        result = scan_directory(tmp_path, recursive=False, verbose=False)

        assert result.total_yaml_files == 2
        assert result.valid_yaml_files == 1
        assert result.invalid_yaml_files == 1

    def test_scan_skips_hidden_directories(self, tmp_path):
        """Scan should skip hidden directories (starting with .)."""
        # Create hidden directory with YAML file
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "file.yaml").write_text("key: value\n")

        # Create visible directory with YAML file
        visible_dir = tmp_path / "visible"
        visible_dir.mkdir()
        (visible_dir / "file.yaml").write_text("key: value\n")

        result = scan_directory(tmp_path, recursive=True, verbose=False)

        # Should only find file in visible directory
        assert result.total_yaml_files == 1
        assert all(".hidden" not in str(f.path) for f in result.files)

    def test_scan_finds_both_yaml_and_yml_extensions(self, tmp_path):
        """Scan should find both .yaml and .yml files."""
        (tmp_path / "file1.yaml").write_text("key: value\n")
        (tmp_path / "file2.yml").write_text("key: value\n")

        result = scan_directory(tmp_path, recursive=False, verbose=False)

        assert result.total_yaml_files == 2

    def test_scan_tracks_file_sizes(self, tmp_path):
        """Scan should track file sizes correctly."""
        yaml_file = tmp_path / "test.yaml"
        content = "key: value\nother: data\n"
        yaml_file.write_text(content)

        result = scan_directory(tmp_path, recursive=False, verbose=False)

        assert len(result.files) == 1
        assert result.files[0].size_bytes == len(content.encode("utf-8"))

    def test_scan_detects_preview_files(self, tmp_path):
        """Scan should detect and categorize preview files."""
        (tmp_path / "app-main.yaml").write_text("key: value\n")
        (tmp_path / "app-preview.yaml").write_text("key: value\n")

        result = scan_directory(tmp_path, recursive=False, verbose=False)

        assert result.total_yaml_files == 2
        assert result.main_branch_files == 1
        assert result.preview_branch_files == 1

        # Check individual file flags
        main_file = next(f for f in result.files if "main" in f.path.name)
        preview_file = next(f for f in result.files if "preview" in f.path.name)

        assert main_file.is_preview is False
        assert preview_file.is_preview is True
