# User guide

## Starting and stopping

Both clients start a browser and keep it for their lifetime. Use them as context
managers so the browser is always torn down:

```python
from website2pdf import Client

with Client() as client:
    client.convert("https://example.com", "example.pdf")
```

Calling `convert()` on a client that has not been started starts it implicitly,
in which case closing it is your job:

```python
client = Client()
try:
    client.convert("https://example.com", "example.pdf")
finally:
    client.close()
```

`start()` and `close()` are both idempotent, so a client can be closed and used
again:

```python
client.close()
client.convert("https://example.com", "again.pdf")  # starts a fresh browser
```

## Targets

A target can be an `http(s)` URL, a `file://` URL, a `data:` URL, or a path to a
local HTML file given as a string or a `Path`:

```python
from pathlib import Path

client.convert("https://example.com")
client.convert("file:///home/me/report.html")
client.convert(Path("report.html"))
client.convert("report.html")  # relative to the working directory
```

Anything else raises [`InvalidTargetError`][website2pdf.InvalidTargetError],
including a local file that does not exist. Note that a Windows path such as
`C:\report.html` is recognised as a path, not as a URL with a `c` scheme.

## Where the PDF goes

Omit the destination and you get the bytes:

```python
data: bytes = client.convert("https://example.com")
```

Give one and you get the path that was written:

```python
path = client.convert("https://example.com", "report.pdf")
path = client.convert("https://example.com", "report")  # .pdf is added
path = client.convert("https://example.com", "out/")  # <title>.pdf inside
path = client.convert("https://example.com", "{title}.pdf")  # named after the page
```

Missing parent directories are created. The file name is sanitised: characters
no filesystem accepts are removed, whitespace is collapsed, Windows reserved
device names such as `CON` are defused, and long names are truncated while the
extension is preserved.

## Several pages

```python
paths = client.convert_many(
    ["https://example.com", "https://example.org"],
    "out/",
    filename_template="{title}.pdf",
)
```

Omit the directory to get a list of `bytes` instead. Results come back in input
order.

Pages that share a title do not overwrite each other, the second file becomes
`Title (2).pdf`, the third `Title (3).pdf`.

## Concurrency

`Client` renders one page after another. [`AsyncClient`][website2pdf.AsyncClient]
renders several at once, in independent browser contexts sharing one browser
process:

```python
import asyncio

from website2pdf import AsyncClient


async def main() -> None:
    async with AsyncClient(concurrency=8) as client:
        paths = await client.convert_many(urls, "out/")


asyncio.run(main())
```

`concurrency` belongs to the client rather than to a call, because it caps how
many browser contexts exist at once.

Every page is rendered before any file is written, so names are assigned in
input order and stay reproducible between runs.

!!! warning "Sync and asyncio do not mix on one thread"
    Playwright's synchronous driver runs an event loop on the calling thread. As
    long as a `Client` is open, `asyncio.run()` on that thread fails with a
    message about asyncio that has nothing to do with your code.

    In an asyncio program, use `AsyncClient`. Several `Client` instances on one
    thread are fine, they share one reference-counted driver.

## Waiting for the page

By default the render happens once the `load` event fires. A page that fetches
its content afterwards will be captured half-empty. Three tools, in order of
preference:

```python
from website2pdf import RenderOptions

# 1. Wait for the network to go quiet.
RenderOptions(wait_until="networkidle")

# 2. Wait for something specific to exist. The most reliable option.
RenderOptions(wait_for_selector="#chart-rendered")

# 3. Wait a fixed time. A last resort, for animations you cannot observe.
RenderOptions(extra_wait=1500)
```

Use them per call or as a client default:

```python
client.convert(url, "out.pdf", render_options=RenderOptions(wait_until="networkidle"))
```

## Print media versus screen media

Chromium prints with `print` CSS media, so a site with `@media print` rules
produces a PDF that does not look like the page in a browser. To reproduce the
on-screen appearance:

```python
RenderOptions(emulate_media="screen")
```

## Page setup

```python
from website2pdf import Margin, PdfOptions

PdfOptions(
    paper_format="A4",
    landscape=True,
    margin=Margin.uniform("1cm"),
    scale=0.8,
    print_background=True,
    page_ranges="1-3, 8",
)
```

Margins take CSS units. `Margin.uniform("1cm")` sets all four sides;
`Margin(top="2cm", bottom="2cm")` sets them individually.

Explicit `width` and `height` take priority over `paper_format`, matching
Chromium's own behaviour:

```python
PdfOptions(width="20cm", height="10cm")
```

Headers and footers need to be switched on before their templates are used,
constructing them the other way round raises
[`OptionsError`][website2pdf.OptionsError] rather than silently doing nothing:

```python
PdfOptions(
    display_header_footer=True,
    header_template='<div style="font-size:8px"><span class="title"></span></div>',
    footer_template='<div style="font-size:8px"><span class="pageNumber"></span></div>',
)
```

## Cookies, headers and authentication

These live on [`BrowserOptions`][website2pdf.BrowserOptions] because they belong
to the browser context, which is created before navigation:

```python
from website2pdf import BrowserOptions, Client

options = BrowserOptions(
    cookies=({"name": "session", "value": "abc123", "domain": "example.com", "path": "/"},),
    extra_http_headers={"Accept-Language": "it-IT"},
    http_credentials=("alice", "secret"),
    user_agent="my-crawler/1.0",
    viewport=(1920, 1080),
    locale="it-IT",
    timezone_id="Europe/Rome",
)

with Client(browser_options=options) as client:
    client.convert("https://example.com/private", "private.pdf")
```

## Defaults and overrides

Options set on the client apply to every conversion; options passed to a call
replace them for that call only:

```python
with Client(pdf_options=PdfOptions(paper_format="A4")) as client:
    client.convert(url, "a4.pdf")
    client.convert(url, "a5.pdf", pdf_options=PdfOptions(paper_format="A5"))
```

The replacement is wholesale, not a merge: the second call above uses a default
`PdfOptions` with `paper_format` changed, not the client's options with one
field patched. Use `dataclasses.replace` when you want to derive one from the
other:

```python
import dataclasses

base = PdfOptions(paper_format="A4", margin=Margin.uniform("1cm"))
landscape = dataclasses.replace(base, landscape=True)
```

## Errors

Everything derives from
[`WebSite2PDFError`][website2pdf.WebSite2PDFError], so a single `except` covers
the library:

```python
from website2pdf import (
    BrowserNotInstalledError,
    InvalidTargetError,
    NavigationError,
    RenderError,
    WebSite2PDFError,
)

try:
    client.convert(url, "out.pdf")
except BrowserNotInstalledError:
    ...  # run `playwright install chromium`
except InvalidTargetError:
    ...  # not a usable URL or file
except NavigationError:
    ...  # the page did not load in time
except RenderError:
    ...  # it loaded but could not be printed
except WebSite2PDFError:
    ...  # anything else from this library
```

`OptionsError` also subclasses `ValueError`, so existing validation code that
catches `ValueError` keeps working.
