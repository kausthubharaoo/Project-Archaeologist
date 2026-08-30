"""
Unit tests for RelationshipAnalyzer.

Zero-dependency tests using Python's built-in unittest module.
"""

import os
import tempfile
import unittest

from relationship_analysis import (
    RelationshipAnalyzer,
    analyze_relationships
)


class TestRelationshipAnalyzer(unittest.TestCase):

    def setUp(self):
        """Create a temporary project for testing."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = self.temp_dir.name

        # app.py imports database.py and utils.py
        self._create_file(
            "app.py",
            """
import database
from utils import helper

def main():
    database.connect()
    helper()
"""
        )

        # database.py imports utils.py
        self._create_file(
            "database.py",
            """
import utils

def connect():
    pass
"""
        )

        # utils.py has no internal imports
        self._create_file(
            "utils.py",
            """
def helper():
    pass
"""
        )

        # External library should NOT create a relationship
        self._create_file(
            "external.py",
            """
import os
import json
"""
        )

        # Syntax error file
        self._create_file(
            "broken.py",
            """
def broken(
    print("invalid")
"""
        )

    def tearDown(self):
        """Remove the temporary project."""

        self.temp_dir.cleanup()

    def _create_file(self, filename, content):
        """Create a Python file inside the temporary project."""

        file_path = os.path.join(
            self.project_path,
            filename
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

    # ---------------------------------------------------------
    # TEST FINDING PYTHON FILES
    # ---------------------------------------------------------

    def test_find_python_files(self):
        """Analyzer should find Python files."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        files = analyzer._find_python_files()

        filenames = {
            os.path.basename(file)
            for file in files
        }

        self.assertIn("app.py", filenames)
        self.assertIn("database.py", filenames)
        self.assertIn("utils.py", filenames)
        self.assertIn("external.py", filenames)
        self.assertIn("broken.py", filenames)

    # ---------------------------------------------------------
    # TEST IGNORED DIRECTORIES
    # ---------------------------------------------------------

    def test_ignored_directories(self):
        """Ignored directories should not be analyzed."""

        ignored_dir = os.path.join(
            self.project_path,
            "__pycache__"
        )

        os.makedirs(ignored_dir)

        ignored_file = os.path.join(
            ignored_dir,
            "ignored.py"
        )

        with open(
            ignored_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write("import something")

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        files = analyzer._find_python_files()

        self.assertNotIn(
            ignored_file,
            files
        )

    # ---------------------------------------------------------
    # TEST MODULE MAP
    # ---------------------------------------------------------

    def test_create_module_map(self):
        """Python files should be mapped to module names."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        files = analyzer._find_python_files()

        analyzer._create_module_map(files)

        self.assertIn(
            "app",
            analyzer.module_to_file
        )

        self.assertIn(
            "database",
            analyzer.module_to_file
        )

        self.assertIn(
            "utils",
            analyzer.module_to_file
        )

        self.assertEqual(
            analyzer.module_to_file["app"],
            "app.py"
        )

    # ---------------------------------------------------------
    # TEST IMPORT RESOLUTION
    # ---------------------------------------------------------

    def test_resolve_internal_import(self):
        """Internal imports should resolve to project files."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        files = analyzer._find_python_files()

        analyzer._create_module_map(files)

        result = analyzer._resolve_import(
            "database"
        )

        self.assertEqual(
            result,
            "database.py"
        )

    def test_resolve_unknown_import(self):
        """External or unknown modules should return empty string."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        files = analyzer._find_python_files()

        analyzer._create_module_map(files)

        result = analyzer._resolve_import(
            "non_existing_module"
        )

        self.assertEqual(
            result,
            ""
        )

    # ---------------------------------------------------------
    # TEST RELATIONSHIP ANALYSIS
    # ---------------------------------------------------------

    def test_analyze_relationships(self):
        """Analyzer should detect relationships between files."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        self.assertTrue(
            result["success"]
        )

        self.assertEqual(
            result["files_analyzed"],
            5
        )

        self.assertGreater(
            result["relationships_found"],
            0
        )

    # ---------------------------------------------------------
    # TEST DEPENDENCIES
    # ---------------------------------------------------------

    def test_dependencies(self):
        """Dependencies should correctly identify outgoing relationships."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        dependencies = result["dependencies"]

        self.assertIn(
            "database.py",
            dependencies["app.py"]
        )

        self.assertIn(
            "utils.py",
            dependencies["app.py"]
        )

        self.assertIn(
            "utils.py",
            dependencies["database.py"]
        )

    # ---------------------------------------------------------
    # TEST DEPENDENTS
    # ---------------------------------------------------------

    def test_dependents(self):
        """Dependents should correctly identify incoming relationships."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        dependents = result["dependents"]

        self.assertIn(
            "app.py",
            dependents["database.py"]
        )

        self.assertIn(
            "app.py",
            dependents["utils.py"]
        )

        self.assertIn(
            "database.py",
            dependents["utils.py"]
        )

    # ---------------------------------------------------------
    # TEST EXTERNAL IMPORTS
    # ---------------------------------------------------------

    def test_external_imports_are_ignored(self):
        """Standard-library imports should not create project relationships."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        dependencies = result["dependencies"]

        # external.py imports os and json,
        # but neither exists inside the project.
        self.assertNotIn(
            "external.py",
            dependencies
        )

    # ---------------------------------------------------------
    # TEST MOST CONNECTED FILES
    # ---------------------------------------------------------

    def test_most_connected_files(self):
        """Most connected files should be returned correctly."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        connected = result["most_connected_files"]

        self.assertIsInstance(
            connected,
            list
        )

        self.assertGreater(
            len(connected),
            0
        )

        # app.py should have:
        # outgoing -> database.py, utils.py
        self.assertTrue(
            any(
                item["file"] == "app.py"
                for item in connected
            )
        )

    # ---------------------------------------------------------
    # TEST HOTSPOTS
    # ---------------------------------------------------------

    def test_hotspots(self):
        """Hotspots should contain highly connected files."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        hotspots = result["hotspots"]

        self.assertIsInstance(
            hotspots,
            list
        )

        for hotspot in hotspots:

            self.assertIn(
                "file",
                hotspot
            )

            self.assertIn(
                "total_relationships",
                hotspot
            )

            self.assertIn(
                "reason",
                hotspot
            )

    # ---------------------------------------------------------
    # TEST PARSE ERRORS
    # ---------------------------------------------------------

    def test_parse_errors(self):
        """Invalid Python files should be reported."""

        analyzer = RelationshipAnalyzer(
            self.project_path
        )

        result = analyzer.analyze()

        errors = result["parse_errors"]

        self.assertGreater(
            len(errors),
            0
        )

        broken_files = [
            error["file"]
            for error in errors
        ]

        self.assertIn(
            "broken.py",
            broken_files
        )

    # ---------------------------------------------------------
    # TEST INVALID PATH
    # ---------------------------------------------------------

    def test_invalid_project_path(self):
        """Invalid project path should return a failure result."""

        analyzer = RelationshipAnalyzer(
            os.path.join(
                self.project_path,
                "does_not_exist"
            )
        )

        result = analyzer.analyze()

        self.assertFalse(
            result["success"]
        )

        self.assertEqual(
            result["files_analyzed"],
            0
        )

        self.assertEqual(
            result["relationships_found"],
            0
        )

    # ---------------------------------------------------------
    # TEST FILE INSTEAD OF DIRECTORY
    # ---------------------------------------------------------

    def test_project_path_is_file(self):
        """A file path should return a failure result."""

        file_path = os.path.join(
            self.project_path,
            "single_file.py"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write("print('hello')")

        analyzer = RelationshipAnalyzer(
            file_path
        )

        result = analyzer.analyze()

        self.assertFalse(
            result["success"]
        )

    # ---------------------------------------------------------
    # TEST CONVENIENCE FUNCTION
    # ---------------------------------------------------------

    def test_analyze_relationships_function(self):
        """Convenience function should return analysis results."""

        result = analyze_relationships(
            self.project_path
        )

        self.assertTrue(
            result["success"]
        )

        self.assertGreater(
            result["files_analyzed"],
            0
        )


if __name__ == "__main__":
    unittest.main()
