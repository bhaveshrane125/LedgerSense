import unittest
from dataclasses import replace

from generator.config import ConfigError, validate_config
from generator.models import GeneratorConfig


class ConfigTests(unittest.TestCase):
    def test_rejects_zero_pdf_count(self):
        with self.assertRaises(ConfigError):
            validate_config(replace(GeneratorConfig(), pdf_count=0))

    def test_rejects_bad_scenario_weights(self):
        with self.assertRaises(ConfigError):
            validate_config(replace(GeneratorConfig(), scenario_weights={"CLEAN": 0.8}))

    def test_rejects_bad_line_item_range(self):
        with self.assertRaises(ConfigError):
            validate_config(replace(GeneratorConfig(), min_line_items=5, max_line_items=1))


if __name__ == "__main__":
    unittest.main()
