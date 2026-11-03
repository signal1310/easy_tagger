import unittest

from src.core.filename_builder import (
    apply_tag_to_tags_list,
    assemble_filename,
    extract_tags_and_base,
    remove_tag_from_tags_list,
)


class TestFilenameBuilder(unittest.TestCase):
    def test_extract_merged_tags(self):
        base, tags = extract_tags_and_base("video_sample [taga tagb -fps 60]")
        self.assertEqual(base, "video_sample")
        self.assertEqual(tags, ["taga", "tagb", "-fps 60"])

    def test_extract_separate_tags_and_dedup(self):
        base, tags = extract_tags_and_base("[taga] [tagb] [taga] [-score 5] my_movie")
        self.assertEqual(base, "my_movie")
        self.assertEqual(tags, ["taga", "tagb", "-score 5"])

    def test_extract_only_tags_falls_back_to_file(self):
        base, tags = extract_tags_and_base(" [여행] _ - [4K] ")
        self.assertEqual(base, "file")
        self.assertEqual(tags, ["여행", "4K"])

    def test_assemble_all_positions_and_styles(self):
        self.assertEqual(
            assemble_filename("video", ["taga", "tagb", "-fps 60"], position="suffix", style="merged"),
            "video [taga tagb -fps 60]",
        )
        self.assertEqual(
            assemble_filename("video", ["taga", "tagb", "-fps 60"], position="suffix", style="separate"),
            "video [taga] [tagb] [-fps 60]",
        )
        self.assertEqual(
            assemble_filename("video", ["taga", "tagb"], position="prefix", style="merged"),
            "[taga tagb] video",
        )
        self.assertEqual(
            assemble_filename("video", ["taga", "tagb"], position="prefix", style="separate"),
            "[taga] [tagb] video",
        )

    def test_assemble_empty_or_blank_tags(self):
        self.assertEqual(assemble_filename("clip", []), "clip")
        self.assertEqual(assemble_filename("clip", ["   ", ""]), "clip")

    def test_apply_tag_normal_and_param(self):
        tags = ["travel", "beach"]
        self.assertEqual(apply_tag_to_tags_list(tags, "beach"), ["travel", "beach"])
        self.assertEqual(apply_tag_to_tags_list(tags, "  "), ["travel", "beach"])

        tags_with_param = ["travel", "-fps 30", "drone"]
        self.assertEqual(
            apply_tag_to_tags_list(tags_with_param, "-fps 60"),
            ["travel", "-fps 60", "drone"],
        )
        self.assertEqual(
            apply_tag_to_tags_list(["travel", "drone"], "[-fps 60]"),
            ["travel", "drone", "-fps 60"],
        )

    def test_remove_tag_normal_and_param(self):
        tags = ["travel", "-fps 60", "beach"]
        self.assertEqual(remove_tag_from_tags_list(tags, "travel"), ["-fps 60", "beach"])
        self.assertEqual(remove_tag_from_tags_list(tags, "[beach]"), ["travel", "-fps 60"])
        self.assertEqual(remove_tag_from_tags_list(tags, "-fps"), ["travel", "beach"])
        self.assertEqual(remove_tag_from_tags_list(tags, "nonexistent"), tags)


if __name__ == "__main__":
    unittest.main()

