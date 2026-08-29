"""
Relationship Analyzer Module for Project Archaeologist.

Zero-dependency analyzer using Python's standard library to discover
relationships between Python source files through import statements.
- Python import relationship detection
- Dependency mapping
- Incoming/outgoing relationship counts
- Most connected files
- Potential relationship hotspots
"""

import ast
import os
from collections import defaultdict
from typing import Any, Dict, List, Set


# Directories that should not be analyzed
IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
}


class RelationshipAnalyzer:
    """
    Analyze relationships between Python files in a project.

    The analyzer uses Python's built-in AST module to detect:
        import module
        from module import something

    Only relationships between files that actually exist inside
    the project are recorded.
    """

    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(os.path.expanduser(project_path))

        # Maps module names to their corresponding Python file
        self.module_to_file: Dict[str, str] = {}

        # Maps file -> files it depends on
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)

        # Maps file -> files that depend on it
        self.dependents: Dict[str, Set[str]] = defaultdict(set)

        # Files that could not be parsed
        self.parse_errors: List[Dict[str, str]] = []

    # ---------------------------------------------------------
    # 1. FIND PYTHON FILES
    # ---------------------------------------------------------

    def _find_python_files(self) -> List[str]:
        """Find all Python files while skipping ignored directories."""

        python_files = []

        if not os.path.isdir(self.project_path):
            return python_files

        for root, dirs, files in os.walk(self.project_path):

            # Prevent os.walk from entering ignored directories
            dirs[:] = [
                directory
                for directory in dirs
                if directory not in IGNORED_DIRECTORIES
            ]

            for filename in files:
                if filename.endswith(".py"):
                    full_path = os.path.join(root, filename)
                    python_files.append(full_path)

        return python_files

    # ---------------------------------------------------------
    # 2. CREATE MODULE MAP
    # ---------------------------------------------------------

    def _create_module_map(self, python_files: List[str]) -> None:
        """
        Create a mapping between Python module names and file paths.
        """

        for file_path in python_files:

            relative_path = os.path.relpath(
                file_path,
                self.project_path
            )

            # Convert Windows paths to Unix-style paths
            relative_path = relative_path.replace("\\", "/")

            # Convert folder separators into module separators
            module_name = relative_path.replace("/", ".")

            # Create module name without .py
            module_name_without_extension = module_name

            if module_name_without_extension.endswith(".py"):
                module_name_without_extension = (
                    module_name_without_extension[:-3]
                )

            # Remove __init__ from package module names
            if module_name_without_extension.endswith(".__init__"):
                module_name_without_extension = (
                    module_name_without_extension[:-9]
                )

            # Map module name without .py to the actual .py file
            self.module_to_file[
                module_name_without_extension
            ] = relative_path

            # Also map the filename with .py
            self.module_to_file[
                module_name
            ] = relative_path

    # ---------------------------------------------------------
    # 3. RESOLVE IMPORT
    # ---------------------------------------------------------
    def _resolve_import(
        self,
        module_name: str
    ) -> str:
        """
        Try to find which project file corresponds to an imported module.

        Returns:
            Relative file path or empty string if it is external/unknown.
        """

        if not module_name:
            return ""

        # Exact module match
        if module_name in self.module_to_file:
            return self.module_to_file[module_name]

        # Try progressively shorter module names.
        #
        # Example:
        # myproject.database.models
        #
        # might resolve to:
        # myproject/database.py

        parts = module_name.split(".")

        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])

            if candidate in self.module_to_file:
                return self.module_to_file[candidate]

        return ""

    # ---------------------------------------------------------
    # 4. ANALYZE IMPORTS
    # ---------------------------------------------------------

    def _analyze_file(self, file_path: str) -> None:
        """Analyze imports inside one Python file."""

        relative_file = os.path.relpath(
            file_path,
            self.project_path
        ).replace("\\", "/")

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="replace"
            ) as file:
                source_code = file.read()

            tree = ast.parse(source_code, filename=file_path)

        except (SyntaxError, OSError, UnicodeError) as error:
            self.parse_errors.append({
                "file": relative_file,
                "error": str(error)
            })
            return

        for node in ast.walk(tree):

            # ---------------------------------------------
            # import database
            # import database.models
            # ---------------------------------------------

            if isinstance(node, ast.Import):

                for alias in node.names:

                    imported_module = alias.name

                    target_file = self._resolve_import(
                        imported_module
                    )

                    if target_file and target_file != relative_file:

                        self.dependencies[relative_file].add(
                            target_file
                        )

                        self.dependents[target_file].add(
                            relative_file
                        )

            # ---------------------------------------------
            # from database import connect
            # from database.models import User
            # ---------------------------------------------

            elif isinstance(node, ast.ImportFrom):

                module_name = node.module or ""

                target_file = self._resolve_import(
                    module_name
                )

                if target_file and target_file != relative_file:

                    self.dependencies[relative_file].add(
                        target_file
                    )

                    self.dependents[target_file].add(
                        relative_file
                    )

    # ---------------------------------------------------------
    # 5. BUILD RELATIONSHIP MAP
    # ---------------------------------------------------------

    def _build_relationship_map(
        self,
        python_files: List[str]
    ) -> None:
        """Analyze all Python files."""

        for file_path in python_files:
            self._analyze_file(file_path)

    # ---------------------------------------------------------
    # 6. MOST CONNECTED FILES
    # ---------------------------------------------------------

    def _get_most_connected_files(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find files with the highest total number of relationships.

        Total relationships =
            outgoing dependencies + incoming dependents
        """

        all_files = set(self.dependencies.keys()) | set(
            self.dependents.keys()
        )

        results = []

        for file_path in all_files:

            outgoing = len(
                self.dependencies.get(file_path, set())
            )

            incoming = len(
                self.dependents.get(file_path, set())
            )

            total = outgoing + incoming

            results.append({
                "file": file_path,
                "incoming": incoming,
                "outgoing": outgoing,
                "total_relationships": total
            })

        results.sort(
            key=lambda item: item["total_relationships"],
            reverse=True
        )

        return results[:limit]

    # ---------------------------------------------------------
    # 7. RELATIONSHIP HOTSPOTS
    # ---------------------------------------------------------

    def _get_hotspots(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify files with unusually high numbers of relationships.

        This does NOT mean the files are broken.
        They are simply highly connected and may deserve attention.
        """

        connected_files = self._get_most_connected_files(
            limit=len(self.module_to_file)
        )

        if not connected_files:
            return []

        # Average relationship count
        total_relationships = sum(
            item["total_relationships"]
            for item in connected_files
        )

        average = (
            total_relationships / len(connected_files)
            if connected_files
            else 0
        )

        hotspots = []

        for item in connected_files:

            if item["total_relationships"] > average:
                hotspots.append({
                    "file": item["file"],
                    "incoming": item["incoming"],
                    "outgoing": item["outgoing"],
                    "total_relationships": item[
                        "total_relationships"
                    ],
                    "reason": "High number of file relationships"
                })

        return hotspots[:limit]

    # ---------------------------------------------------------
    # 8. MAIN ANALYSIS
    # ---------------------------------------------------------

    def analyze(self) -> Dict[str, Any]:
        """
        Run the complete relationship analysis.

        Returns a structured dictionary that Member 4 can use
        to create the final Project Archaeologist report.
        """

        if not os.path.exists(self.project_path):

            return {
                "success": False,
                "error": (
                    f"Project path does not exist: "
                    f"{self.project_path}"
                ),
                "files_analyzed": 0,
                "relationships_found": 0,
                "dependencies": {},
                "dependents": {},
                "most_connected_files": [],
                "hotspots": [],
                "parse_errors": []
            }

        if not os.path.isdir(self.project_path):

            return {
                "success": False,
                "error": (
                    f"Project path is not a directory: "
                    f"{self.project_path}"
                ),
                "files_analyzed": 0,
                "relationships_found": 0,
                "dependencies": {},
                "dependents": {},
                "most_connected_files": [],
                "hotspots": [],
                "parse_errors": []
            }

        # Find Python files
        python_files = self._find_python_files()

        # Build module -> file mapping
        self._create_module_map(python_files)

        # Analyze relationships
        self._build_relationship_map(python_files)

        # Convert sets to sorted lists for JSON compatibility
        dependency_output = {
            file: sorted(list(targets))
            for file, targets in self.dependencies.items()
        }

        dependent_output = {
            file: sorted(list(targets))
            for file, targets in self.dependents.items()
        }

        # Count relationships
        relationships_found = sum(
            len(targets)
            for targets in self.dependencies.values()
        )

        most_connected = self._get_most_connected_files()

        hotspots = self._get_hotspots()

        return {
            "success": True,
            "files_analyzed": len(python_files),
            "relationships_found": relationships_found,

            "dependencies": dependency_output,

            "dependents": dependent_output,

            "most_connected_files": most_connected,

            "hotspots": hotspots,

            "parse_errors": self.parse_errors
        }


# -------------------------------------------------------------
# CONVENIENCE FUNCTION
# -------------------------------------------------------------

def analyze_relationships(
    project_path: str
) -> Dict[str, Any]:
    """
    Convenience function for the rest of Project Archaeologist.

    Example:

        result = analyze_relationships("./my_project")
    """

    analyzer = RelationshipAnalyzer(project_path)

    return analyzer.analyze()


# -------------------------------------------------------------
# SIMPLE TEST WHEN RUN DIRECTLY
# -------------------------------------------------------------

if __name__ == "__main__":

    import sys

    # Use current directory if no path is provided
    project = sys.argv[1] if len(sys.argv) > 1 else "."

    result = analyze_relationships(project)

    print("\nPROJECT RELATIONSHIP ANALYSIS")
    print("=" * 40)

    if not result["success"]:
        print("Error:", result["error"])
        sys.exit(1)

    print(
        f"Python files analyzed: "
        f"{result['files_analyzed']}"
    )

    print(
        f"Relationships found: "
        f"{result['relationships_found']}"
    )

    print("\nDEPENDENCIES")
    print("-" * 40)

    for file, dependencies in result["dependencies"].items():

        print(f"\n{file}")

        for dependency in dependencies:
            print(f"  -> {dependency}")

    print("\nMOST CONNECTED FILES")
    print("-" * 40)

    for item in result["most_connected_files"]:

        print(
            f"{item['file']} | "
            f"incoming={item['incoming']} | "
            f"outgoing={item['outgoing']} | "
            f"total={item['total_relationships']}"
        )

    print("\nPOTENTIAL HOTSPOTS")
    print("-" * 40)

    for hotspot in result["hotspots"]:

        print(
            f"{hotspot['file']} | "
            f"{hotspot['total_relationships']} relationships"
        )

    if result["parse_errors"]:

        print("\nFILES WITH PARSE ERRORS")
        print("-" * 40)

        for error in result["parse_errors"]:

            print(
                f"{error['file']}: "
                f"{error['error']}"
            )
