#!/usr/bin/env python3
"""
Cross-platform test runner for Cumination addon.

This script detects the platform (Windows/Linux/Mac) and runs the pytest
testing suite with the appropriate virtual environment activation.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --coverage         # Run tests with coverage report
    python run_tests.py --site pornhub     # Run specific site test
    python run_tests.py --verbose          # Run with verbose output
"""

import sys
import platform
import subprocess
import argparse
from pathlib import Path


def get_platform_info():
    """Detect the operating system."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system in ["Linux", "Darwin"]:  # Darwin is macOS
        return "unix"
    else:
        return "unknown"


def safe_print(text):
    """Print text safely, handling Unicode encoding issues on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: remove emojis and special characters
        print(text.encode("ascii", "replace").decode("ascii"))


def is_runnable_python(python_path):
    """Return True when the candidate interpreter can actually start."""
    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


def find_python_executable():
    """Find the appropriate Python executable in the virtual environment."""
    platform_type = get_platform_info()
    repo_root = Path(__file__).parent

    if platform_type == "windows":
        # Windows: Check both .venv and .venv-win directories
        python_paths = [
            repo_root / ".venv" / "Scripts" / "python.exe",
            repo_root / ".venv" / "Scripts" / "python3.exe",
            repo_root / ".venv-win" / "Scripts" / "python.exe",
            repo_root / ".venv-win" / "Scripts" / "python3.exe",
        ]
    else:
        # Unix-like: .venv/bin/python3 or .venv/bin/python
        python_paths = [
            repo_root / ".venv" / "bin" / "python3",
            repo_root / ".venv" / "bin" / "python",
        ]

    # Check which Python executable exists
    for python_path in python_paths:
        if python_path.exists() and is_runnable_python(python_path):
            return str(python_path)

        if python_path.exists():
            safe_print(
                f"WARNING: Ignoring unusable virtual environment Python: {python_path}"
            )

    # Fallback to system Python
    safe_print("WARNING: No usable virtual environment found, using system Python")
    return sys.executable


def build_pytest_command(args):
    """Build the pytest command based on provided arguments."""
    python_exe = find_python_executable()

    # Base command
    cmd = [python_exe, "-m", "pytest"]

    # Add coverage if requested
    if args.coverage:
        cmd.extend(
            [
                "--cov=plugin.video.cumination/resources/lib",
                "--cov-report=term-missing",
                "--cov-report=html",
            ]
        )

    # Add specific site test if requested
    if args.site:
        test_file = f"tests/sites/test_{args.site}.py"
        if not Path(test_file).exists():
            safe_print(f"ERROR: Test file not found: {test_file}")
            sys.exit(1)
        cmd.append(test_file)

    # Add verbose output if requested
    if args.verbose:
        cmd.append("-v")

    # Add any additional pytest arguments
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    return cmd


def check_venv_exists():
    """Check if a usable virtual environment exists and print setup instructions."""
    platform_type = get_platform_info()
    repo_root = Path(__file__).parent

    if platform_type == "windows":
        # Check both .venv and .venv-win on Windows
        venv_paths = [
            repo_root / ".venv" / "Scripts" / "python.exe",
            repo_root / ".venv-win" / "Scripts" / "python.exe",
        ]
        existing_paths = [path for path in venv_paths if path.exists()]
    else:
        venv_path = repo_root / ".venv" / "bin" / "python3"
        existing_paths = [venv_path] if venv_path.exists() else []

    usable_paths = [path for path in existing_paths if is_runnable_python(path)]

    if not usable_paths:
        if existing_paths:
            safe_print("WARNING: Virtual environment exists but is not usable here!")
        else:
            safe_print("WARNING: Virtual environment not detected!")
        safe_print("\nSetup instructions:")
        safe_print("=" * 60)

        if platform_type == "windows":
            safe_print("Windows:")
            safe_print("  python -m venv .venv")
            safe_print("  .venv\\Scripts\\activate")
            safe_print("  pip install -r requirements-test.txt")
        else:
            safe_print("Linux/Mac:")
            safe_print("  python3 -m venv .venv")
            safe_print("  source .venv/bin/activate")
            safe_print("  pip install -r requirements-test.txt")

        safe_print("=" * 60)
        safe_print("\nWARNING: Continuing with system Python...\n")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run Cumination addon tests with pytest",
        epilog="Examples:\n"
        "  python run_tests.py\n"
        "  python run_tests.py --coverage\n"
        "  python run_tests.py --site pornhub --verbose\n"
        "  python run_tests.py tests/test_utils.py::test_parse_html\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage report"
    )

    parser.add_argument(
        "--site", type=str, help="Run tests for a specific site (e.g., --site pornhub)"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Run tests with verbose output"
    )

    parser.add_argument(
        "pytest_args", nargs="*", help="Additional arguments to pass to pytest"
    )

    args = parser.parse_args()

    # Display platform information
    platform_type = get_platform_info()
    system_name = platform.system()
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    safe_print("=" * 60)
    safe_print("Cumination Test Runner")
    safe_print("=" * 60)
    safe_print(f"Platform: {system_name} ({platform_type})")
    safe_print(f"Python Version: {python_version}")
    safe_print(f"Working Directory: {Path.cwd()}")
    safe_print("=" * 60)
    safe_print("")

    # Check for virtual environment
    check_venv_exists()

    # Build and execute pytest command
    cmd = build_pytest_command(args)

    safe_print(f"Running command: {' '.join(cmd)}")
    safe_print("=" * 60)
    safe_print("")

    try:
        result = subprocess.run(cmd, cwd=str(Path(__file__).parent))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        safe_print("\n\nWARNING: Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        safe_print(f"\nERROR: Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
