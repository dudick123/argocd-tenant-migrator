"""Directory scanner for ApplicationSet YAML files."""

import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def scan_directory(base_dir: Path) -> Dict[str, List[Path]]:
    """
    Scan directory for ApplicationSet YAML files organized by tenant.

    Directory structure expected:
    - base_dir/
      - tenant-a/
        - app1-main.yaml
        - app2-preview.yaml
      - tenant-b/
        - app3-main.yaml

    Args:
        base_dir: Base directory to scan

    Returns:
        Dictionary mapping tenant names to lists of YAML file paths
    """
    tenant_files: Dict[str, List[Path]] = {}

    if not base_dir.exists():
        raise ValueError(f"Input directory does not exist: {base_dir}")

    logger.debug(f"Scanning directory: {base_dir}")

    # Find all YAML files
    yaml_patterns = ["*.yaml", "*.yml"]
    yaml_files = []

    for pattern in yaml_patterns:
        yaml_files.extend(base_dir.rglob(pattern))

    logger.debug(f"Found {len(yaml_files)} YAML files")

    # Group files by tenant (parent directory)
    for yaml_file in yaml_files:
        # Skip hidden directories and files
        if any(part.startswith(".") for part in yaml_file.parts):
            logger.debug(f"Skipping hidden file: {yaml_file}")
            continue

        # Get tenant name from parent directory relative to base_dir
        try:
            relative_path = yaml_file.relative_to(base_dir)
            if len(relative_path.parts) > 1:
                tenant_name = relative_path.parts[0]
            else:
                # Files directly in base_dir
                tenant_name = "default"

            if tenant_name not in tenant_files:
                tenant_files[tenant_name] = []

            tenant_files[tenant_name].append(yaml_file)
            logger.debug(f"Added {yaml_file.name} to tenant '{tenant_name}'")

        except ValueError:
            logger.warning(f"Could not determine tenant for file: {yaml_file}")
            continue

    logger.info(f"Found {len(tenant_files)} tenants with YAML files")

    return tenant_files
