import copy
import os
import tempfile
import unittest
from unittest.mock import patch

from tests import get_qapp

get_qapp()

from PyQt6.QtCore import QMimeData, QPointF, Qt, QUrl
from PyQt6.QtGui import QCloseEvent, QDropEvent

from src.core.config_manager import load_config, load_default_config
from src.ui.main_window import MainWindow


class TestMainWindowWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "test_config.json")
        self.win = MainWindow(config_path=self.config_file)
        self.win.config["groups"] = copy.deepcopy(load_default_config().get("groups", []))
        self.win.refresh_groups()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _touch(self, name: str) -> str:
        p = os.path.join(self.temp_dir.name, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write("content")
        return p

    def test_suffix_merged_and_prefix_separate_with_undo_and_pin(self):
        f1 = self._touch("my_video.mp4")
        self.win.config["position"], self.win.config["style"] = "suffix", "merged"

        self.win.file_ctrl.apply_tag_to_files([f1], "여행")
        e1 = os.path.join(self.temp_dir.name, "my_video [여행].mp4")
        self.assertTrue(os.path.exists(e1))

        self.win.file_ctrl.apply_tag_to_files([e1], "4K")
        e2 = os.path.join(self.temp_dir.name, "my_video [여행 4K].mp4")
        self.assertTrue(os.path.exists(e2))

        self.win.file_ctrl.apply_tag_to_files([e2], "-fps 60")
        e3 = os.path.join(self.temp_dir.name, "my_video [여행 4K -fps 60].mp4")
        self.assertTrue(os.path.exists(e3))

        self.win.undo_last_action()
        self.assertTrue(os.path.exists(e2))
        self.assertFalse(os.path.exists(e3))

        old_pin = self.win.config.get("always_on_top", False)
        self.win.toggle_pin()
        self.assertEqual(self.win.config.get("always_on_top"), not old_pin)

        # Prefix + separate
        f2 = self._touch("clip.mov")
        self.win.config["position"], self.win.config["style"] = "prefix", "separate"
        self.win.file_ctrl.apply_tag_to_files([f2], "드론")
        p1 = os.path.join(self.temp_dir.name, "[드론] clip.mov")
        self.win.file_ctrl.apply_tag_to_files([p1], "-score 5")
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, "[드론] [-score 5] clip.mov")))

    def test_multi_file_batch_toggle_and_unknown_tag_detection(self):
        f1 = self._touch("clip1 [여행 신규미등록태그].mp4")
        f2 = self._touch("clip2.mp4")
        self.win.file_ctrl.set_active_files([f1, f2])

        # Verify auto-detected group & button
        btn_unknown = next((b for b in self.win.all_tag_buttons if b.data.get("name") == "신규미등록태그"), None)
        self.assertIsNotNone(btn_unknown)
        self.assertEqual(btn_unknown.tag_state, "partial")

        btn_travel = next(b for b in self.win.all_tag_buttons if b.data.get("name") == "여행")
        self.assertEqual(btn_travel.tag_state, "partial")

        # Click partial -> applies to all ('on')
        self.win.file_ctrl.on_tag_button_clicked(btn_travel)
        f2_tagged = os.path.join(self.temp_dir.name, "clip2 [여행].mp4")
        self.assertTrue(os.path.exists(f2_tagged))
        self.assertEqual(btn_travel.tag_state, "on")

        # Click 'on' -> removes from all ('off')
        self.win.file_ctrl.on_tag_button_clicked(btn_travel)
        self.assertEqual(btn_travel.tag_state, "off")

        # Undo restores '여행' to both files
        self.win.undo_last_action()
        self.assertEqual(btn_travel.tag_state, "on")

    def test_prompt_tag_resolution_and_window_drop(self):
        f = self._touch("movie.mp4")
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(f)])
        self.win.dropEvent(QDropEvent(QPointF(10, 10), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(self.win.active_file_path, os.path.normpath(f))

        btn_score = next(b for b in self.win.all_tag_buttons if b.data.get("param_val_mode") == "prompt")
        with patch("src.ui.controllers.file_controller.ThemedPromptDialog") as MockPrompt:
            MockPrompt.return_value.exec.return_value = 1
            MockPrompt.return_value.get_text.return_value = "9.5"
            self.win.file_ctrl.on_tag_button_clicked(btn_score)

        expected = os.path.join(self.temp_dir.name, "movie [-score 9.5].mp4")
        self.assertTrue(os.path.exists(expected))
        self.assertEqual(btn_score.tag_state, "on")

    def test_ui_invariants_and_persistence(self):
        self.assertEqual(self.win.contextMenuPolicy(), Qt.ContextMenuPolicy.NoContextMenu)
        self.assertEqual(self.win.scroll_area.contextMenuPolicy(), Qt.ContextMenuPolicy.NoContextMenu)
        self.assertEqual(self.win.groups_container.contextMenuPolicy(), Qt.ContextMenuPolicy.NoContextMenu)
        self.assertTrue(hasattr(self.win, "btn_add_group") and hasattr(self.win, "btn_menu"))
        self.assertFalse(hasattr(self.win, "btn_undo") or hasattr(self.win, "btn_pin"))

        self.win.resize(500, 440)
        self.win.move(120, 160)
        self.win.config.update({"theme": "light", "position": "prefix", "style": "separate", "button_height": 42})
        self.win.closeEvent(QCloseEvent())

        saved = load_config(self.config_file)
        self.assertEqual((saved["window_width"], saved["window_height"]), (500, 440))
        self.assertEqual((saved["window_x"], saved["window_y"]), (120, 160))
        self.assertEqual(saved["button_height"], 42)

    def test_main_entrypoint_startup(self):
        import main
        with patch("main.QApplication") as MockApp, patch("main.MainWindow") as MockWin, patch("main.sys.exit") as mock_exit:
            MockApp.return_value.exec.return_value = 0
            main.main()
            MockWin.assert_called_once()
            MockWin.return_value.show.assert_called_once()
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
