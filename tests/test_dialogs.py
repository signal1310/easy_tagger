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
        s_dlg.spin_height.setValue(44)
        s_dlg.chk_always_on_top.setChecked(True)
        s_dlg._save_and_accept()

        updated = s_dlg.get_updated_config()
        self.assertEqual(updated["theme"], "light")
        self.assertEqual(updated["position"], "prefix")
        self.assertEqual(updated["style"], "separate")
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

        msg = ThemedMessageBox(
            QMessageBox.Icon.Warning, "경고", "내용", QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok, "dark"
        )
        self.assertEqual(msg.windowTitle(), "경고")


if __name__ == "__main__":
    unittest.main()
