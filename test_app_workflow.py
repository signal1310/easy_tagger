import os
import sys
import tempfile
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestAppWorkflow(unittest.TestCase):
    def setUp(self):
        import copy
        from config_manager import load_default_config
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "test_config.json")
        self.win = MainWindow(config_path=self.config_file)
        self.win.config["groups"] = copy.deepcopy(load_default_config().get("groups", []))
        self.win._refresh_groups()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_suffix_merged_workflow(self):
        test_file = os.path.join(self.temp_dir.name, "my_video.mp4")
        with open(test_file, "w") as f:
            f.write("test")

        self.win.config["position"] = "suffix"
        self.win.config["style"] = "merged"

        # 1. Apply first tag "여행"
        self.win._apply_tag_to_files([test_file], "여행")
        expected_1 = os.path.join(self.temp_dir.name, "my_video [여행].mp4")
        self.assertTrue(os.path.exists(expected_1))
        self.assertFalse(os.path.exists(test_file))

        # 2. Apply second tag "4K" -> should merge into [여행 4K]
        self.win._apply_tag_to_files([expected_1], "4K")
        expected_2 = os.path.join(self.temp_dir.name, "my_video [여행 4K].mp4")
        self.assertTrue(os.path.exists(expected_2))
        self.assertFalse(os.path.exists(expected_1))

        # 3. Apply param tag "-fps 60"
        self.win._apply_tag_to_files([expected_2], "-fps 60")
        expected_3 = os.path.join(self.temp_dir.name, "my_video [여행 4K -fps 60].mp4")
        self.assertTrue(os.path.exists(expected_3))

        # 4. Test Undo!
        self.win.undo_last_action()
        self.assertTrue(os.path.exists(expected_2))
        self.assertFalse(os.path.exists(expected_3))

        # 5. Test Pin Toggle
        old_pin = self.win.config.get("always_on_top", False)
        self.win._toggle_pin()
        self.assertEqual(self.win.config.get("always_on_top"), not old_pin)

    def test_prefix_separate_workflow(self):
        test_file = os.path.join(self.temp_dir.name, "clip.mov")
        with open(test_file, "w") as f:
            f.write("test")

        self.win.config["position"] = "prefix"
        self.win.config["style"] = "separate"

        self.win._apply_tag_to_files([test_file], "드론")
        expected_1 = os.path.join(self.temp_dir.name, "[드론] clip.mov")
        self.assertTrue(os.path.exists(expected_1))

        self.win._apply_tag_to_files([expected_1], "-score 5")
        expected_2 = os.path.join(self.temp_dir.name, "[드론] [-score 5] clip.mov")
        self.assertTrue(os.path.exists(expected_2))

    def test_variable_width_and_fixed_height(self):
        # Create two buttons with different text lengths
        from tag_button import TagButton
        b1 = TagButton({"label": "A"}, fixed_height=38)
        b2 = TagButton({"label": "A Very Long Tag Name For Testing"}, fixed_height=38)

        # Height must be identical (fixed)
        self.assertEqual(b1.sizeHint().height(), 38)
        self.assertEqual(b2.sizeHint().height(), 38)
        # Width must be variable (longer tag has larger width)
        self.assertGreater(b2.sizeHint().width(), b1.sizeHint().width())

    def test_group_collapse_and_expand(self):
        self.win.show()
        self.assertTrue(len(self.win.group_widgets) > 0)
        gw = self.win.group_widgets[0]
        gw.set_collapsed(False)
        # Initially expanded
        self.assertFalse(gw.collapsed)
        self.assertEqual(gw.lbl_indicator.text(), gw.SYMBOL_EXPANDED)
        self.assertFalse(gw.body_container.isHidden())

        # Toggle collapse
        gw.toggle_collapse()
        self.assertTrue(gw.collapsed)
        self.assertEqual(gw.lbl_indicator.text(), gw.SYMBOL_COLLAPSED)
        self.assertTrue(gw.body_container.isHidden())

        # Toggle back
        gw.toggle_collapse()
        self.assertFalse(gw.collapsed)
        self.assertEqual(gw.lbl_indicator.text(), gw.SYMBOL_EXPANDED)
        self.assertFalse(gw.body_container.isHidden())

    def test_interactive_tag_editor_toggle(self):
        # Create a test file
        test_file = os.path.join(self.temp_dir.name, "nature.mp4")
        with open(test_file, "w") as f:
            f.write("content")

        self.win.config["position"] = "suffix"
        self.win.config["style"] = "merged"

        # Initially no active file
        self.assertIsNone(self.win.active_file_path)
        for btn in self.win.all_tag_buttons:
            self.assertEqual(btn.tag_state, "none")

        # 1. Load active file directly
        self.win._set_active_file(test_file)
        self.assertEqual(self.win.active_file_path, test_file)
        # All buttons should be 'off' because nature.mp4 has no tags
        # and should KEEP their distinctive background colors (not replaced by monochrome gray)
        for btn in self.win.all_tag_buttons:
            self.assertEqual(btn.tag_state, "off")
            self.assertNotIn("#f4f4f5", btn.styleSheet().lower())
            self.assertNotIn("#232327", btn.styleSheet().lower())

        # 2. Click the first tag button (e.g. '여행') -> should toggle ON and rename
        btn_travel = self.win.all_tag_buttons[0]
        self.win._on_tag_button_clicked(btn_travel)

        # File renamed to nature [여행].mp4
        expected_path = os.path.join(self.temp_dir.name, "nature [여행].mp4")
        self.assertEqual(self.win.active_file_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))
        self.assertEqual(btn_travel.tag_state, "on")

        # 3. Click the first tag button again -> should toggle OFF and remove tag
        self.win._on_tag_button_clicked(btn_travel)
        reverted_path = os.path.join(self.temp_dir.name, "nature.mp4")
        self.assertEqual(self.win.active_file_path, reverted_path)
        self.assertTrue(os.path.exists(reverted_path))
        self.assertEqual(btn_travel.tag_state, "off")

    def test_repeated_tag_drop_no_duplicate_error(self):
        # User scenario:
        # a.txt dropped on tag 'a' -> renamed to a [a].txt
        # Then same file dropped on tag 'a' again -> should not give duplicate filename error
        test_file = os.path.join(self.temp_dir.name, "a.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        self.win.config["position"] = "suffix"
        self.win.config["style"] = "merged"

        # 1. First drop on tag 'a'
        self.win._apply_tag_to_files([test_file], "a")
        tagged_path = os.path.join(self.temp_dir.name, "a [a].txt")
        self.assertTrue(os.path.exists(tagged_path))
        self.assertEqual(os.path.normcase(self.win.active_file_path), os.path.normcase(tagged_path))

        # 2. Second drop of the exact same file (using forward slashes as Qt url.toLocalFile() can return)
        qt_url_path = tagged_path.replace("\\", "/")
        # This should execute gracefully without raising errors or popups
        self.win._apply_tag_to_files([qt_url_path], "a")
        self.assertTrue(os.path.exists(tagged_path))
        self.assertEqual(os.path.normcase(self.win.active_file_path), os.path.normcase(tagged_path))

    def test_tag_button_drop_event(self):
        from PyQt6.QtCore import QMimeData, QUrl, QPointF, Qt
        from PyQt6.QtGui import QDropEvent
        from tag_button import TagButton

        btn = TagButton({"label": "테스트", "tag_text": "테스트"}, fixed_height=38)
        dropped_results = []
        btn.filesDropped.connect(lambda bdata, paths: dropped_results.append((bdata, paths)))

        test_file = os.path.join(self.temp_dir.name, "sample.mp4")
        with open(test_file, "w") as f:
            f.write("content")

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(test_file)])
        drop_ev = QDropEvent(
            QPointF(10.0, 10.0),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        btn.dropEvent(drop_ev)
        self.assertEqual(len(dropped_results), 1)
        self.assertEqual(dropped_results[0][1][0], os.path.normpath(test_file))

    def test_tag_name_and_description_tooltip(self):
        from tag_button import TagButton
        data = {
            "name": "인터뷰",
            "description": "인물 인터뷰 영상 자료",
            "bg_color": "#bae6fd",
        }
        btn = TagButton(data, fixed_height=38)
        self.assertEqual(btn.text(), "인터뷰")
        self.assertEqual(btn.toolTip(), "인물 인터뷰 영상 자료")
        self.assertNotIn("우클릭", btn.toolTip())

    def test_auto_detect_unknown_tags_from_file(self):
        # Create a file with a tag that does NOT exist in the program
        test_file = os.path.join(self.temp_dir.name, "clip [신규미등록태그].mp4")
        with open(test_file, "w") as f:
            f.write("content")

        # Load file into window
        self.win._set_active_file(test_file)

        # Verify that "감지된 태그" group was created
        groups = self.win.config.get("groups", [])
        detected_group = next((g for g in groups if g.get("id") == "group-detected" or g.get("name") == "감지된 태그"), None)
        self.assertIsNotNone(detected_group)

        # Verify that "신규미등록태그" button was created in the detected group
        matching_btns = [b for b in detected_group.get("buttons", []) if b.get("name") == "신규미등록태그"]
        self.assertEqual(len(matching_btns), 1)
        new_bdata = matching_btns[0]
        self.assertEqual(new_bdata["name"], "신규미등록태그")

        # Verify the button is shown in UI and highlighted ON
        btn_widget = next((b for b in self.win.all_tag_buttons if b.data.get("name") == "신규미등록태그"), None)
        self.assertIsNotNone(btn_widget)
        self.assertEqual(btn_widget.tag_state, "on")
        self.assertEqual(btn_widget.text(), "✓ 신규미등록태그")

        # Clicking the button should toggle it OFF and remove the tag from the file!
        self.win._on_tag_button_clicked(btn_widget)
        renamed_file = os.path.join(self.temp_dir.name, "clip.mp4")
        self.assertTrue(os.path.exists(renamed_file))
        self.assertEqual(btn_widget.tag_state, "off")
        self.assertEqual(btn_widget.text(), "신규미등록태그")

    def test_tag_dialog_name_and_description(self):
        from tag_dialog import TagDialog
        dlg = TagDialog(initial_data={"name": "브이로그", "description": "일상 기록", "bg_color": "#fed7aa"}, button_height=38)
        self.assertEqual(dlg.edit_name.text(), "브이로그")
        self.assertEqual(dlg.edit_desc.text(), "일상 기록")

        dlg.edit_name.setText("시네마틱")
        dlg.edit_desc.setText("영화 같은 영상")
        dlg._save_and_accept()

        saved = dlg.get_data()
        self.assertEqual(saved["name"], "시네마틱")
        self.assertNotIn("label", saved)
        self.assertNotIn("tag_text", saved)
        self.assertEqual(saved["tag_type"], "normal")
        self.assertEqual(saved["description"], "영화 같은 영상")

        # Fixed param tag via unified input
        dlg.edit_name.setText("[-fps 120]")
        dlg._save_and_accept()
        saved_fixed = dlg.get_data()
        self.assertEqual(saved_fixed["name"], "-fps 120")
        self.assertEqual(saved_fixed["tag_type"], "param")
        self.assertEqual(saved_fixed["param_key"], "-fps")
        self.assertEqual(saved_fixed["param_val_mode"], "fixed")
        self.assertEqual(saved_fixed["param_val"], "120")

        # Prompt param tag via unified input
        dlg.edit_name.setText("-score ?")
        dlg._save_and_accept()
        saved_prompt = dlg.get_data()
        self.assertEqual(saved_prompt["name"], "-score ?")
        self.assertEqual(saved_prompt["tag_type"], "param")
        self.assertEqual(saved_prompt["param_key"], "-score")
        self.assertEqual(saved_prompt["param_val_mode"], "prompt")
        self.assertEqual(saved_prompt["param_val"], "")

    def test_tooltip_theme_contrast(self):
        from theme_manager import ThemeManager
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPalette

        # 1. Light Mode Tooltip
        light_style = ThemeManager.get_main_style("light")
        self.assertIn("QToolTip", light_style)
        self.assertIn("background-color: #ffffff", light_style)
        self.assertIn("color: #18181b", light_style)

        ThemeManager.apply_theme_to_app("light")
        pal_light = QApplication.instance().palette()
        self.assertEqual(pal_light.color(QPalette.ColorRole.ToolTipBase).name().lower(), "#ffffff")
        self.assertEqual(pal_light.color(QPalette.ColorRole.ToolTipText).name().lower(), "#18181b")

        # 2. Dark Mode Tooltip
        dark_style = ThemeManager.get_main_style("dark")
        self.assertIn("QToolTip", dark_style)
        self.assertIn("background-color: #26262a", dark_style)
        self.assertIn("color: #ededed", dark_style)

        ThemeManager.apply_theme_to_app("dark")
        pal_dark = QApplication.instance().palette()
        self.assertEqual(pal_dark.color(QPalette.ColorRole.ToolTipBase).name().lower(), "#26262a")
        self.assertEqual(pal_dark.color(QPalette.ColorRole.ToolTipText).name().lower(), "#ededed")

    def test_config_persistence_across_sessions(self):
        from PyQt6.QtGui import QCloseEvent
        from config_manager import load_config, save_config

        # 1. Modify various properties
        self.win.resize(520, 480)
        self.win.move(150, 200)
        self.win.config["always_on_top"] = True
        self.win.config["theme"] = "light"
        self.win.config["position"] = "prefix"
        self.win.config["style"] = "separate"
        self.win.config["button_height"] = 42

        # 2. Simulate close event
        ev = QCloseEvent()
        self.win.closeEvent(ev)

        # 3. Verify on disk config
        saved_cfg = load_config(self.config_file)
        self.assertEqual(saved_cfg.get("window_width"), 520)
        self.assertEqual(saved_cfg.get("window_height"), 480)
        self.assertEqual(saved_cfg.get("window_x"), 150)
        self.assertEqual(saved_cfg.get("window_y"), 200)
        self.assertEqual(saved_cfg.get("always_on_top"), True)
        self.assertEqual(saved_cfg.get("theme"), "light")
        self.assertEqual(saved_cfg.get("position"), "prefix")
        self.assertEqual(saved_cfg.get("style"), "separate")
        self.assertEqual(saved_cfg.get("button_height"), 42)
        self.assertTrue(len(saved_cfg.get("groups", [])) > 0)

    def test_tag_reorder_within_same_group(self):
        # Setup group with 3 tags: T1, T2, T3
        self.win.config["groups"] = [
            {
                "id": "g1",
                "name": "그룹 1",
                "collapsed": False,
                "buttons": [
                    {"id": "t1", "name": "태그1", "label": "태그1", "tag_text": "태그1"},
                    {"id": "t2", "name": "태그2", "label": "태그2", "tag_text": "태그2"},
                    {"id": "t3", "name": "태그3", "label": "태그3", "tag_text": "태그3"},
                ]
            }
        ]
        self.win._refresh_groups()

        # Reorder: move t3 before t1 -> [t3, t1, t2]
        self.win._on_tag_reorder(source_tag_id="t3", target_tag_id="t1", drop_pos="before")
        btn_ids = [b["id"] for b in self.win.config["groups"][0]["buttons"]]
        self.assertEqual(btn_ids, ["t3", "t1", "t2"])

        # Reorder: move t3 after t2 -> [t1, t2, t3]
        self.win._on_tag_reorder(source_tag_id="t3", target_tag_id="t2", drop_pos="after")
        btn_ids = [b["id"] for b in self.win.config["groups"][0]["buttons"]]
        self.assertEqual(btn_ids, ["t1", "t2", "t3"])

    def test_tag_move_to_different_group(self):
        self.win.config["groups"] = [
            {
                "id": "g1",
                "name": "그룹 1",
                "collapsed": False,
                "buttons": [
                    {"id": "t1", "name": "태그1", "label": "태그1", "tag_text": "태그1"},
                ]
            },
            {
                "id": "g2",
                "name": "그룹 2",
                "collapsed": False,
                "buttons": [
                    {"id": "t2", "name": "태그2", "label": "태그2", "tag_text": "태그2"},
                ]
            }
        ]
        self.win._refresh_groups()

        # Move t1 into g2 via _on_tag_moved_to_group
        self.win._on_tag_moved_to_group(source_tag_id="t1", target_group_id="g2")
        g1_ids = [b["id"] for b in self.win.config["groups"][0]["buttons"]]
        g2_ids = [b["id"] for b in self.win.config["groups"][1]["buttons"]]
        self.assertEqual(g1_ids, [])
        self.assertEqual(g2_ids, ["t2", "t1"])

        # Move t1 back to g1 before t2? Move t2 before t1 in g2 first:
        self.win._on_tag_reorder(source_tag_id="t2", target_tag_id="t1", drop_pos="after")
        g2_ids = [b["id"] for b in self.win.config["groups"][1]["buttons"]]
        self.assertEqual(g2_ids, ["t1", "t2"])

    def test_group_reorder(self):
        self.win.config["groups"] = [
            {"id": "g1", "name": "그룹 1", "buttons": []},
            {"id": "g2", "name": "그룹 2", "buttons": []},
            {"id": "g3", "name": "그룹 3", "buttons": []},
        ]
        self.win._refresh_groups()

        # Move g3 before g1 -> [g3, g1, g2]
        self.win._on_group_reorder(source_group_id="g3", target_group_id="g1", drop_pos="before")
        group_ids = [g["id"] for g in self.win.config["groups"]]
        self.assertEqual(group_ids, ["g3", "g1", "g2"])

        # Move g3 after g2 -> [g1, g2, g3]
        self.win._on_group_reorder(source_group_id="g3", target_group_id="g2", drop_pos="after")
        group_ids = [g["id"] for g in self.win.config["groups"]]
        self.assertEqual(group_ids, ["g1", "g2", "g3"])

    def test_titlebar_theme_safe_call(self):
        from theme_manager import ThemeManager
        # Ensure apply_titlebar_theme executes safely without raising exceptions
        ThemeManager.apply_titlebar_theme(self.win, "dark")
        ThemeManager.apply_titlebar_theme(self.win, "light")

    def test_group_dialog_theme_and_data(self):
        from dialog_utils import GroupDialog, ThemedPromptDialog
        dlg_dark = GroupDialog(title="그룹 이름 변경", initial_name="기존그룹", effective_theme="dark")
        self.assertEqual(dlg_dark.edit_name.text(), "기존그룹")
        self.assertEqual(dlg_dark.get_group_name(), "기존그룹")
        dlg_dark.edit_name.setText("새로운그룹")
        dlg_dark._save_and_accept()
        self.assertEqual(dlg_dark.get_group_name(), "새로운그룹")

        prompt_light = ThemedPromptDialog(title="속성값 입력", label_text="값:", initial_text="60", effective_theme="light")
        self.assertEqual(prompt_light.get_text(), "60")
        prompt_light.edit_text.setText("120")
        prompt_light._save_and_accept()
        self.assertEqual(prompt_light.get_text(), "120")

    def test_multi_file_batch_workflow(self):
        f1 = os.path.join(self.temp_dir.name, "clip1 [여행].mp4")
        f2 = os.path.join(self.temp_dir.name, "clip2.mp4")
        for p in (f1, f2):
            with open(p, "w") as f:
                f.write("data")

        self.win.config["position"] = "suffix"
        self.win.config["style"] = "merged"

        # 1. Load multiple files into active editing mode
        self.win._set_active_files([f1, f2])
        self.assertEqual(len(self.win.active_file_paths), 2)

        btn_travel = next(b for b in self.win.all_tag_buttons if b.data.get("name") == "여행")
        btn_4k = next(b for b in self.win.all_tag_buttons if b.data.get("name") == "4K")

        # '여행' is on f1 only -> partial ("◐ 여행"); '4K' is on neither -> off
        self.assertEqual(btn_travel.tag_state, "partial")
        self.assertEqual(btn_travel.text(), "◐ 여행")
        self.assertEqual(btn_4k.tag_state, "off")

        # 2. Click '여행' (partial) -> adds '여행' to f2 so all files have '여행' (state becomes 'on')
        self.win._on_tag_button_clicked(btn_travel)
        f2_tagged = os.path.join(self.temp_dir.name, "clip2 [여행].mp4")
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2_tagged))
        self.assertEqual(btn_travel.tag_state, "on")
        self.assertEqual(btn_travel.text(), "✓ 여행")

        # 3. Click '여행' again (on) -> removes '여행' from both files (state becomes 'off')
        self.win._on_tag_button_clicked(btn_travel)
        f1_untagged = os.path.join(self.temp_dir.name, "clip1.mp4")
        self.assertTrue(os.path.exists(f1_untagged))
        self.assertTrue(os.path.exists(f2))
        self.assertEqual(btn_travel.tag_state, "off")

        # 4. Undo -> restores '여행' to both files and keeps both active
        self.win.undo_last_action()
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2_tagged))
        self.assertEqual(len(self.win.active_file_paths), 2)
        self.assertEqual(btn_travel.tag_state, "on")

    def test_tag_button_outline_style_on_file_drop(self):
        """Verifies that unapplied tags display their tag color as border outline when files are active."""
        test_file = os.path.join(self.temp_dir.name, "doc.txt")
        with open(test_file, "w") as f:
            f.write("text")

        self.win.config["theme"] = "light"
        self.win._apply_theme()
        self.win._set_active_file(test_file)

        btn_travel = self.win.all_tag_buttons[0]
        self.assertEqual(btn_travel.tag_state, "off")
        style = btn_travel.styleSheet().lower()
        # Border should be solid outline and background should be clean white in light mode
        self.assertIn("border: 2px solid", style)
        self.assertIn("#ffffff", style)

    def test_icon_factory_rendering(self):
        """Verifies that all modern vector icons render properly as valid QIcons with HiDPI multi-scale support."""
        import icon_factory
        for name in icon_factory.SVG_ICONS.keys():
            icon_dark = icon_factory.get_icon(name, theme="dark", size=16)
            icon_light = icon_factory.get_icon(name, theme="light", size=16)
            self.assertFalse(icon_dark.isNull(), f"Failed rendering dark icon: {name}")
            self.assertFalse(icon_light.isNull(), f"Failed rendering light icon: {name}")
            # Ensure multi-scale pixmaps are attached for HiDPI
            self.assertTrue(len(icon_dark.availableSizes()) >= 5, f"Missing HiDPI scales for {name}")

        # Check get_pixmap HiDPI devicePixelRatio
        pix = icon_factory.get_pixmap("file", size=16, dpr=2.0)
        self.assertEqual(pix.devicePixelRatio(), 2.0)
        self.assertEqual(pix.width(), 32)

    def test_config_init_missing_self_healing(self):
        """Verifies that if config.init.json is absent, load_default_config recreates it automatically."""
        import config_manager
        with tempfile.TemporaryDirectory() as td:
            missing_init = os.path.join(td, "non_existent_config.init.json")
            self.assertFalse(os.path.exists(missing_init))
            cfg = config_manager.load_default_config(init_path=missing_init)
            self.assertTrue(os.path.exists(missing_init), "config.init.json should be recreated automatically")
            self.assertTrue(len(cfg.get("groups", [])) >= 2)

    def test_context_menus_and_tag_sizing(self):
        """Verifies context menu removal on window, group context menu capabilities, and snug tag sizing."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QFontMetrics
        from tag_button import TagButton

        # 1. Window context menus removed
        self.assertEqual(self.win.contextMenuPolicy(), Qt.ContextMenuPolicy.NoContextMenu)
        self.assertEqual(self.win.scroll_area.contextMenuPolicy(), Qt.ContextMenuPolicy.NoContextMenu)
        self.assertEqual(self.win.groups_container.contextMenuPolicy(), Qt.ContextMenuPolicy.NoContextMenu)
        self.assertFalse(hasattr(self.win, "_show_window_context_menu"))

        # 2. Tag sizing: 1-2 char tags fit snugly without old 55px hard minimum
        b1 = TagButton({"name": "1"}, fixed_height=38)
        b2 = TagButton({"name": "4K"}, fixed_height=38)
        self.assertLess(b1.width(), 55)
        self.assertLess(b2.width(), 55)

        # 3. Long tag sizing: no clipping
        long_name = "매우길고긴동영상태그이름테스트2026하이라이트"
        b_long = TagButton({"name": long_name}, fixed_height=38)
        calc_f = QFont(b_long.font())
        calc_f.setPixelSize(13)
        calc_f.setWeight(QFont.Weight.Bold)
        fm = QFontMetrics(calc_f)
        adv = fm.horizontalAdvance(long_name)
        # Button width must provide enough space for bold text + padding + border
        self.assertGreaterEqual(b_long.width(), adv + 16)

    def test_hamburger_menu_and_dialog_titles(self):
        """Verifies top action bar is simplified to Add Group + Hamburger menu, and dialogs have simplified titles."""
        from settings_dialog import SettingsDialog
        from dialog_utils import HelpDialog

        # 1. Top action bar contains only add group and hamburger menu
        self.assertTrue(hasattr(self.win, "btn_add_group"))
        self.assertTrue(hasattr(self.win, "btn_menu"))
        self.assertFalse(hasattr(self.win, "btn_undo"))
        self.assertFalse(hasattr(self.win, "btn_pin"))
        self.assertFalse(hasattr(self.win, "btn_settings"))
        self.assertFalse(hasattr(self.win, "btn_help"))

        # 2. Dialog titles
        settings_dlg = SettingsDialog(self.win.config, effective_theme="dark", parent=self.win)
        self.assertEqual(settings_dlg.windowTitle(), "환경 설정")

        help_dlg = HelpDialog(effective_theme="dark", parent=self.win)
        self.assertEqual(help_dlg.windowTitle(), "도움말")

        # 3. Clean button properties (no label or tag_text)
        for g in self.win.config.get("groups", []):
            for b in g.get("buttons", []):
                self.assertNotIn("label", b)
                self.assertNotIn("tag_text", b)
                self.assertIn("name", b)


if __name__ == "__main__":
    unittest.main()

