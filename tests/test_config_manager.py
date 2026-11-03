import json
import os
import tempfile
import unittest

from src.core.config_manager import (
    is_ephemeral_group,
    load_config,
    load_default_config,
    normalize_tag_data,
    save_config,
)
from src.core.paths import BASE_DIR, get_resource_path


class TestConfigManager(unittest.TestCase):
    def test_paths_resolution(self):
        icon_path = get_resource_path(os.path.join("assets", "icon.png"))
        self.assertTrue(os.path.exists(icon_path))
        self.assertTrue(os.path.exists(os.path.join(BASE_DIR, "main.py")))

    def test_load_default_config_builtin(self):
        cfg = load_default_config()
        self.assertIn("groups", cfg)
        self.assertGreaterEqual(len(cfg["groups"]), 2)
        self.assertIn("theme", cfg)

    def test_config_json_created_from_builtin_defaults_when_missing(self):
        with tempfile.TemporaryDirectory() as td:
            missing_cfg = os.path.join(td, "config.json")
            self.assertFalse(os.path.exists(missing_cfg))
            loaded = load_config(missing_cfg)
            self.assertTrue(os.path.exists(missing_cfg))
            self.assertGreaterEqual(len(loaded.get("groups", [])), 2)
            self.assertEqual(loaded.get("theme"), "system")

    def test_normalize_tag_data_strips_redundant_keys(self):
        legacy = {
            "id": "b1",
            "label": "구버전 설명 라벨",
            "tag_text": "[여행]",
            "param_key": "-old",
            "param_val_mode": "fixed",
            "param_val": "1",
        }
        norm = normalize_tag_data(legacy)
        self.assertEqual(norm["name"], "여행")
        self.assertEqual(norm["description"], "구버전 설명 라벨")
        self.assertNotIn("label", norm)
        self.assertNotIn("tag_text", norm)
        self.assertNotIn("param_key", norm)

    def test_ephemeral_group_filtering_and_legacy_migration(self):
        self.assertTrue(is_ephemeral_group({"id": "group-detected", "name": "아무이름"}))
        self.assertTrue(is_ephemeral_group({"id": "g-temp", "name": "감지된 태그"}))
        self.assertFalse(is_ephemeral_group({"id": "g-normal", "name": "기본 태그"}))

        with tempfile.TemporaryDirectory() as td:
            cfg_path = os.path.join(td, "config.json")
            # 1. Legacy flat buttons format migration
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump({"buttons": [{"id": "b1", "label": "테스트", "tag_text": "테스트"}]}, f)

            loaded = load_config(cfg_path)
            self.assertEqual(loaded["groups"][0]["name"], "기본 그룹")
            self.assertEqual(loaded["groups"][0]["buttons"][0]["name"], "테스트")
            self.assertIn("theme", loaded)

            # 2. Ephemeral group never persisted by save_config
            loaded["groups"].insert(0, {"id": "group-detected", "name": "감지된 태그", "buttons": []})
            save_config(loaded, cfg_path)
            reloaded = load_config(cfg_path)
            self.assertFalse(any(is_ephemeral_group(g) for g in reloaded["groups"]))

            # 3. Corrupted config.json falls back cleanly
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write("not valid json")
            fallback = load_config(cfg_path)
            self.assertGreaterEqual(len(fallback.get("groups", [])), 2)


if __name__ == "__main__":
    unittest.main()

