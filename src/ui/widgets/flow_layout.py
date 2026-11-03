from typing import List, Optional

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout, QLayoutItem, QWidget, QWidgetItem

from src.ui.animation import MotionHelper


class FlowLayout(QLayout):
    """
    Standard Qt FlowLayout that arranges widgets horizontally and wraps
    them onto new rows when horizontal space is filled.
    """

    def __init__(self, parent=None, margin: int = 0, h_spacing: int = -1, v_spacing: int = -1):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items: List[QLayoutItem] = []
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        while self.takeAt(0):
            pass

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def insertWidget(self, index: int, widget: QWidget, animate: bool = True):
        item = QWidgetItem(widget)
        self._items.insert(max(0, min(index, len(self._items))), item)
        self.invalidate()
        self.relayout(animate=animate)

    def indexOf(self, widget: QWidget) -> int:
        for idx, item in enumerate(self._items):
            if item.widget() == widget:
                return idx
        return -1

    def removeWidget(self, widget: QWidget, animate: bool = True):
        idx = self.indexOf(widget)
        if idx >= 0:
            self.takeAt(idx)
            self.invalidate()
            self.relayout(animate=animate)

    def moveWidget(self, widget: QWidget, new_index: int, animate: bool = True):
        idx = self.indexOf(widget)
        if idx >= 0 and idx != new_index:
            item = self.takeAt(idx)
            self._items.insert(max(0, min(new_index, len(self._items))), item)
            self.invalidate()
            self.relayout(animate=animate)

    def relayout(self, animate: bool = True):
        pw = self.parentWidget()
        if pw and pw.isVisible():
            r = pw.rect()
            if r.width() > 0:
                self._do_layout(r, False, animate=animate)
                pw.updateGeometry()
                p = pw.parentWidget()
                while p:
                    if p.layout():
                        p.layout().activate()
                    p = p.parentWidget()

    def horizontalSpacing(self) -> int:
        return self._h_spacing if self._h_spacing >= 0 else 10

    def verticalSpacing(self) -> int:
        return self._v_spacing if self._v_spacing >= 0 else 10

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), True, animate=False)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, False, animate=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool, animate: bool = False) -> int:
        margins = self.contentsMargins()
        eff = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x, y, line_height = eff.x(), eff.y(), 0
        space_x, space_y = self.horizontalSpacing(), self.verticalSpacing()

        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + space_x
            if next_x - space_x > eff.right() and line_height > 0:
                x = eff.x()
                y += line_height + space_y
                next_x = x + hint.width() + space_x
                line_height = 0

            if not test_only:
                target_rect = QRect(QPoint(x, y), hint)
                widget = item.widget()
                if widget:
                    is_dragging = getattr(widget, "_is_live_dragging", False)
                    if animate and not is_dragging and widget.isVisible():
                        old_pos = widget.pos()
                        target_pos = QPoint(x, y)
                        if old_pos != target_pos and not old_pos.isNull():
                            MotionHelper.glide_pos(widget, target_pos, old_pos)
                            widget.resize(hint)
                        else:
                            item.setGeometry(target_rect)
                    else:
                        item.setGeometry(target_rect)

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + margins.bottom()

