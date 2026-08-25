from __future__ import annotations

from functools import partial
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from ctrlsolar.web.routes import ApiError, json_bytes, route_api

logger = logging.getLogger(__name__)


class DashboardServer:
    def __init__(self, controller, host: str = "0.0.0.0", port: int = 8080, history_store=None):
        self.controller = controller
        self.history_store = history_store
        self.host = host
        self.port = port
        static_dir = Path(__file__).with_name("static")
        handler = partial(
            DashboardRequestHandler,
            controller=controller,
            history_store=history_store,
            directory=static_dir,
        )
        self.server = ThreadingHTTPServer((host, port), handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    def start(self) -> None:
        logger.info("Dashboard listening on http://%s:%s", self.host, self.port)
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, controller, history_store=None, **kwargs):
        self.controller = controller
        self.history_store = history_store
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            try:
                status, payload = route_api(self.path, self.controller, self.history_store)
                self._send_json(payload, status=status)
            except ApiError as exc:
                self._send_json({"error": str(exc)}, status=exc.status)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return
        super().do_GET()

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        logger.debug(format, *args)
