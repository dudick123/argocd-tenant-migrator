# ArgoCD Scanner - Python Learning Walkthrough

A guided tour through this CLI application for junior Python developers. Learn modern Python patterns, best practices, and software architecture through a real-world project.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Key Python Concepts Used](#key-python-concepts-used)
4. [Module-by-Module Breakdown](#module-by-module-breakdown)
5. [Design Patterns](#design-patterns)
6. [Best Practices Demonstrated](#best-practices-demonstrated)
7. [Testing Strategy](#testing-strategy)
8. [Common Python Idioms](#common-python-idioms)

---

## Project Overview

### What Does This Project Do?

This is a CLI (Command-Line Interface) tool that:
1. Scans directories for YAML files
2. Validates their syntax
3. Detects preview branch files
4. Displays beautiful formatted output

### Why Is This a Good Learning Project?

- ✅ Real-world application with actual use case
- ✅ Modern Python 3.12+ features
- ✅ Clean architecture with separation of concerns
- ✅ Comprehensive test coverage (81%)
- ✅ Type hints throughout
- ✅ Professional CLI with rich output

---

## Project Structure

```
argocd-tenant-migrator/
├── src/argocd_scanner/          # Main application code
│   ├── __init__.py              # Package marker + version
│   ├── models.py                # Data structures
│   ├── scanner.py               # Core business logic
│   ├── output.py                # Display/presentation
│   └── cli.py                   # User interface
├── tests/                       # Test suite
│   ├── test_scanner.py          # Scanner logic tests
│   ├── test_output.py           # Output formatting tests
│   └── test_cli.py              # CLI integration tests
├── pyproject.toml               # Project configuration
└── README.md                    # User documentation
```

### Why This Structure?

**Separation of Concerns**: Each module has a single, clear responsibility:
- **models.py**: Data definitions
- **scanner.py**: Business logic
- **output.py**: Presentation
- **cli.py**: User interaction

This makes the code:
- Easier to understand
- Easier to test
- Easier to modify
- Easier to reuse

---

## Key Python Concepts Used

### 1. Type Hints (Type Annotations)

**What are they?**
Type hints tell Python (and developers) what type of data a variable should hold.

**Example from our code:**

```python
def is_valid_yaml(file_path: Path) -> tuple[bool, str | None]:
    """
    file_path: Path    <- This parameter expects a Path object
    -> tuple[...]      <- This function returns a tuple
    str | None         <- The string can be None (Python 3.10+ syntax)
    """
```

**Why use them?**
- Catch errors before running code
- Better IDE autocomplete
- Self-documenting code
- Easier to maintain

### 2. Dataclasses

**What are they?**
A decorator that automatically generates common methods for classes that store data.

**Example from `models.py`:**

```python
from dataclasses import dataclass

@dataclass
class FileInfo:
    path: Path
    is_valid: bool
    is_preview: bool
    error_message: str | None = None  # Optional with default
    size_bytes: int = 0               # Optional with default
```

**What @dataclass gives you automatically:**
- `__init__()` method
- `__repr__()` method (string representation)
- `__eq__()` method (equality comparison)

**Without @dataclass, you'd need to write:**

```python
class FileInfo:
    def __init__(self, path, is_valid, is_preview, error_message=None, size_bytes=0):
        self.path = path
        self.is_valid = is_valid
        self.is_preview = is_preview
        self.error_message = error_message
        self.size_bytes = size_bytes

    def __repr__(self):
        return f"FileInfo(path={self.path}, is_valid={self.is_valid}...)"

    def __eq__(self, other):
        # ... comparison logic
```

### 3. Path Objects (from pathlib)

**What are they?**
Object-oriented way to work with file paths (better than strings).

**Example:**

```python
from pathlib import Path

# Old way (strings):
import os
file_path = "/home/user/file.txt"
parent = os.path.dirname(file_path)
name = os.path.basename(file_path)

# New way (Path objects):
file_path = Path("/home/user/file.txt")
parent = file_path.parent          # Cleaner!
name = file_path.name              # More readable!
exists = file_path.exists()        # Easy to use!
```

**Benefits:**
- Cross-platform (works on Windows, Mac, Linux)
- More readable methods
- Less error-prone
- Built-in operations

### 4. List Comprehensions

**What are they?**
Concise way to create lists from other iterables.

**Example from `scanner.py`:**

```python
# Count valid files
valid_count = sum(1 for f in files if f.is_valid)

# Traditional way:
valid_count = 0
for f in files:
    if f.is_valid:
        valid_count += 1
```

**More examples:**

```python
# Create list of squares
squares = [x**2 for x in range(10)]
# Result: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Filter and transform
even_squares = [x**2 for x in range(10) if x % 2 == 0]
# Result: [0, 4, 16, 36, 64]
```

### 5. Context Managers (with statement)

**What are they?**
Ensure resources are properly cleaned up (like closing files).

**Example from `scanner.py`:**

```python
with open(file_path, encoding="utf-8") as f:
    content = f.read()
# File is automatically closed here, even if an error occurs!
```

**Without context manager:**

```python
f = open(file_path, encoding="utf-8")
try:
    content = f.read()
finally:
    f.close()  # Must remember to close!
```

### 6. Exception Handling

**What is it?**
Gracefully handle errors instead of crashing.

**Example from `scanner.py`:**

```python
try:
    yaml.safe_load(content)
    return (True, None)
except yaml.YAMLError as e:
    error_msg = str(e).split("\n")[0]
    return (False, f"YAML syntax error: {error_msg}")
except UnicodeDecodeError:
    return (False, "Not a valid text file")
```

**Pattern:**
1. Try the operation
2. Catch specific exceptions
3. Handle each type appropriately
4. Never use bare `except:` (catch specific exceptions)

---

## Module-by-Module Breakdown

### 1. models.py - Data Structures

**Purpose**: Define the shape of our data.

#### FileInfo Dataclass

```python
@dataclass
class FileInfo:
    """Information about a single YAML file."""
    path: Path              # Where is the file?
    is_valid: bool          # Is the YAML valid?
    is_preview: bool        # Is it a preview branch?
    error_message: str | None = None  # Error if invalid
    size_bytes: int = 0     # How big is it?
```

**Key Concept**: **Value Objects**
- Represents data without behavior
- Immutable (doesn't change)
- Easy to pass around
- Easy to test

#### ScanResult Dataclass

```python
@dataclass
class ScanResult:
    """Results from scanning a directory."""
    input_path: Path
    recursive: bool
    directories_scanned: int
    total_yaml_files: int
    valid_yaml_files: int
    invalid_yaml_files: int
    main_branch_files: int
    preview_branch_files: int
    files: list[FileInfo]
    scan_duration_seconds: float
    errors: list[str]
```

**Key Concept**: **Aggregate Root**
- Combines multiple related pieces of data
- Provides complete picture of scan results
- Single object to pass around

**Learning Point**: When you have multiple related pieces of data, group them in a dataclass instead of passing many individual parameters.

---

### 2. scanner.py - Business Logic

**Purpose**: Core functionality - scan files and validate YAML.

#### Function: is_preview_file()

```python
def is_preview_file(file_path: Path) -> bool:
    """Detect if a file is a preview branch based on filename."""
    return "preview" in file_path.name.lower()
```

**What This Teaches:**

1. **Single Responsibility**: Does one thing well
2. **Pure Function**: Same input → same output (no side effects)
3. **String Methods**: `.lower()` for case-insensitive comparison
4. **`in` operator**: Check substring presence

**Why lowercase?**
- Makes comparison case-insensitive
- "PREVIEW", "preview", "Preview" all match

#### Function: is_valid_yaml()

```python
def is_valid_yaml(file_path: Path) -> tuple[bool, str | None]:
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if not content or not content.strip():
            return (True, None)  # Empty is valid

        yaml.safe_load(content)
        return (True, None)

    except yaml.YAMLError as e:
        return (False, f"YAML syntax error: {str(e)}")
    except UnicodeDecodeError:
        return (False, "Not a valid text file")
```

**What This Teaches:**

1. **Return Multiple Values**: Tuple unpacking
   ```python
   is_valid, error = is_valid_yaml(path)
   ```

2. **Error Handling**: Try/except for different error types

3. **Guard Clause**: Early return for special cases
   ```python
   if not content or not content.strip():
       return (True, None)  # Exit early
   ```

4. **String Methods**: `.strip()` removes whitespace

#### Function: scan_directory()

**The Pipeline Pattern:**

```python
def scan_directory(path: Path, recursive: bool, verbose: bool) -> ScanResult:
    # 1. Setup
    start_time = time.time()
    files = []
    errors = []

    # 2. Collection
    for file_path in path.rglob(pattern):  # or path.glob()
        if any(part.startswith(".") for part in file_path.parts):
            continue  # Skip hidden directories
        _process_file(file_path, files, errors, verbose)

    # 3. Analysis
    valid_count = sum(1 for f in files if f.is_valid)
    main_count = sum(1 for f in files if not f.is_preview)

    # 4. Return Results
    return ScanResult(...)
```

**What This Teaches:**

1. **Path.glob() vs Path.rglob()**:
   - `glob("*.yaml")`: Current directory only
   - `rglob("*.yaml")`: Recursive (all subdirectories)

2. **Generator Expression**: Memory efficient
   ```python
   sum(1 for f in files if f.is_valid)
   # Instead of creating a list first
   ```

3. **any() Function**: Check if any item matches
   ```python
   any(part.startswith(".") for part in file_path.parts)
   # True if ANY part starts with "."
   ```

4. **Time Tracking**:
   ```python
   start = time.time()
   # ... do work ...
   duration = time.time() - start
   ```

---

### 3. output.py - Presentation Layer

**Purpose**: Format data for display (separate from business logic).

#### Function: create_summary_table()

```python
def create_summary_table(result: ScanResult) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Directories Scanned", str(result.directories_scanned))
    table.add_row("Total YAML Files Found", str(result.total_yaml_files))
    # ...

    return table
```

**What This Teaches:**

1. **Builder Pattern**: Build object step by step
   ```python
   table = Table()       # Create
   table.add_column()    # Configure
   table.add_row()       # Populate
   return table          # Return
   ```

2. **Type Conversion**: `str()` to convert numbers to strings

3. **Rich Library**: Professional terminal output
   - Tables with borders
   - Colored text
   - Justified columns

#### Function: create_file_tree()

**Complex Data Transformation:**

```python
# 1. Group files by directory
files_by_dir: dict[Path, list] = {}
for file_info in result.files:
    rel_path = file_info.path.relative_to(result.input_path)
    parent = rel_path.parent

    if parent not in files_by_dir:
        files_by_dir[parent] = []
    files_by_dir[parent].append((rel_path.name, file_info))

# 2. Build tree structure
for dir_path in sorted(files_by_dir.keys()):
    for filename, file_info in sorted(files_by_dir[dir_path]):
        if file_info.is_preview:
            status = "[yellow]🔍 Preview[/yellow]"
        else:
            status = "[green]✓[/green]" if file_info.is_valid else "[red]✗[/red]"
        tree.add(f"{filename} {status}")
```

**What This Teaches:**

1. **Dictionary Pattern**: Group items by key
   ```python
   # Pattern for grouping:
   groups = {}
   for item in items:
       key = get_key(item)
       if key not in groups:
           groups[key] = []
       groups[key].append(item)
   ```

2. **Ternary Operator**: Inline if/else
   ```python
   status = "[green]✓[/green]" if file_info.is_valid else "[red]✗[/red]"
   # Same as:
   if file_info.is_valid:
       status = "[green]✓[/green]"
   else:
       status = "[red]✗[/red]"
   ```

3. **F-strings**: String formatting
   ```python
   f"{filename} {status}"  # Embed variables
   ```

4. **sorted()**: Sort collections
   ```python
   sorted(files_by_dir.keys())  # Returns sorted list
   ```

---

### 4. cli.py - User Interface

**Purpose**: Handle user interaction and orchestrate other modules.

```python
from typing import Annotated
import typer

app = typer.Typer()

@app.command()
def main(
    input_path: Annotated[Path, typer.Option(
        "--input-path",
        help="Directory path to scan for YAML files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    )],
    recursive: Annotated[bool, typer.Option(
        "--recursive",
        help="Recursively scan subdirectories"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose",
        help="Enable verbose output"
    )] = False,
) -> None:
    try:
        result = scan_directory(input_path, recursive, verbose)
        display_results(result, verbose)
        if result.errors:
            display_errors(result.errors)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)
```

**What This Teaches:**

1. **Typer Framework**: Modern CLI creation
   - Type hints → command-line arguments
   - Automatic `--help` generation
   - Validation built-in

2. **Annotated Type**: Metadata on parameters
   ```python
   Annotated[Path, typer.Option(...)]
   #         ^^^^  ^^^^^^^^^^^^^^^^
   #         type  metadata
   ```

3. **Default Arguments**:
   ```python
   recursive: bool = False  # Optional, defaults to False
   ```

4. **Orchestration**: Combines other modules
   ```python
   result = scan_directory()    # Business logic
   display_results(result)      # Presentation
   ```

5. **Error Boundaries**: Top-level exception handling
   - Catches any unexpected errors
   - Shows user-friendly message
   - Exits with error code

---

## Design Patterns

### 1. Pipeline Pattern

**What is it?**
Process data through a series of steps.

**Our Pipeline:**

```
Input → Scan → Validate → Categorize → Format → Output
  │       │        │          │           │        │
  │       │        │          │           │        └─ Rich display
  │       │        │          │           └─ Create tables/trees
  │       │        │          └─ Main vs Preview
  │       │        └─ YAML syntax check
  │       └─ Find YAML files
  └─ Directory path
```

**In Code:**

```python
# Step 1: Scan
files = []
for file_path in path.rglob("*.yaml"):
    # Step 2: Validate
    is_valid, error = is_valid_yaml(file_path)
    # Step 3: Categorize
    is_preview = is_preview_file(file_path)
    # Step 4: Collect
    files.append(FileInfo(...))

# Step 5: Format and Display
display_results(ScanResult(...))
```

### 2. Separation of Concerns

**What is it?**
Each module has a single, clear responsibility.

| Module | Responsibility | Knows About |
|--------|---------------|-------------|
| models.py | Data structure | Nothing else |
| scanner.py | Business logic | models only |
| output.py | Presentation | models only |
| cli.py | User interface | Everything (orchestrator) |

**Why?**
- Change one without affecting others
- Test each independently
- Reuse in different contexts

### 3. Dependency Injection

**What is it?**
Pass dependencies as parameters instead of creating them inside.

**Example:**

```python
# Bad: Hard-coded dependency
def process_file(file_path):
    validator = YAMLValidator()  # Created inside
    return validator.validate(file_path)

# Good: Injected dependency
def process_file(file_path, validator):  # Passed in
    return validator.validate(file_path)
```

**In our code:**

```python
def display_results(result: ScanResult, verbose: bool):
    # Receives data, doesn't create it
    table = create_summary_table(result)
    console.print(table)
```

---

## Best Practices Demonstrated

### 1. Type Hints Everywhere

```python
def scan_directory(
    path: Path,           # What type of input
    recursive: bool,
    verbose: bool
) -> ScanResult:         # What type of output
    """Docstring explaining what it does."""
```

**Benefits:**
- Catch errors early
- Better IDE support
- Self-documenting
- Refactoring safety

### 2. Docstrings

```python
def is_preview_file(file_path: Path) -> bool:
    """Detect if a file is a preview branch based on filename.

    Checks if 'preview' appears in the filename (case-insensitive).

    Args:
        file_path: Path to the file to check

    Returns:
        True if filename contains 'preview', False otherwise

    Examples:
        >>> is_preview_file(Path("app-preview.yaml"))
        True
        >>> is_preview_file(Path("app-main.yaml"))
        False
    """
```

**What to include:**
- What the function does
- What parameters mean
- What it returns
- Examples if helpful

### 3. Small, Focused Functions

```python
# Good: Single responsibility
def is_preview_file(file_path: Path) -> bool:
    return "preview" in file_path.name.lower()

# Bad: Multiple responsibilities
def process_file(file_path):
    # 50 lines of mixed logic
    # Validation, categorization, formatting...
```

**Rule of thumb:** If you can't describe it in one sentence, split it.

### 4. Immutable Data

```python
@dataclass
class FileInfo:
    path: Path
    is_valid: bool
    # No methods that modify these fields!
    # Create new objects instead of modifying
```

**Why?**
- Easier to reason about
- Safer in concurrent code
- Prevents bugs from unexpected changes

### 5. Error Handling

```python
# Specific exceptions
try:
    yaml.safe_load(content)
except yaml.YAMLError as e:      # Specific
    handle_yaml_error(e)
except UnicodeDecodeError:       # Specific
    handle_encoding_error()

# Never do this:
except:  # Too broad! Don't know what went wrong
    pass
```

### 6. Guard Clauses

```python
# Good: Early returns
def process(value):
    if not value:
        return None  # Exit early
    if value < 0:
        return None  # Exit early
    # Main logic here
    return result

# Bad: Nested ifs
def process(value):
    if value:
        if value >= 0:
            # Main logic deeply nested
            return result
        else:
            return None
    else:
        return None
```

---

## Testing Strategy

### 1. Unit Tests

Test individual functions in isolation.

**Example from `test_scanner.py`:**

```python
def test_preview_in_filename_lowercase():
    """Lowercase 'preview' should be detected."""
    path = Path("/test/app-preview.yaml")
    assert is_preview_file(path) is True
```

**What makes a good unit test:**
- ✅ Tests one thing
- ✅ Clear name describing what it tests
- ✅ Arrange → Act → Assert structure
- ✅ Fast (no file I/O, network, etc.)

### 2. Integration Tests

Test components working together.

**Example from `test_cli.py`:**

```python
def test_scan_with_preview_files(tmp_path):
    # Arrange: Create test files
    (tmp_path / "main.yaml").write_text("key: value\n")
    (tmp_path / "preview.yaml").write_text("key: value\n")

    # Act: Run the CLI
    result = runner.invoke(app, ["--input-path", str(tmp_path)])

    # Assert: Check output
    assert result.exit_code == 0
    assert "Main Branch Files" in result.stdout
    assert "Preview Branch Files" in result.stdout
```

### 3. Test Fixtures

Reusable test data.

```python
@pytest.fixture
def test_data_path():
    """Provide path to test data directory."""
    return Path(__file__).parent.parent / "io-artifact-examples" / "input"

def test_something(test_data_path):  # Fixture injected
    result = scan_directory(test_data_path, recursive=True)
    assert result.total_yaml_files > 0
```

### 4. Temporary Directories

```python
def test_scan_empty_directory(tmp_path):  # pytest provides tmp_path
    result = scan_directory(tmp_path, recursive=False)
    assert result.total_yaml_files == 0
    # tmp_path automatically cleaned up!
```

---

## Common Python Idioms

### 1. The "if not X" Pattern

```python
# Check if string is empty
if not content:
    return

# Check if list is empty
if not files:
    return

# Check if value is None
if value is None:  # Use 'is' for None
    return
```

### 2. List Comprehensions

```python
# Transform
numbers = [1, 2, 3, 4]
squares = [n**2 for n in numbers]  # [1, 4, 9, 16]

# Filter
evens = [n for n in numbers if n % 2 == 0]  # [2, 4]

# Filter + Transform
even_squares = [n**2 for n in numbers if n % 2 == 0]  # [4, 16]
```

### 3. Dictionary Get with Default

```python
# Instead of:
if key in dict:
    value = dict[key]
else:
    value = default

# Use:
value = dict.get(key, default)
```

### 4. String Formatting

```python
name = "Python"
version = 3.12

# F-strings (modern, preferred)
f"Using {name} version {version}"

# Old ways (don't use):
"Using {} version {}".format(name, version)
"Using %s version %s" % (name, version)
```

### 5. Path Joining

```python
# Good
base = Path("/home/user")
file = base / "documents" / "file.txt"  # Overloaded / operator

# Bad
file = base + "/documents/file.txt"  # String concatenation
```

### 6. Context Managers for Resources

```python
# Always use 'with' for files
with open(file_path) as f:
    content = f.read()
# File automatically closed

# Also works for:
with database.connect() as conn:
    conn.execute(query)
```

---

## Learning Exercises

### Beginner Exercises

1. **Add a new file extension**:
   - Modify `scanner.py` to also scan `.yml` files
   - Run tests to verify it works

2. **Add file count to output**:
   - Add a row to summary table showing file count by extension
   - `.yaml` vs `.yml`

3. **Add a color option**:
   - Add `--no-color` flag to CLI
   - Pass it through to output module
   - Disable Rich colors when set

### Intermediate Exercises

1. **Add size-based filtering**:
   - Add `--min-size` and `--max-size` options
   - Filter files by size
   - Update tests

2. **Add JSON output format**:
   - Add `--format` option (table or json)
   - Create `to_json()` method on ScanResult
   - Output JSON instead of tables when requested

3. **Add file modification time**:
   - Add `modified_time` to FileInfo
   - Display in verbose mode
   - Sort files by modification time

### Advanced Exercises

1. **Add parallel scanning**:
   - Use `concurrent.futures` to scan files in parallel
   - Measure performance improvement
   - Maintain thread safety

2. **Add caching**:
   - Cache validation results (file hash → is_valid)
   - Skip re-validating unchanged files
   - Use pickle or shelve for persistence

3. **Add plugin system**:
   - Create plugin interface for custom validators
   - Load plugins from a directory
   - Allow users to add custom validation rules

---

## Additional Resources

### Python Learning

- **Official Python Tutorial**: https://docs.python.org/3/tutorial/
- **Real Python**: https://realpython.com/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html

### Libraries Used

- **Typer Documentation**: https://typer.tiangolo.com/
- **Rich Documentation**: https://rich.readthedocs.io/
- **PyYAML Documentation**: https://pyyaml.org/wiki/PyYAMLDocumentation
- **Pytest Documentation**: https://docs.pytest.org/

### Design Patterns

- **Python Patterns**: https://python-patterns.guide/
- **Refactoring Guru**: https://refactoring.guru/design-patterns/python

### Best Practices

- **PEP 8 Style Guide**: https://pep8.org/
- **Google Python Style Guide**: https://google.github.io/styleguide/pyguide.html
- **The Hitchhiker's Guide to Python**: https://docs.python-guide.org/

---

## Questions to Test Your Understanding

1. Why do we use dataclasses instead of regular classes?
2. What's the difference between `Path.glob()` and `Path.rglob()`?
3. Why do we separate business logic (scanner) from presentation (output)?
4. What does the `with` statement do and why is it important?
5. Why use type hints if Python doesn't enforce them?
6. What's the benefit of small, single-purpose functions?
7. How does the pipeline pattern help organize code?
8. Why test both individual functions and integrated components?

---

## Next Steps

1. **Read through each module**: Start with `models.py`, then `scanner.py`
2. **Run the code**: Try the CLI with different options
3. **Run the tests**: See how testing works
4. **Make small changes**: Try the beginner exercises
5. **Read the imports**: Understand what each library does
6. **Study the patterns**: Identify where each pattern is used

Happy learning! 🐍📚
