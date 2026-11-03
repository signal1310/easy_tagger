from typing import Dict, Optional, Tuple

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from src.ui.icons.svg_data import SVG_ICONS

_icon_cache: Dict[Tuple[str, str, int], QIcon] = {}
_pixmap_cache: Dict[Tuple[str, str, int, float], QPixmap] = {}


def get_default_color(theme: str) -> str:
    return "#d4d4d8" if theme == "dark" else "#52525b"


def get_screen_dpr() -> float:
    """Returns current primary screen device pixel ratio, defaulting to 1.0."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app:
        try:
            screen = app.primaryScreen()
            if screen:
                return max(1.0, float(screen.devicePixelRatio()))
        except Exception:
            pass
    return 1.0


def _render_svg_pixmap(renderer: QSvgRenderer, logical_size: int, scale: float) -> QPixmap:
    """Renders vector SVG with anti-aliasing onto a high-DPI aware QPixmap."""
    px_size = max(1, int(round(logical_size * scale)))
    pix = QPixmap(px_size, px_size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    pix.setDevicePixelRatio(scale)
    return pix


def get_pixmap(
    name: str,
    color: Optional[str] = None,
    theme: str = "dark",
    size: int = 16,
    dpr: Optional[float] = None,
) -> QPixmap:
    resolved_color = color or get_default_color(theme)
    target_dpr = dpr or get_screen_dpr()
    cache_key = (name, resolved_color, size, round(target_dpr, 2))
    if cache_key in _pixmap_cache:
        return _pixmap_cache[cache_key]

    template = SVG_ICONS.get(name)
    if not template:
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        return pix

    svg_str = template.format(color=resolved_color)
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    pix = _render_svg_pixmap(renderer, size, target_dpr)

    _pixmap_cache[cache_key] = pix
    return pix


def get_icon(
    name: str, color: Optional[str] = None, theme: str = "dark", size: int = 16
) -> QIcon:
    resolved_color = color or get_default_color(theme)
    cache_key = (name, resolved_color, size)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    template = SVG_ICONS.get(name)
    if not template:
        return QIcon()

    svg_str = template.format(color=resolved_color)
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))

    icon = QIcon()
    for scale in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0):
        icon.addPixmap(_render_svg_pixmap(renderer, size, scale))

    _icon_cache[cache_key] = icon
    return icon

