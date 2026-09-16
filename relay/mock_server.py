from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


@dataclass
class MockResponse:
    status: int = 200
    body: str = '{"ok": true, "source": "Relay mock"}'
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json; charset=utf-8"})


class MockServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, logger: Callable[[str], None] | None = None) -> None:
        self.host, self.port, self.logger = host, port, logger or (lambda _: None)
        self.routes: dict[str, MockResponse] = {"/": MockResponse()}
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._server is not None

    def set_route(self, path: str, response: MockResponse) -> None:
        path = path.strip() or "/"
        self.routes[path if path.startswith("/") else "/" + path] = response

    def start(self) -> None:
        if self.running:
            return
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def _reply(self) -> None:
                route = owner.routes.get(self.path.split("?", 1)[0], MockResponse(status=404, body=json.dumps({"error": "route not found"})))
                payload = route.body.encode("utf-8")
                self.send_response(route.status)
                headers = dict(route.headers); headers.setdefault("Content-Length", str(len(payload)))
                for key, value in headers.items(): self.send_header(key, value)
                self.end_headers()
                if self.command != "HEAD": self.wfile.write(payload)
                owner.logger(f"{self.command} {self.path} -> {route.status}")
            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = _reply
            def log_message(self, fmt: str, *args: object) -> None: return
        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.port = int(self._server.server_address[1])
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True); self._thread.start()
        self.logger(f"Mock server listening on http://{self.host}:{self.port}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown(); self._server.server_close(); self._server = None; self._thread = None
            self.logger("Mock server stopped")
