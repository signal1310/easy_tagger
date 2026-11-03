import os
import tempfile
import unittest

from src.services.file_rename_service import (
    apply_tag_batch,
    compute_button_tag_state,
    extract_files_tags,
    normalize_existing_paths,
    remove_tag_batch,
)
from src.services.undo_service import UndoService


class TestFileAndUndoServices(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def _touch(self, name: str) -> str:
        p = os.path.join(self.root, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write("data")
        return p

    def test_normalize_existing_paths_and_tag_states(self):
        f1 = self._touch("clip1 [여행].mp4")
        f2 = self._touch("clip2.mp4")
        missing = os.path.join(self.root, "missing.mp4")

        valid = normalize_existing_paths([f1, "", f1.upper(), f2, missing])
        self.assertEqual(len(valid), 2)

        tags_list = extract_files_tags(valid)
        self.assertEqual(compute_button_tag_state([], {"name": "여행"}), "none")
        self.assertEqual(compute_button_tag_state(tags_list, {"name": "여행"}), "partial")
        self.assertEqual(compute_button_tag_state(tags_list, {"name": "4K"}), "off")
        self.assertEqual(compute_button_tag_state([["여행"], ["여행", "4K"]], {"name": "여행"}), "on")

    def test_apply_tag_batch_success_idempotent_missing_and_collision(self):
        f1 = self._touch("video.mp4")
        missing = os.path.join(self.root, "no_such_file.mp4")

        res1 = apply_tag_batch([f1, missing], "4K", position="suffix", style="merged")
        expected = os.path.join(self.root, "video [4K].mp4")
        self.assertEqual(len(res1.rename_batch), 1)
        self.assertTrue(os.path.exists(expected))
        self.assertEqual(len(res1.errors), 1)  # missing file recorded

        # Idempotent re-apply
        res_same = apply_tag_batch([expected.replace("\\", "/")], "4K")
        self.assertEqual(res_same.already_tagged_count, 1)
        self.assertEqual(len(res_same.errors), 0)

        # Filename collision when applying tag
        f_plain = self._touch("video.mp4")  # now both 'video.mp4' and 'video [4K].mp4' exist!
        res_collision = apply_tag_batch([f_plain], "4K")
        self.assertEqual(len(res_collision.rename_batch), 0)
        self.assertEqual(len(res_collision.errors), 1)
        self.assertIn("이미 존재하는 파일명", res_collision.errors[0])

    def test_remove_tag_batch_and_collision(self):
        f_tagged = self._touch("doc [완료].txt")
        self._touch("doc.txt")  # collision target!

        res_col = remove_tag_batch([f_tagged], "완료")
        self.assertEqual(len(res_col.rename_batch), 0)
        self.assertEqual(len(res_col.errors), 1)

        os.remove(os.path.join(self.root, "doc.txt"))
        res_ok = remove_tag_batch([f_tagged], "완료")
        self.assertEqual(len(res_ok.rename_batch), 1)
        self.assertTrue(os.path.exists(os.path.join(self.root, "doc.txt")))

    def test_undo_service_lifecycle_and_edge_cases(self):
        undo = UndoService()
        self.assertFalse(undo.can_undo)
        self.assertIsNone(undo.undo_last())

        orig = self._touch("a.mp4")
        res = apply_tag_batch([orig], "여행")
        undo.push(res.rename_batch)
        self.assertTrue(undo.can_undo)
        self.assertEqual(undo.count, 1)

        undo_res = undo.undo_last()
        self.assertIsNotNone(undo_res)
        self.assertEqual(undo_res.reverted_count, 1)
        self.assertTrue(os.path.exists(orig))
        self.assertFalse(undo.can_undo)

        # Undo when target file was deleted externally
        undo.push([(orig, os.path.join(self.root, "deleted_target.mp4"))])
        err_res = undo.undo_last()
        self.assertEqual(err_res.reverted_count, 0)
        self.assertEqual(len(err_res.errors), 1)

        # Undo collision when old_path already exists alongside new_path
        cur_tagged = self._touch("b [여행].mp4")
        old_plain = self._touch("b.mp4")
        undo.push([(old_plain, cur_tagged)])
        col_res = undo.undo_last()
        self.assertEqual(col_res.reverted_count, 0)
        self.assertIn("이미 존재함", col_res.errors[0])


if __name__ == "__main__":
    unittest.main()
