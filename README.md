<p align="center">
    <a href="https://github.com/uNickz/WebSite2PDF">
        <img src="https://raw.githubusercontent.com/uNickz/WebSite2PDF/main/.github/graphics/GitHub-Banner-WebSite2PDF.png" width="500px" alt="WebSite2PDF">
    </a>
</p>

<p align="center">
    <a href="https://pypi.org/project/website2pdf/"><img src="https://img.shields.io/pypi/v/website2pdf.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/website2pdf/"><img src="https://img.shields.io/pypi/pyversions/website2pdf.svg" alt="Python versions"></a>
    <a href="https://github.com/uNickz/WebSite2PDF/actions/workflows/ci.yml"><img src="https://github.com/uNickz/WebSite2PDF/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <a href="https://github.com/uNickz/WebSite2PDF/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/website2pdf.svg" alt="MIT licence"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
    <a href="https://mypy-lang.org/"><img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy"></a>
</p>

<p align="center">
    <a href="https://unickz.github.io/WebSite2PDF/">Documentation</a>
    •
    <a href="https://pypi.org/project/website2pdf/">PyPI</a>
    •
    <a href="https://github.com/uNickz/WebSite2PDF/blob/main/CHANGELOG.md">Changelog</a>
    •
    <a href="https://t.me/uNickzProjects">News</a>
    •
    <a href="https://github.com/uNickz/WebSite2PDF/discussions">Chat</a>
</p>

# WebSite2PDF

Render web pages and local HTML files to PDF, from Python or from the shell.
Fully typed, async-capable, and driven by headless Chromium through
[Playwright](https://playwright.dev/python/).

```python
from website2pdf import Client

with Client() as client:
    client.convert("https://example.com", "example.pdf")
```

## Installation

```bash
pip install website2pdf
```

Then download the browser Playwright manages. **This step is required**, the
library has nothing to render with until it has run:

```bash
playwright install chromium
```

For the command line, install the extra as well:

```bash
pip install "website2pdf[cli]"
```

Python 3.10 or newer. The browser download is roughly 150 MB and is shared by
every project on the machine.

## Usage

### One page

```python
from website2pdf import Client

with Client() as client:
    # Get the bytes back...
    data = client.convert("https://example.com")

    # ...or write a file, and get its path.
    path = client.convert("https://example.com", "report.pdf")

    # Name the file after the page title.
    path = client.convert("https://example.com", "{title}.pdf")
```

Local files work the same way, as a path or a `file://` URL:

```python
from pathlib import Path

client.convert(Path("invoice.html"), "invoice.pdf")
```

### Many pages

```python
with Client() as client:
    paths = client.convert_many(
        ["https://example.com", "https://example.org"],
        "out/",
    )
```

Pages that share a title do not overwrite each other: the second file becomes
`Title (2).pdf`.

### Concurrently

`AsyncClient` renders several pages at once in independent browser contexts,
sharing a single browser process.

```python
import asyncio

from website2pdf import AsyncClient


async def main() -> None:
    async with AsyncClient(concurrency=8) as client:
        await client.convert_many(urls, "out/")


asyncio.run(main())
```

### Options

Three immutable option objects, each covering one concern. Set them on the
client as defaults, override them per call.

```python
from website2pdf import BrowserOptions, Client, Margin, PdfOptions, RenderOptions

with Client(
    pdf_options=PdfOptions(paper_format="A4", margin=Margin.uniform("1cm")),
    render_options=RenderOptions(wait_until="networkidle"),
    browser_options=BrowserOptions(user_agent="my-crawler/1.0"),
) as client:
    client.convert("https://example.com", "default.pdf")
    client.convert(
        "https://example.com",
        "landscape.pdf",
        pdf_options=PdfOptions(landscape=True, print_background=False),
    )
```

A page that fills itself in after loading needs an explicit wait:

```python
client.convert(
    "https://example.com",
    "chart.pdf",
    render_options=RenderOptions(wait_for_selector="#chart-ready"),
)
```

Chromium prints with `print` media by default. To reproduce what a visitor
sees on screen:

```python
render_options = RenderOptions(emulate_media="screen")
```

The full reference lives in the [options
documentation](https://unickz.github.io/WebSite2PDF/options/).

### Command line

```bash
website2pdf https://example.com -o report.pdf
website2pdf https://example.com https://example.org -o out/
website2pdf https://example.com --format A5 --landscape --margin 1cm
website2pdf https://example.com -o - > report.pdf          # straight to stdout
cat urls.txt | website2pdf - -o out/ --concurrency 8        # one URL per line
```

`website2pdf --help` lists every option.

## Errors

Everything the library raises derives from `WebSite2PDFError`, so one `except`
covers it:

```python
from website2pdf import BrowserNotInstalledError, NavigationError, WebSite2PDFError

try:
    client.convert(url, "out.pdf")
except BrowserNotInstalledError:
    ...  # tells you to run `playwright install chromium`
except NavigationError:
    ...  # the page did not load in time
except WebSite2PDFError:
    ...  # anything else from this library
```

## Notes

`Client` runs Playwright's synchronous driver on the calling thread, which
means `asyncio.run()` cannot start on that thread while a client is open. In an
asyncio program, use `AsyncClient`. Several `Client` instances on one thread are
fine, they share one reference-counted driver.

PDF rendering is Chromium-only: it is the only engine that exposes a print-to-PDF
command.

## Migrating from 0.x

Version 1.0 is a rewrite with a new import name and a new API. Nothing from 0.x
carries over unchanged.

| 0.x | 1.0 |
| --- | --- |
| `import WebSite2PDF` | `import website2pdf` |
| `c.pdf(url)` | `c.convert(url)` |
| `c.pdf(url, filename="x.pdf")` | `c.convert(url, "x.pdf")` |
| `c.pdf([urls], filename=[names])` | `c.convert_many(urls, "out/")` |
| `pdfOptions={"landscape": True}` | `pdf_options=PdfOptions(landscape=True)` |
| `seleniumOptions=["--no-sandbox"]` | `browser_options=BrowserOptions(args=("--no-sandbox",))` |
| `delay=3` | `render_options=RenderOptions(wait_until="networkidle")` |
| `"paperWidth"` / `"marginTop"` … | `width=` / `Margin(top=...)`, CSS units |
| Firefox fallback | removed; Chromium only |

`Client` is now a context manager, and `convert()` returns `bytes` when you omit
the destination and a `Path` when you give one, never a union of four types.
The [migration
guide](https://unickz.github.io/WebSite2PDF/migration/) walks through it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short:

```bash
uv sync --all-extras --all-groups
uv run playwright install chromium
uv run pytest
```

## Licence

[MIT](LICENSE).
