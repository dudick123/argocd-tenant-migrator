# ArgoCD Tenant Migrator

A command line utility to migrate ArgoCD ApplicationSets from SCM Generators to Git Generators.

## Overview

This tool scans a directory for ArgoCD ApplicationSet YAML manifests that use SCM Generators, extracts relevant information, and generates JSON configuration files for new ApplicationSets using Git Generators. It automatically detects and skips preview branch ApplicationSets, focusing only on main branch configurations.

## Features

- Scans directories containing ApplicationSet YAML files organized by tenant
- Automatically detects and differentiates between main and preview branch ApplicationSets
- Extracts essential information: name, source, revision, manifest path, project, namespace, and cluster
- Generates JSON configuration files organized by tenant
- Supports dry-run mode to preview changes before executing
- Verbose logging for debugging
- Detailed migration statistics

## Installation

### Using UV (Recommended)

```bash
# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uv sync
uv pip install -e .
```

### Using pip

```bash
# Install dependencies
pip install -e .
```

## Usage

### Basic Usage

```bash
argocd-migrator --input-dir /path/to/applicationsets --output-dir /path/to/output
```

### Command Options

- `--input-dir, -i`: Directory to scan for ApplicationSet manifests (default: current directory)
- `--output-dir, -o`: Directory for generated JSON configuration files (default: `output`)
- `--cluster-name, -c`: Target cluster name to override in all ApplicationSets (optional)
- `--dry-run, -n`: Simulate migration without writing output files
- `--verbose, -v`: Enable detailed logging output
- `--help`: Show help message and exit

### Examples

#### Dry Run to Preview Changes

```bash
argocd-migrator --input-dir manifests/dev --dry-run --verbose
```

#### Migrate with Custom Output Directory

```bash
argocd-migrator --input-dir manifests/dev --output-dir configs/dev
```

#### Migrate with Cluster Name Override

```bash
argocd-migrator --input-dir manifests/dev --cluster-name production-cluster
```

This will set the `cluster` property to `production-cluster` for all ApplicationSets in the generated JSON files, regardless of what cluster is specified in the source YAML manifests.

#### Migrate Current Directory

```bash
argocd-migrator
```

## Input Structure

The tool expects ApplicationSet YAML files organized by tenant:

```text
manifests/dev/
├── team-a/
│   ├── team-a-api-main.yaml
│   └── team-a-gateway-main.yaml
└── team-b/
    ├── team-b-service-main.yaml
    └── team-b-service-preview.yaml  # This will be skipped
```

## Output Structure

Generated JSON configuration files are organized by tenant:

```text
output/
├── team-a/
│   └── config.json
└── team-b/
    └── config.json
```

### Output Format

Each `config.json` file contains an array of ApplicationSet configurations:

```json
[
  {
    "name": "team-a-api-main",
    "source": "https://github.com/myorg/team-a-api",
    "revision": "main",
    "manifestPath": "manifests/prod",
    "project": "team-a-project",
    "namespace": "team-a-prod",
    "cluster": "prod-cluster"
  }
]
```

## Preview Branch Detection

The tool automatically detects preview branches using:

- Filename containing "preview"
- SCM Generator branch match patterns containing "preview"
- Pull request generators

Preview branch ApplicationSets are skipped and not included in the output.

## Tech Stack

- Python 3.10+
- UV for package management
- Typer for CLI interface
- PyYAML for YAML parsing
- Rich for enhanced terminal output and logging

## Development

### Running Tests

```bash
# Create test data
mkdir -p test-input/team-a test-input/team-b

# Run the tool on test data
argocd-migrator --input-dir test-input --output-dir test-output --dry-run --verbose
```

## License

MIT
