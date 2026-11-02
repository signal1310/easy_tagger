import os
from typing import Optional, Dict, Tuple
from PyQt6.QtCore import QByteArray, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

SVG_ICONS: Dict[str, str] = {
    "folder-plus": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/>
        <line x1="12" y1="10" x2="12" y2="16"/>
        <line x1="9" y1="13" x2="15" y2="13"/>
    </svg>""",
    "undo": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 7v6h6"/>
        <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>
    </svg>""",
    "pin": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="17" x2="12" y2="22"/>
        <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v7.55l-1.78.9A2 2 0 0 0 5 15.24V17Z"/>
    </svg>""",
    "settings": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
        <circle cx="12" cy="12" r="3"/>
    </svg>""",
    "file": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
        <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
    </svg>""",
    "files": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 7h-3a2 2 0 0 1-2-2V2"/>
        <path d="M9 18a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h7l4 4v10a2 2 0 0 1-2 2Z"/>
        <path d="M3 7.6v12.8A1.6 1.6 0 0 0 4.6 22h9.8"/>
    </svg>""",
    "x": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
    </svg>""",
    "plus": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>""",
    "chevron-down": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"/>
    </svg>""",
    "chevron-right": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="9 18 15 12 9 6"/>
    </svg>""",
    "edit": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
    </svg>""",
    "copy": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
        <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
    </svg>""",
    "trash": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 6h18"/>
        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
        <line x1="10" y1="11" x2="10" y2="17"/>
        <line x1="14" y1="11" x2="14" y2="17"/>
    </svg>""",
    "check": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
    </svg>""",
    "moon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
    </svg>""",
    "sun": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="4"/>
        <path d="M12 2v2"/>
        <path d="M12 20v2"/>
        <path d="m4.93 4.93 1.41 1.41"/>
        <path d="m17.66 17.66 1.41 1.41"/>
        <path d="M2 12h2"/>
        <path d="M20 12h2"/>
        <path d="m6.34 17.66-1.41 1.41"/>
        <path d="m19.07 4.93-1.41 1.41"/>
    </svg>""",
    "monitor": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
    </svg>""",
}

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
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(p)
    p.end()
    pix.setDevicePixelRatio(scale)
    return pix


def get_pixmap(name: str, color: Optional[str] = None, theme: str = "dark", size: int = 16, dpr: Optional[float] = None) -> QPixmap:
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


def get_icon(name: str, color: Optional[str] = None, theme: str = "dark", size: int = 16) -> QIcon:
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
    # HiDPI support: Pre-render vector SVG at multiple DPI scales (1.0x ~ 4.0x)
    # Qt's style engine will automatically pick the exact matching physical resolution
    for scale in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0):
        scaled_pix = _render_svg_pixmap(renderer, size, scale)
        icon.addPixmap(scaled_pix)

    _icon_cache[cache_key] = icon
    return icon


def dump_svg_files(target_dir: str = "assets/icons"):
    """Dumps all SVG icon files to the assets/icons directory."""
    os.makedirs(target_dir, exist_ok=True)
    for name, svg_code in SVG_ICONS.items():
        out_path = os.path.join(target_dir, f"{name}.svg")
        # Default to currentColor
        clean_svg = svg_code.format(color="currentColor").strip()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(clean_svg)

