"""Command-line interface.

Installed as the `website2pdf` console script by the `cli` extra:

```bash
pip install "website2pdf[cli]"
```

Typer lives behind that extra so that importing the library from code does not
drag a CLI framework along with it.
"""

import asyncio
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, cast

from . import __version__
from .aio import AsyncClient
from .errors import WebSite2PDFError
from .options import BrowserOptions, Margin, PdfOptions, RenderOptions

try:
    import typer
except ModuleNotFoundError as exc:  # pragma: no cover - depends on the chosen extra
    _MISSING_TYPER = (
        "The website2pdf command line needs Typer, which is not installed.\n"
        'Install it with: pip install "website2pdf[cli]"'
    )
    raise SystemExit(_MISSING_TYPER) from exc

STDOUT = "-"


class PaperFormatChoice(str, Enum):
    """Paper sizes accepted by `--format`."""

    Letter = "Letter"
    Legal = "Legal"
    Tabloid = "Tabloid"
    Ledger = "Ledger"
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"


class WaitUntilChoice(str, Enum):
    """Navigation milestones accepted by `--wait-until`."""

    commit = "commit"
    domcontentloaded = "domcontentloaded"
    load = "load"
    networkidle = "networkidle"


class MediaChoice(str, Enum):
    """CSS media types accepted by `--media`."""

    print = "print"
    screen = "screen"


app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Render web pages and local HTML files to PDF.",
)


def _version(value: bool) -> None:
    """Print the version and exit when `--version` was passed.

    Args:
        value: Whether the flag was given.

    Raises:
        Exit: Always, when the flag was given.
    """
    if value:
        typer.echo(f"website2pdf {__version__}")
        raise typer.Exit


def _expand_targets(targets: list[str]) -> list[str]:
    """Replace a `-` entry with one target per line read from stdin.

    Args:
        targets: Raw targets from the command line.

    Returns:
        The expanded target list.

    Raises:
        BadParameter: If nothing is left to convert.
    """
    expanded: list[str] = []
    for target in targets:
        if target == STDOUT:
            expanded.extend(line.strip() for line in sys.stdin if line.strip())
        else:
            expanded.append(target)

    if not expanded:
        message = "no targets to convert"
        raise typer.BadParameter(message)
    return expanded


def _parse_headers(headers: list[str]) -> dict[str, str]:
    """Parse repeated `Name: value` options into a mapping.

    Args:
        headers: Raw `--header` values.

    Returns:
        The parsed headers.

    Raises:
        BadParameter: If an entry has no colon.
    """
    parsed: dict[str, str] = {}
    for header in headers:
        name, separator, value = header.partition(":")
        if not separator or not name.strip():
            message = f"expected 'Name: value', got {header!r}"
            raise typer.BadParameter(message)
        parsed[name.strip()] = value.strip()
    return parsed


