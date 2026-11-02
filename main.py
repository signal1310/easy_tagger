import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QGuiApplication
from main_window import MainWindow
from config_manager import get_resource_path


def main():
    # Enable fractional HiDPI scaling (125%, 150%, 175%) on Windows without blurry integer rounding
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    # Ensure Windows taskbar displays the custom application icon
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("easytagger.app.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Easy Tagger")
    app.setOrganizationName("EasyTagger")

    icon_ico = get_resource_path(os.path.join("assets", "icon.ico"))
    icon_png = get_resource_path(os.path.join("assets", "icon.png"))
    if os.path.exists(icon_ico):
        app.setWindowIcon(QIcon(icon_ico))
    elif os.path.exists(icon_png):
        app.setWindowIcon(QIcon(icon_png))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

