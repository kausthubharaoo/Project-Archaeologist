from pathlib import Path
import json
import subprocess

from .errors import (
    ProjectNotFoundError,
    InvalidProjectError,
    GitRepositoryError,
)


IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
}


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".html",
    ".css",
    ".scss",
    ".sql",
}


def validate_project(path: str) -> Path:
    """
    Check whether the given project path exists
    and is a directory.
    """

    project = Path(path).expanduser().resolve()

    if not project.exists():
        raise ProjectNotFoundError(
            f"Project path does not exist: {project}"
        )

    if not project.is_dir():
        raise InvalidProjectError(
            f"Path is not a directory: {project}"
        )

    return project


def should_ignore(path: Path) -> bool:
    """
    Return True when a file/folder belongs to an ignored directory.
    """

    return any(
        part in IGNORED_DIRECTORIES
        for part in path.parts
    )


def get_project_files(project: Path):
    """
    Return all files belonging to the project while
    ignoring unnecessary directories.
    """

    for path in project.rglob("*"):

        if should_ignore(path):
            continue

        if path.is_file():
            yield path


def scan_command(path: str) -> int:
    """
    Scan project structure.

    Finds:
        - files
        - folders
        - file extensions
        - total size
        - empty files
        - empty folders
    """

    project = validate_project(path)

    files = []
    folders = []

    empty_files = []
    empty_folders = []

    extension_count = {}

    total_size = 0

    for item in project.rglob("*"):

        if should_ignore(item):
            continue

        if item.is_dir():

            folders.append(item)

        elif item.is_file():

            files.append(item)

            try:
                size = item.stat().st_size
            except OSError:
                continue

            total_size += size

            if size == 0:
                empty_files.append(item)

            extension = item.suffix.lower()

            if extension:
                extension_count[extension] = (
                    extension_count.get(extension, 0) + 1
                )
            else:
                extension_count["[no extension]"] = (
                    extension_count.get("[no extension]", 0) + 1
                )

    for folder in folders:

        try:

            has_content = False

            for child in folder.iterdir():

                if should_ignore(child):
                    continue

                has_content = True
                break

            if not has_content:
                empty_folders.append(folder)

        except OSError:
            continue

    print()
    print("=" * 60)
    print("PROJECT ARCHAEOLOGIST - PROJECT SCAN")
    print("=" * 60)

    print(f"Project          : {project}")
    print(f"Files            : {len(files)}")
    print(f"Folders          : {len(folders)}")
    print(f"Total size       : {format_size(total_size)}")
    print(f"Empty files      : {len(empty_files)}")
    print(f"Empty folders    : {len(empty_folders)}")

    print()
    print("FILE TYPES")
    print("-" * 60)

    if extension_count:

        sorted_extensions = sorted(
            extension_count.items(),
            key=lambda x: (-x[1], x[0])
        )

        for extension, count in sorted_extensions:
            print(f"{extension:<20} {count}")

    else:
        print("No files found.")

    if empty_files:

        print()
        print("EMPTY FILES")
        print("-" * 60)

        for file in empty_files:
            try:
                relative_path = file.relative_to(project)
            except ValueError:
                relative_path = file

            print(f"- {relative_path}")

    if empty_folders:

        print()
        print("EMPTY FOLDERS")
        print("-" * 60)

        for folder in empty_folders:
            try:
                relative_path = folder.relative_to(project)
            except ValueError:
                relative_path = folder

            print(f"- {relative_path}")

    print()
    print("Scan completed successfully.")
    print()

    return 0


