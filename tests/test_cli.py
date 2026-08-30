import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from archaeologist.cli import (
    create_parser,
    execute_command,
)
from archaeologist.commands import (
    scan_command,
    analyze_command,
    report_command,
    git_command,
)
from archaeologist.errors import (
    ProjectNotFoundError,
    InvalidProjectError,
)


class TestCLIParser(unittest.TestCase):
    """Tests for the command-line argument parser."""

    def test_help_parser(self):
        parser = create_parser()

        args = parser.parse_args(["scan", "."])

        self.assertEqual(args.command, "scan")
        self.assertEqual(args.path, ".")

    def test_analyze_parser(self):
        parser = create_parser()

        args = parser.parse_args(["analyze", "."])

        self.assertEqual(args.command, "analyze")
        self.assertEqual(args.path, ".")

    def test_git_parser(self):
        parser = create_parser()

        args = parser.parse_args(["git", "."])

        self.assertEqual(args.command, "git")
        self.assertEqual(args.path, ".")

    def test_report_parser(self):
        parser = create_parser()

        args = parser.parse_args(
            ["report", ".", "--format", "json"]
        )

        self.assertEqual(args.command, "report")
        self.assertEqual(args.path, ".")
        self.assertEqual(args.format, "json")


class TestProjectValidation(unittest.TestCase):
    """Tests for project path validation."""

    def test_invalid_project_path(self):
        invalid_path = "this/path/does/not/exist"

        with self.assertRaises(ProjectNotFoundError):
            scan_command(invalid_path)

    def test_file_instead_of_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            test_file = temp_path / "example.txt"
            test_file.write_text(
                "hello",
                encoding="utf-8"
            )

            with self.assertRaises(InvalidProjectError):
                scan_command(str(test_file))


class TestScanCommand(unittest.TestCase):
    """Tests for the project scanner."""

    def test_scan_empty_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()

            with redirect_stdout(output):
                result = scan_command(temp_dir)

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(
                "PROJECT ARCHAEOLOGIST - PROJECT SCAN",
                text
            )

            self.assertIn(
                "Scan completed successfully.",
                text
            )

    def test_scan_detects_empty_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)

            empty_file = project / "empty.txt"
            empty_file.touch()

            output = io.StringIO()

            with redirect_stdout(output):
                result = scan_command(temp_dir)

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(
                "Empty files      : 1",
                text
            )

            self.assertIn(
                "empty.txt",
                text
            )

    def test_scan_detects_file_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)

            python_file = project / "hello.py"

            python_file.write_text(
                "print('hello')\n",
                encoding="utf-8"
            )

            output = io.StringIO()

            with redirect_stdout(output):
                result = scan_command(temp_dir)

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(".py", text)


class TestAnalyzeCommand(unittest.TestCase):
    """Tests for code analysis."""

    def test_analyze_python_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)

            source_file = project / "example.py"

            source_file.write_text(
                "# comment\n"
                "\n"
                "x = 10\n"
                "print(x)\n"
                "# TODO: improve this\n"
                "# FIXME: test this\n",
                encoding="utf-8"
            )

            output = io.StringIO()

            with redirect_stdout(output):
                result = analyze_command(temp_dir)

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(
                "Source files     : 1",
                text
            )

            self.assertIn(
                "Total lines      : 6",
                text
            )

            self.assertIn(
                "TODOs            : 1",
                text
            )

            self.assertIn(
                "FIXMEs           : 1",
                text
            )

    def test_analyze_empty_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()

            with redirect_stdout(output):
                result = analyze_command(temp_dir)

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(
                "Source files     : 0",
                text
            )


class TestGitCommand(unittest.TestCase):
    """Tests for Git analysis."""

    @patch(
        "archaeologist.commands.run_git"
    )
    def test_git_command(self, mock_run_git):
        mock_run_git.side_effect = [
            "true",
            "Sheershika",
            "5",
            "abc123 - Test commit (Test User)",
            "2 Test User <test@example.com>",
            "file.py\nREADME.md\nfile.py",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()

            with redirect_stdout(output):
                result = git_command(temp_dir)

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(
                "GIT ANALYSIS",
                text
            )

            self.assertIn(
                "Sheershika",
                text
            )

            self.assertIn(
                "Commit count     : 5",
                text
            )

            self.assertIn(
                "file.py",
                text
            )

    @patch(
        "archaeologist.commands.run_git"
    )
    def test_git_command_without_repository(
        self,
        mock_run_git
    ):
        mock_run_git.side_effect = Exception(
            "Not a Git repository"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(Exception):
                git_command(temp_dir)


class TestReportCommand(unittest.TestCase):
    """Tests for report generation."""

    def test_terminal_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()

            with redirect_stdout(output):
                result = report_command(
                    temp_dir,
                    output_format="terminal"
                )

            self.assertEqual(result, 0)

            text = output.getvalue()

            self.assertIn(
                "PROJECT ARCHAEOLOGIST REPORT",
                text
            )

            self.assertIn(
                "PROJECT STRUCTURE",
                text
            )

            self.assertIn(
                "CODE ANALYSIS",
                text
            )

            self.assertIn(
                "GIT ANALYSIS",
                text
            )

    def test_json_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()

            with redirect_stdout(output):
                result = report_command(
                    temp_dir,
                    output_format="json"
                )

            self.assertEqual(result, 0)

            text = output.getvalue()

            data = json.loads(text)

            self.assertIn(
                "project",
                data
            )

            self.assertIn(
                "scan",
                data
            )

            self.assertIn(
                "analysis",
                data
            )

            self.assertIn(
                "git",
                data
            )


class TestCommandExecution(unittest.TestCase):
    """Tests that the CLI sends commands to the correct functions."""

    @patch("archaeologist.cli.scan_command")
    def test_execute_scan(self, mock_scan):
        mock_scan.return_value = 0

        parser = create_parser()

        args = parser.parse_args(
            ["scan", "."]
        )

        result = execute_command(args)

        self.assertEqual(result, 0)

        mock_scan.assert_called_once_with(".")


    @patch("archaeologist.cli.analyze_command")
    def test_execute_analyze(self, mock_analyze):
        mock_analyze.return_value = 0

        parser = create_parser()

        args = parser.parse_args(
            ["analyze", "."]
        )

        result = execute_command(args)

        self.assertEqual(result, 0)

        mock_analyze.assert_called_once_with(".")


    @patch("archaeologist.cli.git_command")
    def test_execute_git(self, mock_git):
        mock_git.return_value = 0

        parser = create_parser()

        args = parser.parse_args(
            ["git", "."]
        )

        result = execute_command(args)

        self.assertEqual(result, 0)

        mock_git.assert_called_once_with(".")


    @patch("archaeologist.cli.report_command")
    def test_execute_report(self, mock_report):
        mock_report.return_value = 0

        parser = create_parser()

        args = parser.parse_args(
            ["report", ".", "--format", "json"]
        )

        result = execute_command(args)

        self.assertEqual(result, 0)

        mock_report.assert_called_once_with(
            ".",
            output_format="json"
        )


if __name__ == "__main__":
    unittest.main()