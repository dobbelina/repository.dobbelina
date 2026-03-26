# 💎 Cumination (Modernized Fork)

<img src="https://user-images.githubusercontent.com/46063764/103461711-a9eb6280-4d20-11eb-983b-516b022cbbf5.png" width="250" align="right">

[![Latest Version](https://img.shields.io/badge/dynamic/xml?color=hotpink&label=version&query=%2Faddon%2F@version&url=https%3A%2F%2Fraw.githubusercontent.com%2Frpeters1430%2Frepository.dobbelina%2Fmaster%2Fplugin.video.cumination%2Faddon.xml)](https://github.com/rpeters1430/repository.dobbelina)
[![Tests Passing](https://github.com/rpeters1430/repository.dobbelina/actions/workflows/pytest.yml/badge.svg)](https://github.com/rpeters1430/repository.dobbelina/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Welcome to the **Modernized Fork** of Cumination. This repository is dedicated to maintaining and improving the premier adult video aggregator for Kodi, focusing on reliability, speed, and modern web standards.

---

## 🚀 Why this Fork?

The original Cumination was built on complex Regex patterns that break whenever a site updates its layout. This fork has undergone a massive **Modernization Effort** to ensure a stable viewing experience.

### Key Differences & Improvements:
- ✅ **100% BeautifulSoup4 Migration**: All 137+ site scrapers have been migrated from fragile Regex to robust HTML parsing. This reduces breakage by ~70%.
- 🛡️ **FlareSolverr Integration**: Built-in support to bypass Cloudflare protection. If a site like **PimpBunny** is blocked, this fork handles it automatically.
- 📺 **Enhanced Live Cams**: 
  - **Stripchat**: Fully fixed with a local manifest proxy and MOUFLON HLS rewriting for perfect Kodi compatibility.
  - **Reallifecam**: Robust domain-agnostic scraping supporting `.to`, `.in`, `.org`, `.us`, and more.
- 🧪 **Testing Infrastructure**: We maintain over 2000 tests and 113+ site fixtures. Every change is verified via CI/CD to prevent regressions.
- 🆕 **Exclusive Sites**: Added new providers not found in the original repo, including **PimpBunny** and improved JAV/Hentai support.

---

## 🛠️ Installation

### 1. Download the Repository
Download the latest repository ZIP to enable auto-updates:
👉 **[repository.dobbelina-1.0.6.zip](https://rpeters1430.github.io/repository.dobbelina/repository.dobbelina/repository.dobbelina-1.0.6.zip)**

### 2. Install FlareSolverr (Highly Recommended)
Many modern sites use Cloudflare. To access them:
1. Install **FlareSolverr** on your network (Docker, Windows, or Linux).
2. Enable it in the **Cumination Addon Settings** under the "Network" or "Advanced" tab.

---

## 📈 Project Status

| Milestone | Progress | Status |
|-----------|----------|--------|
| BeautifulSoup Migration | 137/137 Sites | ✅ **100% Complete** |
| Live Cam Overhaul | All Major Sites | ✅ **Stable** |
| Testing Coverage | 79.0% | 🚀 **Growing** |
| Python 3 Compatibility | Matrix/Nexus/Omega | ✅ **Verified** |

For a detailed roadmap, see [docs/development/MODERNIZATION.md](docs/development/MODERNIZATION.md).

---

## 🤝 Contributing

We love contributors! If you want to help:
1. Check the [Issues](https://github.com/rpeters1430/repository.dobbelina/issues) for broken sites.
2. Read our [Development Setup Guide](docs/guides/SETUP.md).
3. Submit a Pull Request.

### Development Setup
```bash
# Install dependencies
pip install -r requirements-test.txt

# Run tests
pytest
```

On Windows, if the repository already contains a Linux-created `.venv`, create a Windows environment in `.venv-win` instead:

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\activate
python -m pip install -r requirements-test.txt
python run_tests.py
```

---

## 📜 Credits & Disclaimer

- **Original Authors**: Whitecream & holisticdioxide.
- **Modernization & Maintenance**: RPeters1430.
- **Contributors**: Fantastic people from Reddit and GitHub including jdoedev, 12asdfg12, and camilt.

**Disclaimer**: This addon is for adult audiences only. All content is scraped from public websites. The maintainers do not host or own any of the media.

---
<div align="center">
  <i>Maintained with ❤️ for the community.</i>
</div>
