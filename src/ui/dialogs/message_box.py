from PyQt6.QtWidgets import QMessageBox

from src.ui.styles.theme_manager import ThemeManager


class ThemedMessageBox(QMessageBox):
    """
    Themed message box for warnings and confirmation questions,
    styled with the app's current theme and Windows native titlebar.
    """

    def __init__(
        self, icon, title: str, text: str, buttons, default_button, effective_theme: str = "dark", parent=None
    ):
        super().__init__(icon, title, text, buttons, parent)
        self.effective_theme = effective_theme
        self.setDefaultButton(default_button)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    @classmethod
    def question(cls, parent, title: str, text: str, effective_theme: str = "dark") -> bool:
        box = cls(
            QMessageBox.Icon.Question,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
            effective_theme=effective_theme,
            parent=parent,
        )
        return box.exec() == QMessageBox.StandardButton.Yes

    @classmethod
    def warning(cls, parent, title: str, text: str, effective_theme: str = "dark") -> None:
        box = cls(
            QMessageBox.Icon.Warning,
            title,
            text,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
            effective_theme=effective_theme,
            parent=parent,
        )
        box.exec()

