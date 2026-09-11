"""Victor Desktop Launcher — Unifies API Server, Native Desktop App, and Companion."""

import os
from pathlib import Path
import sys
import threading
import time

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
    if "--mascot" in sys.argv:
        # Dedicated desktop mascot companion process
        launch_desktop_mascot()
        return

    # 1. Start backend server in daemon thread
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()

    # 2. Give server a moment to bind port
    time.sleep(1.0)

    # 3. Launch desktop companion in a daemon thread
    mascot_thread = threading.Thread(target=launch_desktop_mascot, daemon=True)
    mascot_thread.start()

    # 4. Resolve application icon
    icon_file = root_dir / "victor" / "sprite" / "icon.ico"
    if not icon_file.exists() and getattr(sys, "frozen", False):
        icon_file = Path(sys.executable).parent / "victor" / "sprite" / "icon.ico"

    # 5. Launch Full Native Desktop Application Window
    try:
        import webview
        window = webview.create_window(
            title="Victor // The Artificial Soul",
            url="http://127.0.0.1:8000",
            width=1160,
            height=760,
            min_size=(800, 600),
            background_color="#0A0B0D",
            text_select=True,
        )
        if icon_file.exists():
            webview.start(icon=str(icon_file))
        else:
            webview.start()
    except Exception as e:
        # Graceful fallback to default browser if native webview encounters an issue
        import webbrowser
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except Exception:
            pass
        # Keep process running for the companion
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
