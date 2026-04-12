import json
import tempfile
import unittest
from pathlib import Path

from app.pine_app import create_project, package_hint, status


class PineAppTests(unittest.TestCase):
    def test_create_project_with_rpi5_target(self):
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "pine-lite"
            config_path = create_project("pine-lite", "rpi5", project_root)

            self.assertTrue(config_path.exists())
            payload = json.loads(config_path.read_text())
            self.assertEqual(payload["target"], "rpi5")

    def test_status_contains_roadmap(self):
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "pine-lite"
            config_path = create_project("pine-lite", "desktop", project_root)
            output = status(config_path)
            self.assertIn("Roadmap", output)
            self.assertIn("rpi5", output)

    def test_package_hint_formats(self):
        with tempfile.TemporaryDirectory() as td:
            project_root = Path(td) / "pine-lite"
            config_path = create_project("pine-lite", "desktop", project_root)

            self.assertIn(".exe", package_hint(config_path, "exe"))
            self.assertIn(".deb", package_hint(config_path, "deb"))


if __name__ == "__main__":
    unittest.main()
