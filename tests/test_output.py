"""Tests for the output module."""

from pathlib import Path

from rich.table import Table
from rich.tree import Tree

from argocd_scanner.models import FileInfo, ScanResult
from argocd_scanner.output import (
    create_file_details_table,
    create_file_tree,
    create_summary_table,
)


class TestCreateSummaryTable:
    """Tests for create_summary_table function."""

    def test_creates_table_with_correct_statistics(self):
        """Summary table should contain all scan statistics."""
        result = ScanResult(
            input_path=Path("/test/path"),
            recursive=True,
            directories_scanned=5,
            total_yaml_files=10,
            valid_yaml_files=8,
            invalid_yaml_files=2,
            main_branch_files=7,
            preview_branch_files=3,
            applicationset_files=6,
            files=[],
            scan_duration_seconds=1.234,
            errors=[],
        )

        table = create_summary_table(result)

        assert isinstance(table, Table)
        # Check that table has correct number of columns
        assert len(table.columns) == 2

    def test_table_includes_scan_duration(self):
        """Summary table should include formatted scan duration."""
        result = ScanResult(
            input_path=Path("/test"),
            recursive=False,
            directories_scanned=1,
            total_yaml_files=5,
            valid_yaml_files=5,
            invalid_yaml_files=0,
            main_branch_files=5,
            preview_branch_files=0,
            applicationset_files=5,
            files=[],
            scan_duration_seconds=2.567,
            errors=[],
        )

        table = create_summary_table(result)

        # Table should be created successfully
        assert isinstance(table, Table)


class TestCreateFileTree:
    """Tests for create_file_tree function."""

    def test_creates_tree_for_files(self):
        """File tree should be created with file information."""
        files = [
            FileInfo(path=Path("/test/file1.yaml"), is_valid=True, is_preview=False, is_applicationset=True, size_bytes=100),
            FileInfo(path=Path("/test/file2.yaml"), is_valid=False, is_preview=False, is_applicationset=False, size_bytes=200),
        ]

        result = ScanResult(
            input_path=Path("/test"),
            recursive=False,
            directories_scanned=1,
            total_yaml_files=2,
            valid_yaml_files=1,
            invalid_yaml_files=1,
            main_branch_files=2,
            preview_branch_files=0,
            applicationset_files=1,
            files=files,
            scan_duration_seconds=0.5,
            errors=[],
        )

        tree = create_file_tree(result)

        assert isinstance(tree, Tree)

    def test_empty_file_list(self):
        """Tree should handle empty file list gracefully."""
        result = ScanResult(
            input_path=Path("/test"),
            recursive=False,
            directories_scanned=1,
            total_yaml_files=0,
            valid_yaml_files=0,
            invalid_yaml_files=0,
            main_branch_files=0,
            preview_branch_files=0,
            applicationset_files=0,
            files=[],
            scan_duration_seconds=0.1,
            errors=[],
        )

        tree = create_file_tree(result)

        assert isinstance(tree, Tree)


class TestCreateFileDetailsTable:
    """Tests for create_file_details_table function."""

    def test_creates_detailed_table(self):
        """Detailed table should include file paths, status, size, and notes."""
        files = [
            FileInfo(
                path=Path("/test/valid.yaml"),
                is_valid=True,
                is_preview=False,
                is_applicationset=True,
                size_bytes=0,
            ),
            FileInfo(
                path=Path("/test/invalid.yaml"),
                is_valid=False,
                is_preview=False,
                is_applicationset=False,
                error_message="YAML syntax error",
                size_bytes=150,
            ),
        ]

        result = ScanResult(
            input_path=Path("/test"),
            recursive=False,
            directories_scanned=1,
            total_yaml_files=2,
            valid_yaml_files=1,
            invalid_yaml_files=1,
            main_branch_files=2,
            preview_branch_files=0,
            applicationset_files=1,
            files=files,
            scan_duration_seconds=0.5,
            errors=[],
        )

        table = create_file_details_table(result)

        assert isinstance(table, Table)
        # Should have 4 columns: File Path, Status, Size, Notes
        assert len(table.columns) == 4

    def test_table_shows_empty_file_note(self):
        """Detailed table should note empty invalid files."""
        files = [
            FileInfo(
                path=Path("/test/empty.yaml"),
                is_valid=False,
                is_preview=False,
                is_applicationset=False,
                error_message="Empty YAML file (no content)",
                size_bytes=0
            ),
        ]

        result = ScanResult(
            input_path=Path("/test"),
            recursive=False,
            directories_scanned=1,
            total_yaml_files=1,
            valid_yaml_files=0,
            invalid_yaml_files=1,
            main_branch_files=1,
            preview_branch_files=0,
            applicationset_files=0,
            files=files,
            scan_duration_seconds=0.1,
            errors=[],
        )

        table = create_file_details_table(result)

        assert isinstance(table, Table)