@app.command()
def convert(
    targets: Annotated[
        list[str],
        typer.Argument(
            metavar="TARGET...",
            help="URLs or local HTML files. Pass - to read one target per line from stdin.",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help=(
                "File to write, a directory when converting several targets, "
                "or - to write the PDF to stdout. Defaults to the current directory."
            ),
        ),
    ] = None,
    name_template: Annotated[
        str,
        typer.Option("--name", help="File name template. {title} is the only placeholder."),
    ] = "{title}.pdf",
    paper_format: Annotated[
        PaperFormatChoice, typer.Option("--format", help="Paper size.")
    ] = PaperFormatChoice.A4,
    landscape: Annotated[bool, typer.Option("--landscape", help="Use landscape.")] = False,
    margin: Annotated[
        str | None,
        typer.Option("--margin", help="Margin on all four sides, e.g. 1cm."),
    ] = None,
    scale: Annotated[float, typer.Option("--scale", help="Rendering scale, 0.1 to 2.0.")] = 1.0,
    background: Annotated[
        bool,
        typer.Option("--background/--no-background", help="Paint background graphics."),
    ] = True,
    page_ranges: Annotated[
        str | None,
        typer.Option("--pages", help="Pages to emit, e.g. 1-3,8."),
    ] = None,
    prefer_css_page_size: Annotated[
        bool,
        typer.Option("--prefer-css-page-size", help="Let the page CSS choose the paper size."),
    ] = False,
    wait_until: Annotated[
        WaitUntilChoice, typer.Option("--wait-until", help="Navigation milestone to wait for.")
    ] = WaitUntilChoice.load,
    wait_for: Annotated[
        str | None,
        typer.Option("--wait-for", help="CSS selector to wait for before rendering."),
    ] = None,
    extra_wait: Annotated[
        float, typer.Option("--extra-wait", help="Extra idle time in ms after the page is ready.")
    ] = 0.0,
    media: Annotated[
        MediaChoice | None,
        typer.Option("--media", help="CSS media to emulate. Chromium prints with print media."),
    ] = None,
    timeout: Annotated[
        float, typer.Option("--timeout", help="Navigation timeout in ms. 0 disables it.")
    ] = 30_000.0,
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-j", help="Pages to render at the same time.")
    ] = 4,
    user_agent: Annotated[str | None, typer.Option("--user-agent", help="User-Agent.")] = None,
    header: Annotated[
        list[str] | None,
        typer.Option("--header", "-H", help="Extra request header as 'Name: value'. Repeatable."),
    ] = None,
    ignore_https_errors: Annotated[
        bool, typer.Option("--insecure", help="Accept invalid TLS certificates.")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Do not list written files.")
    ] = False,
    _version_flag: Annotated[
        bool | None,
        typer.Option("--version", callback=_version, is_eager=True, help="Show the version."),
    ] = None,
) -> None:
    """Render one or more targets to PDF."""
    expanded = _expand_targets(targets)
    to_stdout = output is not None and str(output) == STDOUT

    if to_stdout and len(expanded) > 1:
        message = "- writes a single PDF to stdout; give a directory for several targets"
        raise typer.BadParameter(message)

    # Resolve the destination here rather than inside the coroutine: filesystem
    # probing does not belong on the event loop, and a usage error should be
    # reported before a browser is launched.
    destination = None if to_stdout else (output or Path.cwd())
    into_directory = destination is not None and destination.is_dir()
    if destination is not None and not into_directory and len(expanded) > 1:
        message = "--output must be an existing directory when converting several targets"
        raise typer.BadParameter(message)

    try:
        pdf_options = PdfOptions(
            paper_format=paper_format.value,
            landscape=landscape,
            margin=Margin.uniform(margin) if margin else None,
            scale=scale,
            print_background=background,
            prefer_css_page_size=prefer_css_page_size,
            page_ranges=page_ranges,
        )
        render_options = RenderOptions(
            wait_until=wait_until.value,
            timeout=timeout,
            emulate_media=media.value if media else None,
            wait_for_selector=wait_for,
            extra_wait=extra_wait,
        )
        browser_options = BrowserOptions(
            user_agent=user_agent,
            ignore_https_errors=ignore_https_errors,
            extra_http_headers=_parse_headers(header or []) or None,
        )
    except WebSite2PDFError as exc:
        raise typer.BadParameter(str(exc)) from exc

    try:
        written = asyncio.run(
            _convert_all(
                expanded,
                destination,
                into_directory=into_directory,
                name_template=name_template,
                concurrency=concurrency,
                pdf_options=pdf_options,
                render_options=render_options,
                browser_options=browser_options,
            )
        )
    except WebSite2PDFError as exc:
        typer.secho(f"error: {exc}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc

    if to_stdout:
        sys.stdout.buffer.write(cast("bytes", written[0]))
        return

    if not quiet:
        for path in written:
            typer.echo(str(path), err=True)


async def _convert_all(
    targets: list[str],
    output: Path | None,
    *,
    into_directory: bool,
    name_template: str,
    concurrency: int,
    pdf_options: PdfOptions,
    render_options: RenderOptions,
    browser_options: BrowserOptions,
) -> list[Path] | list[bytes]:
    """Run the conversions and return either the written paths or the PDF bytes.

    Args:
        targets: Expanded targets.
        output: Destination, or `None` to return bytes for stdout.
        into_directory: Whether `output` names a directory.
        name_template: File name template.
        concurrency: Pages rendered at the same time.
        pdf_options: PDF rendering options.
        render_options: Navigation options.
        browser_options: Browser and context options.

    Returns:
        Written paths, or a single-element list of PDF bytes when `output` is
        `None`.
    """
    async with AsyncClient(
        pdf_options=pdf_options,
        browser_options=browser_options,
        render_options=render_options,
        concurrency=concurrency,
    ) as client:
        if output is None:
            return [await client.convert(targets[0])]
        if into_directory:
            return await client.convert_many(targets, output, filename_template=name_template)
        return [await client.convert(targets[0], output)]


def main() -> None:
    """Entry point for the `website2pdf` console script."""
    app()


if __name__ == "__main__":
    main()
