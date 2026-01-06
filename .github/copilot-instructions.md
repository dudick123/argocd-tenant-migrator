# ArgoCD Tenant Migrator - Copilot Instructions

## Project Overview
CLI tool that migrates ArgoCD ApplicationSets from SCM Generators (GitHub organization scanning) to Git Generators (static JSON configs). Scans tenant-organized YAML files, extracts metadata, and generates per-tenant JSON config files.

## Architecture & Data Flow
1. **Scanner** ([scanner.py](../src/argocd_migrator/scanner.py)): Recursively finds `*.yaml`/`*.yml` files, groups by tenant (parent directory name)
2. **Parser** ([parser.py](../src/argocd_migrator/parser.py)): Extracts ApplicationSet fields from YAML, detects preview branches (filename contains "preview" or manifest has preview branchMatch/pullRequest generators)
3. **Migrator** ([migrator.py](../src/argocd_migrator/migrator.py)): Generates JSON configs per tenant, filters out preview branches, optionally overrides cluster names
4. **Validator** ([validator.py](../src/argocd_migrator/validator.py)): Validates against JSON Schema ([schema.py](../src/argocd_migrator/schema.py)) using jsonschema with Draft7Validator

## Critical Patterns

### Preview Detection Logic
Preview ApplicationSets are **automatically excluded** from migration. Detection happens via:
- Filename check: `"preview" in file_path.name.lower()`
- Manifest patterns: `branchMatch` containing "preview" or `pullRequest` generators
- See `is_preview_branch()` in [parser.py](../src/argocd_migrator/parser.py#L50-L95)

### Field Mapping (YAML → JSON)
```python
# From spec.template.spec in YAML → flat JSON
{
  "name": metadata.name,
  "source": spec.source.repoURL,
  "revision": spec.source.targetRevision,
  "manifestPath": spec.source.path,  # MUST NOT start with /
  "project": spec.project,
  "namespace": spec.destination.namespace,
  "cluster": spec.destination.server,  # Can be overridden via --cluster-name
}
```

### Directory Structure Convention
```
input-dir/
  team-a/              # Tenant name from parent directory
    app1-main.yaml
    app2-preview.yaml  # Skipped automatically
output-dir/
  team-a/
    config.json        # Array of ApplicationSet configs
```

## Development Workflows

### Running the CLI
```bash
# Install with UV (preferred)
uv sync && uv pip install -e .

# Run migration
argocd-migrator -i test-input -o test-output --verbose

# Dry run to preview
argocd-migrator -i test-input --dry-run -v

# Override cluster for all configs
argocd-migrator -i test-input -o test-output -c production-aks-cluster
```

### Testing
The project uses **directory-based integration tests** (no pytest fixtures yet):
- Input: `test-input/team-{a,b}/*.yaml`
- Expected outputs: `test-output-validated/`, `test-output-with-cluster/`
- Run with: `argocd-migrator -i test-input -o actual-output && diff -r actual-output test-output-validated`

### Validation Modes
1. **Standalone**: `argocd-migrator --validate` - validates existing JSON files in output-dir
2. **Pre-write**: `--validate-on-migrate` - validates before writing during migration
3. Schema enforces Kubernetes naming rules (lowercase alphanumeric + hyphens, see `K8S_NAME_PATTERN` in [schema.py](../src/argocd_migrator/schema.py#L4-L6))

## Project-Specific Rules

### Logging Strategy
- Uses `rich.logging.RichHandler` for pretty console output
- `--verbose` flag enables DEBUG level (shows skipped previews, cluster overrides)
- Always log skipped preview branches at DEBUG level (users expect them to be filtered silently)

### Error Handling Patterns
- File not found → raise `ValueError` with clear message (see [scanner.py](../src/argocd_migrator/scanner.py#L32-L33))
- Validation errors → collect ALL errors per item, report by index with field paths
- Missing YAML fields → log warning and skip file (graceful degradation)

### Dependencies
- **typer**: CLI framework (no completion, see [cli.py](../src/argocd_migrator/cli.py#L15))
- **rich**: Console output and tracebacks
- **jsonschema**: Validation with `Draft7Validator` and `FormatChecker`
- Package managed via **pyproject.toml** with UV for dev dependencies (black, ruff, pytest)

## Common Gotchas
- The `manifestPath` field MUST be relative (pattern: `^[^/].*` in schema)
- Tenant name defaults to "default" for files in root of input-dir
- Cluster override applies to ALL ApplicationSets when `--cluster-name` is set
- Empty tenant configs (all preview branches) are warned but not errors
