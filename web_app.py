import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from urllib.parse import urlparse


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(PROJECT_ROOT, "web")


def extract_hotspots(output):
    marker = "POTENTIAL HOTSPOTS"

    if marker not in output:
        return "No hotspots found."

    section = output.split(marker, 1)[1]

    lines = []

    for line in section.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines) if lines else "No hotspots found."


def find_project_root(folder):
    entries = [
        os.path.join(folder, name)
        for name in os.listdir(folder)
    ]

    directories = [
        path for path in entries
        if os.path.isdir(path)
    ]

    files = [
        path for path in entries
        if os.path.isfile(path)
    ]

    # If ZIP contains one top-level folder, analyze that folder.
    if len(directories) == 1 and not files:
        return directories[0]

    return folder


class ProjectArchaeologistHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/analyze":
            self.handle_analysis()
            return

        self.send_error(404, "Not found")

    def handle_analysis(self):

        temp_dir = None

        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            if content_length <= 0:
                self.send_json({
                    "success": False,
                    "error": "No project ZIP file was uploaded."
                }, 400)
                return

            # Limit upload size to 50 MB.
            max_size = 50 * 1024 * 1024

            if content_length > max_size:
                self.send_json({
                    "success": False,
                    "error": "ZIP file is too large. Maximum size is 50 MB."
                }, 400)
                return

            zip_data = self.rfile.read(content_length)

            temp_dir = tempfile.mkdtemp(
                prefix="archaeologist_"
            )

            zip_path = os.path.join(
                temp_dir,
                "project.zip"
            )

            with open(zip_path, "wb") as f:
                f.write(zip_data)

            extract_dir = os.path.join(
                temp_dir,
                "project"
            )

            os.makedirs(extract_dir)

            # Safely extract ZIP.
            with zipfile.ZipFile(zip_path, "r") as archive:

                for member in archive.infolist():

                    member_path = os.path.abspath(
                        os.path.join(
                            extract_dir,
                            member.filename
                        )
                    )

                    if not member_path.startswith(
                        os.path.abspath(extract_dir)
                        + os.sep
                    ):
                        raise ValueError(
                            "Unsafe ZIP file detected."
                        )

                archive.extractall(extract_dir)

            project_path = find_project_root(extract_dir)

            # Run main analyzer on uploaded project.
            analyzer_result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(
                        PROJECT_ROOT,
                        "analyzer.py"
                    ),
                    project_path
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            analyzer_output = analyzer_result.stdout

            # Run relationship analyzer on uploaded project.
            relationship_result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(
                        PROJECT_ROOT,
                        "relationship_analysis.py"
                    ),
                    project_path
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            relationship_output = relationship_result.stdout

            files_match = __import__("re").search(
                r"Total Files\s*:\s*(\d+)",
                analyzer_output
            )

            lines_match = __import__("re").search(
                r"Total Lines of Code\s*:\s*(\d+)",
                analyzer_output
            )

            functions_match = __import__("re").search(
                r"Functions Detected\s*:\s*(\d+)",
                analyzer_output
            )

            todos_match = __import__("re").search(
                r"Total TODOs Found\s*:\s*(\d+)",
                analyzer_output
            )

            response = {
                "success": (
                    analyzer_result.returncode == 0
                    and relationship_result.returncode == 0
                ),

                "files": int(files_match.group(1))
                if files_match else 0,

                "lines": int(lines_match.group(1))
                if lines_match else 0,

                "functions": int(functions_match.group(1))
                if functions_match else 0,

                "todos": int(todos_match.group(1))
                if todos_match else 0,

                "analysis": analyzer_output,

                "relationships": relationship_output,

                "hotspots": extract_hotspots(
                    relationship_output
                ),

                "error": (
                    analyzer_result.stderr
                    + "\n"
                    + relationship_result.stderr
                ).strip()
            }

            self.send_json(response, 200)

        except zipfile.BadZipFile:

            self.send_json({
                "success": False,
                "error": "The uploaded file is not a valid ZIP file."
            }, 400)

        except Exception as e:

            self.send_json({
                "success": False,
                "error": str(e)
            }, 500)

        finally:

            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

    def send_json(self, response, status_code):

        data = json.dumps(response).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(data))
        )

        self.end_headers()

        self.wfile.write(data)


def run_server():

    port = int(
        os.environ.get("PORT", 8000)
    )

    server_address = (
        "0.0.0.0",
        port
    )

    server = http.server.ThreadingHTTPServer(
        server_address,
        ProjectArchaeologistHandler
    )

    print("=" * 55)
    print("       PROJECT ARCHAEOLOGIST WEB SERVER")
    print("=" * 55)
    print()
    print("Website running on port:")
    print(port)
    print()
    print("Press CTRL+C to stop the server.")
    print()

    server.serve_forever()


if __name__ == "__main__":
    run_server()