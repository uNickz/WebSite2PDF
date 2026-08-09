"""Synchronous client for converting pages to PDF."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, overload

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from . import _driver
from ._browser import (
    navigation_failed,
    navigation_timeout,
    render_failed,
    translate_launch_error,
)
from ._naming import DEFAULT_TEMPLATE, build_filename, deduplicate, resolve_destination
from ._targets import normalize_target
from .errors import RenderError
from .options import BrowserOptions, PdfOptions, RenderOptions

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import TracebackType

    from playwright.sync_api import Browser, Playwright


class Client:
    """Convert web pages and local HTML files to PDF with headless Chromium.

    The browser is started once and reused across conversions; each conversion
    runs in its own browser context, so cookies and storage never leak between
    pages.

    Use it as a context manager so the browser is always torn down:

    ```python
    with Client() as client:
        pdf = client.convert("https://example.com")
    ```

    Calling `convert()` on a client that has not been started will start it
    implicitly, in which case `close()` is the caller's responsibility.

    Note:
        Playwright's synchronous driver runs an event loop on the calling
        thread, so `asyncio.run()` will fail on that thread while a client is
        open. In an asyncio program use [`AsyncClient`][website2pdf.AsyncClient]
        instead. Several `Client` instances on one thread are fine: they
        share one reference-counted driver.
    """

    def __init__(
        self,
        *,
        pdf_options: PdfOptions | None = None,
        browser_options: BrowserOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> None:
        """Configure the defaults applied to every conversion.

        Args:
            pdf_options: Default PDF rendering options.
            browser_options: Browser launch and context options.
            render_options: Default navigation and waiting options.
        """
        self.pdf_options = pdf_options or PdfOptions()
        self.browser_options = browser_options or BrowserOptions()
        self.render_options = render_options or RenderOptions()
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def __enter__(self) -> Client:
        """Start the browser.

        Returns:
            This client, ready for use.
        """
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Shut the browser down, whether or not the block succeeded."""
        self.close()

    @property
    def is_running(self) -> bool:
        """Whether the browser is currently started."""
        return self._browser is not None

    def start(self) -> None:
        """Start the browser if it is not already running.

        Calling this on a running client is a no-op rather than an error, so a
        client can be started and stopped repeatedly.

        Raises:
            BrowserNotInstalledError: If the Chromium binary is missing.
            BrowserLaunchError: If Chromium is present but will not start.
        """
        if self._browser is not None:
            return

        playwright = _driver.acquire()
        try:
            browser = playwright.chromium.launch(**self.browser_options.to_launch_kwargs())
        except PlaywrightError as exc:
            _driver.release()
            raise translate_launch_error(exc) from exc

        self._playwright = playwright
        self._browser = browser

    def close(self) -> None:
        """Shut the browser down. Safe to call more than once."""
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright = None
            _driver.release()

    @overload
    def convert(
        self,
        target: str | Path,
        dest: None = None,
        *,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> bytes: ...

    @overload
    def convert(
        self,
        target: str | Path,
        dest: str | Path,
        *,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> Path: ...

    def convert(
        self,
        target: str | Path,
        dest: str | Path | None = None,
        *,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> bytes | Path:
        """Render a single page to PDF.

        Args:
            target: URL, `file://` URL, or path to a local HTML file.
            dest: Where to write the PDF. When omitted the PDF is returned as
                bytes. May be a file name, a name containing `{title}`, or an
                existing directory.
            pdf_options: Overrides this client's PDF options for this call.
            render_options: Overrides this client's render options for this call.

        Returns:
            The PDF bytes when `dest` is omitted, otherwise the path written.

        Raises:
            InvalidTargetError: If `target` is not a usable URL or file.
            NavigationError: If the page could not be loaded.
            RenderError: If the page could not be printed.
        """
        data, title = self._render(target, pdf_options, render_options)
        if dest is None:
            return data

        path = resolve_destination(dest, title)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    @overload
    def convert_many(
        self,
        targets: Iterable[str | Path],
        dest_dir: None = None,
        *,
        filename_template: str = DEFAULT_TEMPLATE,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> list[bytes]: ...

    @overload
    def convert_many(
        self,
        targets: Iterable[str | Path],
        dest_dir: str | Path,
        *,
        filename_template: str = DEFAULT_TEMPLATE,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> list[Path]: ...

    def convert_many(
        self,
        targets: Iterable[str | Path],
        dest_dir: str | Path | None = None,
        *,
        filename_template: str = DEFAULT_TEMPLATE,
        pdf_options: PdfOptions | None = None,
        render_options: RenderOptions | None = None,
    ) -> list[bytes] | list[Path]:
        """Render several pages to PDF, one after another.

        Pages that share a title do not overwrite each other; the second and
        later files gain a `" (2)"` suffix.

        Args:
            targets: URLs or local HTML files.
            dest_dir: Directory to write into. Created if missing. When omitted
                the PDFs are returned as bytes.
            filename_template: Name template for each file. `{title}` is the
                only supported placeholder.
            pdf_options: Overrides this client's PDF options for this call.
            render_options: Overrides this client's render options for this call.

        Returns:
            A list of PDF bytes when `dest_dir` is omitted, otherwise the list
            of paths written, in input order.
        """
        if dest_dir is None:
            return [self._render(target, pdf_options, render_options)[0] for target in targets]

        directory = Path(dest_dir)
        directory.mkdir(parents=True, exist_ok=True)

        used: set[str] = set()
        written: list[Path] = []
        for target in targets:
            data, title = self._render(target, pdf_options, render_options)
            name = deduplicate(build_filename(title, filename_template), used)
            used.add(name)
            path = directory / name
            path.write_bytes(data)
            written.append(path)
        return written

    def _ensure_browser(self) -> Browser:
        """Start the browser if needed and hand back a usable handle.

        Returns:
            The running browser.

        Raises:
            RenderError: If the browser is unexpectedly absent after starting.
        """
        self.start()
        browser = self._browser
        if browser is None:  # pragma: no cover - start() guarantees a browser
            message = "the browser is not running"
            raise RenderError(message)
        return browser

    def _render(
        self,
        target: str | Path,
        pdf_options: PdfOptions | None,
        render_options: RenderOptions | None,
    ) -> tuple[bytes, str]:
        """Load one page in a fresh context and print it.

        Args:
            target: URL or local HTML file.
            pdf_options: PDF options for this call, or `None` for the default.
            render_options: Render options for this call, or `None` for the default.

        Returns:
            A `(pdf_bytes, page_title)` pair.

        Raises:
            NavigationError: If the page could not be loaded.
            RenderError: If the page could not be printed.
        """
        url = normalize_target(target)
        pdf = pdf_options or self.pdf_options
        render = render_options or self.render_options
        browser = self._ensure_browser()

        context = browser.new_context(**self.browser_options.to_context_kwargs())
        try:
            # Cookies go on the context, before navigation: adding them to an
            # already-navigated page requires being on the target domain.
            if self.browser_options.cookies:
                context.add_cookies(list(self.browser_options.cookies))  # type: ignore[arg-type]

            page = context.new_page()

            if render.emulate_media is not None:
                page.emulate_media(media=render.emulate_media)

            try:
                page.goto(url, wait_until=render.wait_until, timeout=render.timeout)
            except PlaywrightTimeoutError as exc:
                raise navigation_timeout(url, render.timeout) from exc
            except PlaywrightError as exc:
                raise navigation_failed(url, exc) from exc

            if render.wait_for_selector is not None:
                try:
                    page.wait_for_selector(render.wait_for_selector, timeout=render.timeout)
                except PlaywrightTimeoutError as exc:
                    raise navigation_timeout(url, render.timeout) from exc
            if render.extra_wait > 0:
                page.wait_for_timeout(render.extra_wait)

            title = page.title()
            try:
                data = page.pdf(**pdf.to_playwright())
            except PlaywrightError as exc:
                raise render_failed(url, exc) from exc

            return data, title
        finally:
            context.close()
