"""Shared fixtures.

The integration tests serve their own HTML over loopback instead of hitting a
real site, so the suite is deterministic and works offline.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class _QuietHandler(SimpleHTTPRequestHandler):
    """A static file handler that does not spam the test output."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Swallow the per-request access log."""


@pytest.fixture(scope="session")
def http_server() -> Iterator[str]:
    """Serve ``tests/fixtures`` over loopback for the duration of the session.

    Yields:
        The base URL of the running server, without a trailing slash.
    """
    handler = partial(_QuietHandler, directory=str(FIXTURES_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
