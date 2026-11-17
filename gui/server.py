#!/usr/bin/env python3
"""
Local graphical interface for the "Enquête sur une maladie" project.

Starts a small web server on 127.0.0.1 (standard library only, no extra
dependencies) and opens the interface in the default browser. From there you
can run the ./run.sh pipeline, follow its log live, stop it, and explore the
CSV results and generated figures.

Usage:
    python3 gui/server.py [--port 8765] [--no-browser]
"""

import argparse
import csv
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

GUI_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GUI_DIR.parent
STATIC_DIR = GUI_DIR / "static"
RESULTS_DIR = PROJECT_DIR / "results"
LOG_DIR = PROJECT_DIR / "logs"
ARCHIVE_DIR = PROJECT_DIR / "archive"
DATA_DIR = PROJECT_DIR / "data"
RUN_SCRIPT = PROJECT_DIR / "run.sh"

CSV_FILES = [
    "age_diabetes.csv",
    "bmi_diabetes_comparison.csv",
    "age_bmi_diabetes_python.csv",
    "age_bmi_diabetes.csv",
]

IMAGE_FILES = [
    "obesity_age.png",
    "bmi_age_comparison.png",
]


# --------------------------------------------------
# 2. Pipeline runner (one run at a time)
# --------------------------------------------------

REQUIRED_MODULES = "import pandas, numpy, matplotlib"


