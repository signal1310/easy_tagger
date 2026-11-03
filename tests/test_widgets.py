import json
import os
import tempfile
import unittest
from unittest.mock import patch

from tests import get_qapp

get_qapp()

from PyQt6.QtCore import QEvent, QMimeData, QPointF, QPropertyAnimation, QRect, Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont, QFontMetrics, QMouseEvent
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

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

        # insertWidget, indexOf, removeWidget, moveWidget
        new_btn = QPushButton("신규")
        fl.insertWidget(1, new_btn)
        self.assertEqual(fl.indexOf(new_btn), 1)
        self.assertEqual(fl.count(), 4)

        fl.moveWidget(new_btn, 0)
        self.assertEqual(fl.indexOf(new_btn), 0)

        fl.removeWidget(new_btn)
        self.assertEqual(fl.indexOf(new_btn), -1)
        self.assertEqual(fl.count(), 3)

    def test_tag_button_sizing_tooltips_and_drop_events(self):
        b_short = TagButton({"name": "1"}, fixed_height=38)
        b_two = TagButton({"name": "4K"}, fixed_height=38)
        long_name = "매우길고긴동영상태그이름테스트2026하이라이트"
        b_long = TagButton({"name": long_name, "description": "설명텍스트"}, fixed_height=38, effective_theme="light")

        self.assertEqual(b_short.sizeHint().height(), 38)
        self.assertLess(b_short.width(), 110)
        self.assertLess(b_two.width(), 110)
        self.assertGreater(b_long.sizeHint().width(), b_short.sizeHint().width())

        calc_f = QFont(b_long.font())
        calc_f.setPixelSize(13)
        calc_f.setWeight(QFont.Weight.Bold)
        self.assertGreaterEqual(b_long.width(), QFontMetrics(calc_f).horizontalAdvance(long_name) + 16)

        # Concise tooltips per state without verbose position/format headers
        self.assertNotIn("위치:", b_short.toolTip())
        self.assertNotIn("형태:", b_short.toolTip())
        self.assertIn("설명텍스트", b_long.toolTip())
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

        # 4. Auto-expand on hover when dragging files over collapsed group
        gw.set_collapsed(True, notify=False)
        self.assertTrue(gw.collapsed)
        m_file = QMimeData()
        m_file.setUrls([QUrl.fromLocalFile("test.mp4")])
        enter_ev = QDragEnterEvent(QPointF(10, 10), Qt.DropAction.CopyAction, m_file, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        gw.dragEnterEvent(enter_ev)
        self.assertTrue(enter_ev.isAccepted())
        self.assertTrue(gw._auto_expand_timer.isActive())

        # Trigger auto-expand timeout
        gw._on_auto_expand_timeout()
        self.assertFalse(gw.collapsed)

        # Cancel auto-expand on drag leave
        gw.set_collapsed(True, notify=False)
        gw._start_auto_expand()
        self.assertTrue(gw._auto_expand_timer.isActive())
        gw.dragLeaveEvent(QDragLeaveEvent())
        self.assertFalse(gw._auto_expand_timer.isActive())

        # File drop on group emits filesDropped
        dropped_files = []
        gw.filesDropped.connect(lambda p: dropped_files.extend(p))
        gw.dropEvent(QDropEvent(QPointF(10, 10), Qt.DropAction.CopyAction, m_file, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(len(dropped_files), 1)
        self.assertIn("test.mp4", dropped_files[0])

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

        # Verify GroupWidget context menu actions (integrated group settings)
        from PyQt6.QtWidgets import QMenu
        recorded_actions = []
        def fake_exec(menu_self, *args, **kwargs):
            recorded_actions.extend([a.text() for a in menu_self.actions() if not a.isSeparator()])
            return None
        with patch.object(QMenu, "exec", new=fake_exec):
            gw._show_context_menu()
        self.assertEqual(recorded_actions, ["태그 추가...", "그룹 설정...", "그룹 삭제"])

    def test_live_drag_tag_and_group(self):
        gw = GroupWidget({"id": "g1", "name": "그룹A", "collapsed": False}, fixed_height=38)
        tag_btn = TagButton({"id": "t1", "name": "태그1"}, fixed_height=38)
        gw.flow_layout.addWidget(tag_btn)

        # Test TagButton live drag lifecycle
        tag_btn._start_live_tag_drag()
        self.assertTrue(tag_btn._is_live_dragging)
        self.assertIn("#38bdf8", tag_btn.styleSheet())

        # Test eventFilter intercepts mouse release anywhere and resets border
        from PyQt6.QtGui import QMouseEvent
        rel_ev = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(0, 0), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        tag_btn.eventFilter(tag_btn, rel_ev)
        self.assertFalse(tag_btn._is_live_dragging)
        self.assertNotIn("#38bdf8", tag_btn.styleSheet())

        # Test GroupWidget live drag lifecycle
        gw.start_live_drag()
        self.assertEqual(gw.header_frame.property("live_dragging"), "true")

        gw.finish_live_drag()
        self.assertEqual(gw.header_frame.property("live_dragging"), "false")

    def test_cross_group_drag_preview_and_commit_on_drop(self):
        class MockWin(QWidget):
            def __init__(self):
                super().__init__()
                self.config = {
                    "groups": [
                        {"id": "g1", "name": "그룹1", "buttons": []},
                        {"id": "g2", "name": "그룹2", "buttons": []},
                        {"id": "g3", "name": "그룹3", "buttons": [{"id": "t1", "name": "태그1"}]},
                    ]
                }
                self.groups_container = QWidget(self)
                self.groups_layout = FlowLayout(self.groups_container)
                self.group_widgets = []

        win = MockWin()
        win.resize(400, 600)
        win.show()
        gw1 = GroupWidget(win.config["groups"][0], parent=win.groups_container)
        gw2 = GroupWidget(win.config["groups"][1], parent=win.groups_container)
        gw3 = GroupWidget(win.config["groups"][2], parent=win.groups_container)
        gw1.setGeometry(0, 0, 380, 100)
        gw2.setGeometry(0, 110, 380, 100)
        gw3.setGeometry(0, 220, 380, 100)
        win.group_widgets = [gw1, gw2, gw3]
        for gw in (gw1, gw2, gw3):
            gw.show()

        t1_btn = TagButton({"id": "t1", "name": "태그1"}, parent=gw3.body_container)
        gw3.flow_layout.addWidget(t1_btn)

        t1_btn._start_live_tag_drag()
        self.assertEqual(t1_btn._origin_gw, gw3)

        # 1. Hover over Group 2: Group 2 gets preview placeholder, t1 is NOT committed to Group 2
        g2_pos = gw2.mapToGlobal(QPointF(10, 10).toPoint())
        t1_btn._handle_live_tag_move(g2_pos)
        self.assertEqual(t1_btn._target_gw, gw2)
        self.assertIsNotNone(t1_btn._placeholder)
        self.assertEqual(t1_btn._placeholder_gw, gw2)
        self.assertEqual(t1_btn.parent(), gw3.body_container)  # NOT absorbed by Group 2!

        # 2. Hover over Group 1: Group 2 placeholder cleaned up, Group 1 gets preview placeholder
        g1_pos = gw1.mapToGlobal(QPointF(10, 10).toPoint())
        t1_btn._handle_live_tag_move(g1_pos)
        self.assertEqual(t1_btn._target_gw, gw1)
        self.assertEqual(t1_btn._placeholder_gw, gw1)
        self.assertEqual(gw2.flow_layout.count(), 0)  # Group 2 closed gap!
        self.assertEqual(t1_btn.parent(), gw3.body_container)  # Still in Group 3!

        # 3. Hover back to Group 2: works seamlessly back and forth!
        t1_btn._handle_live_tag_move(g2_pos)
        self.assertEqual(t1_btn._target_gw, gw2)
        self.assertEqual(gw1.flow_layout.count(), 0)  # Group 1 closed gap!
        self.assertEqual(gw2.flow_layout.count(), 1)  # Group 2 has placeholder!
        self.assertEqual(t1_btn.parent(), gw3.body_container)

        # 4. Hover to Group 1 and drop: placeholder removed, t1 committed to Group 1
        t1_btn._handle_live_tag_move(g1_pos)
        self.assertIsNotNone(t1_btn._placeholder)
        self.assertEqual(t1_btn.parent(), gw3.body_container)
        t1_btn._finish_live_tag_drag()
        self.assertIsNone(t1_btn._placeholder)
        self.assertEqual(t1_btn.parent(), gw1.body_container)
        self.assertEqual(gw1.flow_layout.count(), 1)
        self.assertEqual(gw2.flow_layout.count(), 0)
        self.assertEqual(gw3.flow_layout.count(), 0)
        self.assertEqual([b["id"] for b in win.config["groups"][0]["buttons"]], ["t1"])

    def test_drag_collapsed_group_delay_and_placeholder_color(self):
        class MockWin(QWidget):
            def __init__(self):
                super().__init__()
                self.config = {
                    "groups": [
                        {"id": "g1", "name": "그룹1", "buttons": []},
                        {"id": "g2", "name": "그룹2", "collapsed": True, "buttons": []},
                    ]
                }
                self.groups_container = QWidget(self)
                self.groups_layout = FlowLayout(self.groups_container)
                self.group_widgets = []

        win = MockWin()
        win.resize(400, 600)
        win.show()
        gw1 = GroupWidget(win.config["groups"][0], parent=win.groups_container)
        gw2 = GroupWidget(win.config["groups"][1], parent=win.groups_container)
        gw1.setGeometry(0, 0, 380, 100)
        gw2.setGeometry(0, 110, 380, 100)
        win.group_widgets = [gw1, gw2]
        gw1.show()
        gw2.show()

        custom_tag = TagButton({"id": "t_custom", "name": "보라태그", "bg_color": "#c084fc"}, parent=gw1.body_container)
        gw1.flow_layout.addWidget(custom_tag)

        custom_tag._start_live_tag_drag()
        # Hover over collapsed gw2
        g2_pos = gw2.mapToGlobal(QPointF(20, 20).toPoint())
        custom_tag._handle_live_tag_move(g2_pos)

        # gw2 must NOT be expanded immediately
        self.assertTrue(gw2.collapsed)
        # auto-expand timer must be ticking
        self.assertTrue(gw2._auto_expand_timer.isActive())
        # placeholder must NOT be created/inserted into the collapsed group
        self.assertIsNone(custom_tag._placeholder)

        # Move back to open gw1: gw2 auto expand cancelled
        g1_pos = gw1.mapToGlobal(QPointF(20, 20).toPoint())
        custom_tag._handle_live_tag_move(g1_pos)
        self.assertFalse(gw2._auto_expand_timer.isActive())

        custom_tag._finish_live_tag_drag()

    def test_group_collapse_expand_animation(self):
        win = QWidget()
        win.resize(400, 600)
        win.show()
        gw = GroupWidget({"id": "g_anim", "name": "애니메이션그룹", "collapsed": False}, parent=win)
        gw.setGeometry(0, 0, 380, 150)
        gw.show()
        btn1 = TagButton({"id": "t1", "name": "태그1"}, parent=gw.body_container)
        gw.flow_layout.addWidget(btn1)
        QApplication.processEvents()

        # 1. Trigger collapse with animation
        gw.set_collapsed(True, notify=True, animate=True)
        self.assertTrue(gw.collapsed)
        self.assertIsNotNone(gw._collapse_anim)
        self.assertTrue(gw._collapse_anim.state() == QPropertyAnimation.State.Running)

        # Let animation finish
        gw._collapse_anim.stop()
        gw._collapse_anim.finished.emit()
        self.assertFalse(gw.body_container.isVisible())
        self.assertIsNone(gw._collapse_anim)

        # 2. Trigger expand via toggle_collapse
        gw.toggle_collapse()
        self.assertFalse(gw.collapsed)
        self.assertTrue(gw.body_container.isVisible())
        self.assertIsNotNone(gw._collapse_anim)
        self.assertTrue(gw._collapse_anim.state() == QPropertyAnimation.State.Running)

        gw._collapse_anim.stop()
        gw._collapse_anim.finished.emit()
        self.assertIsNone(gw._collapse_anim)
        self.assertTrue(gw.body_container.isVisible())

        # 3. Test _on_auto_expand_timeout during tag live drag
        gw.set_collapsed(True, notify=False, animate=False)
        self.assertTrue(gw.collapsed)
        btn1._start_live_tag_drag()
        self.assertEqual(TagButton._active_drag_tag, btn1)

        gw._on_auto_expand_timeout()
        self.assertFalse(gw.collapsed)
        self.assertIsNotNone(gw._collapse_anim)

        btn1._finish_live_tag_drag()
        self.assertIsNone(TagButton._active_drag_tag)

    def test_tag_position_indicator_styles_puzzle_and_edge(self):
        # 1. Clean button text (no brackets for bracket tags, # for hashtag tags, no arrows)
        btn_pre = TagButton({"name": "태그", "position": "prefix", "format": "bracket"}, parent=None)
        self.assertNotIn("⇤", btn_pre.text())
        self.assertNotIn("[", btn_pre.text())
        self.assertEqual(btn_pre.text(), "태그")

        btn_suf = TagButton({"name": "태그", "position": "suffix", "format": "hashtag"}, parent=None)
        self.assertNotIn("⇥", btn_suf.text())
        self.assertEqual(btn_suf.text(), "#태그")

        # 2. Puzzle style: asymmetric border-radius, clean text
        class MockPuzzleWin(QWidget):
            def __init__(self):
                super().__init__()
                self.config = {"tag_position_indicator_style": "puzzle", "tag_format": "bracket", "position": "suffix"}
        pwin = MockPuzzleWin()
        btn_b_pre = TagButton({"name": "접두태그", "position": "prefix"}, parent=pwin)
        self.assertIn("border-top-left-radius: 9px;", btn_b_pre.styleSheet())
        self.assertIn("border-top-right-radius: 2px;", btn_b_pre.styleSheet())

        btn_b_suf = TagButton({"name": "접미태그", "position": "suffix"}, parent=pwin)
        self.assertIn("border-top-left-radius: 2px;", btn_b_suf.styleSheet())
        self.assertIn("border-top-right-radius: 9px;", btn_b_suf.styleSheet())

        # 3. Style C (edge): accent border bar on left/right
        class MockEdgeWin(QWidget):
            def __init__(self):
                super().__init__()
                self.config = {"tag_position_indicator_style": "edge", "tag_format": "bracket", "position": "suffix"}
        ewin = MockEdgeWin()
        btn_c_pre = TagButton({"name": "접두태그", "position": "prefix"}, parent=ewin)
        self.assertIn("border-left: 3.5px solid", btn_c_pre.styleSheet())

        btn_c_suf = TagButton({"name": "접미태그", "position": "suffix"}, parent=ewin)
        self.assertIn("border-right: 3.5px solid", btn_c_suf.styleSheet())

        # 4. Group override: forces all child buttons to uniform position & format
        gw_override = GroupWidget({
            "id": "g_ovr", "name": "통일그룹",
            "override_tags": True, "tag_position": "prefix", "tag_format": "hashtag"
        })
        btn_child = TagButton({"name": "원래접미", "position": "suffix", "format": "bracket"}, parent=gw_override.body_container)
        gw_override.flow_layout.addWidget(btn_child)
        pos, fmt, _ = btn_child.get_resolved_properties()
        self.assertEqual(pos, "prefix")
        self.assertEqual(fmt, "hashtag")
        self.assertIn("#원래접미", btn_child.text())


if __name__ == "__main__":
    unittest.main()
