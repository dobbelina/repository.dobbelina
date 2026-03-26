# Test Runner Documentation

## Overview

The `run_tests.py` script is a cross-platform test runner that automatically detects your operating system (Windows/Linux/Mac) and runs the pytest testing suite with the appropriate configuration.

## Features

- **Platform Detection**: Automatically detects Windows, Linux, or macOS
- **Virtual Environment Support**: Uses a runnable `.venv` or `.venv-win` on Windows, and falls back to system Python only when no usable venv is available
- **Multiple Test Options**: Run all tests, specific sites, or custom test files
- **Coverage Reports**: Generate HTML and terminal coverage reports
- **Verbose Output**: Optional detailed test output

## Installation

Before using the test runner, set up your development environment:

### Windows
```bash
# Create virtual environment (use .venv or .venv-win)
python -m venv .venv
# OR
python -m venv .venv-win

# Activate virtual environment
.venv\Scripts\activate
# OR
.venv-win\Scripts\activate

# Install dependencies
pip install -r requirements-test.txt
```

> **Note**: The test runner automatically detects both `.venv` and `.venv-win` directories on Windows, and skips broken interpreters such as a Linux-created `.venv`.

### Linux/Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
```

## Usage

### Basic Commands

```bash
# Run all tests
python run_tests.py

# Run tests with coverage report
python run_tests.py --coverage

# Run tests for a specific site
python run_tests.py --site pornhub

# Run tests with verbose output
python run_tests.py --site xvideos --verbose

# Run a specific test file
python run_tests.py tests/test_utils.py

# Run a specific test function
python run_tests.py tests/test_utils.py::test_parse_html -v
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--coverage` | Generate coverage report (HTML and terminal) |
| `--site SITENAME` | Run tests for a specific site (e.g., `--site pornhub`) |
| `-v, --verbose` | Run tests with verbose output |
| `--help` | Show help message |

### Examples

**Run all tests with coverage:**
```bash
python run_tests.py --coverage
```

**Test a specific site with verbose output:**
```bash
python run_tests.py --site spankbang -v
```

**Run specific test file:**
```bash
python run_tests.py tests/sites/test_pornhub.py
```

**Run specific test with additional pytest options:**
```bash
python run_tests.py tests/test_utils.py -k "test_parse" -v
```

## Output

The script displays:
1. **Platform Information**: Operating system and Python version
2. **Virtual Environment Status**: Whether using venv or system Python
3. **Test Results**: pytest output with test results
4. **Coverage Report**: (if `--coverage` is used) HTML report saved to `htmlcov/`

### Example Output

```
============================================================
Cumination Test Runner
============================================================
Platform: Windows (windows)
Python Version: 3.13.11
Working Directory: C:\Users\...\repository.dobbelina
============================================================

Running command: C:\...\python.exe -m pytest -v tests/sites/test_85po.py
============================================================

============================= test session starts =============================
...
============================== 6 passed in 0.10s ==============================
```

## Troubleshooting

### Virtual Environment Not Found

If you see either warning:
```
WARNING: Virtual environment not detected!
WARNING: Virtual environment exists but is not usable here!
```

Follow the setup instructions displayed by the script to create and activate a usable virtual environment for your platform.

### Test File Not Found

If you use `--site sitename` and get an error:
```
ERROR: Test file not found: tests/sites/test_sitename.py
```

Make sure:
1. The site name is spelled correctly
2. The test file exists in `tests/sites/`
3. You're running the command from the repository root

### Platform-Specific Issues

**Windows**: If you see Unicode encoding errors, the script automatically falls back to ASCII-safe output.

**Linux/Mac**: Make sure the script has execute permissions:
```bash
chmod +x run_tests.py
```

## Integration with CI/CD

The script can be used in GitHub Actions or other CI systems:

```yaml
- name: Run tests
  run: python run_tests.py --coverage
```

## Advanced Usage

### Custom pytest Arguments

You can pass additional pytest arguments directly:

```bash
# Run tests matching a pattern
python run_tests.py -k "test_list"

# Stop on first failure
python run_tests.py -x

# Show local variables on failure
python run_tests.py -l

# Run tests in parallel (requires pytest-xdist)
python run_tests.py -n auto
```

### Coverage Reports

When using `--coverage`, reports are generated in:
- **Terminal**: Displayed after test completion
- **HTML**: Saved to `htmlcov/index.html`

Open the HTML report in a browser:
```bash
# Windows
start htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Mac
open htmlcov/index.html
```

## See Also

- [CLAUDE.md](../CLAUDE.md) - Development guide
- [MODERNIZATION.md](../MODERNIZATION.md) - Project roadmap
- [pytest Documentation](https://docs.pytest.org/) - Official pytest docs
