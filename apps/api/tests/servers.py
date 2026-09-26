import threading

from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class Route:
    """
    One canned response.

    head_length overrides the Content-Length answered to HEAD, so a host can
    understate what the following GET delivers. advertise_length=False makes
    GET stream until the connection closes, like a host without Content-Length.
    """

    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    head_length: int | None = None
    advertise_length: bool = True


class LoopbackServer:
    """Base for servers that bind an ephemeral loopback port on a thread."""

    def __init__(self, handler: type[BaseHTTPRequestHandler]) -> None:
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join()


class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


class Server(LoopbackServer):
    """Answers from a route table and records every request line."""

    def __init__(self, routes: dict[str, Route]) -> None:
        self.routes = routes
        self.hits: list[str] = []
        super().__init__(self._handler())

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(QuietHandler):
            def do_GET(self) -> None:
                self._respond(head_only=False)

            def do_HEAD(self) -> None:
                self._respond(head_only=True)

            def _respond(self, *, head_only: bool) -> None:
                server.hits.append(f"{self.command} {self.path}")
                route = server.routes.get(self.path)
                if route is None:
                    self.send_error(404)
                    return

                self.send_response(route.status)
                for name, value in route.headers.items():
                    self.send_header(name, value)
                length = self._advertised_length(route, head_only=head_only)
                if length is not None:
                    self.send_header("Content-Length", str(length))
                self.end_headers()
                if not head_only:
                    self.wfile.write(route.body)

            @staticmethod
            def _advertised_length(route: Route, *, head_only: bool) -> int | None:
                if head_only and route.head_length is not None:
                    return route.head_length
                return len(route.body) if route.advertise_length else None

        return Handler


class UpstashStub(LoopbackServer):
    """Upstash REST server: INCR, EXPIRE and TTL as POST /<command>/<key>."""

    def __init__(self) -> None:
        self.paths: list[str] = []
        self._counts: dict[str, int] = {}
        super().__init__(self._handler())

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        stub = self

        class Handler(QuietHandler):
            def do_POST(self) -> None:
                stub.paths.append(self.path)
                command, _, key = self.path.lstrip("/").partition("/")
                result = 60
                if command == "incr":
                    result = stub._counts[key] = stub._counts.get(key, 0) + 1  # noqa: SLF001
                body = f'{{"result": {result}}}'.encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler
