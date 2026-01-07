"""Data models for the ArgoCD scanner."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileInfo:
    """Information about a scanned YAML file.

    Attributes:
        path: Path to the YAML file
        is_valid: Whether the file contains valid YAML
        is_preview: Whether this is a preview branch file
        is_applicationset: Whether this is an ArgoCD ApplicationSet
        error_message: Error message if YAML is invalid
        size_bytes: File size in bytes
    """

    path: Path
    is_valid: bool
    is_preview: bool
    is_applicationset: bool = False
    error_message: str | None = None
    size_bytes: int = 0


@dataclass
class ScanResult:
    """Results from a directory scan.

    Attributes:
        input_path: The directory that was scanned
        recursive: Whether the scan was recursive
        directories_scanned: Number of directories scanned
        total_yaml_files: Total number of YAML files found
        valid_yaml_files: Number of valid YAML files
        invalid_yaml_files: Number of invalid YAML files
        main_branch_files: Number of main branch files
        preview_branch_files: Number of preview branch files
        applicationset_files: Number of ArgoCD ApplicationSet files
        files: List of FileInfo objects for all scanned files
        scan_duration_seconds: Time taken to complete the scan
        errors: List of non-file errors (permissions, etc.)
    """

    input_path: Path
    recursive: bool
    directories_scanned: int
    total_yaml_files: int
    valid_yaml_files: int
    invalid_yaml_files: int
    main_branch_files: int
    preview_branch_files: int
    applicationset_files: int
    files: list[FileInfo]
    scan_duration_seconds: float
    errors: list[str]
