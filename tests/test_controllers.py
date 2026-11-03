import copy
import os
import tempfile
import unittest
from unittest.mock import patch

from tests import get_qapp

get_qapp()

from src.core.config_manager import load_default_config
from src.ui.main_window import MainWindow


class TestControllers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "ctrl_config.json")
        self.win = MainWindow(config_path=self.config_file)
        self.win.config["groups"] = copy.deepcopy(load_default_config().get("groups", []))
        self.win.refresh_groups()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_group_controller_dialog_flows(self):
        initial_count = len(self.win.config["groups"])

        # 1. Add Group
        with patch("src.ui.controllers.group_controller.GroupDialog") as MockGD:
            MockGD.return_value.exec.return_value = 1
            MockGD.return_value.get_group_name.return_value = "신규그룹"
            self.win.group_ctrl.add_new_group()
        self.assertEqual(len(self.win.config["groups"]), initial_count + 1)
        new_gid = self.win.config["groups"][-1]["id"]

        # 2. Edit Group Settings (Integrated name & properties override)
        with patch("src.ui.dialogs.group_properties_dialog.GroupPropertiesDialog") as MockGPD:
            MockGPD.return_value.exec.return_value = 1
            MockGPD.return_value.get_data.return_value = {
                "name": "변경된그룹", "override_tags": True, "tag_position": "prefix", "tag_format": "hashtag"
            }
            self.win.group_ctrl.edit_group_settings(new_gid)
        self.assertEqual(self.win.config["groups"][-1]["name"], "변경된그룹")
        self.assertTrue(self.win.config["groups"][-1]["override_tags"])

        # 3. Add Tag to Group
        with patch("src.ui.controllers.group_controller.TagDialog") as MockTD:
            MockTD.return_value.exec.return_value = 1
            MockTD.return_value.get_data.return_value = {
                "id": "btn-new-1", "name": "새태그", "tag_type": "normal", "bg_color": "#bae6fd"
            }
            self.win.group_ctrl.add_tag_to_group(new_gid)
        self.assertEqual(len(self.win.config["groups"][-1]["buttons"]), 1)

        # 4. Edit & Duplicate & Delete Tag
        btn_data = self.win.config["groups"][-1]["buttons"][0]
        with patch("src.ui.controllers.group_controller.TagDialog") as MockTD:
            MockTD.return_value.exec.return_value = 1
            MockTD.return_value.get_data.return_value = {
                "id": "btn-new-1", "name": "편집태그", "tag_type": "normal", "bg_color": "#a7f3d0"
            }
            self.win.group_ctrl.edit_tag_button(btn_data)
        self.assertEqual(self.win.config["groups"][-1]["buttons"][0]["name"], "편집태그")

        self.win.group_ctrl.duplicate_tag_button(self.win.config["groups"][-1]["buttons"][0])
        self.assertEqual(len(self.win.config["groups"][-1]["buttons"]), 2)

        with patch("src.ui.controllers.group_controller.ThemedMessageBox.question", return_value=True):
            self.win.group_ctrl.delete_tag_button(self.win.config["groups"][-1]["buttons"][1])
            self.assertEqual(len(self.win.config["groups"][-1]["buttons"]), 1)

            # 5. Delete Group
            self.win.group_ctrl.delete_group(new_gid)
            self.assertEqual(len(self.win.config["groups"]), initial_count)

    def test_window_dialogs_and_prompt_cancel(self):
        with patch("src.ui.main_window.SettingsDialog") as MockSD:
            MockSD.return_value.exec.return_value = 1
            MockSD.return_value.get_updated_config.return_value = {"button_height": 46, "theme": "light"}
            self.win.open_settings_dialog()
        self.assertEqual(self.win.config["button_height"], 46)
        self.assertEqual(self.win.config["theme"], "light")

        with patch("src.ui.main_window.HelpDialog") as MockHD:
            MockHD.return_value.exec.return_value = 1
            self.win.open_help_dialog()
            MockHD.assert_called_once()

        # Cancelled prompt returns None without renaming
        with patch("src.ui.controllers.file_controller.ThemedPromptDialog") as MockPrompt:
            MockPrompt.return_value.exec.return_value = 0
            resolved = self.win.file_ctrl.resolve_tag_to_apply({"name": "-score ?", "param_val_mode": "prompt"})
            self.assertIsNone(resolved)

    def test_file_controller_no_active_click_drop_and_clear(self):
        btn = self.win.all_tag_buttons[0]
        self.win.file_ctrl.on_tag_button_clicked(btn)
        self.assertEqual(self.win.active_file_paths, [])

        sample = os.path.join(self.temp_dir.name, "drop_target.mp4")
        with open(sample, "w", encoding="utf-8") as f:
            f.write("data")
        self.win.file_ctrl.on_files_dropped_on_button({"name": "4K"}, [sample])
        expected = os.path.join(self.temp_dir.name, "drop_target [4K].mp4")
        self.assertTrue(os.path.exists(expected))
        self.assertEqual(self.win.active_file_path, expected)

        self.win.action_bar.btn_close_active_file.click()
        self.assertEqual(self.win.active_file_paths, [])
        self.assertEqual(self.win.windowTitle(), "Easy Tagger")


if __name__ == "__main__":
    unittest.main()
