import argparse
import sys

from . import __version__

from .commands import (
    scan_command,
    analyze_command,
    git_command,
    report_command,
)

from .errors import ArchaeologistError


EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_INTERRUPTED = 130


def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="archaeologist",
        description=(
            "Project Archaeologist - "
            "analyze and understand your codebase."
        ),
        epilog=(
            "Example: python -m archaeologist scan ."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan project files and folders.",
        description=(
            "Scan the project structure and show "
            "files, folders, sizes and empty items."
        ),
    )

    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help=(
            "Path to the project. "
            "Default: current directory."
        ),
    )

    # --------------------------------------------------------
    # ANALYZE
    # --------------------------------------------------------

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze source code.",
        description=(
            "Analyze source files, line counts, "
            "TODOs and FIXMEs."
        ),
    )

    analyze_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help=(
            "Path to the project. "
            "Default: current directory."
        ),
    )

    # --------------------------------------------------------
    # GIT
    # --------------------------------------------------------

    git_parser = subparsers.add_parser(
        "git",
        help="Analyze Git repository information.",
        description=(
            "Analyze commits, branches, contributors "
            "and frequently changed files."
        ),
    )

    git_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help=(
            "Path to the Git repository. "
            "Default: current directory."
        ),
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report_parser = subparsers.add_parser(
        "report",
        help="Generate a complete project report.",
        description=(
            "Combine project scanning, code analysis "
            "and Git information into one report."
        ),
    )

    report_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help=(
            "Path to the project. "
            "Default: current directory."
        ),
    )

    report_parser.add_argument(
        "--format",
        choices=[
            "terminal",
            "json",
        ],
        default="terminal",
        help=(
            "Report format. "
            "Choose terminal or json. "
            "Default: terminal."
        ),
    )

    return parser


def execute_command(args) -> int:

    if args.command == "scan":

        return scan_command(
            args.path
        )

    if args.command == "analyze":

        return analyze_command(
            args.path
        )

    if args.command == "git":

        return git_command(
            args.path
        )

    if args.command == "report":

        return report_command(
            args.path,
            output_format=args.format,
        )

    return EXIT_USAGE_ERROR


def main() -> int:

    parser = create_parser()

    try:

        args = parser.parse_args()

        if args.command is None:

            parser.print_help()

            return EXIT_USAGE_ERROR

        return execute_command(args)

    except ArchaeologistError as error:

        print(
            f"Error: {error}",
            file=sys.stderr,
        )

        return EXIT_ERROR

    except KeyboardInterrupt:

        print(
            "\nOperation cancelled.",
            file=sys.stderr,
        )

        return EXIT_INTERRUPTED

    except Exception as error:

        print(
            f"Unexpected error: {error}",
            file=sys.stderr,
        )

        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())