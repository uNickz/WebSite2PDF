---
description: Translate WebSite2PDF 0.x code to the 1.0 API: convert() instead of pdf(), typed option objects, and what was removed and why.
---

# Migrating from 0.x

Version 1.0 is a rewrite. The import name changed, the API changed, and Selenium
was replaced by Playwright. No 0.x code runs unchanged, and there is no
compatibility shim, a shim would have kept the parts that were broken.

Nothing forces you to upgrade: 0.1.3 stays on PyPI under the licence it was
published with.

## At a glance

| 0.x | 1.0 |
| --- | --- |
| `import WebSite2PDF` | `import website2pdf` |
| `WebSite2PDF.Client()` | `website2pdf.Client()` |
| `c.pdf(url)` | `c.convert(url)` |
| `c.pdf(url, filename="x.pdf")` | `c.convert(url, "x.pdf")` |
| `c.pdf([urls], filename=[names])` | `c.convert_many(urls, "out/")` |
| `pdfOptions={"landscape": True}` | `pdf_options=PdfOptions(landscape=True)` |
| `seleniumOptions=["--headless"]` | `browser_options=BrowserOptions(headless=True)` |
| `delay=3` | `render_options=RenderOptions(wait_until="networkidle")` |
| — | `async with AsyncClient()` |
| — | `website2pdf` command |

## Installation

The distribution name is lower case now, and the browser is a separate step:

```bash
pip uninstall WebSite2PDF
pip install website2pdf
playwright install chromium
```

The old chromedriver requirement is gone. Playwright pins a Chromium build to
each release, so there is nothing to match against a system browser.

## The client is a context manager

=== "1.0"

    ```python
    from website2pdf import Client

    with Client() as client:
        client.convert("https://example.com", "example.pdf")
    ```

=== "0.x"

    ```python
    import WebSite2PDF

    c = WebSite2PDF.Client()
    c.pdf("https://example.com", filename="example.pdf")
    ```

In 0.x a client could only be used once: `stop_client()` called `quit()` but left
its handle in place, so the next conversion raised `ClientAlreadyStarted`. Both
`start()` and `close()` are idempotent now, and `ClientAlreadyStarted` and
`ClientAlreadyStopped` no longer exist, they were symptoms of that bug rather
than conditions worth reporting.

## Return types

`pdf()` returned `bytes | Iterable[bytes] | str | Iterable[str]`, which you
could not use without checking at runtime. `convert()` decides by whether you
passed a destination, through typed overloads:

```python
data: bytes = client.convert(url)  # no destination
path: Path = client.convert(url, "out.pdf")  # destination
```

`convert_many()` does the same for lists, and returns a `Path` rather than a
`str`.

## Several pages

0.x took parallel lists of URLs and file names, which silently misbehaved when
they were different lengths. 1.0 takes a directory and a template:

=== "1.0"

    ```python
    paths = client.convert_many(
        ["https://pypi.org", "https://github.com"],
        "out/",
        filename_template="{title}.pdf",
    )
    ```

=== "0.x"

    ```python
    c.pdf(
        ["https://pypi.org", "https://github.com"],
        filename=["pypi.pdf", "github.pdf"],
    )
    ```

Two pages with the same title used to overwrite each other. The second file is
now `Title (2).pdf`.

## Options

Dictionaries with camelCase keys became three typed objects, validated when you
build them.

| 0.x key | 1.0 |
| --- | --- |
| `landscape` | `PdfOptions(landscape=...)` |
| `printBackground` | `PdfOptions(print_background=...)`, now `True` by default |
| `displayHeaderFooter` | `PdfOptions(display_header_footer=...)` |
| `preferCSSPageSize` | `PdfOptions(prefer_css_page_size=...)` |
| `scale` | `PdfOptions(scale=...)` |
| `pageRanges` | `PdfOptions(page_ranges=...)` |
| `headerTemplate` | `PdfOptions(header_template=...)` |
| `footerTemplate` | `PdfOptions(footer_template=...)` |
| `paperWidth`, `paperHeight` (inches) | `PdfOptions(width="8.5in", height="11in")`, any CSS unit |
| `marginTop`, `marginBottom`, … (inches) | `PdfOptions(margin=Margin(top="1cm", …))`, any CSS unit |
| `transferMode` | removed; it never worked |

Sizes are CSS lengths now rather than bare inches, so `"21cm"`, `"8.5in"` and
`"800px"` are all valid.

```python
from website2pdf import Client, Margin, PdfOptions

with Client(
    pdf_options=PdfOptions(
        landscape=True,
        display_header_footer=True,
        prefer_css_page_size=True,
        margin=Margin.uniform("1cm"),
    )
) as client:
    client.convert(url, "out.pdf")
```

## Selenium options

`seleniumOptions` was a list of Chrome command-line switches, several of which
were not real flags (`--instant-process`, `--fast`, `--fast-start`), and all of
which were also passed to Firefox, where they mean nothing.

Most of what people used it for now has a named field:

| 0.x switch | 1.0 |
| --- | --- |
| `--headless` | `BrowserOptions(headless=True)`, the default |
| `--window-size=1920,1080` | `BrowserOptions(viewport=(1920, 1080))` |
| `--user-agent=…` | `BrowserOptions(user_agent=...)` |
| `--ignore-certificate-errors` | `BrowserOptions(ignore_https_errors=True)` |
| `--no-sandbox`, `--disable-dev-shm-usage` | `BrowserOptions(args=("--no-sandbox", "--disable-dev-shm-usage"))` |

`--no-sandbox` and `--disable-dev-shm-usage` are still worth passing inside
containers; the rest of the old default list was cargo cult.

## Delay

`delay` was implemented by waiting for the page's `<html>` element to go stale,
which is not what "wait three seconds" means. It also had a bug: `delay=0`
passed explicitly was ignored, because the argument was selected with a falsy
check.

Say what you are actually waiting for:

```python
from website2pdf import RenderOptions

RenderOptions(wait_until="networkidle")  # the network went quiet
RenderOptions(wait_for_selector="#ready")  # a specific element exists
RenderOptions(extra_wait=3000)  # a fixed 3 seconds, if you must
```

## Cookies

0.x passed cookies to the driver before navigating, which the underlying API
rejects, cookies can only be set once you are on the target domain. They now go
on the browser context, where before navigation is the correct time:

```python
BrowserOptions(cookies=({"name": "session", "value": "abc", "domain": "example.com", "path": "/"},))
```

## Errors

The `Errors` and `Drivers` aggregate classes are gone. Every exception derives
from `WebSite2PDFError`:

```python
from website2pdf import NavigationError, WebSite2PDFError
```

`InvalidUrl` is now `InvalidTargetError`, and `RequestFailed` is now
`RenderError` or `NavigationError` depending on where the failure happened.

## Firefox

Removed. Only Chromium exposes a print-to-PDF command; Playwright's `page.pdf()`
raises on other engines.

In practice nothing is lost. The 0.x Firefox path printed to a printer named
`"Microsoft Print to PDF"` (a Windows-only device that the project's own Linux
CI could never have had) and then waited for a file to appear in an unbounded
loop with no timeout.

## What you gain

- `AsyncClient`, for rendering many pages concurrently.
- A `website2pdf` command line.
- Type hints that survive installation, via `py.typed`.
- `emulate_media`, headers, HTTP basic auth, locale and timezone control.
- File names that are actually safe: the 0.x sanitiser was written in a non-raw
  string, so its escape sequences did not mean what they looked like and it
  removed the wrong characters.
