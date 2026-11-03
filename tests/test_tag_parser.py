import unittest

from src.core.tag_parser import (
    get_tag_name,
    is_tag_in_tags,
    parse_bracket_content,
    parse_tag_definition,
)


class TestTagParser(unittest.TestCase):
    def test_get_tag_name_variants(self):
        self.assertEqual(get_tag_name({"name": "여행"}), "여행")
        self.assertEqual(get_tag_name({"name": "[4K]"}), "4K")
        self.assertEqual(get_tag_name({"tag_text": "[-fps 60]"}), "-fps 60")
        self.assertEqual(get_tag_name({"label": "드론"}), "드론")
        self.assertEqual(get_tag_name({}, default="기본"), "기본")

    def test_parse_tag_definition_normal(self):
        spec = parse_tag_definition(" [하이라이트] ")
        self.assertEqual(spec, {"name": "하이라이트", "tag_type": "normal"})

    def test_parse_tag_definition_fixed_param(self):
        spec = parse_tag_definition("[-fps 120]")
        self.assertEqual(spec["name"], "-fps 120")
        self.assertEqual(spec["tag_type"], "param")
        self.assertEqual(spec["param_key"], "-fps")
        self.assertEqual(spec["param_val_mode"], "fixed")
        self.assertEqual(spec["param_val"], "120")

    def test_parse_tag_definition_bare_param_key(self):
        spec = parse_tag_definition("-hdr")
        self.assertEqual(spec["name"], "-hdr")
        self.assertEqual(spec["tag_type"], "param")
        self.assertEqual(spec["param_key"], "-hdr")
        self.assertEqual(spec["param_val_mode"], "fixed")
        self.assertEqual(spec["param_val"], "")

    def test_parse_tag_definition_prompt_param(self):
        spec = parse_tag_definition("-score ?")
        self.assertEqual(spec["name"], "-score ?")
        self.assertEqual(spec["tag_type"], "param")
        self.assertEqual(spec["param_key"], "-score")
        self.assertEqual(spec["param_val_mode"], "prompt")
        self.assertEqual(spec["param_val"], "")

        fallback_spec = parse_tag_definition("-rating", fallback_mode="prompt")
        self.assertEqual(fallback_spec["name"], "-rating ?")
        self.assertEqual(fallback_spec["param_val_mode"], "prompt")

    def test_parse_bracket_content_quotes_and_params(self):
        self.assertEqual(parse_bracket_content("   "), [])
        parsed = parse_bracket_content('taga tagb -fps 60 -author "John Doe" \'single tag\'')
        self.assertEqual(parsed, ["taga", "tagb", "-fps 60", '-author "John Doe"', "single tag"])

    def test_is_tag_in_tags_normal_and_param(self):
        existing = ["여행", "-fps 60", "-score 9"]
        self.assertTrue(is_tag_in_tags(existing, {"name": "여행"}))
        self.assertFalse(is_tag_in_tags(existing, {"name": "4K"}))

        # Fixed param matches exact value only
        self.assertTrue(is_tag_in_tags(existing, {"name": "-fps 60"}))
        self.assertFalse(is_tag_in_tags(existing, {"name": "-fps 30"}))

        # Prompt param matches any value with same -key
        self.assertTrue(is_tag_in_tags(existing, {"name": "-score ?"}))
        self.assertFalse(is_tag_in_tags(existing, {"name": "-take ?"}))


if __name__ == "__main__":
    unittest.main()

