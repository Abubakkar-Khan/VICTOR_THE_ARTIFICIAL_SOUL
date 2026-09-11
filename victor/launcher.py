"""Victor Desktop Launcher — Unifies API Server, Native Desktop App, and Companion."""

import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# When compiled with console=False, sys.stdout and sys.stderr are None.
# Redirect to devnull to prevent crashes in libraries trying to write to them.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import uvicorn
from victor.desktop.mascot import launch_desktop_mascot


def log_diag(msg: str):
    """Write startup diagnostics to launcher.log."""
    try:
        data_dir = (Path(sys.executable).parent if getattr(sys, "frozen", False) else root_dir) / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        with open(data_dir / "launcher.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def find_available_port(start_port: int = 8000, max_attempts: int = 25) -> int:
    """Find a guaranteed free TCP port, avoiding TIME_WAIT or occupied ports."""
    for port in range(start_port, start_port + max_attempts):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            s.bind(("127.0.0.1", port))
            s.listen(1)
            s.close()
            return port
        except OSError:
            s.close()
            continue
    return start_port


def wait_for_server(port: int, max_wait: float = 20.0) -> bool:
    """Actively poll server until /api/status responds HTTP 200."""
    start_time = time.time()
    status_url = f"http://127.0.0.1:{port}/api/status"
    while time.time() - start_time < max_wait:
        try:
            req = urllib.request.Request(status_url, headers={"User-Agent": "VictorLauncher"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    log_diag(f"Server verified online at {status_url}")
                    return True
        except Exception as ex:
            log_diag(f"Waiting for server at {status_url}: {ex}")
        time.sleep(0.35)
    log_diag(f"Server timed out after {max_wait}s")
    return False


def start_api_server(port: int):
    """Run uvicorn FastAPI server in background thread."""
    try:
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
        from victor.api.server import app
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", log_config=None)
        server = uvicorn.Server(config)
        server.run()
    except Exception as ex:
        log_diag(f"API server exception: {ex}")


def main():
    if "--mascot" in sys.argv:
        # Dedicated desktop mascot companion process
        launch_desktop_mascot()
        return

    # 1. Resolve available port
    port = int(os.environ.get("VICTOR_PORT", "0")) or find_available_port(8000)
    os.environ["VICTOR_PORT"] = str(port)

    # 2. Start backend server in daemon thread
    server_thread = threading.Thread(target=start_api_server, args=(port,), daemon=True)
    server_thread.start()

    # 3. Actively wait for server to bind and respond before presenting UI
    server_ready = wait_for_server(port, max_wait=15.0)

    # 4. Launch desktop companion in background thread
    mascot_thread = threading.Thread(target=launch_desktop_mascot, daemon=True)
    mascot_thread.start()

    # 5. Resolve application icon
    icon_file = root_dir / "victor" / "sprite" / "icon.ico"
    if not icon_file.exists() and getattr(sys, "frozen", False):
        icon_file = Path(sys.executable).parent / "victor" / "sprite" / "icon.ico"
        if not icon_file.exists():
            icon_file = Path(sys.executable).parent / "_internal" / "victor" / "sprite" / "icon.ico"

    target_url = f"http://127.0.0.1:{port}"

    # 6. Launch Full Native Desktop Application Window
    try:
        import webview
        window = webview.create_window(
            title="Victor // The Artificial Soul",
            url=target_url,
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
            webbrowser.open(target_url)
        except Exception:
            pass
        # Keep process running for the companion
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
