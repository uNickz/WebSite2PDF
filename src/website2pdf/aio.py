"""Asynchronous client for converting pages to PDF.

Mirrors :class:`website2pdf.Client`, but renders several pages concurrently in
independent browser contexts sharing a single browser process.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, overload

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from ._browser import (
    navigation_failed,
    navigation_timeout,
    render_failed,
    translate_launch_error,
)
from ._naming import DEFAULT_TEMPLATE, build_filename, deduplicate, resolve_destination
from ._targets import normalize_target
from .errors import OptionsError, RenderError
from .options import BrowserOptions, PdfOptions, RenderOptions

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import TracebackType

    from playwright.async_api import Browser, Playwright

DEFAULT_CONCURRENCY = 4


class AsyncClient:
    """Convert web pages and local HTML files to PDF, concurrently.

    Use it as an async context manager so the browser is always torn down::

        async with AsyncClient() as client:
            pdfs = await client.convert_many(urls)

    Concurrency is a property of the client rather than of a single call,
    because it caps how many browser contexts exist at once.
    """

    def __init__(
        self,
        *,
        pdf_options: PdfOptions | None = None,
        browser_options: BrowserOptions | None = None,
        render_options: RenderOptions | None = None,
        concurrency: int = DEFAULT_CONCURRENCY,
    ) -> None:
        """Configure the defaults applied to every conversion.

        Args:
            pdf_options: Default PDF rendering options.
            browser_options: Browser launch and context options.
            render_options: Default navigation and waiting options.
            concurrency: Maximum number of pages rendered at the same time.

        Raises:
            OptionsError: If ``concurrency`` is below one.
        """
        if concurrency < 1:
            message = f"concurrency must be at least 1, got {concurrency}"
            raise OptionsError(message)

        self.pdf_options = pdf_options or PdfOptions()
        self.browser_options = browser_options or BrowserOptions()
        self.render_options = render_options or RenderOptions()
        self.concurrency = concurrency
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def __aenter__(self) -> AsyncClient:
        """Start the browser.

        Returns:
            This client, ready for use.
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Shut the browser down, whether or not the block succeeded."""
        await self.close()

    @property
    def is_running(self) -> bool:
        """Whether the browser is currently started."""
        return self._browser is not None

    async def start(self) -> None:
        """Start the browser if it is not already running.

        Calling this on a running client is a no-op rather than an error.

        Raises:
            BrowserNotInstalledError: If the Chromium binary is missing.
            BrowserLaunchError: If Chromium is present but will not start.
        """
        if self._browser is not None:
            return

        playwright = await async_playwright().start()
        try:
            browser = await playwright.chromium.launch(**self.browser_options.to_launch_kwargs())
        except PlaywrightError as exc:
            await playwright.stop()
            raise translate_launch_error(exc) from exc

        self._playwright = playwright
        self._browser = browser

    async def close(self) -> None:
        """Shut the browser down. Safe to call more than once."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    @overload
    async def convert(
        self,
        target: str | Path,
        dest: None = None,
        *,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> bytes: ...

    @overload
    async def convert(
        self,
        target: str | Path,
        dest: str | Path,
        *,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> Path: ...

    async def convert(
        self,
        target: str | Path,
        dest: str | Path | None = None,
        *,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> bytes | Path:
        """Render a single page to PDF.

        Args:
            target: URL, ``file://`` URL, or path to a local HTML file.
            dest: Where to write the PDF. When omitted the PDF is returned as
                bytes. May be a file name, a name containing ``{title}``, or an
                existing directory.
            pdf_options: Overrides this client's PDF options for this call.
            render_options: Overrides this client's render options for this call.

        Returns:
            The PDF bytes when ``dest`` is omitted, otherwise the path written.

        Raises:
            InvalidTargetError: If ``target`` is not a usable URL or file.
            NavigationError: If the page could not be loaded.
            RenderError: If the page could not be printed.
        """
        data, title = await self._render(target, pdf_options, render_options)
        if dest is None:
            return data

        path = resolve_destination(dest, title)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return path

    @overload
    async def convert_many(
        self,
        targets: Iterable[str | Path],
        dest_dir: None = None,
        *,
        filename_template: str = DEFAULT_TEMPLATE,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> list[bytes]: ...

    @overload
    async def convert_many(
        self,
        targets: Iterable[str | Path],
        dest_dir: str | Path,
        *,
        filename_template: str = DEFAULT_TEMPLATE,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> list[Path]: ...

    async def convert_many(
        self,
        targets: Iterable[str | Path],
        dest_dir: str | Path | None = None,
        *,
        filename_template: str = DEFAULT_TEMPLATE,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> list[bytes] | list[Path]:
        """Render several pages to PDF, up to ``concurrency`` at a time.

        All pages are rendered before any file is written, so file names are
        assigned in input order and stay reproducible across runs. Pages that
        share a title do not overwrite each other; the second and later files
        gain a ``" (2)"`` suffix.

        Args:
            targets: URLs or local HTML files.
            dest_dir: Directory to write into. Created if missing. When omitted
                the PDFs are returned as bytes.
            filename_template: Name template for each file. ``{title}`` is the
                only supported placeholder.
            pdf_options: Overrides this client's PDF options for this call.
            render_options: Overrides this client's render options for this call.

        Returns:
            A list of PDF bytes when ``dest_dir`` is omitted, otherwise the list
            of paths written, in input order.
        """
        await self.start()
        semaphore = asyncio.Semaphore(self.concurrency)

        async def render_one(target: str | Path) -> tuple[bytes, str]:
            async with semaphore:
                return await self._render(target, pdf_options, render_options)

        rendered = await asyncio.gather(*(render_one(target) for target in targets))

        if dest_dir is None:
            return [data for data, _ in rendered]

        directory = Path(dest_dir)
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)

        used: set[str] = set()
        written: list[Path] = []
        for data, title in rendered:
            name = deduplicate(build_filename(title, filename_template), used)
            used.add(name)
            path = directory / name
            await asyncio.to_thread(path.write_bytes, data)
            written.append(path)
        return written

    async def _ensure_browser(self) -> Browser:
        """Start the browser if needed and hand back a usable handle.

        Returns:
            The running browser.

        Raises:
            RenderError: If the browser is unexpectedly absent after starting.
        """
        await self.start()
        browser = self._browser
        if browser is None:  # pragma: no cover - start() guarantees a browser
            message = "the browser is not running"
            raise RenderError(message)
        return browser

    async def _render(
        self,
        target: str | Path,
        pdf_options: PdfOptions | None,
        render_options: RenderOptions | None,
    ) -> tuple[bytes, str]:
        """Load one page in a fresh context and print it.

        Args:
            target: URL or local HTML file.
            pdf_options: PDF options for this call, or ``None`` for the default.
            render_options: Render options for this call, or ``None`` for the default.

        Returns:
            A ``(pdf_bytes, page_title)`` pair.

        Raises:
            NavigationError: If the page could not be loaded.
            RenderError: If the page could not be printed.
        """
        url = normalize_target(target)
        pdf = pdf_options or self.pdf_options
        render = render_options or self.render_options
        browser = await self._ensure_browser()

        context = await browser.new_context(**self.browser_options.to_context_kwargs())
        try:
            # Cookies go on the context, before navigation: adding them to an
            # already-navigated page requires being on the target domain.
            if self.browser_options.cookies:
                await context.add_cookies(list(self.browser_options.cookies))  # type: ignore[arg-type]

            page = await context.new_page()

            if render.emulate_media is not None:
                await page.emulate_media(media=render.emulate_media)

            try:
                await page.goto(url, wait_until=render.wait_until, timeout=render.timeout)
            except PlaywrightTimeoutError as exc:
                raise navigation_timeout(url, render.timeout) from exc
            except PlaywrightError as exc:
                raise navigation_failed(url, exc) from exc

            if render.wait_for_selector is not None:
                try:
                    await page.wait_for_selector(render.wait_for_selector, timeout=render.timeout)
                except PlaywrightTimeoutError as exc:
                    raise navigation_timeout(url, render.timeout) from exc
            if render.extra_wait > 0:
                await page.wait_for_timeout(render.extra_wait)

            title = await page.title()
            try:
                data = await page.pdf(**pdf.to_playwright())
            except PlaywrightError as exc:
                raise render_failed(url, exc) from exc

            return data, title
        finally:
            await context.close()
