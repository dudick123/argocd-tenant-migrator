"""CLI entry point for ArgoCD Tenant Migrator."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from argocd_migrator.migrator import migrate_applicationsets

app = typer.Typer(
    name="argocd-migrator",
    help="Migrate ArgoCD ApplicationSets from SCM Generators to Git Generators",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.callback(invoke_without_command=True)
def main(
    input_dir: Path = typer.Option(
        Path.cwd(),
        "--input-dir",
        "-i",
        help="Directory to scan for ApplicationSet manifests",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        Path("output"),
        "--output-dir",
        "-o",
        help="Directory for generated JSON configuration files",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Simulate migration without writing output files",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed logging output",
    ),
    cluster_name: Optional[str] = typer.Option(
        None,
        "--cluster-name",
        help="Target cluster name to override in all ApplicationSets",
    ),
    validate: bool = typer.Option(
        False,
        "--validate",
        help="Validate existing JSON configuration files in output directory",
    ),
    validate_on_migrate: bool = typer.Option(
        False,
        "--validate-on-migrate",
        help="Validate configurations before writing during migration",
    ),
) -> None:
    """
    Migrate ArgoCD ApplicationSets from SCM Generators to Git Generators.

    Scans the input directory for ApplicationSet YAML manifests using SCM Generators,
    extracts relevant information, and generates JSON configuration files for new
    ApplicationSets using Git Generators.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    # Check for mutual exclusivity
    if validate and (input_dir != Path.cwd() or cluster_name or validate_on_migrate):
        console.print(
            "[bold red]Error:[/bold red] --validate cannot be used with "
            "migration options (--input-dir, --cluster-name, --validate-on-migrate)"
        )
        raise typer.Exit(code=1)

    # Standalone validation mode
    if validate:
        from argocd_migrator.validator import (
            validate_tenant_directory,
            display_validation_results,
        )

        logger.info(f"Validating configurations in: {output_dir}")

        result = validate_tenant_directory(output_dir)
        display_validation_results(result, output_dir)

        raise typer.Exit(code=0 if result.is_valid() else 1)

    # Migration mode (with optional validation)
    try:
        logger.info(f"Starting migration from: {input_dir}")
        logger.info(f"Output directory: {output_dir}")

        if cluster_name:
            logger.info(f"Target cluster: {cluster_name}")

        if validate_on_migrate:
            logger.info("Validation enabled during migration")

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be written[/yellow]")

        result = migrate_applicationsets(
            input_dir=input_dir,
            output_dir=output_dir,
            dry_run=dry_run,
            cluster_name=cluster_name,
            validate_on_migrate=validate_on_migrate,
        )

        console.print("\n[bold green]Migration completed successfully![/bold green]")
        console.print(f"  Total ApplicationSets processed: {result['total_processed']}")
        console.print(f"  Main branch ApplicationSets: {result['main_count']}")
        console.print(f"  Preview branch ApplicationSets (skipped): {result['preview_count']}")
        console.print(f"  Tenants processed: {result['tenant_count']}")

        if validate_on_migrate:
            if result.get("validation_errors", 0) > 0:
                console.print(
                    f"  [red]Validation errors: {result['validation_errors']} tenant(s)[/red]"
                )
            else:
                console.print("  [green]All validations passed[/green]")

        if not dry_run:
            console.print(f"\n  Output files written to: {output_dir}")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=verbose)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
