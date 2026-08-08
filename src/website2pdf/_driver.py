"""Per-thread sharing of the synchronous Playwright driver.

Playwright's sync API drives its event loop with greenlets inside the calling
thread. A second ``sync_playwright().start()`` on that thread therefore sees a
loop already running and fails with a message telling the caller to use the
async API -- confusing advice for someone who never touched asyncio.

Sharing one reference-counted driver per thread lets several :class:`Client`
instances coexist. Each client still launches its own browser, so their
configurations stay independent.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from playwright.sync_api import Playwright


class _ThreadState(threading.local):
    """Driver handle and reference count, private to each thread."""

    playwright: Playwright | None = None
    refcount: int = 0


_STATE = _ThreadState()


def acquire() -> Playwright:
    """Return this thread's driver, starting it on first use.

    Returns:
        The running Playwright driver for the calling thread.
    """
    if _STATE.playwright is None:
        _STATE.playwright = sync_playwright().start()
        _STATE.refcount = 0

    _STATE.refcount += 1
    return _STATE.playwright


def release() -> None:
    """Give up one reference, stopping the driver once the last one goes."""
    if _STATE.playwright is None:
        return

    _STATE.refcount -= 1
    if _STATE.refcount > 0:
        return

    playwright = _STATE.playwright
    _STATE.playwright = None
    _STATE.refcount = 0
    playwright.stop()
