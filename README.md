# ArgoCD ApplicationSet Scanner

A focused CLI tool to scan directories for ArgoCD ApplicationSet YAML files with beautiful terminal output.

## Features

- Scan directories for YAML files (`.yaml` and `.yml` extensions)
- Validate YAML syntax using PyYAML
- Support for both recursive and non-recursive scanning
- Rich terminal output with tables and directory trees
- Verbose mode for detailed file information
- Graceful error handling with informative messages

## Requirements

- Python 3.12 or higher
- UV package manager (recommended) or pip

## Dependencies

### Core Dependencies

The scanner uses the following production packages:

| Package | Version | Purpose |
|---------|---------|---------|
| **[Typer](https://typer.tiangolo.com/)** | ≥0.15.0 | Modern CLI framework with automatic help generation, type hints support, and excellent developer experience. Handles command-line argument parsing and validation. |
| **[PyYAML](https://pyyaml.org/)** | ≥6.0.2 | YAML parser and emitter for Python. Used to validate YAML syntax in ApplicationSet files and detect malformed configurations. |
| **[Rich](https://rich.readthedocs.io/)** | ≥13.9.0 | Terminal output library for beautiful formatting. Provides tables, trees, colored text, and rich console output that makes the CLI output easy to read and professional. |

### Development Dependencies

These packages are used for development, testing, and code quality:

| Package | Version | Purpose |
|---------|---------|---------|
| **[pytest](https://pytest.org/)** | ≥8.3.0 | Testing framework for writing and running unit and integration tests. Provides fixtures, assertions, and test discovery. |
| **[pytest-cov](https://pytest-cov.readthedocs.io/)** | ≥5.0.0 | Coverage plugin for pytest. Generates code coverage reports to ensure comprehensive test coverage (currently at 81%). |
| **[Ruff](https://docs.astral.sh/ruff/)** | ≥0.8.0 | Fast Python linter and code formatter. Combines the functionality of flake8, black, isort, and more in a single tool written in Rust. |

### Build System

| Package | Purpose |
|---------|---------|
| **[Hatchling](https://hatch.pypa.io/)** | Modern Python build backend that follows PEP 517/518 standards. Handles package building and distribution. |
| **[UV](https://docs.astral.sh/uv/)** | Fast Python package installer and resolver (optional but recommended). Much faster than pip with better dependency resolution. |

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
cd argocd-tenant-migrator

# Install dependencies and the package
uv sync

# The CLI will be available as 'argocd-scanner'
uv run argocd-scanner --help
```

### Using pip

```bash
# Clone the repository
cd argocd-tenant-migrator

# Install in editable mode
pip install -e .

# The CLI will be available as 'argocd-scanner'
argocd-scanner --help
```

## Usage

### Basic Scan

Scan a single directory (non-recursive):

```bash
argocd-scanner --input-path ./my-appsets
```

### Recursive Scan

Scan a directory and all subdirectories:

```bash
argocd-scanner --input-path ./my-appsets --recursive
```

### Verbose Output

Get detailed file information including sizes and validation notes:

```bash
argocd-scanner --input-path ./my-appsets --verbose
```

### Combined Options

Recursive scan with verbose output:

```bash
argocd-scanner --input-path ./my-appsets --recursive --verbose
```

## Command-Line Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--input-path` | Path | Yes | - | Directory path to scan for YAML files |
| `--recursive` | Flag | No | `false` | Recursively scan subdirectories |
| `--verbose` | Flag | No | `false` | Enable verbose output with detailed file information |
| `--help` | Flag | No | - | Show help message and exit |

## Preview Branch Detection

The scanner automatically detects preview branch ApplicationSets based on filename and tracks them separately from main branch files.

### Detection Logic

- **Filename-based detection**: Files with "preview" in the filename (case-insensitive) are marked as preview branch files
- **Separate tracking**: Preview files are counted separately from main branch files in the summary
- **Visual indicators**: Preview files are shown with a 🔍 indicator in the output

### Examples

**Preview files detected:**
- `team-a-app-preview.yaml` 🔍
- `service-PREVIEW.yml` 🔍
- `app-Preview.yaml` 🔍

**Main branch files:**
- `team-a-app-main.yaml` ✓
- `service-prod.yaml` ✓
- `application.yaml` ✓

### Output with Preview Detection

```
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric                 ┃  Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total YAML Files Found │     10 │
│ Main Branch Files      │      7 │
│ Preview Branch Files   │      3 │
│ Valid YAML Files       │      9 │
│ Invalid YAML Files     │      1 │
└────────────────────────┴────────┘
```

## Example Output

### Normal Mode

```
Scanning ArgoCD ApplicationSet YAML Files
==================================================

Scanning directory: /path/to/appsets
Recursive mode: Enabled

Scan Complete!

┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric                 ┃  Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Directories Scanned    │      3 │
│ Total YAML Files Found │     12 │
│ Main Branch Files      │      9 │
│ Preview Branch Files   │      3 │
│ Valid YAML Files       │     11 │
│ Invalid YAML Files     │      1 │
│ Scan Duration          │ 0.15s  │
└────────────────────────┴────────┘

Directory Structure:
appsets
├── team-a/
│   ├── app-main.yaml ✓
│   └── app-preview.yaml 🔍 Preview
└── team-b/
    ├── service.yaml ✓
    └── broken.yaml ✗
```

### Verbose Mode

Adds a detailed file information table:

```
Detailed File Information:

┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ File Path             ┃ Status ┃   Size ┃ Notes               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ team-a/app-main.yaml  │   ✓    │ 1.2 KB │                     │
│ team-a/app-preview... │   🔍   │ 0 bytes│ Preview branch      │
│ team-b/service.yaml   │   ✓    │ 850 B  │                     │
│ team-b/broken.yaml    │   ✗    │ 120 B  │ YAML syntax error...│
└───────────────────────┴────────┴────────┴─────────────────────┘
```

## YAML Validation

The scanner validates YAML syntax for each file:

- **Empty files** are considered valid YAML (representing null/empty document)
- **Malformed YAML** is detected and reported with error messages
- **Binary files** with `.yaml` extension are caught and reported as invalid

## Behavior

### Recursive Scanning

- When `--recursive` is **not** specified: scans only files in the immediate directory
- When `--recursive` is specified: scans all subdirectories recursively

### Hidden Directories

The scanner automatically skips hidden directories (starting with `.`):
- `.git`
- `.venv`
- `.github`
- etc.

### File Extensions

The scanner looks for both common YAML extensions:
- `.yaml`
- `.yml`

## Development

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_scanner.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/
```

### Project Structure

```
argocd-tenant-migrator/
├── src/argocd_scanner/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # CLI entry point (Typer)
│   ├── scanner.py        # Core scanning logic
│   ├── output.py         # Rich terminal output
│   └── models.py         # Data models
├── tests/
│   ├── test_cli.py       # CLI integration tests
│   ├── test_scanner.py   # Scanner unit tests
│   └── test_output.py    # Output formatting tests
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## Exit Codes

- `0`: Success (scan completed, even if some files were invalid)
- `1`: Error (invalid path, permission denied, or unexpected error)
- `130`: Interrupted by user (Ctrl+C)

## License

[Add license information]

## Contributing

[Add contribution guidelines]
