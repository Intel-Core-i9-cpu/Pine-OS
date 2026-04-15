
import gzip

import gzip


import gzip



import json
import tempfile
import unittest
from pathlib import Path


from app.pine_app import (
    ProjectConfig,
    create_project,
    create_rpi5_bootkit,
    create_rpi5_image_bundle,
    package_hint,
    status,
)



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

            output_dir = Path(td) / "dist"

            deb_result = package_hint(config_path, "deb", output_dir)
            exe_result = package_hint(config_path, "exe", output_dir)

            self.assertIn(".deb", deb_result)
            self.assertIn(".exe", exe_result)
            self.assertTrue(any(p.suffix == ".deb" for p in output_dir.iterdir()))

    def test_rpi5_image_bundle_created(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = ProjectConfig(name="pine-lite", target="rpi5")
            out = create_rpi5_image_bundle(cfg, Path(td))
            self.assertTrue(out.exists())
            self.assertEqual(out.suffix, ".img")

    def test_rpi5_bootkit_contains_boot_files(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = ProjectConfig(name="pine-lite", target="rpi5")
            out = create_rpi5_bootkit(cfg, Path(td))
            self.assertTrue((out / "boot" / "config.txt").exists())
            self.assertTrue((out / "boot" / "cmdline.txt").exists())
            self.assertTrue((out / "boot" / "initramfs.cpio.gz").exists())

            raw = gzip.decompress((out / "boot" / "initramfs.cpio.gz").read_bytes())
            self.assertTrue(raw.startswith(b"070701"))




            self.assertIn(".exe", package_hint(config_path, "exe"))
            self.assertIn(".deb", package_hint(config_path, "deb"))

if __name__ == "__main__":
    unittest.main()
