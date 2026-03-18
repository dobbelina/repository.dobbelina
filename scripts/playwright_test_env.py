import sys
import os
from pathlib import Path

# Add project paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "plugin.video.cumination"))

def check_env():
    print("# Playwright Environment Check\n")
    
    # Python version
    print(f"- **Python Version:** {sys.version.split()[0]}")
    
    # Playwright package
    has_pw = False
    try:
        import playwright
        from playwright.sync_api import sync_playwright
        print("- **Playwright Package:** Installed ✅")
        has_pw = True
    except ImportError:
        print("- **Playwright Package:** Not Found ❌ (Run `pip install playwright`) ")

    # Playwright Stealth
    try:
        import playwright_stealth
        print("- **Playwright Stealth:** Installed ✅")
    except ImportError:
        print("- **Playwright Stealth:** Not Found ⚠️ (Optional but recommended: `pip install playwright-stealth`) ")

    # Environment Variable
    pw_enabled = os.environ.get("CUMINATION_ALLOW_PLAYWRIGHT") == "1"
    if pw_enabled:
        print("- **CUMINATION_ALLOW_PLAYWRIGHT:** Enabled (1) ✅")
    else:
        print("- **CUMINATION_ALLOW_PLAYWRIGHT:** Disabled (or not 1) ❌")
        print("  _Note: The extension automatically sets this to 1 when running scripts._")

    # Browser Check
    if has_pw:
        print("- **Browser Check (Chromium):** ", end="", flush=True)
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                    print("Launched successfully ✅")
                except Exception as e:
                    print(f"Failed to launch ❌\n  _Error: {str(e)}_")
                    print("  _Try running: `playwright install chromium`_")
        except Exception as e:
            print(f"Error during browser check: {str(e)} ❌")
    else:
        print("- **Browser Check:** Skipped (Playwright not installed) ⏭️")

if __name__ == "__main__":
    check_env()
