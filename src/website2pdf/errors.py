"""Exception hierarchy raised by :mod:`website2pdf`.

Every exception derives from :class:`WebSite2PDFError`, so callers can catch the
whole library with a single ``except`` clause.
"""

from __future__ import annotations


class WebSite2PDFError(Exception):
    """Base class for every error raised by this library."""


class BrowserNotInstalledError(WebSite2PDFError):
    """The Playwright browser binary has not been downloaded yet."""

    def __init__(self, browser: str = "chromium") -> None:
        """Build the error with an actionable install hint.

        Args:
            browser: Name of the missing Playwright browser.
        """
        message = (
            f"The Playwright {browser} browser is not installed. "
            f"Run `playwright install {browser}` "
            f"(or `python -m playwright install {browser}`) and try again."
        )
        super().__init__(message)


class BrowserLaunchError(WebSite2PDFError):
    """The browser is installed but could not be started."""


class InvalidTargetError(WebSite2PDFError):
    """The target is neither a supported URL nor an existing local file."""


class NavigationError(WebSite2PDFError):
    """The page could not be loaded within the configured timeout."""


class RenderError(WebSite2PDFError):
    """The page loaded but could not be painted into a PDF."""


class OptionsError(WebSite2PDFError, ValueError):
    """An option value, or a combination of options, is invalid."""
