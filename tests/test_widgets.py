import json
import os
import tempfile
import unittest

from tests import get_qapp

get_qapp()

from PyQt6.QtCore import QEvent, QMimeData, QPointF, QRect, Qt, QUrl
from PyQt6.QtGui import QDropEvent, QFont, QFontMetrics, QMouseEvent
from PyQt6.QtWidgets import QPushButton, QWidget

from src.core.defaults import MIME_GROUP, MIME_TAG
from src.ui.widgets.action_bar import ActionBar
from src.ui.widgets.flow_layout import FlowLayout
from src.ui.widgets.group_widget import ClickableHeaderFrame, GroupWidget
from src.ui.widgets.tag_button import TagButton


class TestWidgets(unittest.TestCase):
    def test_flow_layout_wrapping_and_bounds(self):
        host = QWidget()
        fl = FlowLayout(host, margin=4, h_spacing=6, v_spacing=6)
        for txt in ("태그A", "태그B", "태그C", "태그D"):
            btn = QPushButton(txt)
            btn.setFixedSize(60, 30)
            fl.addWidget(btn)

        self.assertEqual(fl.count(), 4)
        self.assertIsNone(fl.itemAt(99))
        self.assertGreater(fl.heightForWidth(100), fl.heightForWidth(400))
        fl.setGeometry(QRect(0, 0, 140, 120))
        self.assertIsNotNone(fl.takeAt(0))
        self.assertEqual(fl.count(), 3)

    def test_tag_button_sizing_tooltips_and_drop_events(self):
        b_short = TagButton({"name": "1"}, fixed_height=38)
        b_two = TagButton({"name": "4K"}, fixed_height=38)
        long_name = "매우길고긴동영상태그이름테스트2026하이라이트"
        b_long = TagButton({"name": long_name, "description": "설명텍스트"}, fixed_height=38, effective_theme="light")

        self.assertEqual(b_short.sizeHint().height(), 38)
        self.assertLess(b_short.width(), 55)
        self.assertLess(b_two.width(), 55)
        self.assertGreater(b_long.sizeHint().width(), b_short.sizeHint().width())

        calc_f = QFont(b_long.font())
        calc_f.setPixelSize(13)
        calc_f.setWeight(QFont.Weight.Bold)
        self.assertGreaterEqual(b_long.width(), QFontMetrics(calc_f).horizontalAdvance(long_name) + 16)

        # Concise tooltips per state
        self.assertEqual(b_short.toolTip(), "")
        self.assertEqual(b_long.toolTip(), "설명텍스트")
        self.assertNotIn("우클릭", b_long.toolTip())
        b_long.set_tag_state("off")
        self.assertIn("border: 2px solid", b_long.styleSheet().lower())
        self.assertIn("#ffffff", b_long.styleSheet().lower())
        self.assertIn("+ 미적용", b_long.toolTip())
        b_long.set_tag_state("partial")
        self.assertIn("◐ 일부 적용됨", b_long.toolTip())
        b_long.set_tag_state("on")
        self.assertIn("✓ 적용됨", b_long.toolTip())

        # File drop & tag reorder drop
        with tempfile.TemporaryDirectory() as td:
            fp = os.path.join(td, "sample.mp4")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("x")
            btn = TagButton({"id": "target-id", "name": "테스트"}, fixed_height=38)
            dropped, reordered = [], []
            btn.filesDropped.connect(lambda d, paths: dropped.append((d, paths)))
            btn.tagReorderRequested.connect(lambda s, t, p: reordered.append((s, t, p)))

            mime_file = QMimeData()
            mime_file.setUrls([QUrl.fromLocalFile(fp)])
            btn.dropEvent(QDropEvent(QPointF(5, 5), Qt.DropAction.CopyAction, mime_file, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
            self.assertEqual(dropped[0][1][0], os.path.normpath(fp))

            mime_tag = QMimeData()
            mime_tag.setData(MIME_TAG, json.dumps({"tag_id": "src-id"}).encode("utf-8"))
            btn.dropEvent(QDropEvent(QPointF(2, 5), Qt.DropAction.MoveAction, mime_tag, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
            self.assertEqual(reordered[0], ("src-id", "target-id", "before"))

    def test_clickable_header_mouse_events(self):
        hdr = ClickableHeaderFrame("기본 태그", "▼", effective_theme="dark")
        clicks, right_clicks = [], []
        hdr.clicked.connect(lambda: clicks.append(True))
        hdr.rightClicked.connect(lambda pos: right_clicks.append(pos))

        # 1. Normal left click + release toggles collapse (emits clicked)
        press_l = QMouseEvent(
            QEvent.Type.MouseButtonPress, QPointF(10, 10), Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        )
        rel_l = QMouseEvent(
            QEvent.Type.MouseButtonRelease, QPointF(10, 10), Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        )
        hdr.mousePressEvent(press_l)
        hdr.mouseReleaseEvent(rel_l)
        self.assertEqual(len(clicks), 1)

        # 2. Ctrl + left click release does NOT toggle collapse
        press_ctrl = QMouseEvent(
            QEvent.Type.MouseButtonPress, QPointF(10, 10), Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
        )
        rel_ctrl = QMouseEvent(
            QEvent.Type.MouseButtonRelease, QPointF(10, 10), Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier,
        )
        hdr.mousePressEvent(press_ctrl)
        hdr.mouseReleaseEvent(rel_ctrl)
        self.assertEqual(len(clicks), 1)

        # 3. Right click emits rightClicked
        press_r = QMouseEvent(
            QEvent.Type.MouseButtonPress, QPointF(12, 12), QPointF(100, 100),
            Qt.MouseButton.RightButton, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier,
        )
        hdr.mousePressEvent(press_r)
        self.assertEqual(len(right_clicks), 1)

    def test_group_widget_and_action_bar(self):
        gw = GroupWidget({"id": "g1", "name": "그룹A", "collapsed": False}, fixed_height=38)
        gw.show()
        self.assertEqual(gw.header_frame.toolTip(), "")
        gw.toggle_collapse()
        self.assertTrue(gw.collapsed)
        self.assertEqual(gw.lbl_indicator.text(), gw.SYMBOL_COLLAPSED)
        gw.toggle_collapse()
        self.assertFalse(gw.collapsed)

        moved, greorder = [], []
        gw.tagMovedToGroupRequested.connect(lambda t, g: moved.append((t, g)))
        gw.groupReorderRequested.connect(lambda s, t, p: greorder.append((s, t, p)))

        m_tag = QMimeData()
        m_tag.setData(MIME_TAG, json.dumps({"tag_id": "t9"}).encode("utf-8"))
        gw.dropEvent(QDropEvent(QPointF(5, 5), Qt.DropAction.MoveAction, m_tag, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(moved[0], ("t9", "g1"))

        m_grp = QMimeData()
        m_grp.setData(MIME_GROUP, json.dumps({"group_id": "g2"}).encode("utf-8"))
        gw.dropEvent(QDropEvent(QPointF(5, 1), Qt.DropAction.MoveAction, m_grp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(greorder[0], ("g2", "g1", "before"))

        bar = ActionBar(effective_theme="dark")
        self.assertEqual(bar.update_active_files_display([], "dark"), "Easy Tagger")
        self.assertEqual(bar.update_active_files_display(["a.mp4"], "dark"), "Easy Tagger - [a.mp4]")
        many = [f"file_{i}.mp4" for i in range(18)]
        self.assertIn("외 17개", bar.update_active_files_display(many, "light"))
        self.assertIn("외 3개", bar.lbl_active_file.toolTip())

        menu = bar.build_hamburger_menu("dark", undo_count=2, is_pinned=True)
        texts = [a.text() for a in menu.actions() if not a.isSeparator()]
        self.assertEqual(len(texts), 4)
        self.assertIn("실행 취소 (2)", texts[0])


if __name__ == "__main__":
    unittest.main()
