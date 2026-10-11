import os
import sys
import threading
import time
import urllib.request


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def load_env_from_bundle() -> None:
    """Apply the bundled .env to os.environ BEFORE importing the app package."""
    env_path = resource_path(".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_env_from_bundle()

import uvicorn
import webview
from fastapi.staticfiles import StaticFiles

from app.main import app

STATIC_DIR = resource_path(os.path.join("app", "standalone_web"))
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="standalone_web")


def make_server(host: str, port: int) -> uvicorn.Server:
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    return uvicorn.Server(config)


def wait_for_server(host: str, port: int, timeout: float = 90.0) -> bool:
    url = f"http://{host}:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))

    server = make_server(host, port)
    server_thread = threading.Thread(
        target=lambda: server.run(), name="uvicorn", daemon=True
    )
    server_thread.start()

    if not wait_for_server(host, port):
        print("ERROR: local service did not start in time. Exiting.")
        sys.exit(1)

    print("=" * 60)
    print("  Nexus Banking AI - Desktop Platform")
    print(f"  Local service ready at http://{host}:{port}")
    print("  The application window is opening...")
    print("  Closing the window stops the platform.")
    print("=" * 60)

    try:
        window = webview.create_window(
            "Nexus Banking AI - Desktop Platform",
            url=f"http://{host}:{port}",
            width=1440,
            height=900,
            min_size=(1100, 720),
            background_color="#0f172a",
        )
        webview.start()
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()