"""Validator for ArgoCD ApplicationSet configuration files."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft7Validator, ValidationError, FormatChecker
from rich.console import Console
from rich.tree import Tree

from argocd_migrator.schema import APPLICATIONSET_SCHEMA

logger = logging.getLogger(__name__)
console = Console()


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.total_files = 0
        self.passed_files = 0
        self.failed_files = 0
        self.errors: Dict[str, List[str]] = {}
        self.warnings: List[str] = []

    def is_valid(self) -> bool:
        """Check if all validations passed."""
        return self.failed_files == 0

    def add_file_pass(self, file_path: str, count: int) -> None:
        """Record a file that passed validation."""
        self.total_files += 1
        self.passed_files += 1
        if count == 0:
            self.warnings.append(f"{file_path}: Empty config (no ApplicationSets)")

    def add_file_fail(self, file_path: str, errors: List[str]) -> None:
        """Record a file that failed validation."""
        self.total_files += 1
        self.failed_files += 1
        self.errors[file_path] = errors


def validate_config_item(item: Dict[str, Any], item_index: int = 0) -> Tuple[bool, List[str]]:
    """
    Validate a single ApplicationSet configuration item.

    Args:
        item: Dictionary representing a single ApplicationSet config
        item_index: Index of this item in the array (for error reporting)

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    validator = Draft7Validator(
        APPLICATIONSET_SCHEMA["items"], format_checker=FormatChecker()
    )
    errors = []

    for error in validator.iter_errors(item):
        # Format error message with field path and description
        field_path = ".".join(str(p) for p in error.path) if error.path else "root"

        if error.validator == "required":
            missing_field = error.message.split("'")[1]
            errors.append(f"Missing required field: '{missing_field}'")
        elif error.validator == "pattern":
            errors.append(f"Field '{field_path}': {error.message}")
        elif error.validator == "format":
            errors.append(f"Field '{field_path}': Invalid format - {error.message}")
        elif error.validator == "minLength":
            errors.append(f"Field '{field_path}': Cannot be empty")
        elif error.validator == "maxLength":
            errors.append(f"Field '{field_path}': Exceeds maximum length")
        elif error.validator == "additionalProperties":
            errors.append(f"Unknown field: {error.message}")
        else:
            errors.append(f"Field '{field_path}': {error.message}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_config_list(configs: List[Dict[str, Any]]) -> Tuple[bool, Dict[int, List[str]]]:
    """
    Validate a list of ApplicationSet configurations.

    Args:
        configs: List of ApplicationSet configuration dictionaries

    Returns:
        Tuple of (all_valid, dict_of_errors_by_index)
    """
    all_valid = True
    errors_by_index: Dict[int, List[str]] = {}

    for index, config in enumerate(configs):
        is_valid, errors = validate_config_item(config, index)
        if not is_valid:
            all_valid = False
            errors_by_index[index] = errors

    return all_valid, errors_by_index


def validate_tenant_config_file(config_file: Path) -> Tuple[bool, List[str], int]:
    """
    Validate a single tenant's config.json file.

    Args:
        config_file: Path to the config.json file

    Returns:
        Tuple of (is_valid, list_of_errors, count_of_items)
    """
    errors = []

    # Check if file exists
    if not config_file.exists():
        return False, [f"File not found: {config_file}"], 0

    # Try to parse JSON
    try:
        with open(config_file, "r") as f:
            configs = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"], 0
    except Exception as e:
        return False, [f"Error reading file: {e}"], 0

    # Check it's a list
    if not isinstance(configs, list):
        return False, ["Config must be an array of ApplicationSets"], 0

    item_count = len(configs)

    # Validate each item in the list
    is_valid, errors_by_index = validate_config_list(configs)

    # Format errors with item information
    formatted_errors = []
    for index, item_errors in errors_by_index.items():
        # Try to get the name for better error messages
        name = configs[index].get("name", f"unnamed-{index}")
        for error in item_errors:
            formatted_errors.append(f"Item {index} ({name}): {error}")

    return is_valid, formatted_errors, item_count


def validate_tenant_directory(output_dir: Path) -> ValidationResult:
    """
    Validate all tenant config files in output directory.

    Args:
        output_dir: Base output directory containing tenant subdirectories

    Returns:
        ValidationResult object with summary of validation
    """
    result = ValidationResult()

    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        result.add_file_fail(str(output_dir), ["Directory does not exist"])
        return result

    # Find all config.json files
    config_files = list(output_dir.rglob("config.json"))

    if not config_files:
        logger.warning(f"No config.json files found in {output_dir}")
        result.warnings.append(f"No config.json files found in {output_dir}")
        return result

    # Validate each config file
    for config_file in config_files:
        tenant_name = config_file.parent.name
        relative_path = config_file.relative_to(output_dir)

        logger.debug(f"Validating {relative_path}")

        is_valid, errors, item_count = validate_tenant_config_file(config_file)

        if is_valid:
            result.add_file_pass(str(relative_path), item_count)
            logger.debug(f"✓ {relative_path}: Valid ({item_count} ApplicationSets)")
        else:
            result.add_file_fail(str(relative_path), errors)
            logger.error(f"✗ {relative_path}: Validation failed")
            for error in errors:
                logger.error(f"  - {error}")

    return result


def display_validation_results(result: ValidationResult, output_dir: Path) -> None:
    """
    Display validation results using Rich formatting.

    Args:
        result: ValidationResult object
        output_dir: Base output directory that was validated
    """
    console.print(f"\n[bold]Validating:[/bold] {output_dir}\n")

    # Create a tree for file results
    tree = Tree("📁 Validation Results")

    # Group by status
    for file_path in sorted(result.errors.keys()):
        errors = result.errors[file_path]
        file_node = tree.add(f"[red]✗[/red] {file_path}")
        for error in errors:
            file_node.add(f"[red]{error}[/red]")

    # Add passed files
    passed_count = result.passed_files
    if passed_count > 0:
        tree.add(f"[green]✓[/green] {passed_count} file(s) passed validation")

    console.print(tree)

    # Display warnings
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total files: {result.total_files}")
    console.print(f"  [green]Passed: {result.passed_files}[/green]")
    console.print(f"  [red]Failed: {result.failed_files}[/red]")

    if result.is_valid():
        console.print("\n[bold green]✓ All validations passed![/bold green]")
    else:
        console.print("\n[bold red]✗ Validation failed[/bold red]")
