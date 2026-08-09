---
description: Every field of PdfOptions, Margin, RenderOptions and BrowserOptions, with defaults, validation rules and header and footer templates.
---

# Options reference

Options are split along the three axes they belong to. Each is a frozen
dataclass validated on construction, so a bad value fails where you wrote it
rather than deep inside a render.

All three can be set on the client as defaults and passed per call as overrides.
An override replaces the default wholesale rather than merging into it; use
`dataclasses.replace` to derive one from another.

## PdfOptions

How the loaded page is painted into a PDF.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `paper_format` | `PaperFormat | None` | `"A4"` | Named paper size. Ignored when `width` or `height` is set |
| `width` | `str | None` | `None` | Explicit page width as a CSS length. Overrides `paper_format` |
| `height` | `str | None` | `None` | Explicit page height as a CSS length. Overrides `paper_format` |
| `scale` | `float` | `1.0` | Rendering scale, between `0.1` and `2.0` |
| `landscape` | `bool` | `False` | Landscape orientation |
| `margin` | `Margin | None` | `None` | Page margins. `None` leaves Chromium's default |
| `print_background` | `bool` | `True` | Paint background graphics |
| `prefer_css_page_size` | `bool` | `False` | Let an `@page` size in the document's CSS win over `paper_format` |
| `page_ranges` | `str | None` | `None` | Pages to emit, e.g. `"1-3, 8"`. `None` emits all |
| `display_header_footer` | `bool` | `False` | Render the header and footer templates |
| `header_template` | `str | None` | `None` | HTML for the page header |
| `footer_template` | `str | None` | `None` | HTML for the page footer |
| `outline` | `bool` | `False` | Embed a document outline |
| `tagged` | `bool` | `False` | Emit a tagged, accessible PDF |

`print_background` defaults to `True`, which is the one place this library
deliberately departs from Chromium's own default: a page converted without its
backgrounds rarely matches what the user saw.

### Validation

- `scale` outside `0.1`–`2.0` raises [`OptionsError`][website2pdf.OptionsError].
- A `header_template` or `footer_template` without `display_header_footer=True`
  raises `OptionsError`, rather than being silently ignored the way the
  underlying API would.

### Paper sizes

`Letter`, `Legal`, `Tabloid`, `Ledger`, `A0`, `A1`, `A2`, `A3`, `A4`, `A5`, `A6`.

### Header and footer templates

Templates are HTML fragments. Chromium substitutes the values of these classes:

| Class | Contains |
| --- | --- |
| `date` | The formatted print date |
| `title` | The document title |
| `url` | The document location |
| `pageNumber` | The current page number |
| `totalPages` | The total number of pages |

```python
PdfOptions(
    display_header_footer=True,
    header_template='<div style="font-size:9px; width:100%; text-align:center">'
    '<span class="title"></span></div>',
    footer_template='<div style="font-size:9px; width:100%; text-align:center">'
    '<span class="pageNumber"></span> / <span class="totalPages"></span></div>',
)
```

Templates are rendered outside the page's own styles, so they start unstyled and
at a very small default size. Set `font-size` explicitly, and leave room with
`margin`, a header with no top margin has nowhere to appear.

## Margin

CSS lengths: `px`, `in`, `cm`, `mm`.

| Field | Type | Default |
| --- | --- | --- |
| `top` | `str` | `"0"` |
| `right` | `str` | `"0"` |
| `bottom` | `str` | `"0"` |
| `left` | `str` | `"0"` |

```python
Margin.uniform("1cm")
Margin(top="2cm", bottom="2cm", left="1.5cm", right="1.5cm")
```

## RenderOptions

How navigation waits for the page to become ready.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `wait_until` | `WaitUntil` | `"load"` | Navigation milestone to wait for |
| `timeout` | `float` | `30000.0` | Navigation timeout in milliseconds. `0` disables it |
| `emulate_media` | `MediaType | None` | `None` | `"print"` or `"screen"` |
| `wait_for_selector` | `str | None` | `None` | CSS selector to wait for before rendering |
| `extra_wait` | `float` | `0.0` | Extra idle milliseconds after the page is ready |

### Milestones

| Value | Fires when |
| --- | --- |
| `commit` | The response has arrived and started being processed |
| `domcontentloaded` | The `DOMContentLoaded` event fires |
| `load` | The `load` event fires |
| `networkidle` | There have been no network connections for 500 ms |

`networkidle` is the safest choice for pages that fetch content after loading,
though it never settles on pages that poll. For those, `wait_for_selector` is
both faster and more reliable.

A negative `timeout` or `extra_wait` raises `OptionsError`.

## BrowserOptions

How the browser process and its context are created.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `headless` | `bool` | `True` | Run without a visible window |
| `args` | `tuple[str, ...]` | `()` | Extra Chromium command-line switches |
| `executable_path` | `str | None` | `None` | Path to a specific Chromium build |
| `channel` | `str | None` | `None` | Branded channel, e.g. `"chrome"`, `"msedge"` |
| `launch_timeout` | `float` | `30000.0` | Milliseconds to wait for the browser to start |
| `user_agent` | `str | None` | `None` | Override the `User-Agent` header |
| `viewport` | `tuple[int, int] | None` | `(1280, 720)` | Viewport size. `None` disables the fixed viewport |
| `device_scale_factor` | `float` | `1.0` | Device pixel ratio |
| `locale` | `str | None` | `None` | BCP 47 locale, e.g. `"it-IT"` |
| `timezone_id` | `str | None` | `None` | IANA timezone, e.g. `"Europe/Rome"` |
| `ignore_https_errors` | `bool` | `False` | Accept invalid TLS certificates |
| `extra_http_headers` | `Mapping[str, str] | None` | `None` | Headers added to every request |
| `http_credentials` | `tuple[str, str] | None` | `None` | `(username, password)` for HTTP basic auth |
| `cookies` | `tuple[Mapping[str, Any], ...]` | `()` | Cookies installed on the context before navigation |

Cookies use Playwright's format. Either `url`, or both `domain` and `path`, are
required for each one:

```python
BrowserOptions(cookies=({"name": "session", "value": "abc", "domain": "example.com", "path": "/"},))
```

!!! danger "ignore_https_errors"
    This turns off certificate validation for the whole context. It exists for
    testing against self-signed certificates. Do not enable it against hosts you
    do not control.
