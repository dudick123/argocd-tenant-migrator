"""Main migration logic for ApplicationSets."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from argocd_migrator.parser import ApplicationSetInfo, parse_applicationset
from argocd_migrator.scanner import scan_directory
from argocd_migrator.validator import validate_config_list

logger = logging.getLogger(__name__)


def generate_config_for_tenant(
    tenant_name: str, app_sets: List[ApplicationSetInfo], cluster_name: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Generate JSON configuration for a tenant's ApplicationSets.

    Args:
        tenant_name: Name of the tenant
        app_sets: List of ApplicationSetInfo objects for the tenant
        cluster_name: Optional cluster name to override in all ApplicationSets

    Returns:
        List of dictionaries representing ApplicationSet configurations
    """
    config = []

    for app_set in app_sets:
        if app_set.is_preview:
            logger.debug(
                f"Skipping preview branch ApplicationSet: {app_set.name} (tenant: {tenant_name})"
            )
            continue

        # Override cluster if specified
        if cluster_name:
            app_set.cluster = cluster_name
            logger.debug(f"Overriding cluster to '{cluster_name}' for {app_set.name}")

        config.append(app_set.to_dict())
        logger.debug(f"Added {app_set.name} to config for tenant {tenant_name}")

    return config


def write_tenant_config(
    tenant_name: str,
    config: List[Dict[str, str]],
    output_dir: Path,
    dry_run: bool,
    validate: bool = False,
) -> bool:
    """
    Write tenant configuration to a JSON file.

    Args:
        tenant_name: Name of the tenant
        config: Configuration data to write
        output_dir: Base output directory
        dry_run: If True, don't actually write the file
        validate: If True, validate config before writing

    Returns:
        True if successful (or would be successful in dry-run), False if validation failed
    """
    if not config:
        logger.info(f"No main branch ApplicationSets found for tenant '{tenant_name}', skipping")
        return True

    tenant_output_dir = output_dir / tenant_name
    config_file = tenant_output_dir / "config.json"

    # Validate if requested
    if validate:
        logger.debug(f"Validating config for tenant '{tenant_name}'")
        is_valid, errors_by_index = validate_config_list(config)

        if not is_valid:
            logger.error(f"Validation failed for tenant '{tenant_name}':")
            for index, errors in errors_by_index.items():
                name = config[index].get("name", f"unnamed-{index}")
                for error in errors:
                    logger.error(f"  Item {index} ({name}): {error}")
            return False

        logger.debug(f"Validation passed for tenant '{tenant_name}'")

    if dry_run:
        logger.info(
            f"[DRY RUN] Would write {len(config)} ApplicationSets to {config_file}"
        )
        logger.debug(f"[DRY RUN] Config content:\n{json.dumps(config, indent=2)}")
        return True

    # Create output directory if it doesn't exist
    tenant_output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON configuration
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Wrote {len(config)} ApplicationSets to {config_file}")
    return True


def migrate_applicationsets(
    input_dir: Path,
    output_dir: Path,
    dry_run: bool = False,
    cluster_name: Optional[str] = None,
    validate_on_migrate: bool = False,
) -> Dict[str, int]:
    """
    Migrate ApplicationSets from SCM Generators to Git Generators.

    Args:
        input_dir: Directory containing ApplicationSet YAML files
        output_dir: Directory to write JSON configuration files
        dry_run: If True, simulate without writing files
        cluster_name: Optional cluster name to override in all ApplicationSets
        validate_on_migrate: If True, validate configs before writing

    Returns:
        Dictionary with migration statistics
    """
    stats = {
        "total_processed": 0,
        "main_count": 0,
        "preview_count": 0,
        "tenant_count": 0,
        "error_count": 0,
        "validation_errors": 0,
    }

    # Scan directory for YAML files organized by tenant
    tenant_files = scan_directory(input_dir)

    if not tenant_files:
        logger.warning("No YAML files found in input directory")
        return stats

    stats["tenant_count"] = len(tenant_files)

    # Process each tenant
    for tenant_name, yaml_files in tenant_files.items():
        logger.info(f"Processing tenant: {tenant_name} ({len(yaml_files)} files)")

        tenant_app_sets: List[ApplicationSetInfo] = []

        # Parse each YAML file
        for yaml_file in yaml_files:
            app_set_info = parse_applicationset(yaml_file)

            if app_set_info:
                tenant_app_sets.append(app_set_info)
                stats["total_processed"] += 1

                if app_set_info.is_preview:
                    stats["preview_count"] += 1
                else:
                    stats["main_count"] += 1
            else:
                stats["error_count"] += 1

        # Generate and write configuration for this tenant
        config = generate_config_for_tenant(tenant_name, tenant_app_sets, cluster_name)
        success = write_tenant_config(
            tenant_name, config, output_dir, dry_run, validate=validate_on_migrate
        )

        if not success:
            stats["validation_errors"] += 1

    logger.info(
        f"Migration complete: {stats['main_count']} main, "
        f"{stats['preview_count']} preview, {stats['error_count']} errors"
    )

    if validate_on_migrate and stats["validation_errors"] > 0:
        logger.warning(f"Validation errors: {stats['validation_errors']} tenant(s)")

    return stats