def analyze_command(path: str) -> int:
    """
    Perform basic source-code analysis.

    Finds:
        - number of source files
        - lines of code
        - TODO comments
        - FIXME comments
        - comments
        - blank lines
    """

    project = validate_project(path)

    source_files = []

    total_lines = 0
    blank_lines = 0
    comment_lines = 0
    todo_count = 0
    fixme_count = 0

    extension_count = {}

    for file in get_project_files(project):

        if file.suffix.lower() not in CODE_EXTENSIONS:
            continue

        source_files.append(file)

        extension = file.suffix.lower()

        extension_count[extension] = (
            extension_count.get(extension, 0) + 1
        )

        try:

            with file.open(
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as source:

                for line in source:

                    total_lines += 1

                    stripped = line.strip()

                    if not stripped:
                        blank_lines += 1

                    if is_comment_line(
                        stripped,
                        file.suffix.lower()
                    ):
                        comment_lines += 1

                    upper_line = line.upper()

                    if "TODO" in upper_line:
                        todo_count += 1

                    if "FIXME" in upper_line:
                        fixme_count += 1

        except (OSError, UnicodeError):
            continue

    code_lines = max(
        total_lines - blank_lines - comment_lines,
        0
    )

    print()
    print("=" * 60)
    print("PROJECT ARCHAEOLOGIST - CODE ANALYSIS")
    print("=" * 60)

    print(f"Project          : {project}")
    print(f"Source files     : {len(source_files)}")
    print(f"Total lines      : {total_lines}")
    print(f"Code lines       : {code_lines}")
    print(f"Blank lines      : {blank_lines}")
    print(f"Comment lines    : {comment_lines}")
    print(f"TODOs            : {todo_count}")
    print(f"FIXMEs           : {fixme_count}")

    print()
    print("SOURCE FILE TYPES")
    print("-" * 60)

    if extension_count:

        sorted_extensions = sorted(
            extension_count.items(),
            key=lambda x: (-x[1], x[0])
        )

        for extension, count in sorted_extensions:
            print(f"{extension:<20} {count}")

    else:
        print("No source files found.")

    print()
    print("Code analysis completed successfully.")
    print()

    return 0


def is_comment_line(line: str, extension: str) -> bool:
    """
    Basic detection of comment-only lines.
    """

    if not line:
        return False

    if extension in {
        ".py",
        ".rb",
        ".sh",
        ".yaml",
        ".yml",
    }:
        return line.startswith("#")

    if extension in {
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".swift",
        ".kt",
        ".kts",
    }:
        return (
            line.startswith("//")
            or line.startswith("/*")
            or line.startswith("*")
        )

    if extension in {
        ".html",
        ".xml",
    }:
        return line.startswith("<!--")

    if extension in {
        ".css",
        ".scss",
    }:
        return (
            line.startswith("/*")
            or line.startswith("*")
        )

    if extension == ".sql":
        return line.startswith("--")

    return False


def run_git(project: Path, *arguments: str) -> str:
    """
    Safely execute a Git command and return its output.
    """

    try:

        result = subprocess.run(
            ["git", *arguments],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    except FileNotFoundError:

        raise GitRepositoryError(
            "Git is not installed or is not available in PATH."
        )

    except subprocess.CalledProcessError as error:

        error_message = error.stderr.strip()

        raise GitRepositoryError(
            error_message or "Git command failed."
        )


def git_command(path: str) -> int:
    """
    Analyze Git repository information.

    Finds:
        - current branch
        - number of commits
        - latest commit
        - contributors
        - most frequently changed files
    """

    project = validate_project(path)

    try:

        run_git(
            project,
            "rev-parse",
            "--is-inside-work-tree",
        )

    except GitRepositoryError:

        raise GitRepositoryError(
            f"{project} is not a Git repository."
        )

    branch = run_git(
        project,
        "branch",
        "--show-current",
    )

    if not branch:
        branch = "detached HEAD"

    commit_count = run_git(
        project,
        "rev-list",
        "--count",
        "HEAD",
    )

    latest_commit = run_git(
        project,
        "log",
        "-1",
        "--pretty=format:%h - %s (%an)",
    )

    contributors = run_git(
        project,
        "shortlog",
        "-sne",
        "HEAD",
    )

    changed_files_output = run_git(
        project,
        "log",
        "--name-only",
        "--pretty=format:",
    )

    frequency = {}

    for line in changed_files_output.splitlines():

        filename = line.strip()

        if not filename:
            continue

        if filename in frequency:
            frequency[filename] += 1
        else:
            frequency[filename] = 1

    most_changed = sorted(
        frequency.items(),
        key=lambda x: (-x[1], x[0])
    )[:10]

    print()
    print("=" * 60)
    print("PROJECT ARCHAEOLOGIST - GIT ANALYSIS")
    print("=" * 60)

    print(f"Repository       : {project}")
    print(f"Current branch   : {branch}")
    print(f"Commit count     : {commit_count}")

    print()
    print("LATEST COMMIT")
    print("-" * 60)
    print(latest_commit or "No commits found.")

    print()
    print("CONTRIBUTORS")
    print("-" * 60)

    if contributors:
        print(contributors)
    else:
        print("No contributor information found.")

    print()
    print("MOST FREQUENTLY CHANGED FILES")
    print("-" * 60)

    if most_changed:

        for filename, count in most_changed:
            print(
                f"{count:>5} changes  {filename}"
            )

    else:
        print("No file history found.")

    print()
    print("Git analysis completed successfully.")
    print()

    return 0


def collect_scan_data(project: Path):
    """
    Collect scan information for the report.
    """

    files = []
    folders = []
    empty_files = []
    empty_folders = []
    extension_count = {}

    total_size = 0

    for item in project.rglob("*"):

        if should_ignore(item):
            continue

        if item.is_dir():
            folders.append(item)

        elif item.is_file():

            files.append(item)

            try:
                size = item.stat().st_size
            except OSError:
                continue

            total_size += size

            if size == 0:
                empty_files.append(item)

            extension = item.suffix.lower()

            if extension:
                extension_count[extension] = (
                    extension_count.get(extension, 0) + 1
                )
            else:
                extension_count["[no extension]"] = (
                    extension_count.get("[no extension]", 0) + 1
                )

    for folder in folders:

        try:

            content = [
                child
                for child in folder.iterdir()
                if not should_ignore(child)
            ]

            if not content:
                empty_folders.append(folder)

        except OSError:
            continue

    return {
        "files": len(files),
        "folders": len(folders),
        "total_size": total_size,
        "empty_files": len(empty_files),
        "empty_folders": len(empty_folders),
        "extensions": extension_count,
    }


def collect_analysis_data(project: Path):
    """
    Collect basic code-analysis information.
    """

    source_files = 0
    total_lines = 0
    blank_lines = 0
    comment_lines = 0
    todo_count = 0
    fixme_count = 0

    for file in get_project_files(project):

        if file.suffix.lower() not in CODE_EXTENSIONS:
            continue

        source_files += 1

        try:

            with file.open(
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as source:

                for line in source:

                    total_lines += 1

                    stripped = line.strip()

                    if not stripped:
                        blank_lines += 1

                    if is_comment_line(
                        stripped,
                        file.suffix.lower()
                    ):
                        comment_lines += 1

                    upper_line = line.upper()

                    if "TODO" in upper_line:
                        todo_count += 1

                    if "FIXME" in upper_line:
                        fixme_count += 1

        except (OSError, UnicodeError):
            continue

    code_lines = max(
        total_lines - blank_lines - comment_lines,
        0
    )

    return {
        "source_files": source_files,
        "total_lines": total_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "todos": todo_count,
        "fixmes": fixme_count,
    }


def collect_git_data(project: Path):
    """
    Collect Git information.
    """

    data = {
        "is_git_repository": False,
        "branch": None,
        "commits": None,
        "latest_commit": None,
        "contributors": [],
        "frequently_changed_files": [],
    }

    try:

        run_git(
            project,
            "rev-parse",
            "--is-inside-work-tree",
        )

    except GitRepositoryError:
        return data

    data["is_git_repository"] = True

    branch = run_git(
        project,
        "branch",
        "--show-current",
    )

    data["branch"] = branch or "detached HEAD"

    data["commits"] = run_git(
        project,
        "rev-list",
        "--count",
        "HEAD",
    )

    data["latest_commit"] = run_git(
        project,
        "log",
        "-1",
        "--pretty=format:%h - %s (%an)",
    )

    contributors = run_git(
        project,
        "shortlog",
        "-sne",
        "HEAD",
    )

    if contributors:
        data["contributors"] = contributors.splitlines()

    changed_files = run_git(
        project,
        "log",
        "--name-only",
        "--pretty=format:",
    )

    frequency = {}

    for line in changed_files.splitlines():

        filename = line.strip()

        if not filename:
            continue

        frequency[filename] = (
            frequency.get(filename, 0) + 1
        )

    data["frequently_changed_files"] = [
        {
            "file": filename,
            "changes": count,
        }
        for filename, count in sorted(
            frequency.items(),
            key=lambda x: (-x[1], x[0])
        )[:10]
    ]

    return data


def report_command(
    path: str,
    output_format: str = "terminal"
) -> int:
    """
    Generate the combined Project Archaeologist report.
    """

    project = validate_project(path)

    scan_data = collect_scan_data(project)
    analysis_data = collect_analysis_data(project)
    git_data = collect_git_data(project)

    report = {
        "project": str(project),
        "scan": scan_data,
        "analysis": analysis_data,
        "git": git_data,
    }

    if output_format == "json":

        print(
            json.dumps(
                report,
                indent=4
            )
        )

        return 0

    print()
    print("=" * 70)
    print("             PROJECT ARCHAEOLOGIST REPORT")
    print("=" * 70)

    print()
    print(f"PROJECT: {project}")

    print()
    print("1. PROJECT STRUCTURE")
    print("-" * 70)

    print(f"Files             : {scan_data['files']}")
    print(f"Folders           : {scan_data['folders']}")
    print(
        f"Total size        : "
        f"{format_size(scan_data['total_size'])}"
    )
    print(f"Empty files       : {scan_data['empty_files']}")
    print(f"Empty folders     : {scan_data['empty_folders']}")

    print()
    print("2. FILE TYPES")
    print("-" * 70)

    if scan_data["extensions"]:

        sorted_extensions = sorted(
            scan_data["extensions"].items(),
            key=lambda x: (-x[1], x[0])
        )

        for extension, count in sorted_extensions:
            print(f"{extension:<20} {count}")

    else:
        print("No files found.")

    print()
    print("3. CODE ANALYSIS")
    print("-" * 70)

    print(
        f"Source files      : "
        f"{analysis_data['source_files']}"
    )

    print(
        f"Total lines       : "
        f"{analysis_data['total_lines']}"
    )

    print(
        f"Code lines        : "
        f"{analysis_data['code_lines']}"
    )

    print(
        f"Blank lines       : "
        f"{analysis_data['blank_lines']}"
    )

    print(
        f"Comment lines     : "
        f"{analysis_data['comment_lines']}"
    )

    print(
        f"TODOs             : "
        f"{analysis_data['todos']}"
    )

    print(
        f"FIXMEs            : "
        f"{analysis_data['fixmes']}"
    )

    print()
    print("4. GIT ANALYSIS")
    print("-" * 70)

    if git_data["is_git_repository"]:

        print(
            f"Current branch    : "
            f"{git_data['branch']}"
        )

        print(
            f"Commit count      : "
            f"{git_data['commits']}"
        )

        print(
            f"Latest commit     : "
            f"{git_data['latest_commit']}"
        )

        print()
        print("Contributors:")

        if git_data["contributors"]:

            for contributor in git_data["contributors"]:
                print(f"  {contributor}")

        else:
            print("  No contributors found.")

        print()
        print("Frequently changed files:")

        if git_data["frequently_changed_files"]:

            for item in git_data[
                "frequently_changed_files"
            ]:

                print(
                    f"  {item['changes']:>5} changes  "
                    f"{item['file']}"
                )

        else:
            print("  No file history found.")

    else:

        print(
            "This project is not a Git repository."
        )

    print()
    print("=" * 70)
    print("Analysis completed successfully.")
    print("=" * 70)
    print()

    return 0


def format_size(size: int) -> str:
    """
    Convert bytes into a human-readable size.
    """

    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"

    return (
        f"{size / (1024 * 1024 * 1024):.2f} GB"
    )