import os
import sys
from typing import Optional


def get_app_dir() -> str:
    """Returns the persistent directory of the executable or project root (where user configs live)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # src/core/paths.py -> src/core -> src -> project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_bundle_dir() -> str:
    """Returns the bundled resources directory (supports PyInstaller _MEIPASS)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return get_app_dir()


def get_resource_path(relative_path: str) -> str:
    """Resolves resource path for both development and bundled PyInstaller environments."""
    bundle_path = os.path.join(get_bundle_dir(), relative_path)
    if os.path.exists(bundle_path):
        return bundle_path
    app_path = os.path.join(get_app_dir(), relative_path)
    if os.path.exists(app_path):
        return app_path
    return bundle_path


BASE_DIR = get_app_dir()
BUNDLE_DIR = get_bundle_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

