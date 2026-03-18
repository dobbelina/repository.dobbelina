import sys
import os
from pathlib import Path

# Add project paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "plugin.video.cumination"))

# Ensure Playwright is allowed
os.environ["CUMINATION_ALLOW_PLAYWRIGHT"] = "1"

try:
    from resources.lib import playwright_helper
except ImportError:
    # Fallback for different environments if needed
    sys.path.insert(0, str(ROOT / "plugin.video.cumination" / "resources" / "lib"))
    import playwright_helper

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 playwright_sniff_bridge.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    try:
        video_url = playwright_helper.sniff_video_url(url)
        print(video_url if video_url else "No video URL found")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
