"""
Unit tests for GitAnalyzer.

Zero-dependency tests using Python's built-in unittest module.
"""

import os
import subprocess
import tempfile
import unittest

from git_analysis import GitAnalyzer, analyze_git


class TestGitAnalyzer(unittest.TestCase):

    def setUp(self):
        """Create a temporary Git repository for testing."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        # Check whether Git is installed.
        if not shutil_which_git():
            self.skipTest("Git is not installed on this system.")

        # Initialize Git repository.
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Configure Git user for the temporary repository.
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.repo_path,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.repo_path,
            check=True
        )

        # Create initial file.
        self._create_file(
            "app.py",
            "print('Hello World')\n"
        )

        self._git_add_and_commit(
            "Initial commit"
        )

        # Second commit.
        self._create_file(
            "database.py",
            "def connect():\n    pass\n"
        )

        self._git_add_and_commit(
            "Add database"
        )

        # Third commit.
        self._create_file(
            "utils.py",
            "def helper():\n    return True\n"
        )

        self._git_add_and_commit(
            "Add utilities"
        )

    def tearDown(self):
        """Remove temporary repository."""

        self.temp_dir.cleanup()

    # ---------------------------------------------------------
    # HELPER FUNCTIONS
    # ---------------------------------------------------------

    def _create_file(self, filename, content):
        """Create a file inside the temporary repository."""

        file_path = os.path.join(
            self.repo_path,
            filename
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

    def _git_add_and_commit(self, message):
        """Add all files and create a Git commit."""

        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo_path,
            check=True
        )

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )


# -------------------------------------------------------------
# GIT INSTALLATION TESTS
# -------------------------------------------------------------


class TestGitInstallation(unittest.TestCase):

    def test_git_installed(self):
        """Git should be available on the system."""

        analyzer = GitAnalyzer(
            tempfile.gettempdir()
        )

        result = analyzer._is_git_installed()

        self.assertTrue(
            result
        )


# -------------------------------------------------------------
# GIT REPOSITORY TESTS
# -------------------------------------------------------------


class TestGitRepository(unittest.TestCase):

    def setUp(self):
        """Create a temporary Git repository."""

        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        if not shutil_which_git():
            self.skipTest("Git is not installed on this system.")

        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_is_git_repository(self):
        """Valid Git repository should be detected."""

        analyzer = GitAnalyzer(
            self.repo_path
        )

        self.assertTrue(
            analyzer.is_git_repository()
        )

    def test_non_git_directory(self):
        """Normal directory should not be detected as Git repository."""

        temp_dir = tempfile.TemporaryDirectory()

        try:
            analyzer = GitAnalyzer(
                temp_dir.name
            )

            self.assertFalse(
                analyzer.is_git_repository()
            )

        finally:
            temp_dir.cleanup()


# -------------------------------------------------------------
# BRANCH TESTS
# -------------------------------------------------------------


class TestBranches(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        if not shutil_which_git():
            self.skipTest("Git is not installed on this system.")

        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.repo_path,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.repo_path,
            check=True
        )

        self._create_file(
            "app.py",
            "print('test')\n"
        )

        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo_path,
            check=True
        )

        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_file(self, filename, content):
        with open(
            os.path.join(self.repo_path, filename),
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

    def test_current_branch(self):
        """Current branch should be detected."""

        analyzer = GitAnalyzer(
            self.repo_path
        )

        branch = analyzer.get_current_branch()

        self.assertIsNotNone(
            branch
        )

    def test_get_branches(self):
        """Branch information should be returned."""

        analyzer = GitAnalyzer(
            self.repo_path
        )

        result = analyzer.get_branches()

        self.assertIn(
            "current",
            result
        )

        self.assertIn(
            "total_local_branches",
            result
        )

        self.assertIn(
            "branches",
            result
        )

        self.assertGreaterEqual(
            result["total_local_branches"],
            1
        )


# -------------------------------------------------------------
# COMMIT STATISTICS TESTS
# -------------------------------------------------------------


class TestCommitStatistics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        if not shutil_which_git():
            self.skipTest("Git is not installed on this system.")

        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.repo_path,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.repo_path,
            check=True
        )

        for i in range(3):
            with open(
                os.path.join(
                    self.repo_path,
                    "file.py"
                ),
                "w",
                encoding="utf-8"
            ) as file:
                file.write(
                    f"print('commit {i}')\n"
                )

            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True
            )

            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"Commit {i}"
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_commit_statistics(self):
        """Commit statistics should count commits."""

        analyzer = GitAnalyzer(
            self.repo_path
        )

        result = analyzer.get_commit_statistics()

        self.assertEqual(
            result["total_commits"],
            3
        )

        self.assertGreaterEqual(
            result["commits_last_7_days"],
            0
        )

        self.assertGreaterEqual(
            result["commits_last_30_days"],
            0
        )


# -------------------------------------------------------------
# RECENT COMMITS TESTS
# -------------------------------------------------------------


class TestRecentCommits(unittest.TestCase):

    def test_recent_commits(self):
        """Recent commits should contain expected fields."""

        temp_dir = create_test_repository()

        try:
            analyzer = GitAnalyzer(
                temp_dir
            )

            commits = analyzer.get_recent_commits(
                limit=10
            )

            self.assertGreater(
                len(commits),
                0
            )

            commit = commits[0]

            self.assertIn(
                "hash",
                commit
            )

            self.assertIn(
                "message",
                commit
            )

            self.assertIn(
                "author",
                commit
            )

            self.assertIn(
                "date",
                commit
            )

        finally:
            cleanup_temp_directory(temp_dir)


# -------------------------------------------------------------
# FREQUENTLY CHANGED FILES TESTS
# -------------------------------------------------------------


class TestFrequentlyChangedFiles(unittest.TestCase):

    def test_frequently_changed_files(self):
        """Frequently changed files should be detected."""

        temp_dir = create_test_repository()

        try:
            analyzer = GitAnalyzer(
                temp_dir
            )

            files = analyzer.get_frequently_changed_files(
                limit=10
            )

            self.assertIsInstance(
                files,
                list
            )

            if files:
                self.assertIn(
                    "file",
                    files[0]
                )

                self.assertIn(
                    "changes",
                    files[0]
                )

        finally:
            cleanup_temp_directory(temp_dir)


# -------------------------------------------------------------
# CONTRIBUTOR TESTS
# -------------------------------------------------------------


class TestContributors(unittest.TestCase):

    def test_contributors(self):
        """Contributor information should be returned."""

        temp_dir = create_test_repository()

        try:
            analyzer = GitAnalyzer(
                temp_dir
            )

            result = analyzer.get_contributors(
                limit=10
            )

            self.assertIn(
                "total_contributors",
                result
            )

            self.assertIn(
                "contributors",
                result
            )

            self.assertGreater(
                result["total_contributors"],
                0
            )

            self.assertGreater(
                len(result["contributors"]),
                0
            )

            contributor = result["contributors"][0]

            self.assertIn(
                "name",
                contributor
            )

            self.assertIn(
                "commits",
                contributor
            )

        finally:
            cleanup_temp_directory(temp_dir)


# -------------------------------------------------------------
# COMPLETE ANALYSIS TESTS
# -------------------------------------------------------------


class TestCompleteAnalysis(unittest.TestCase):

    def test_analyze(self):
        """Complete Git analysis should return expected structure."""

        temp_dir = create_test_repository()

        try:
            analyzer = GitAnalyzer(
                temp_dir
            )

            result = analyzer.analyze()

            self.assertTrue(
                result["is_git_repo"]
            )

            self.assertIsNotNone(
                result["branch"]
            )

            self.assertGreater(
                result["total_commits"],
                0
            )

            self.assertIsInstance(
                result["recent_commits"],
                list
            )

            self.assertIsInstance(
                result["frequently_changed_files"],
                list
            )

            self.assertIsInstance(
                result["contributors"],
                list
            )

            self.assertIsInstance(
                result["branches"],
                list
            )

            self.assertIsNone(
                result["error"]
            )

        finally:
            cleanup_temp_directory(temp_dir)

    def test_analyze_git_convenience_function(self):
        """analyze_git() should return complete analysis."""

        temp_dir = create_test_repository()

        try:
            result = analyze_git(
                temp_dir
            )

            self.assertTrue(
                result["is_git_repo"]
            )

            self.assertGreater(
                result["total_commits"],
                0
            )

        finally:
            cleanup_temp_directory(temp_dir)


# -------------------------------------------------------------
# INVALID PATH TESTS
# -------------------------------------------------------------


class TestInvalidPaths(unittest.TestCase):

    def test_non_existing_path(self):
        """Non-existing path should be handled safely."""

        analyzer = GitAnalyzer(
            "/this/path/does/not/exist"
        )

        result = analyzer.analyze()

        self.assertFalse(
            result["is_git_repo"]
        )

        self.assertEqual(
            result["total_commits"],
            0
        )

        self.assertIsNotNone(
            result["error"]
        )

    def test_file_instead_of_directory(self):
        """A file path should not be treated as a repository."""

        temp_dir = tempfile.TemporaryDirectory()

        try:
            file_path = os.path.join(
                temp_dir.name,
                "test.txt"
            )

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:
                file.write("test")

            analyzer = GitAnalyzer(
                file_path
            )

            result = analyzer.analyze()

            self.assertFalse(
                result["is_git_repo"]
            )

        finally:
            temp_dir.cleanup()


# -------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------


def shutil_which_git():
    """Check whether Git is available."""

    import shutil

    return shutil.which("git") is not None


def create_test_repository():
    """Create a temporary Git repository with sample commits."""

    temp_dir = tempfile.mkdtemp()

    subprocess.run(
        ["git", "init"],
        cwd=temp_dir,
        capture_output=True,
        text=True,
        check=True
    )

    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        check=True
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        check=True
    )

    for i in range(3):

        file_path = os.path.join(
            temp_dir,
            "app.py"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(
                f"# Version {i}\n"
                f"print('Hello {i}')\n"
            )

        subprocess.run(
            ["git", "add", "."],
            cwd=temp_dir,
            check=True
        )

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Test commit {i}"
            ],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=True
        )

    return temp_dir


def cleanup_temp_directory(path):
    """Remove temporary directory."""

    import shutil

    shutil.rmtree(
        path,
        ignore_errors=True
    )


if __name__ == "__main__":
    unittest.main()
    
