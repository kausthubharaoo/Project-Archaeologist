"""
Git Analyzer Module for Project Archaeologist.

Zero-dependency analyzer using Python's standard library to extract Git repository
metadata, commit metrics, active branches, contributor stats, and file churn.
"""

from collections import Counter
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple


class GitAnalyzer:
    """Safe Git repository analyzer leveraging subprocess and standard library tools."""

    def __init__(self, repo_path: str, command_timeout: int = 15):
        """
        Initialize the GitAnalyzer.

        Args:
            repo_path: Path to the target directory.
            command_timeout: Maximum seconds allowed for a single git subprocess call.
        """
        self.repo_path = os.path.abspath(os.path.expanduser(repo_path))
        self.command_timeout = command_timeout

    def _is_git_installed(self) -> bool:
        """Check whether git binary is available on the system PATH."""
        return shutil.which("git") is not None

    def _run_git(self, args: List[str]) -> Tuple[bool, str, str]:
        """
        Execute a git command safely with subprocess.

        Args:
            args: List of command arguments passed to git (e.g. ['status']).

        Returns:
            Tuple of (success_boolean, stdout_string, stderr_string).
        """
        if not self._is_git_installed():
            return False, "", "Git executable not found on system PATH."

        if not os.path.exists(self.repo_path):
            return False, "", f"Directory does not exist: {self.repo_path}"

        if not os.path.isdir(self.repo_path):
            return False, "", f"Path is not a directory: {self.repo_path}"

        try:
            cmd = ["git"] + args
            process = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.command_timeout,
            )
            success = process.returncode == 0
            return success, process.stdout.strip(), process.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", f"Git command timed out after {self.command_timeout}s: git {' '.join(args)}"
        except PermissionError as e:
            return False, "", f"Permission denied executing git command: {str(e)}"
        except FileNotFoundError:
            return False, "", "Git command failed: git binary not found."
        except Exception as e:
            return False, "", f"Unexpected error running git command: {str(e)}"

    def is_git_repository(self) -> bool:
        """
        Determine if the target directory is inside a valid Git repository.

        Returns:
            True if valid Git work tree, False otherwise.
        """
        if not os.path.exists(self.repo_path) or not os.path.isdir(self.repo_path):
            return False

        success, stdout, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return success and stdout == "true"

    def get_current_branch(self) -> Optional[str]:
        """
        Find the current Git branch.

        Returns:
            Branch name string, or None if unavailable/detached/empty.
        """
        # Try modern git branch --show-current
        success, stdout, _ = self._run_git(["branch", "--show-current"])
        if success and stdout:
            return stdout

        # Fallback to rev-parse --abbrev-ref HEAD
        success, stdout, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if success and stdout:
            if stdout == "HEAD":
                success_tag, tag_out, _ = self._run_git(["describe", "--tags", "--exact-match"])
                if success_tag and tag_out:
                    return f"detached (tag: {tag_out})"
                return "detached HEAD"
            return stdout

        return None

    def get_branches(self) -> Dict[str, Any]:
        """
        List all local branch names and total count.

        Returns:
            Dictionary with local branch names, count, and current branch.
        """
        current_branch = self.get_current_branch()
        success, stdout, _ = self._run_git(["branch", "--list", "--format=%(refname:short)"])
        
        branches: List[str] = []
        if success and stdout:
            branches = [line.strip() for line in stdout.splitlines() if line.strip()]

        if not branches and current_branch:
            branches = [current_branch]

        return {
            "current": current_branch,
            "total_local_branches": len(branches),
            "branches": branches,
        }

    def get_commit_statistics(self) -> Dict[str, int]:
        """
        Calculate total commits, commits in last 7 days, and commits in last 30 days.

        Returns:
            Dictionary with commit statistics counts.
        """
        stats = {
            "total_commits": 0,
            "commits_last_7_days": 0,
            "commits_last_30_days": 0,
        }

        # Check if HEAD exists (empty repo with 0 commits check)
        success_head, _, _ = self._run_git(["rev-parse", "--verify", "HEAD"])
        if not success_head:
            return stats

        # 1. Total commits
        success, stdout, _ = self._run_git(["rev-list", "--count", "HEAD"])
        if success and stdout.isdigit():
            stats["total_commits"] = int(stdout)

        # 2. Commits in last 7 days
        success_7d, stdout_7d, _ = self._run_git(["rev-list", "--count", "--since=7 days ago", "HEAD"])
        if success_7d and stdout_7d.isdigit():
            stats["commits_last_7_days"] = int(stdout_7d)

        # 3. Commits in last 30 days
        success_30d, stdout_30d, _ = self._run_git(["rev-list", "--count", "--since=30 days ago", "HEAD"])
        if success_30d and stdout_30d.isdigit():
            stats["commits_last_30_days"] = int(stdout_30d)

        return stats

    def get_recent_commits(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch the latest commits with short hash, message, author name, and date.
        Emails are strictly omitted for privacy.

        Args:
            limit: Maximum number of commits to retrieve (default 10).

        Returns:
            List of commit dictionaries.
        """
        commits: List[Dict[str, str]] = []

        # %h: short hash, %s: commit message, %an: author name, %as: author date (YYYY-MM-DD)
        # Using null-byte delimiter (%x00) for deterministic parsing
        fmt = "%h%x00%s%x00%an%x00%as"
        success, stdout, _ = self._run_git(["log", f"-n{max(1, limit)}", f"--pretty=format:{fmt}"])

        if not success or not stdout:
            return commits

        for line in stdout.splitlines():
            parts = line.split("\x00")
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0].strip(),
                    "message": parts[1].strip(),
                    "author": parts[2].strip(),
                    "date": parts[3].strip(),
                })
            elif len(parts) == 3:
                commits.append({
                    "hash": parts[0].strip(),
                    "message": parts[1].strip(),
                    "author": parts[2].strip(),
                    "date": "unknown",
                })

        return commits

    def get_frequently_changed_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze Git commit history to identify files modified most frequently (churn).

        Args:
            limit: Number of top files to return (default 10).

        Returns:
            List of dictionaries with file path and changes count.
        """
        success, stdout, _ = self._run_git(["log", "--name-only", "--pretty=format:"])
        if not success or not stdout:
            return []

        counter: Counter[str] = Counter()
        for raw_line in stdout.splitlines():
            file_path = raw_line.strip()
            if not file_path:
                continue
            normalized_path = file_path.replace("\\", "/")
            counter[normalized_path] += 1

        top_files = counter.most_common(limit)
        return [{"file": path, "changes": count} for path, count in top_files]

    def get_contributors(self, limit: int = 10) -> Dict[str, Any]:
        """
        Find the total number of distinct contributors and top contributors by commit count.
        Avoids exposing emails or sensitive personal identifiers.

        Args:
            limit: Maximum top contributors to return.

        Returns:
            Dictionary containing total_contributors and list of top contributors.
        """
        success, stdout, _ = self._run_git(["shortlog", "-sn", "--no-merges", "HEAD"])
        if not success or not stdout:
            # Fallback using git log format
            success_log, stdout_log, _ = self._run_git(["log", "--format=%an"])
            if not success_log or not stdout_log:
                return {"total_contributors": 0, "contributors": []}

            counter = Counter(line.strip() for line in stdout_log.splitlines() if line.strip())
            top_authors = counter.most_common(limit)
            return {
                "total_contributors": len(counter),
                "contributors": [{"name": name, "commits": count} for name, count in top_authors],
            }

        contributors_list: List[Dict[str, Any]] = []
        all_contributors_count = 0

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            all_contributors_count += 1
            if len(contributors_list) < limit:
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    commits_str, name = parts
                    try:
                        commits_count = int(commits_str.strip())
                    except ValueError:
                        commits_count = 0
                    contributors_list.append({
                        "name": name.strip(),
                        "commits": commits_count,
                    })
                else:
                    parts_space = line.split(maxsplit=1)
                    if len(parts_space) == 2 and parts_space[0].isdigit():
                        contributors_list.append({
                            "name": parts_space[1].strip(),
                            "commits": int(parts_space[0]),
                        })

        return {
            "total_contributors": all_contributors_count,
            "contributors": contributors_list,
        }

    def analyze(self) -> Dict[str, Any]:
        """
        Execute full Git analysis and return structured dictionary.
        Does not crash on non-git directories or missing git tools.

        Returns:
            Structured dictionary compliant with Project Archaeologist specifications.
        """
        if not os.path.exists(self.repo_path):
            return {
                "is_git_repo": False,
                "branch": None,
                "total_commits": 0,
                "commits_last_7_days": 0,
                "commits_last_30_days": 0,
                "recent_commits": [],
                "frequently_changed_files": [],
                "total_contributors": 0,
                "contributors": [],
                "branches": [],
                "error": f"Target path does not exist: {self.repo_path}",
            }

        if not self._is_git_installed():
            return {
                "is_git_repo": False,
                "branch": None,
                "total_commits": 0,
                "commits_last_7_days": 0,
                "commits_last_30_days": 0,
                "recent_commits": [],
                "frequently_changed_files": [],
                "total_contributors": 0,
                "contributors": [],
                "branches": [],
                "error": "Git executable is not installed or not found on system PATH.",
            }

        if not self.is_git_repository():
            return {
                "is_git_repo": False,
                "branch": None,
                "total_commits": 0,
                "commits_last_7_days": 0,
                "commits_last_30_days": 0,
                "recent_commits": [],
                "frequently_changed_files": [],
                "total_contributors": 0,
                "contributors": [],
                "branches": [],
                "error": "Directory is not a Git repository.",
            }

        branch_info = self.get_branches()
        commit_stats = self.get_commit_statistics()
        recent_commits = self.get_recent_commits(limit=10)
        frequent_files = self.get_frequently_changed_files(limit=10)
        contrib_info = self.get_contributors(limit=10)

        return {
            "is_git_repo": True,
            "branch": branch_info.get("current"),
            "total_commits": commit_stats.get("total_commits", 0),
            "commits_last_7_days": commit_stats.get("commits_last_7_days", 0),
            "commits_last_30_days": commit_stats.get("commits_last_30_days", 0),
            "recent_commits": recent_commits,
            "frequently_changed_files": frequent_files,
            "total_contributors": contrib_info.get("total_contributors", 0),
            "contributors": contrib_info.get("contributors", []),
            "branches": branch_info.get("branches", []),
            "error": None,
        }


def analyze_git(repo_path: str) -> Dict[str, Any]:
    """
    Convenience function to analyze a Git repository path.

    Args:
        repo_path: Path to the directory.

    Returns:
        Structured dictionary with Git metrics and metadata.
    """
    analyzer = GitAnalyzer(repo_path)
    return analyzer.analyze()
