"""Render web pages and local HTML files to PDF.

Synchronous use::

    from website2pdf import Client

    with Client() as client:
        client.convert("https://example.com", "example.pdf")

Concurrent use::

    import asyncio
    from website2pdf import AsyncClient


    async def main() -> None:
        async with AsyncClient(concurrency=8) as client:
            await client.convert_many(urls, dest_dir="out/")


    asyncio.run(main())

Rendering requires the Chromium binary that Playwright manages. Install it
once with ``playwright install chromium``.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .aio import AsyncClient
from .client import Client
from .errors import (
    BrowserLaunchError,
    BrowserNotInstalledError,
    InvalidTargetError,
    NavigationError,
    OptionsError,
    RenderError,
    WebSite2PDFError,
)
from .options import (
    BrowserOptions,
    Margin,
    MediaType,
    PaperFormat,
    PdfOptions,
    RenderOptions,
    WaitUntil,
)

try:
    __version__ = version("website2pdf")
except PackageNotFoundError:  # pragma: no cover - only hit when running from a raw checkout
    __version__ = "0.0.0.dev0"

__all__ = [
    "AsyncClient",
    "BrowserLaunchError",
    "BrowserNotInstalledError",
    "BrowserOptions",
    "Client",
    "InvalidTargetError",
    "Margin",
    "MediaType",
    "NavigationError",
    "OptionsError",
    "PaperFormat",
    "PdfOptions",
    "RenderError",
    "RenderOptions",
    "WaitUntil",
    "WebSite2PDFError",
    "__version__",
]
