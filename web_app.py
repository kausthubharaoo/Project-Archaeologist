import http.server
import json
import os
import re
import subprocess
import sys
from urllib.parse import urlparse, parse_qs


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
        if line and not line.startswith("-"):
            lines.append(line)

    if not lines:
        return "No hotspots found."

    return "\n".join(lines)
class ProjectArchaeologistHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.path = "/index.html"
            return super().do_GET()

        if parsed.path == "/api/analyze":
            self.handle_analysis()
            return

        return super().do_GET()

    def handle_analysis(self):
        try:
            # Run main project analyzer
            analyzer_result = subprocess.run(
                [sys.executable, os.path.join(PROJECT_ROOT, "analyzer.py")],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            analyzer_output = analyzer_result.stdout

            # Run relationship analyzer
            relationship_result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(PROJECT_ROOT, "relationship_analysis.py")
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            relationship_output = relationship_result.stdout

            # Extract numbers from analyzer output
            files_match = re.search(
                r"Total Files\s*:\s*(\d+)", analyzer_output
            )

            lines_match = re.search(
                r"Total Lines of Code\s*:\s*(\d+)", analyzer_output
            )

            functions_match = re.search(
                r"Functions Detected\s*:\s*(\d+)", analyzer_output
            )

            todos_match = re.search(
                r"Total TODOs Found\s*:\s*(\d+)", analyzer_output
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

                "hotspots": extract_hotspots(relationship_output),

                "error": (
                    analyzer_result.stderr
                    + "\n"
                    + relationship_result.stderr
                ).strip()
            }

            self.send_json(response, 200)

        except Exception as e:
            self.send_json({
                "success": False,
                "files": 0,
                "lines": 0,
                "functions": 0,
                "todos": 0,
                "analysis": "",
                "relationships": "",
                "hotspots": "",
                "error": str(e)
            }, 500)

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
    port = int(os.environ.get("PORT", 8000))
    server_address = ("0.0.0.0", port)

    server = http.server.ThreadingHTTPServer(
        server_address,
        ProjectArchaeologistHandler
    )

    print("=" * 55)
    print("       PROJECT ARCHAEOLOGIST WEB SERVER")
    print("=" * 55)
    print()
    print("Website running at:")
    print(f"http://0.0.0.0:{port}")
    print()
    print("Press CTRL+C to stop the server.")
    print()

    server.serve_forever()


if __name__ == "__main__":
    run_server()