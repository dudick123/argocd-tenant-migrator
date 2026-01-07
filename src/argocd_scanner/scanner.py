"""Core directory scanning and YAML validation logic."""

import time
from pathlib import Path

import yaml

from argocd_scanner.models import FileInfo, ScanResult


def is_preview_file(file_path: Path) -> bool:
    """Detect if a file is a preview branch based on filename.

    Checks if 'preview' appears in the filename (case-insensitive).

    Args:
        file_path: Path to the file to check

    Returns:
        True if filename contains 'preview' (case-insensitive), False otherwise

    Examples:
        - team-a-app-preview.yaml -> True
        - service-PREVIEW.yml -> True
        - app-main.yaml -> False
    """
    return "preview" in file_path.name.lower()


def is_valid_yaml(file_path: Path) -> tuple[bool, str | None]:
    """Validate if a file contains valid YAML.

    Empty files are considered invalid and will return an error.

    Args:
        file_path: Path to the YAML file to validate

    Returns:
        Tuple of (is_valid, error_message).
        If valid: (True, None)
        If invalid: (False, error_message)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Empty files are invalid
        if not content or not content.strip():
            return (False, "Empty YAML file (no content)")

        # Try to parse the YAML
        yaml.safe_load(content)
        return (True, None)

    except yaml.YAMLError as e:
        error_msg = str(e).split("\n")[0]  # Get first line of error
        return (False, f"YAML syntax error: {error_msg}")

    except UnicodeDecodeError:
        return (False, "Not a valid text file (encoding error)")

    except Exception as e:
        return (False, f"Error reading file: {str(e)}")


def is_applicationset(file_path: Path) -> bool:
    """Detect if a YAML file contains an ArgoCD ApplicationSet.

    Checks if the YAML document has kind: ApplicationSet.

    Args:
        file_path: Path to the YAML file to check

    Returns:
        True if the file is an ApplicationSet, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)

        if isinstance(content, dict):
            return content.get("kind") == "ApplicationSet"

        return False
    except Exception:
        return False


def scan_directory(path: Path, recursive: bool, verbose: bool) -> ScanResult:
    """Scan a directory for YAML files and validate them.

    Args:
        path: Directory path to scan
        recursive: If True, scan subdirectories recursively
        verbose: If True, provide detailed scanning information

    Returns:
        ScanResult object containing scan statistics and file information
    """
    start_time = time.time()

    files: list[FileInfo] = []
    errors: list[str] = []
    directories_scanned = 0
    dirs_seen: set[Path] = set()

    # Determine YAML file patterns
    yaml_extensions = ["*.yaml", "*.yml"]

    try:
        if recursive:
            # Recursive scan: find all YAML files in tree
            for pattern in yaml_extensions:
                for file_path in path.rglob(pattern):
                    # Skip hidden directories
                    if any(part.startswith(".") for part in file_path.parts):
                        continue

                    # Track directories
                    parent = file_path.parent
                    if parent not in dirs_seen:
                        dirs_seen.add(parent)
                        directories_scanned += 1

                    # Validate and collect file info
                    _process_file(file_path, files, errors, verbose)
        else:
            # Non-recursive: scan only immediate children
            directories_scanned = 1  # The input directory itself

            for pattern in yaml_extensions:
                for file_path in path.glob(pattern):
                    if file_path.is_file():
                        _process_file(file_path, files, errors, verbose)

    except PermissionError as e:
        errors.append(f"Permission denied accessing directory: {e}")
    except Exception as e:
        errors.append(f"Unexpected error during scan: {e}")

    # Calculate statistics
    valid_count = sum(1 for f in files if f.is_valid)
    invalid_count = sum(1 for f in files if not f.is_valid)
    main_count = sum(1 for f in files if not f.is_preview)
    preview_count = sum(1 for f in files if f.is_preview)
    appset_count = sum(1 for f in files if f.is_applicationset)

    scan_duration = time.time() - start_time

    return ScanResult(
        input_path=path,
        recursive=recursive,
        directories_scanned=directories_scanned,
        total_yaml_files=len(files),
        valid_yaml_files=valid_count,
        invalid_yaml_files=invalid_count,
        main_branch_files=main_count,
        preview_branch_files=preview_count,
        applicationset_files=appset_count,
        files=files,
        scan_duration_seconds=scan_duration,
        errors=errors,
    )


def _process_file(file_path: Path, files: list[FileInfo], errors: list[str], verbose: bool) -> None:
    """Process a single YAML file.

    Args:
        file_path: Path to the file to process
        files: List to append FileInfo to
        errors: List to append errors to
        verbose: Whether to provide verbose output
    """
    try:
        # Get file size
        size_bytes = file_path.stat().st_size

        # Validate YAML
        is_valid, error_message = is_valid_yaml(file_path)

        # Detect preview branch
        is_preview = is_preview_file(file_path)

        # Detect ApplicationSet (only for valid YAML files)
        is_appset = False
        if is_valid:
            is_appset = is_applicationset(file_path)

        # Add to files list
        files.append(
            FileInfo(
                path=file_path,
                is_valid=is_valid,
                is_preview=is_preview,
                is_applicationset=is_appset,
                error_message=error_message,
                size_bytes=size_bytes,
            )
        )

    except PermissionError:
        errors.append(f"Permission denied reading file: {file_path}")
    except Exception as e:
        errors.append(f"Error processing file {file_path}: {e}")
