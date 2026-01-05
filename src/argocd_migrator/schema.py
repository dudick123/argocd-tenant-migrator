"""JSON Schema for ArgoCD ApplicationSet configuration files."""

# Kubernetes naming pattern: lowercase alphanumeric, hyphens, max length
# Must start and end with alphanumeric, hyphens allowed in middle
K8S_NAME_PATTERN = "^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"

# ArgoCD ApplicationSet configuration schema
# This schema validates the JSON output format for Git Generator-based ApplicationSets
APPLICATIONSET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "minItems": 0,
    "items": {
        "type": "object",
        "required": [
            "name",
            "source",
            "revision",
            "manifestPath",
            "project",
            "namespace",
            "cluster",
        ],
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 253,
                "pattern": K8S_NAME_PATTERN,
                "description": "ApplicationSet name (must be valid Kubernetes name)",
            },
            "source": {
                "type": "string",
                "minLength": 1,
                "format": "uri",
                "description": "Git repository URL (https://, git@, etc.)",
            },
            "revision": {
                "type": "string",
                "minLength": 1,
                "description": "Git branch, tag, or commit SHA",
            },
            "manifestPath": {
                "type": "string",
                "minLength": 1,
                "pattern": "^[^/].*",  # Must not start with /
                "description": "Path to manifests within the repository (relative path)",
            },
            "project": {
                "type": "string",
                "minLength": 1,
                "maxLength": 253,
                "pattern": K8S_NAME_PATTERN,
                "description": "ArgoCD project name (must be valid Kubernetes name)",
            },
            "namespace": {
                "type": "string",
                "minLength": 1,
                "maxLength": 63,
                "pattern": K8S_NAME_PATTERN,
                "description": "Target Kubernetes namespace (must be valid K8s name)",
            },
            "cluster": {
                "type": "string",
                "minLength": 1,
                "description": "Target ArgoCD cluster name or server URL",
            },
        },
        "additionalProperties": False,
    },
}
