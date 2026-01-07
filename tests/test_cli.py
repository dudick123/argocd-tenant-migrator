"""Tests for the CLI module."""

from pathlib import Path

from typer.testing import CliRunner

from argocd_scanner.cli import app

runner = CliRunner()


class TestCLI:
    """Tests for the CLI interface."""

    def test_help_command(self):
        """Test that --help displays help message."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Scan directories for ArgoCD ApplicationSet YAML files" in result.stdout
        assert "--input-path" in result.stdout
        assert "--recursive" in result.stdout
        assert "--verbose" in result.stdout

    def test_missing_required_input_path(self):
        """Test that CLI fails when --input-path is not provided."""
        result = runner.invoke(app, [])

        assert result.exit_code != 0
        # Typer outputs errors to both stdout and stderr
        output = result.stdout + (result.stderr or "")
        assert "Missing option" in output or "required" in output.lower()

    def test_scan_with_test_data(self):
        """Test scanning the test data directory."""
        test_data_dir = Path(__file__).parent.parent / "io-artifact-examples" / "input" / "team-a"

        if not test_data_dir.exists():
            # Skip if test data doesn't exist
            return

        result = runner.invoke(app, ["--input-path", str(test_data_dir)])

        assert result.exit_code == 0
        assert "Scan Complete!" in result.stdout
        assert "Total YAML Files Found" in result.stdout
        assert "team-a-app-a-main.yaml" in result.stdout

    def test_recursive_flag(self):
        """Test that --recursive flag works."""
        test_data_dir = Path(__file__).parent.parent / "io-artifact-examples" / "input"

        if not test_data_dir.exists():
            return

        result = runner.invoke(app, ["--input-path", str(test_data_dir), "--recursive"])

        assert result.exit_code == 0
        assert "Recursive mode: Enabled" in result.stdout

    def test_verbose_flag(self):
        """Test that --verbose flag shows detailed information."""
        test_data_dir = Path(__file__).parent.parent / "io-artifact-examples" / "input" / "team-a"

        if not test_data_dir.exists():
            return

        result = runner.invoke(app, ["--input-path", str(test_data_dir), "--verbose"])

        assert result.exit_code == 0
        assert "Detailed File Information" in result.stdout
        assert "Size" in result.stdout

    def test_nonexistent_directory(self):
        """Test that CLI fails gracefully with non-existent directory."""
        result = runner.invoke(app, ["--input-path", "/nonexistent/path/to/dir"])

        assert result.exit_code != 0
        # Typer validates path existence, so error comes from Typer

    def test_recursive_and_verbose_together(self):
        """Test that --recursive and --verbose flags work together."""
        test_data_dir = Path(__file__).parent.parent / "io-artifact-examples" / "input"

        if not test_data_dir.exists():
            return

        result = runner.invoke(
            app, ["--input-path", str(test_data_dir), "--recursive", "--verbose"]
        )

        assert result.exit_code == 0
        assert "Recursive mode: Enabled" in result.stdout
        assert "Detailed File Information" in result.stdout

    def test_scan_with_preview_files(self, tmp_path):
        """Test scanning with both main and preview files."""
        (tmp_path / "main.yaml").write_text("key: value\n")
        (tmp_path / "preview.yaml").write_text("key: value\n")

        result = runner.invoke(app, ["--input-path", str(tmp_path)])

        assert result.exit_code == 0
        assert "Main Branch Files" in result.stdout
        assert "Preview Branch Files" in result.stdout

    def test_scan_shows_applicationset_count(self):
        """Test that CLI shows ApplicationSet count in output."""
        test_data_dir = Path(__file__).parent.parent / "io-artifact-examples" / "input" / "team-a"

        if not test_data_dir.exists():
            return

        result = runner.invoke(app, ["--input-path", str(test_data_dir)])

        assert result.exit_code == 0
        assert "ApplicationSet Files" in result.stdout
