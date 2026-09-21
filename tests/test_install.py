import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_install_contains_only_self_contained_resources_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "keep.txt").write_text("existing user change")
            result = installer.install(project)
            target = Path(result["installed"])
            actual = {str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()}
            self.assertEqual(actual, set(installer.FILES))
            for relative in installer.FILES:
                self.assertEqual((target / relative).read_bytes(), (ROOT / relative).read_bytes())
            with self.assertRaises(ValueError):
                installer.install(project)
            self.assertEqual((project / "keep.txt").read_text(), "existing user change")
            self.assertFalse(result["runtime_loading_verified"])

    def test_symlink_ancestor_cannot_write_outside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            outside = base / "outside"
            project.mkdir()
            outside.mkdir()
            (project / ".agents").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(project)
            self.assertEqual(list(outside.iterdir()), [])

    def test_missing_source_does_not_leave_partial_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project, source = base / "project", base / "source"
            project.mkdir()
            source.mkdir()
            with self.assertRaises(ValueError):
                installer.install(project, source)
            self.assertEqual(list(project.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