def find_python():
    """
    Return the first Python interpreter that has the project's dependencies.

    On macOS, "python3" is often Apple's /usr/bin/python3, which does not have
    pandas, while the packages are installed for a Homebrew Python such as
    python3.12. run.sh calls "python3", so we look for a suitable interpreter.
    """
    names = ["python3", "python3.14", "python3.13", "python3.12", "python3.11"]
    extra_dirs = ["/opt/homebrew/bin", "/usr/local/bin"]

    candidates = [sys.executable]
    for name in names:
        found = shutil.which(name)
        if found:
            candidates.append(found)
        for directory in extra_dirs:
            path = os.path.join(directory, name)
            if os.access(path, os.X_OK):
                candidates.append(path)

    seen = set()
    for candidate in candidates:
        real = os.path.realpath(candidate)
        if real in seen:
            continue
        seen.add(real)
        try:
            result = subprocess.run(
                [candidate, "-c", REQUIRED_MODULES],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return candidate
    return None


def python_shim_dir(python):
    """Create a temporary directory whose "python3" points to the given interpreter."""
    shim_dir = Path(tempfile.mkdtemp(prefix="enquete-gui-python-"))
    (shim_dir / "python3").symlink_to(python)
    return shim_dir


def _restore_default_signals():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def _signal_group(process, sig):
    try:
        os.killpg(process.pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


class PipelineRunner:

    def __init__(self):
        self.lock = threading.Lock()
        self.process = None
        self.lines = []
        self.exit_code = None
        self.started_at = None
        self.finished_at = None
        self.options = {}
        self.stopping = False
        self.shim = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, force_download, skip_tests):
        with self.lock:
            if self.is_running():
                return False

            args = ["bash", str(RUN_SCRIPT)]
            if force_download:
                args.append("-f")
            if skip_tests:
                args.append("-s")

            env = dict(os.environ, PYTHONUNBUFFERED="1")

            self.lines = []
            python = find_python()
            self.shim = None
            if python:
                # Put a "python3" with the dependencies first on PATH for run.sh
                self.shim = python_shim_dir(python)
                env["PATH"] = f"{self.shim}{os.pathsep}{env.get('PATH', '')}"
                self.lines.append(f"[GUI] Using Python: {python}")
            else:
                self.lines.append(
                    "[GUI] No Python with pandas, numpy and matplotlib was found. "
                    "Install them with: python3 -m pip install -r requirements.txt"
                )
            self.exit_code = None
            self.stopping = False
            self.started_at = datetime.now().isoformat(timespec="seconds")
            self.finished_at = None
            self.options = {
                "force_download": force_download,
                "skip_tests": skip_tests,
            }

            # New session so that "stop" can signal the whole process group,
            # exactly like pressing Ctrl+C in a terminal.
            self.process = subprocess.Popen(
                args,
                cwd=PROJECT_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                # If this server was started in the background, SIGINT is
                # inherited as "ignored" and run.sh could not trap it.
                preexec_fn=_restore_default_signals,
            )

            threading.Thread(target=self._read_output, daemon=True).start()
            return True

    def _read_output(self):
        process = self.process
        shim = self.shim  # captured now: a later run may replace self.shim
        for raw in iter(process.stdout.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            with self.lock:
                self.lines.append(line)
        process.stdout.close()
        code = process.wait()
        if shim:
            shutil.rmtree(shim, ignore_errors=True)
        with self.lock:
            self.exit_code = code
            self.finished_at = datetime.now().isoformat(timespec="seconds")

    def stop(self):
        with self.lock:
            if not self.is_running():
                return False
            self.stopping = True
            process = self.process
            # SIGINT triggers run.sh's trap, which removes temporary files
            _signal_group(process, signal.SIGINT)

        # Escalate if the pipeline has not exited after a few seconds
        def escalate():
            if process.poll() is None:
                _signal_group(process, signal.SIGTERM)

        threading.Timer(5.0, escalate).start()
        return True

    def status(self, offset):
        with self.lock:
            running = self.is_running()
            if running:
                state = "stopping" if self.stopping else "running"
            elif self.started_at is None:
                state = "idle"
            elif self.exit_code == 0:
                state = "success"
            elif self.stopping:
                state = "stopped"
            else:
                state = "failed"

            offset = max(0, min(offset, len(self.lines)))
            return {
                "state": state,
                "exit_code": self.exit_code,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "options": self.options,
                "offset": len(self.lines),
                "lines": self.lines[offset:],
            }


RUNNER = PipelineRunner()


# --------------------------------------------------
# 3. Helpers
# --------------------------------------------------

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {"columns": reader.fieldnames or [], "rows": list(reader)}


def file_info(path):
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def list_files(directory, pattern):
    if not directory.is_dir():
        return []
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return [file_info(p) for p in files if p.is_file()]


def results_payload():
    tables = {}
    for name in CSV_FILES:
        path = RESULTS_DIR / name
        if path.is_file():
            data = read_csv(path)
            data.update(file_info(path))
            tables[name] = data

    images = [file_info(RESULTS_DIR / n) for n in IMAGE_FILES if (RESULTS_DIR / n).is_file()]

    dataset = {
        "zip": (DATA_DIR / "LLCP2022ASC.zip").is_file(),
        "asc": (DATA_DIR / "LLCP2022.ASC").is_file(),
    }

    return {
        "tables": tables,
        "images": images,
        "dataset": dataset,
        "logs": list_files(LOG_DIR, "run_*.log"),
        "archives": list_files(ARCHIVE_DIR, "results_*.tar.gz"),
    }


def safe_child(directory, name):
    """Return directory/name only if name is a plain file name inside directory."""
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None
    path = directory / name
    return path if path.is_file() else None


# --------------------------------------------------
# 4. HTTP handler
# --------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    server_version = "EnqueteMaladieGUI/1.0"

    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet

    # ---- response helpers ----

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type, download_name=None):
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.end_headers()
        self.wfile.write(body)

    def not_found(self):
        self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    # ---- GET ----

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path

        if path in ("/", "/index.html"):
            return self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        if path == "/api/results":
            return self.send_json(results_payload())

        if path == "/api/status":
            query = parse_qs(url.query)
            try:
                offset = int(query.get("offset", ["0"])[0])
            except ValueError:
                offset = 0
            return self.send_json(RUNNER.status(offset))

        if path.startswith("/files/results/"):
            name = path.rsplit("/", 1)[-1]
            target = safe_child(RESULTS_DIR, name)
            if target is None:
                return self.not_found()
            if target.suffix == ".png":
                return self.send_file(target, "image/png")
            if target.suffix == ".csv":
                return self.send_file(target, "text/csv; charset=utf-8", target.name)
            return self.not_found()

        if path.startswith("/files/logs/"):
            target = safe_child(LOG_DIR, path.rsplit("/", 1)[-1])
            if target is None or target.suffix != ".log":
                return self.not_found()
            return self.send_file(target, "text/plain; charset=utf-8")

        if path.startswith("/files/archive/"):
            target = safe_child(ARCHIVE_DIR, path.rsplit("/", 1)[-1])
            if target is None or not target.name.endswith(".tar.gz"):
                return self.not_found()
            return self.send_file(target, "application/gzip", target.name)

        if path == "/files/report":
            target = PROJECT_DIR / "docs" / "rapport.pdf"
            if not target.is_file():
                return self.not_found()
            return self.send_file(target, "application/pdf")

        return self.not_found()

    # ---- POST ----

    def do_POST(self):
        # Only accept JSON requests from this page. A cross-site form cannot
        # send this content type without a CORS preflight, which we never allow.
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self.send_json({"error": "JSON required"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self.send_json({"error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)

        path = urlparse(self.path).path

        if path == "/api/run":
            started = RUNNER.start(
                force_download=bool(body.get("force_download")),
                skip_tests=bool(body.get("skip_tests")),
            )
            if not started:
                return self.send_json({"error": "A run is already in progress."}, HTTPStatus.CONFLICT)
            return self.send_json({"ok": True})

        if path == "/api/stop":
            return self.send_json({"ok": RUNNER.stop()})

        return self.not_found()


# --------------------------------------------------
# 5. Entry point
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Graphical interface for the diabetes analysis project.")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765).")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically.")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"

    print(f"Enquête sur une maladie — GUI running at {url}")
    print("Press Ctrl+C to quit.")

    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        RUNNER.stop()
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
