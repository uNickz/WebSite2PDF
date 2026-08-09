# WebSite2PDF

Render web pages and local HTML files to PDF, from Python or from the shell.
Fully typed, async-capable, and driven by headless Chromium through
[Playwright](https://playwright.dev/python/).

```python
from website2pdf import Client

with Client() as client:
    client.convert("https://example.com", "example.pdf")
```

```bash
website2pdf https://example.com -o example.pdf
```

## What it gives you

- **One call per job.** `convert()` returns `bytes` when you omit the
  destination and a `Path` when you give one, decided by typed overloads, so
  your editor and type checker both know which.
- **Concurrency that is real.** `AsyncClient` is asyncio-native and renders
  several pages at once in independent browser contexts sharing one browser
  process, rather than one browser per page.
- **Options you cannot typo.** Three frozen dataclasses that validate on
  construction, instead of dictionaries with magic string keys.
- **A browser that matches the library.** Playwright ships a pinned Chromium
  build, so there is no driver to keep in step with a system browser.
- **Type hints that survive installation.** The package ships `py.typed`.

## Where to go next

<div class="grid cards" markdown>

- **[Installation](installation.md)**: including the browser download step that
  is easy to miss.
- **[User guide](guide.md)**: single pages, batches, waiting for content,
  cookies and headers.
- **[Command line](cli.md)**: every flag, with examples.
- **[Options reference](options.md)**: every field of every option object.
- **[Migrating from 0.x](migration.md)**: what changed and how to translate it.
- **[API reference](api.md)**: generated from the source.

</div>

## Requirements

Python 3.10 or newer, on Linux, macOS or Windows. PDF rendering is Chromium-only:
it is the only engine that exposes a print-to-PDF command.
