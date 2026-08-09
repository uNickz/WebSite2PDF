"""Typed, immutable option objects.

Options are split along the three axes they actually belong to:

* `PdfOptions` -- how the loaded page is painted into a PDF.
* `BrowserOptions` -- how the browser and its context are created.
* `RenderOptions` -- how navigation waits for the page to be ready.

Each object is a frozen dataclass, so defaults can be shared safely between
clients and calls without the aliasing hazard of mutable default arguments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from .errors import OptionsError

if TYPE_CHECKING:
    from collections.abc import Mapping

PaperFormat = Literal[
    "Letter", "Legal", "Tabloid", "Ledger", "A0", "A1", "A2", "A3", "A4", "A5", "A6"
]
"""Paper sizes Chromium understands by name."""

WaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]
"""Navigation milestone to wait for before rendering."""

MediaType = Literal["print", "screen"]
"""CSS media type to emulate."""

MIN_SCALE = 0.1
MAX_SCALE = 2.0
DEFAULT_TIMEOUT_MS = 30_000.0


@dataclass(frozen=True, slots=True)
class Margin:
    """Page margins, expressed in CSS units (`px`, `in`, `cm`, `mm`)."""

    top: str = "0"
    right: str = "0"
    bottom: str = "0"
    left: str = "0"

    @classmethod
    def uniform(cls, value: str) -> Margin:
        """Build a margin with the same value on all four sides.

        Args:
            value: CSS length, for example `"1cm"`.

        Returns:
            A margin applying `value` to every side.
        """
        return cls(top=value, right=value, bottom=value, left=value)

    def to_playwright(self) -> dict[str, str]:
        """Convert to the mapping Playwright's `page.pdf()` expects.

        Returns:
            A dict with `top`, `right`, `bottom` and `left` keys.
        """
        return {"top": self.top, "right": self.right, "bottom": self.bottom, "left": self.left}


@dataclass(frozen=True, slots=True)
class PdfOptions:
    """How the loaded page is painted into a PDF.

    Attributes:
        paper_format: Named paper size. Ignored when `width` or `height` is set.
        width: Explicit page width as a CSS length. Overrides `paper_format`.
        height: Explicit page height as a CSS length. Overrides `paper_format`.
        scale: Rendering scale between 0.1 and 2.0.
        landscape: Whether to use landscape orientation.
        margin: Page margins. `None` leaves Chromium's default.
        print_background: Whether to paint background graphics. Defaults to
            `True` because a page converted without its backgrounds rarely
            matches what the user saw.
        prefer_css_page_size: Whether an `@page` size in the document's CSS
            wins over `paper_format`.
        page_ranges: Pages to emit, for example `"1-3, 8"`. `None` emits all.
        display_header_footer: Whether to render the header and footer templates.
        header_template: HTML for the page header.
        footer_template: HTML for the page footer.
        outline: Whether to embed a document outline.
        tagged: Whether to emit a tagged (accessible) PDF.
    """

    paper_format: PaperFormat | None = "A4"
    width: str | None = None
    height: str | None = None
    scale: float = 1.0
    landscape: bool = False
    margin: Margin | None = None
    print_background: bool = True
    prefer_css_page_size: bool = False
    page_ranges: str | None = None
    display_header_footer: bool = False
    header_template: str | None = None
    footer_template: str | None = None
    outline: bool = False
    tagged: bool = False

    def __post_init__(self) -> None:
        """Validate values that Chromium would otherwise reject opaquely.

        Raises:
            OptionsError: If `scale` is out of range, or a header or footer
                template is supplied without enabling `display_header_footer`.
        """
        if not MIN_SCALE <= self.scale <= MAX_SCALE:
            message = f"scale must be between {MIN_SCALE} and {MAX_SCALE}, got {self.scale}"
            raise OptionsError(message)

        has_template = self.header_template is not None or self.footer_template is not None
        if has_template and not self.display_header_footer:
            message = (
                "header_template/footer_template are ignored unless "
                "display_header_footer=True is also set"
            )
            raise OptionsError(message)

    def to_playwright(self) -> dict[str, Any]:
        """Convert to keyword arguments for Playwright's `page.pdf()`.

        Returns:
            Only the keys this object actually constrains, so Chromium's own
            defaults apply to everything else.
        """
        options: dict[str, Any] = {
            "scale": self.scale,
            "landscape": self.landscape,
            "print_background": self.print_background,
            "prefer_css_page_size": self.prefer_css_page_size,
            "display_header_footer": self.display_header_footer,
            "outline": self.outline,
            "tagged": self.tagged,
        }

        # Playwright gives width/height priority over format; make that explicit
        # rather than sending contradictory values.
        if self.width is not None or self.height is not None:
            if self.width is not None:
                options["width"] = self.width
            if self.height is not None:
                options["height"] = self.height
        elif self.paper_format is not None:
            options["format"] = self.paper_format

        if self.margin is not None:
            options["margin"] = self.margin.to_playwright()
        if self.page_ranges is not None:
            options["page_ranges"] = self.page_ranges
        if self.header_template is not None:
            options["header_template"] = self.header_template
        if self.footer_template is not None:
            options["footer_template"] = self.footer_template

        return options


@dataclass(frozen=True, slots=True)
class BrowserOptions:
    """How the browser process and its context are created.

    Attributes:
        headless: Whether to run without a visible window.
        args: Extra Chromium command-line switches.
        executable_path: Path to a specific Chromium build.
        channel: Branded channel such as `"chrome"` or `"msedge"`.
        launch_timeout: Milliseconds to wait for the browser to start.
        user_agent: Override for the `User-Agent` header.
        viewport: Viewport size as `(width, height)`. `None` disables the
            fixed viewport.
        device_scale_factor: Device pixel ratio.
        locale: BCP 47 locale, for example `"it-IT"`.
        timezone_id: IANA timezone, for example `"Europe/Rome"`.
        ignore_https_errors: Whether to accept invalid TLS certificates.
        extra_http_headers: Headers added to every request.
        http_credentials: `(username, password)` for HTTP basic auth.
        cookies: Cookies installed on the context before navigation, in
            Playwright's cookie format.
    """

    headless: bool = True
    args: tuple[str, ...] = ()
    executable_path: str | None = None
    channel: str | None = None
    launch_timeout: float = DEFAULT_TIMEOUT_MS
    user_agent: str | None = None
    viewport: tuple[int, int] | None = (1280, 720)
    device_scale_factor: float = 1.0
    locale: str | None = None
    timezone_id: str | None = None
    ignore_https_errors: bool = False
    extra_http_headers: Mapping[str, str] | None = None
    http_credentials: tuple[str, str] | None = None
    cookies: tuple[Mapping[str, Any], ...] = ()

    def to_launch_kwargs(self) -> dict[str, Any]:
        """Convert to keyword arguments for `playwright.chromium.launch()`.

        Returns:
            Only the keys this object constrains.
        """
        options: dict[str, Any] = {
            "headless": self.headless,
            "timeout": self.launch_timeout,
        }
        if self.args:
            options["args"] = list(self.args)
        if self.executable_path is not None:
            options["executable_path"] = self.executable_path
        if self.channel is not None:
            options["channel"] = self.channel
        return options

    def to_context_kwargs(self) -> dict[str, Any]:
        """Convert to keyword arguments for `browser.new_context()`.

        Returns:
            Only the keys this object constrains.
        """
        options: dict[str, Any] = {
            "ignore_https_errors": self.ignore_https_errors,
            "device_scale_factor": self.device_scale_factor,
        }
        if self.viewport is not None:
            width, height = self.viewport
            options["viewport"] = {"width": width, "height": height}
        else:
            options["no_viewport"] = True
        if self.user_agent is not None:
            options["user_agent"] = self.user_agent
        if self.locale is not None:
            options["locale"] = self.locale
        if self.timezone_id is not None:
            options["timezone_id"] = self.timezone_id
        if self.extra_http_headers:
            options["extra_http_headers"] = dict(self.extra_http_headers)
        if self.http_credentials is not None:
            username, password = self.http_credentials
            options["http_credentials"] = {"username": username, "password": password}
        return options


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """How navigation waits for the page to become ready.

    Attributes:
        wait_until: Navigation milestone to wait for. `"networkidle"` is the
            safest choice for pages that fetch content after load.
        timeout: Navigation timeout in milliseconds. `0` disables it.
        emulate_media: CSS media type to emulate. Chromium renders PDFs with
            `print` media by default; pass `"screen"` to reproduce the
            on-screen appearance instead.
        wait_for_selector: CSS selector to wait for before rendering.
        extra_wait: Additional idle time in milliseconds after the page is
            ready. A last resort for animations that cannot be observed.
    """

    wait_until: WaitUntil = "load"
    timeout: float = DEFAULT_TIMEOUT_MS
    emulate_media: MediaType | None = None
    wait_for_selector: str | None = None
    extra_wait: float = 0.0

    def __post_init__(self) -> None:
        """Validate the timing values.

        Raises:
            OptionsError: If `timeout` or `extra_wait` is negative.
        """
        if self.timeout < 0:
            message = f"timeout must not be negative, got {self.timeout}"
            raise OptionsError(message)
        if self.extra_wait < 0:
            message = f"extra_wait must not be negative, got {self.extra_wait}"
            raise OptionsError(message)
