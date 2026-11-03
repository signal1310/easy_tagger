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

    def test_extract_hashtags_and_special_words(self):
        # 1. Words containing '#' embedded without boundaries must NOT be treated as tags
        base1, tags1 = extract_tags_and_base("C#_강의")
        self.assertEqual(base1, "C#_강의")
        self.assertEqual(tags1, [])

        base2, tags2 = extract_tags_and_base("C# 강의")
        self.assertEqual(base2, "C# 강의")
        self.assertEqual(tags2, [])

        base3, tags3 = extract_tags_and_base("트랙#1")
        self.assertEqual(base3, "트랙#1")
        self.assertEqual(tags3, [])

        # 2. Standalone hashtag with whitespace boundary IS extracted
        base4, tags4 = extract_tags_and_base("트랙 #1")
        self.assertEqual(base4, "트랙")
        self.assertEqual(tags4, ["1"])

        # 3. Mixed brackets, embedded words, and standalone hashtags
        base5, tags5 = extract_tags_and_base("[2026] C#_강의 #중요 #하이라이트")
        self.assertEqual(base5, "C#_강의")
        self.assertEqual(tags5, ["2026", "중요", "하이라이트"])

    def test_assemble_heterogeneous_tags(self):
        specs = {
            "2026": {"position": "prefix", "format": "bracket"},
            "여행": {"position": "prefix", "format": "hashtag"},
            "1080p": {"position": "suffix", "format": "bracket"},
            "완료": {"position": "suffix", "format": "hashtag"},
        }
        res = assemble_filename("video", ["2026", "여행", "1080p", "완료"], tag_specs=specs)
        self.assertEqual(res, "[2026] #여행 video [1080p] #완료")


if __name__ == "__main__":
    unittest.main()

