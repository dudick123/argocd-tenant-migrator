"""CLI entry point for the ArgoCD scanner."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from argocd_scanner.output import display_errors, display_results
from argocd_scanner.scanner import scan_directory

app = typer.Typer(
    name="argocd-scanner",
    help="Scan directories for ArgoCD ApplicationSet YAML files.",
    add_completion=False,
)
console = Console()


@app.command()
def main(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input-path",
            help="Directory path to scan for YAML files",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            help="Recursively scan subdirectories",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Enable verbose output with detailed file information",
        ),
    ] = False,
) -> None:
    """
    Scan directories for ArgoCD ApplicationSet YAML files.

    This tool scans the specified directory for YAML files (.yaml and .yml),
    validates their syntax, and provides a detailed report with statistics.

    Examples:

        # Scan a single directory (non-recursive)
        argocd-scanner --input-path ./my-appsets

        # Scan recursively with verbose output
        argocd-scanner --input-path ./my-appsets --recursive --verbose
    """
    try:
        # Run the scan
        result = scan_directory(input_path, recursive, verbose)

        # Display results
        display_results(result, verbose)

        # Display errors if any
        if result.errors:
            display_errors(result.errors)

        # Exit successfully (even if some files were invalid)
        # No need to explicitly exit - function will return normally

    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user[/yellow]")
        raise typer.Exit(code=130)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if verbose:
            # Show full traceback in verbose mode
            import traceback

            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
