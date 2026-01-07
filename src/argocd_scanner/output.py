"""Rich terminal output formatting for scan results."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from argocd_scanner.models import ScanResult

console = Console()


def display_results(result: ScanResult, verbose: bool) -> None:
    """Display scan results with rich formatting.

    Args:
        result: ScanResult object containing scan data
        verbose: If True, show detailed file information
    """
    # Header
    console.print()
    console.print("[bold cyan]Scanning ArgoCD ApplicationSet YAML Files[/bold cyan]")
    console.print("=" * 50)
    console.print()

    # Scan configuration
    console.print(f"Scanning directory: [green]{result.input_path}[/green]")
    recursive_mode = "Enabled" if result.recursive else "Disabled"
    console.print(f"Recursive mode: [yellow]{recursive_mode}[/yellow]")
    console.print()

    # Status message
    console.print("[bold green]Scan Complete![/bold green]")
    console.print()

    # Summary table
    summary_table = create_summary_table(result)
    console.print(summary_table)
    console.print()

    # Directory tree (if files found)
    if result.files:
        console.print("[bold]Directory Structure:[/bold]")
        file_tree = create_file_tree(result)
        console.print(file_tree)
        console.print()

    # Verbose mode: detailed file list
    if verbose and result.files:
        console.print("[bold]Detailed File Information:[/bold]")
        console.print()
        file_details_table = create_file_details_table(result)
        console.print(file_details_table)
        console.print()


def create_summary_table(result: ScanResult) -> Table:
    """Create a summary statistics table.

    Args:
        result: ScanResult object containing scan data

    Returns:
        Rich Table object with summary statistics
    """
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="green")

    table.add_row("Directories Scanned", str(result.directories_scanned))
    table.add_row("Total YAML Files Found", str(result.total_yaml_files))
    table.add_row("ApplicationSet Files", str(result.applicationset_files))
    table.add_row("Main Branch Files", str(result.main_branch_files))
    table.add_row("Preview Branch Files", str(result.preview_branch_files))
    table.add_row("Valid YAML Files", str(result.valid_yaml_files))

    # Highlight invalid files in red if any
    invalid_style = "red" if result.invalid_yaml_files > 0 else "green"
    table.add_row(
        "Invalid YAML Files", f"[{invalid_style}]{result.invalid_yaml_files}[/{invalid_style}]"
    )

    table.add_row("Scan Duration", f"{result.scan_duration_seconds:.3f}s")

    return table


def create_file_tree(result: ScanResult) -> Tree:
    """Create a visual tree of scanned files.

    Args:
        result: ScanResult object containing scan data

    Returns:
        Rich Tree object showing directory structure
    """
    # Build tree structure
    tree = Tree(f"[bold]{result.input_path.name or str(result.input_path)}[/bold]")

    # Group files by directory
    files_by_dir: dict[Path, list] = {}
    for file_info in result.files:
        # Get relative path from input directory
        try:
            rel_path = file_info.path.relative_to(result.input_path)
            parent = rel_path.parent
        except ValueError:
            # If file is not relative to input_path, use absolute
            parent = file_info.path.parent
            rel_path = file_info.path

        if parent not in files_by_dir:
            files_by_dir[parent] = []
        files_by_dir[parent].append((rel_path.name, file_info))

    # Sort directories for consistent output
    sorted_dirs = sorted(files_by_dir.keys(), key=lambda p: str(p))

    # Build tree
    if len(sorted_dirs) == 1 and str(sorted_dirs[0]) == ".":
        # Files are in the root directory
        for filename, file_info in sorted(files_by_dir[sorted_dirs[0]]):
            if file_info.is_preview:
                status = "[yellow]🔍 Preview[/yellow]"
            else:
                status = "[green]✓[/green]" if file_info.is_valid else "[red]✗[/red]"
            tree.add(f"{filename} {status}")
    else:
        # Files are in subdirectories
        dir_nodes: dict[Path, Tree] = {}

        for dir_path in sorted_dirs:
            if str(dir_path) == ".":
                # Root level files
                for filename, file_info in sorted(files_by_dir[dir_path]):
                    if file_info.is_preview:
                        status = "[yellow]🔍 Preview[/yellow]"
                    else:
                        status = "[green]✓[/green]" if file_info.is_valid else "[red]✗[/red]"
                    tree.add(f"{filename} {status}")
            else:
                # Create directory nodes as needed
                current_node = tree
                parts = list(dir_path.parts)

                for i, part in enumerate(parts):
                    partial_path = Path(*parts[: i + 1])
                    if partial_path not in dir_nodes:
                        dir_nodes[partial_path] = current_node.add(f"[blue]{part}/[/blue]")
                    current_node = dir_nodes[partial_path]

                # Add files to the directory node
                for filename, file_info in sorted(files_by_dir[dir_path]):
                    if file_info.is_preview:
                        status = "[yellow]🔍 Preview[/yellow]"
                    else:
                        status = "[green]✓[/green]" if file_info.is_valid else "[red]✗[/red]"
                    current_node.add(f"{filename} {status}")

    return tree


def create_file_details_table(result: ScanResult) -> Table:
    """Create a detailed file information table for verbose mode.

    Args:
        result: ScanResult object containing scan data

    Returns:
        Rich Table object with detailed file information
    """
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")
    table.add_column("File Path", style="cyan", no_wrap=False)
    table.add_column("Status", justify="center")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Notes", style="dim")

    # Sort files by path for consistent output
    sorted_files = sorted(result.files, key=lambda f: str(f.path))

    for file_info in sorted_files:
        # Get relative path if possible
        try:
            display_path = str(file_info.path.relative_to(result.input_path))
        except ValueError:
            display_path = str(file_info.path)

        # Status icon
        if file_info.is_preview:
            status = "[yellow]🔍[/yellow]"
        else:
            status = "[green]✓[/green]" if file_info.is_valid else "[red]✗[/red]"

        # File size formatting
        size_str = _format_file_size(file_info.size_bytes)

        # Notes column
        notes = ""
        if file_info.is_preview:
            notes = "Preview branch"
        elif file_info.size_bytes == 0:
            notes = "Empty file"
        elif file_info.error_message:
            notes = file_info.error_message

        table.add_row(display_path, status, size_str, notes)

    return table


def display_errors(errors: list[str]) -> None:
    """Display error messages in a panel.

    Args:
        errors: List of error messages to display
    """
    if not errors:
        return

    console.print()
    error_content = "\n".join(f"• {error}" for error in errors)
    panel = Panel(
        error_content,
        title="[bold red]Errors Encountered[/bold red]",
        border_style="red",
    )
    console.print(panel)
    console.print()


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 KB", "2.3 MB")
    """
    if size_bytes == 0:
        return "0 bytes"
    elif size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
