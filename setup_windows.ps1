<#
    Unified environment setup for Cumination on Windows.
    Run from an elevated PowerShell prompt:

        powershell -ExecutionPolicy Bypass -File "./setup_windows.ps1"

    Installs: Python 3, git, ImageMagick, pngquant (if available), and Python test dependencies.
#>

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$primaryVenvPath = Join-Path $repoRoot '.venv'
$windowsVenvPath = Join-Path $repoRoot '.venv-win'
$venvPath = $primaryVenvPath

function Require-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Please run this script from an Administrator PowerShell session.'
    }
}

function Command-Exists {
    param(
        [Parameter(Mandatory = $true)][string]$Name
    )
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WithWinget {
    param(
        [string]$Id,
        [string]$Name
    )
    if (Command-Exists -Name 'winget') {
        Write-Host "Installing $Name via winget..." -ForegroundColor Cyan
        winget install --id $Id -e --accept-package-agreements --accept-source-agreements
        return $true
    }
    return $false
}

function Install-WithChoco {
    param(
        [string]$Package,
        [string]$Name
    )
    if (Command-Exists -Name 'choco') {
        Write-Host "Installing $Name via Chocolatey..." -ForegroundColor Cyan
        choco install -y $Package
        return $true
    }
    return $false
}

function Ensure-Tool {
    param(
        [string]$CheckCommand,
        [string]$WingetId,
        [string]$ChocoName,
        [string]$DisplayName
    )

    if (Command-Exists -Name $CheckCommand) {
        Write-Host "$DisplayName already installed." -ForegroundColor Green
        return
    }

    if (-not (Install-WithWinget -Id $WingetId -Name $DisplayName)) {
        if (-not (Install-WithChoco -Package $ChocoName -Name $DisplayName)) {
            throw "Unable to install $DisplayName automatically. Install it manually and re-run the script."
        }
    }
}

function Test-PythonExecutable {
    param(
        [Parameter(Mandatory = $true)][string]$PythonPath
    )

    if (-not (Test-Path $PythonPath)) {
        return $false
    }

    try {
        & $PythonPath --version *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Ensure-PythonEnv {
    $global:venvPath = $primaryVenvPath

    $primaryPython = Join-Path $primaryVenvPath 'Scripts\python.exe'
    if ((Test-Path $primaryPython) -and -not (Test-PythonExecutable -PythonPath $primaryPython)) {
        Write-Warning ".venv exists but is not usable on this Windows machine. Creating a Windows-specific environment in .venv-win instead."
        $global:venvPath = $windowsVenvPath
    }

    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath" -ForegroundColor Cyan
        python -m venv $venvPath
    }

    $activatePath = Join-Path $venvPath 'Scripts/Activate.ps1'
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $activatePath

    python -m pip install --upgrade pip
    python -m pip install -r (Join-Path $repoRoot 'requirements-test.txt')

    Write-Host "Environment ready. Activate later with:`n`n    . $activatePath`n" -ForegroundColor Green
}

Require-Admin

Ensure-Tool -CheckCommand 'git' -WingetId 'Git.Git' -ChocoName 'git' -DisplayName 'Git'
Ensure-Tool -CheckCommand 'python' -WingetId 'Python.Python.3' -ChocoName 'python' -DisplayName 'Python 3'
Ensure-Tool -CheckCommand 'magick' -WingetId 'ImageMagick.ImageMagick' -ChocoName 'imagemagick' -DisplayName 'ImageMagick'

try {
    Ensure-Tool -CheckCommand 'pngquant' -WingetId 'Kornelski.pngquant' -ChocoName 'pngquant' -DisplayName 'pngquant'
} catch {
    Write-Warning "pngquant could not be installed automatically. The logo scripts will still work without it."
}

Ensure-PythonEnv

Write-Host "Setup complete. Run 'pytest' inside the activated virtual environment to execute tests." -ForegroundColor Green
