import os
import json
import unittest

from src.autodeploy.repo_parser import parse_project


class TestRepoParser(unittest.TestCase):
    def setUp(self):
        self.root = os.path.join(os.path.dirname(__file__), "fixtures", "sample_repo")

    def test_parse_basic(self):
        spec, result = parse_project(self.root)
        self.assertEqual(spec.language, "python")
        self.assertIn("requirements.txt", result.files_found)
        self.assertTrue(result.files_found["requirements.txt"]) 
        self.assertTrue(spec.start_commands)
        self.assertEqual(spec.name, "sample_repo")

    def test_python_version_detection(self):
        spec, _ = parse_project(self.root)
        self.assertTrue(spec.python_required is not None)


if __name__ == "__main__":
    unittest.main()

