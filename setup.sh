#!/usr/bin/env bash

# Unified environment setup for Cumination
# Installs system dependencies and Python test requirements for Ubuntu, Fedora 43, or Windows (via helper script).
# Usage: ./setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$REPO_ROOT/.venv}"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

require_sudo() {
    if [[ $(id -u) -ne 0 ]]; then
        if command_exists sudo; then
            SUDO="sudo"
        else
            echo "This script requires administrative privileges but sudo was not found." >&2
            exit 1
        fi
    else
        SUDO=""
    fi
}

install_ubuntu() {
    echo "Detected Ubuntu/Debian. Installing dependencies..."
    require_sudo
    $SUDO apt-get update
    # Provide both python3 and the `python` shim used in repo docs.
    $SUDO apt-get install -y python3 python3-venv python3-pip python-is-python3 imagemagick pngquant git
}

install_fedora() {
    echo "Detected Fedora. Installing dependencies..."
    require_sudo
    $SUDO dnf install -y python3 python3-pip ImageMagick pngquant git
}

create_venv_and_install() {
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "Creating Python virtual environment at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    python -m pip install --upgrade pip
    python -m pip install -r "$REPO_ROOT/requirements-test.txt"
    echo "Environment ready. Activate with: source \"$VENV_DIR/bin/activate\""
}

case "${OS:-$(uname -s)}" in
    *[Ww]indows*|MSYS*|MINGW*|CYGWIN*)
        echo "Windows environment detected. Run setup_windows.ps1 from PowerShell as Administrator:"
        echo "  powershell -ExecutionPolicy Bypass -File \"$REPO_ROOT/setup_windows.ps1\""
        exit 0
        ;;
    *)
        ;;
esac

if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case "$ID" in
        ubuntu|debian)
            install_ubuntu
            ;;
        fedora)
            install_fedora
            ;;
        *)
            echo "Unsupported Linux distribution: $ID" >&2
            exit 1
            ;;
    esac
else
    echo "/etc/os-release not found. Unable to determine OS." >&2
    exit 1
fi

if ! command_exists python3; then
    echo "python3 is required but was not installed successfully." >&2
    exit 1
fi

create_venv_and_install

echo "Setup complete. You can run tests with 'pytest' inside the activated virtual environment."
