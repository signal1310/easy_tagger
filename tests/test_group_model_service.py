import os
import tempfile
import unittest

from src.services.group_model_service import GroupModelService
from src.services.tag_detection_service import detect_and_register_unknown_tags


class TestGroupModelService(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "groups": [
                {
                    "id": "g1",
                    "name": "그룹 1",
                    "collapsed": False,
                    "buttons": [
                        {"id": "t1", "name": "태그1"},
                        {"id": "t2", "name": "태그2"},
                        {"id": "t3", "name": "태그3"},
                    ],
                },
                {
                    "id": "g2",
                    "name": "그룹 2",
                    "collapsed": False,
                    "buttons": [{"id": "t4", "name": "태그4"}],
                },
            ]
        }

    def test_group_crud_and_collapse(self):
        new_g = GroupModelService.add_group(self.cfg, "그룹 3")
        self.assertEqual(len(self.cfg["groups"]), 3)
        self.assertTrue(GroupModelService.rename_group(self.cfg, new_g["id"], "그룹 3 수정"))
        self.assertFalse(GroupModelService.rename_group(self.cfg, "invalid", "이름"))
        self.assertFalse(GroupModelService.rename_group(self.cfg, new_g["id"], ""))

        self.assertTrue(GroupModelService.set_group_collapsed(self.cfg, "g1", True))
        self.assertTrue(self.cfg["groups"][0]["collapsed"])
        self.assertFalse(GroupModelService.set_group_collapsed(self.cfg, "missing", True))

        deleted_name = GroupModelService.delete_group(self.cfg, new_g["id"])
        self.assertEqual(deleted_name, "그룹 3 수정")
        self.assertIsNone(GroupModelService.delete_group(self.cfg, "missing"))

    def test_tag_crud_and_duplicate(self):
        self.assertEqual(GroupModelService.add_tag(self.cfg, "g2", {"id": "t5", "name": "새태그"}), "그룹 2")
        self.assertIsNone(GroupModelService.add_tag(self.cfg, "missing", {"id": "t6", "name": "무시"}))

        self.assertTrue(GroupModelService.update_tag(self.cfg, {"id": "t5", "name": "수정태그"}))
        self.assertFalse(GroupModelService.update_tag(self.cfg, {"id": "missing", "name": "무시"}))

        dup = GroupModelService.duplicate_tag(self.cfg, {"id": "t1", "name": "태그1", "label": "구속성"})
        self.assertIsNotNone(dup)
        self.assertEqual(dup["name"], "태그1 (복사)")
        self.assertNotIn("label", dup)
        self.assertEqual(self.cfg["groups"][0]["buttons"][1]["id"], dup["id"])

        GroupModelService.delete_tag(self.cfg, dup["id"])
        self.assertEqual([b["id"] for b in self.cfg["groups"][0]["buttons"]], ["t1", "t2", "t3"])

    def test_tag_and_group_reordering(self):
        # Reorder within same group
        GroupModelService.reorder_tag(self.cfg, "t3", "t1", "before")
        self.assertEqual([b["id"] for b in self.cfg["groups"][0]["buttons"]], ["t3", "t1", "t2"])
        GroupModelService.reorder_tag(self.cfg, "t3", "t2", "after")
        self.assertEqual([b["id"] for b in self.cfg["groups"][0]["buttons"]], ["t1", "t2", "t3"])
        self.assertIsNone(GroupModelService.reorder_tag(self.cfg, "t1", "t1", "before"))

        # Move tag across groups
        moved = GroupModelService.move_tag_to_group(self.cfg, "t1", "g2")
        self.assertEqual(moved, ("태그1", "그룹 2"))
        self.assertEqual([b["id"] for b in self.cfg["groups"][1]["buttons"]], ["t4", "t1"])
        self.assertIsNone(GroupModelService.move_tag_to_group(self.cfg, "t1", "g2"))  # same group no-op

        # Reorder groups
        GroupModelService.reorder_group(self.cfg, "g2", "g1", "before")
        self.assertEqual([g["id"] for g in self.cfg["groups"]], ["g2", "g1"])
        GroupModelService.reorder_group(self.cfg, "g2", "g1", "after")
        self.assertEqual([g["id"] for g in self.cfg["groups"]], ["g1", "g2"])

    def test_detect_unknown_tags_service(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "sample [태그2 미등록A -fps 60].mp4")
            with open(p, "w", encoding="utf-8") as f:
                f.write("x")
            discovered = detect_and_register_unknown_tags(self.cfg, [p])
            self.assertEqual(discovered, ["미등록A", "-fps 60"])
            self.assertEqual(self.cfg["groups"][0]["id"], "group-detected")
            # Second call should detect nothing new
            self.assertEqual(detect_and_register_unknown_tags(self.cfg, [p]), [])


if __name__ == "__main__":
    unittest.main()

