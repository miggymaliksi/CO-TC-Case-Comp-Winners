"""Start a private loopback API for the desktop window; never install at startup."""

import os
from pathlib import Path
import signal
import socket
import sys

ROOT = Path(__file__).resolve().parent.parent
# Packaged launchers pass the original checkout, whose database/models stay in place.
if len(sys.argv) == 2:
    ROOT = Path(sys.argv[1]).resolve()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from local_ai_runtime import start, stop
import uvicorn


def main():
    # Whitelist the only model preference needed here. Never load cloud credentials.
    config = ROOT / ".env"
    if config.is_file():
        for line in config.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "SAVOR_LOCAL_MODEL":
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    # The OS assigns and reserves a free port, avoiding conflicts with VS Code.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        print(f"SAVOR_DESKTOP_PORT={listener.getsockname()[1]}", flush=True)

        # Handle Quit even during model startup so owned processes get cleaned up.
        def shutdown(*_):
            raise KeyboardInterrupt()

        signal.signal(signal.SIGTERM, shutdown)
        model_process = None
        try:
            model_process = start()
            server = uvicorn.Server(
                uvicorn.Config(
                    "backend.main:app",
                    host="127.0.0.1",
                    log_level="warning",
                    timeout_graceful_shutdown=2,
                )
            )
            server.run(sockets=[listener])
        finally:
            stop(model_process)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
