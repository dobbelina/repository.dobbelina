# Development Setup

Use these helper scripts to install prerequisites for running tests and the logo-processing utilities.

## Linux (Ubuntu/Debian or Fedora 43)

From the repository root:

```bash
./setup.sh
```

The script detects the distribution, installs system packages (Python 3, git, ImageMagick, pngquant), creates `.venv`, and installs Python test dependencies from `requirements-test.txt`. Activate the environment afterward with:

```bash
source .venv/bin/activate
```

On Ubuntu, `setup.sh` also installs `python-is-python3`, so both `python` and `python3` resolve correctly for commands like `python run_tests.py`.

## Windows 10/11

Open an **Administrator** PowerShell session in the repository root and run:

```powershell
powershell -ExecutionPolicy Bypass -File ./setup_windows.ps1
```

The script installs Git, Python 3, ImageMagick, and attempts to install pngquant (skipped with a warning if unavailable). It creates `.venv` when that environment is usable on Windows, or `.venv-win` when the repository already contains a non-Windows `.venv`. Reactivate later with:

```powershell
. .\.venv\Scripts\Activate.ps1
```

If the setup script created `.venv-win`, reactivate with:

```powershell
. .\.venv-win\Scripts\Activate.ps1
```

## Running Tests

After activation on any platform, run:

```bash
pytest
```

ImageMagick and pngquant are required by the logo-processing scripts (e.g., `process_logos.py`).
