import unittest

from tests import get_qapp

get_qapp()

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from src.ui.icons import icon_factory
from src.ui.styles.theme_manager import ThemeManager


class TestThemeAndIcons(unittest.TestCase):
    def test_resolve_effective_theme_and_luminance_contrast(self):
        self.assertEqual(ThemeManager.resolve_effective_theme("dark"), "dark")
        self.assertEqual(ThemeManager.resolve_effective_theme("light"), "light")
        self.assertIn(ThemeManager.resolve_effective_theme("system"), ("dark", "light"))
        self.assertEqual(ThemeManager.resolve_effective_theme("unknown"), "dark")

        # Bright pastel -> dark text; deep dark -> white text; invalid -> fallback dark text
        self.assertEqual(ThemeManager.get_contrast_text_color("#bae6fd"), "#0f172a")
        self.assertEqual(ThemeManager.get_contrast_text_color("#18181b"), "#ffffff")
        self.assertEqual(ThemeManager.get_contrast_text_color("not-a-color"), "#0f172a")

    def test_adapt_color_for_theme(self):
        # Bright pastel in dark mode gets toned down
        adapted_dark, fg_dark = ThemeManager.adapt_color_for_theme("#bae6fd", "dark")
        self.assertEqual(fg_dark, "#ededed")
        self.assertLess(QColor(adapted_dark).lightness(), QColor("#bae6fd").lightness())

        # Already-dark color in dark mode stays unchanged
        same_dark, _ = ThemeManager.adapt_color_for_theme("#1e293b", "dark")
        self.assertEqual(same_dark, "#1e293b")

        # Light mode keeps original color
        adapted_light, fg_light = ThemeManager.adapt_color_for_theme("#bae6fd", "light")
        self.assertEqual(adapted_light, "#bae6fd")
        self.assertEqual(fg_light, "#0f172a")

        # Invalid hex fallback
        self.assertEqual(ThemeManager.adapt_color_for_theme("bad", "dark"), ("#2a2a30", "#ededed"))
        self.assertEqual(ThemeManager.adapt_color_for_theme("bad", "light"), ("#e4e4e7", "#18181b"))

    def test_qss_and_palette_application(self):
        app = get_qapp()
        light_style = ThemeManager.get_main_style("light")
        self.assertIn("QToolTip", light_style)
        self.assertIn("background-color: #ffffff", light_style)
        self.assertIn("color: #18181b", light_style)

        ThemeManager.apply_theme_to_app("light")
        pal_light = app.palette()
        self.assertEqual(pal_light.color(QPalette.ColorRole.ToolTipBase).name().lower(), "#ffffff")
        self.assertEqual(pal_light.color(QPalette.ColorRole.ToolTipText).name().lower(), "#18181b")

        dark_style = ThemeManager.get_main_style("dark")
        self.assertIn("background-color: #26262a", dark_style)
        self.assertIn("color: #ededed", dark_style)

        ThemeManager.apply_theme_to_app("dark")
        pal_dark = app.palette()
        self.assertEqual(pal_dark.color(QPalette.ColorRole.ToolTipBase).name().lower(), "#26262a")
        self.assertEqual(pal_dark.color(QPalette.ColorRole.ToolTipText).name().lower(), "#ededed")

        self.assertIn("QMenu", ThemeManager.get_context_menu_style("dark"))
        self.assertIn("QDialog", ThemeManager.get_dialog_style("light"))

        dummy = QWidget()
        ThemeManager.apply_titlebar_theme(dummy, "dark")
        ThemeManager.apply_titlebar_theme(dummy, "light")

    def test_icon_factory_rendering_and_caching(self):
        for name in icon_factory.SVG_ICONS:
            ic_dark = icon_factory.get_icon(name, theme="dark", size=16)
            ic_light = icon_factory.get_icon(name, theme="light", size=16)
            self.assertFalse(ic_dark.isNull(), f"Null dark icon: {name}")
            self.assertFalse(ic_light.isNull(), f"Null light icon: {name}")
            self.assertGreaterEqual(len(ic_dark.availableSizes()), 5)

        # Cache hit and unknown icon fallback
        self.assertIs(icon_factory.get_icon("menu", theme="dark", size=16), icon_factory.get_icon("menu", theme="dark", size=16))
        self.assertTrue(icon_factory.get_icon("nonexistent_icon").isNull())

        pix = icon_factory.get_pixmap("file", size=16, dpr=2.0)
        self.assertEqual(pix.devicePixelRatio(), 2.0)
        self.assertEqual(pix.width(), 32)
        fallback_pix = icon_factory.get_pixmap("nonexistent_icon", size=14)
        self.assertEqual(fallback_pix.width(), 14)


if __name__ == "__main__":
    unittest.main()
