import unittest

from tests import get_qapp

get_qapp()

from PyQt6.QtWidgets import QLabel, QMessageBox, QPushButton

from src.core.defaults import APP_NAME, APP_VERSION
from src.ui.dialogs.group_dialog import GroupDialog
from src.ui.dialogs.help_dialog import HelpDialog
from src.ui.dialogs.message_box import ThemedMessageBox
from src.ui.dialogs.prompt_dialog import ThemedPromptDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.tag_dialog import TagDialog


class TestDialogs(unittest.TestCase):
    def test_tag_dialog_unified_syntax_and_color(self):
        dlg = TagDialog(
            initial_data={"name": "브이로그", "description": "일상 기록", "bg_color": "#fed7aa"},
            button_height=38,
        )
        self.assertEqual(dlg.windowTitle(), "태그 상세 설정")
        self.assertEqual(dlg.edit_name.text(), "브이로그")
        self.assertEqual(dlg.edit_desc.text(), "일상 기록")

        dlg.edit_name.setText("시네마틱")
        dlg.edit_desc.setText("영화 같은 영상")
        dlg.color_picker._emit_color("#a7f3d0")
        dlg._save_and_accept()

        saved = dlg.get_data()
        self.assertEqual(saved["name"], "시네마틱")
        self.assertEqual(saved["bg_color"], "#a7f3d0")
        self.assertNotIn("label", saved)
        self.assertNotIn("tag_text", saved)
        self.assertEqual(saved["tag_type"], "normal")
        self.assertEqual(saved["description"], "영화 같은 영상")

        # Fixed param tag
        dlg.edit_name.setText("[-fps 120]")
        dlg._save_and_accept()
        saved_fixed = dlg.get_data()
        self.assertEqual(saved_fixed["name"], "-fps 120")
        self.assertEqual(saved_fixed["tag_type"], "param")
        self.assertEqual(saved_fixed["param_key"], "-fps")
        self.assertEqual(saved_fixed["param_val_mode"], "fixed")
        self.assertEqual(saved_fixed["param_val"], "120")

        # Prompt param tag
        dlg.edit_name.setText("-score ?")
        dlg._save_and_accept()
        saved_prompt = dlg.get_data()
        self.assertEqual(saved_prompt["name"], "-score ?")
        self.assertEqual(saved_prompt["param_val_mode"], "prompt")
        self.assertEqual(saved_prompt["param_val"], "")

        # Enter key triggers save anywhere in TagDialog
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import Qt, QEvent
        enter_ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        tag_dlg_enter = TagDialog(initial_data={"name": "엔터테스트"})
        tag_dlg_enter.keyPressEvent(enter_ev)
        self.assertEqual(tag_dlg_enter.get_data()["name"], "엔터테스트")

        # Focus input helper selects all
        tag_dlg_enter.edit_name.setText("포커스테스트")
        tag_dlg_enter._focus_input()
        self.assertEqual(tag_dlg_enter.edit_name.selectedText(), "포커스테스트")

        # Dark theme preset color adaptation
        dark_tag_dlg = TagDialog(effective_theme="dark")
        swatches = [b for b in dark_tag_dlg.color_picker.findChildren(QPushButton) if b.objectName() != "btnSecondary"]
        self.assertGreaterEqual(len(swatches), 9)

        # Auto-detect hashtag when typing '#'
        auto_hash_dlg = TagDialog()
        auto_hash_dlg.edit_name.setText("#여행")
        self.assertEqual(auto_hash_dlg.combo_fmt.currentData(), "hashtag")
        self.assertIn("#여행", auto_hash_dlg.preview_btn.text())
        auto_hash_dlg._save_and_accept()
        saved_hash = auto_hash_dlg.get_data()
        self.assertEqual(saved_hash["name"], "여행")
        self.assertEqual(saved_hash["format"], "hashtag")
        self.assertEqual(saved_hash["tag_type"], "normal")

        # Hashtag tags do not support param attributes
        hash_param_dlg = TagDialog()
        hash_param_dlg.combo_fmt.setCurrentIndex(hash_param_dlg.combo_fmt.findData("hashtag"))
        hash_param_dlg.edit_name.setText("-fps 60")
        hash_param_dlg._save_and_accept()
        saved_hash_param = hash_param_dlg.get_data()
        self.assertEqual(saved_hash_param["tag_type"], "normal")
        self.assertNotIn("param_key", saved_hash_param)

        # Preview button reflects puzzle indicator style and lacks verbose position/format tooltip
        from PyQt6.QtWidgets import QWidget
        class MockPuzzleParent(QWidget):
            def __init__(self):
                super().__init__()
                self.config = {"tag_position_indicator_style": "puzzle", "position": "prefix", "tag_format": "bracket"}
        puzzle_parent = MockPuzzleParent()
        puzzle_dlg = TagDialog(parent=puzzle_parent)
        puzzle_dlg.edit_name.setText("모서리테스트")
        self.assertNotIn("⇤", puzzle_dlg.preview_btn.text())
        self.assertIn("border-top-left-radius: 9px;", puzzle_dlg.preview_btn.styleSheet())
        self.assertNotIn("위치:", puzzle_dlg.preview_btn.toolTip())
        self.assertNotIn("형태:", puzzle_dlg.preview_btn.toolTip())
        self.assertIn("#0d5477", swatches[0].styleSheet())

    def test_settings_and_help_dialogs_titles_and_version(self):
        cfg = {
            "theme": "dark",
            "position": "suffix",
            "style": "merged",
            "button_height": 38,
            "always_on_top": False,
        }
        s_dlg = SettingsDialog(cfg, effective_theme="dark")
        self.assertEqual(s_dlg.windowTitle(), "환경 설정")
        self.assertEqual(s_dlg.lbl_version.text(), f"{APP_NAME} {APP_VERSION}")

        s_dlg.combo_theme.setCurrentIndex(s_dlg.combo_theme.findData("light"))
        s_dlg.combo_position.setCurrentIndex(s_dlg.combo_position.findData("prefix"))
        s_dlg.combo_style.setCurrentIndex(s_dlg.combo_style.findData("separate"))
        s_dlg.combo_format.setCurrentIndex(s_dlg.combo_format.findData("hashtag"))
        s_dlg.combo_indicator_style.setCurrentIndex(s_dlg.combo_indicator_style.findData("puzzle"))
        s_dlg.spin_height.setValue(44)
        s_dlg.chk_always_on_top.setChecked(True)
        s_dlg._save_and_accept()

        updated = s_dlg.get_updated_config()
        self.assertEqual(updated["theme"], "light")
        self.assertEqual(updated["position"], "prefix")
        self.assertEqual(updated["style"], "separate")
        self.assertEqual(updated["tag_format"], "hashtag")
        self.assertEqual(updated["tag_position_indicator_style"], "puzzle")
        self.assertEqual(updated["button_height"], 44)
        self.assertTrue(updated["always_on_top"])

        h_dlg = HelpDialog(effective_theme="light")
        self.assertEqual(h_dlg.windowTitle(), "도움말")
        self.assertEqual(h_dlg.lbl_version.text(), f"{APP_NAME} {APP_VERSION}")
        for lbl in h_dlg.findChildren(QLabel):
            self.assertNotIn("<b>", lbl.text())

    def test_group_prompt_and_message_box_dialogs(self):
        g_dlg = GroupDialog(title="그룹 이름 변경", initial_name="기존그룹", effective_theme="dark")
        self.assertEqual(g_dlg.get_group_name(), "기존그룹")
        self.assertEqual(g_dlg.edit_name.placeholderText(), "")
        # Empty input should be ignored and preserve previous valid group_name
        g_dlg.edit_name.setText("   ")
        g_dlg._save_and_accept()
        self.assertEqual(g_dlg.get_group_name(), "기존그룹")

        g_dlg.edit_name.setText("새로운그룹")
        g_dlg._save_and_accept()
        self.assertEqual(g_dlg.get_group_name(), "새로운그룹")

        p_dlg = ThemedPromptDialog("속성값 입력", "값:", initial_text="60", effective_theme="light")
        self.assertEqual(p_dlg.get_text(), "60")
        p_dlg.edit_text.setText(" 120 ")
        p_dlg._save_and_accept()
        self.assertEqual(p_dlg.get_text(), "120")

        from src.ui.dialogs.group_properties_dialog import GroupPropertiesDialog
        gp_dlg = GroupPropertiesDialog({"name": "테스트그룹", "override_tags": False}, effective_theme="dark")
        self.assertEqual(gp_dlg.windowTitle(), "그룹 설정")
        self.assertEqual(gp_dlg.edit_name.text(), "테스트그룹")
        gp_dlg.edit_name.setText("")
        gp_dlg._save_and_accept()
        # Empty name should not accept
        self.assertEqual(gp_dlg.get_data().get("name"), "테스트그룹")

        gp_dlg.edit_name.setText("이름변경그룹")
        gp_dlg.chk_override.setChecked(True)
        gp_dlg.combo_position.setCurrentIndex(gp_dlg.combo_position.findData("prefix"))
        gp_dlg.combo_format.setCurrentIndex(gp_dlg.combo_format.findData("hashtag"))
        gp_dlg._save_and_accept()
        gp_data = gp_dlg.get_data()
        self.assertEqual(gp_data["name"], "이름변경그룹")
        self.assertTrue(gp_data["override_tags"])
        self.assertEqual(gp_data["tag_position"], "prefix")
        self.assertEqual(gp_data["tag_format"], "hashtag")

        msg = ThemedMessageBox(
            QMessageBox.Icon.Warning, "경고", "내용", QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok, "dark"
        )
        self.assertEqual(msg.windowTitle(), "경고")


if __name__ == "__main__":
    unittest.main()
