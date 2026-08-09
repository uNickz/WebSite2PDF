"""Translation of Playwright failures into this library's exception types.

Playwright signals every problem with a single `Error` class, so the useful
distinctions live in the message text. Keeping that string matching in one
place means the sync and async clients stay in agreement about what a given
failure means.
"""

from __future__ import annotations

from .errors import (
    BrowserLaunchError,
    BrowserNotInstalledError,
    NavigationError,
    RenderError,
    WebSite2PDFError,
)

_MISSING_BROWSER_MARKERS = (
    "executable doesn't exist",
    "playwright install",
    "looks like playwright was just installed",
)


def translate_launch_error(exc: Exception) -> WebSite2PDFError:
    """Classify a browser launch failure.

    Args:
        exc: The exception raised by Playwright.

    Returns:
        [`BrowserNotInstalledError`][website2pdf.BrowserNotInstalledError] when the browser
        binary is missing, otherwise
        [`BrowserLaunchError`][website2pdf.BrowserLaunchError].
    """
    text = str(exc)
    lowered = text.lower()
    if any(marker in lowered for marker in _MISSING_BROWSER_MARKERS):
        return BrowserNotInstalledError()

    message = f"could not launch Chromium: {text}"
    return BrowserLaunchError(message)


def navigation_timeout(url: str, timeout: float) -> NavigationError:
    """Build the error for a navigation that ran out of time.

    Args:
        url: The URL being loaded.
        timeout: The timeout in milliseconds that was exceeded.

    Returns:
        A navigation error naming both the URL and the budget.
    """
    message = (
        f"timed out after {timeout:.0f} ms loading {url}; "
        f"raise RenderOptions.timeout or relax RenderOptions.wait_until"
    )
    return NavigationError(message)


def navigation_failed(url: str, exc: Exception) -> NavigationError:
    """Build the error for a navigation that failed outright.

    Args:
        url: The URL being loaded.
        exc: The exception raised by Playwright.

    Returns:
        A navigation error carrying Playwright's own explanation.
    """
    message = f"could not load {url}: {exc}"
    return NavigationError(message)


def render_failed(url: str, exc: Exception) -> RenderError:
    """Build the error for a page that loaded but could not be printed.

    Args:
        url: The URL that was loaded.
        exc: The exception raised by Playwright.

    Returns:
        A render error carrying Playwright's own explanation.
    """
    message = f"could not render {url} to PDF: {exc}"
    return RenderError(message)
