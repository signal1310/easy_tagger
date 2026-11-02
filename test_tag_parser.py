import unittest
from tag_parser import (
    extract_tags_and_base,
    assemble_filename,
    apply_tag_to_tags_list,
    remove_tag_from_tags_list,
)

class TestTagParser(unittest.TestCase):
    def test_extract_merged_tags(self):
        base, tags = extract_tags_and_base("video_sample [taga tagb -fps 60]")
        self.assertEqual(base, "video_sample")
        self.assertEqual(tags, ["taga", "tagb", "-fps 60"])

    def test_extract_separate_tags(self):
        base, tags = extract_tags_and_base("[taga] [tagb] [-score 5] my_movie")
        self.assertEqual(base, "my_movie")
        self.assertEqual(tags, ["taga", "tagb", "-score 5"])

    def test_assemble_suffix_merged(self):
        result = assemble_filename("video", ["taga", "tagb", "-fps 60"], position="suffix", style="merged")
        self.assertEqual(result, "video [taga tagb -fps 60]")

    def test_assemble_suffix_separate(self):
        result = assemble_filename("video", ["taga", "tagb", "-fps 60"], position="suffix", style="separate")
        self.assertEqual(result, "video [taga] [tagb] [-fps 60]")

    def test_assemble_prefix_merged(self):
        result = assemble_filename("video", ["taga", "tagb"], position="prefix", style="merged")
        self.assertEqual(result, "[taga tagb] video")

    def test_assemble_prefix_separate(self):
        result = assemble_filename("video", ["taga", "tagb"], position="prefix", style="separate")
        self.assertEqual(result, "[taga] [tagb] video")

    def test_apply_normal_tag_no_duplicate(self):
        tags = ["travel", "beach"]
        new_tags = apply_tag_to_tags_list(tags, "beach")
        self.assertEqual(new_tags, ["travel", "beach"])

    def test_apply_param_tag_replaces_existing(self):
        tags = ["travel", "-fps 30", "drone"]
        new_tags = apply_tag_to_tags_list(tags, "-fps 60")
        self.assertEqual(new_tags, ["travel", "-fps 60", "drone"])

    def test_apply_param_tag_adds_if_absent(self):
        tags = ["travel", "drone"]
        new_tags = apply_tag_to_tags_list(tags, "[-fps 60]")
        self.assertEqual(new_tags, ["travel", "drone", "-fps 60"])

    def test_remove_tag(self):
        tags = ["travel", "-fps 60", "beach"]
        rem = remove_tag_from_tags_list(tags, "travel")
        self.assertEqual(rem, ["-fps 60", "beach"])
        rem2 = remove_tag_from_tags_list(tags, "-fps")
        self.assertEqual(rem2, ["travel", "beach"])

if __name__ == '__main__':
    unittest.main()

