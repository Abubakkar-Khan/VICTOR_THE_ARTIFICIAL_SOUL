"""Victor Desktop Launcher — Unifies API Server, Web Workshop, and Desktop Mascot."""

import os
from pathlib import Path
import sys
import threading
import time
import webbrowser

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import uvicorn
from victor.api.server import app
from victor.desktop.mascot import launch_desktop_mascot


def start_api_server():
    """Run uvicorn FastAPI server in background thread."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def main():
    # Start server thread
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()

    # Give server a moment to bind port
    time.sleep(1.2)

    # Open Workshop in browser
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

    # Launch desktop companion on main thread
    launch_desktop_mascot()


if __name__ == "__main__":
    main()
