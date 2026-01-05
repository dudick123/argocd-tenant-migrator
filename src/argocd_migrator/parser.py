"""YAML parser for ApplicationSet manifests."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ApplicationSetInfo:
    """Container for extracted ApplicationSet information."""

    def __init__(
        self,
        name: str,
        namespace: str,
        source: str,
        revision: str,
        manifest_path: str,
        project: str,
        cluster: str,
        is_preview: bool = False,
    ):
        self.name = name
        self.namespace = namespace
        self.source = source
        self.revision = revision
        self.manifest_path = manifest_path
        self.project = project
        self.cluster = cluster
        self.is_preview = is_preview

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "source": self.source,
            "revision": self.revision,
            "manifestPath": self.manifest_path,
            "project": self.project,
            "namespace": self.namespace,
            "cluster": self.cluster,
        }

    def __repr__(self) -> str:
        return f"ApplicationSetInfo(name={self.name}, is_preview={self.is_preview})"


def is_preview_branch(file_path: Path, manifest: Dict[str, Any]) -> bool:
    """
    Determine if an ApplicationSet is for a preview branch.

    Checks both the filename and the manifest content for preview branch indicators.

    Args:
        file_path: Path to the YAML file
        manifest: Parsed YAML manifest

    Returns:
        True if this is a preview branch ApplicationSet
    """
    # Check filename for "preview" keyword
    if "preview" in file_path.name.lower():
        logger.debug(f"Detected preview branch from filename: {file_path.name}")
        return True

    # Check for regex patterns in SCM generator that indicate preview branches
    # Common patterns: refs/heads/preview/*, ^preview/.*, etc.
    try:
        spec = manifest.get("spec", {})
        generators = spec.get("generators", [])

        for generator in generators:
            if "scmProvider" in generator:
                scm = generator["scmProvider"]
                # Check for branch filters
                filters = scm.get("filters", [])
                for f in filters:
                    if "branchMatch" in f:
                        branch_match = f["branchMatch"]
                        if "preview" in branch_match.lower():
                            logger.debug(
                                f"Detected preview branch from branchMatch: {branch_match}"
                            )
                            return True

            # Also check for pullRequest generators (typically preview branches)
            if "pullRequest" in generator:
                logger.debug("Detected pull request generator (preview)")
                return True

    except Exception as e:
        logger.warning(f"Error checking for preview branch in {file_path}: {e}")

    return False


def extract_applicationset_info(
    file_path: Path, manifest: Dict[str, Any]
) -> Optional[ApplicationSetInfo]:
    """
    Extract relevant information from an ApplicationSet manifest.

    Args:
        file_path: Path to the YAML file
        manifest: Parsed YAML manifest

    Returns:
        ApplicationSetInfo object or None if extraction fails
    """
    try:
        # Check if it's a preview branch
        is_preview = is_preview_branch(file_path, manifest)

        # Extract metadata
        metadata = manifest.get("metadata", {})
        name = metadata.get("name", "")
        namespace = metadata.get("namespace", "argocd")

        # Extract spec information
        spec = manifest.get("spec", {})
        template = spec.get("template", {})
        template_spec = template.get("spec", {})

        # Extract source information
        source = template_spec.get("source", {})
        repo_url = source.get("repoURL", "")
        target_revision = source.get("targetRevision", "main")
        path = source.get("path", "")

        # Extract destination information
        destination = template_spec.get("destination", {})
        dest_namespace = destination.get("namespace", namespace)
        cluster = destination.get("name", destination.get("server", ""))

        # Extract project
        project = template_spec.get("project", "default")

        if not name or not repo_url:
            logger.warning(f"Missing required fields in {file_path}")
            return None

        return ApplicationSetInfo(
            name=name,
            namespace=dest_namespace,
            source=repo_url,
            revision=target_revision,
            manifest_path=path,
            project=project,
            cluster=cluster,
            is_preview=is_preview,
        )

    except Exception as e:
        logger.error(f"Failed to extract information from {file_path}: {e}")
        return None


def parse_applicationset(file_path: Path) -> Optional[ApplicationSetInfo]:
    """
    Parse an ApplicationSet YAML file and extract information.

    Args:
        file_path: Path to the YAML file

    Returns:
        ApplicationSetInfo object or None if parsing fails
    """
    try:
        logger.debug(f"Parsing {file_path}")

        with open(file_path, "r") as f:
            manifest = yaml.safe_load(f)

        if not manifest:
            logger.warning(f"Empty manifest in {file_path}")
            return None

        # Verify it's an ApplicationSet
        kind = manifest.get("kind", "")
        if kind != "ApplicationSet":
            logger.debug(f"Skipping non-ApplicationSet file: {file_path} (kind={kind})")
            return None

        return extract_applicationset_info(file_path, manifest)

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return None
