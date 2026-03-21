import os
import os.path

files = os.listdir(os.path.dirname(__file__))
# Sites intentionally excluded from Kodi runtime listing.
EXCLUDED_SITE_MODULES = {"luxuretv.py", "missav.py", "pornxpert.py"}
__all__ = [
    filename[:-3]
    for filename in files
    if not filename.startswith("__")
    and filename.endswith(".py")
    and filename not in EXCLUDED_SITE_MODULES
]
