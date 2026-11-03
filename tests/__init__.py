import os
import sys
from typing import Optional

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

_APP: Optional[QApplication] = None


def get_qapp() -> QApplication:
    """Returns and retains the singleton offscreen QApplication instance for GUI tests."""
    global _APP
    inst = QApplication.instance()
    if inst is None:
        _APP = QApplication(sys.argv)
        return _APP
    _APP = inst
    return _APP
