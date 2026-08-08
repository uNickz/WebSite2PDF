# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - Unreleased

A full rewrite. The import name, the API and the rendering engine all change,
so 0.x code does not run against this release. See
[Migrating from 0.x](https://unickz.github.io/WebSite2PDF/migration/).

### Changed

- **The package is now `website2pdf`**, lower case, in a `src/` layout. `import
  WebSite2PDF` no longer resolves.
- **Rendering moved from Selenium to Playwright.** Playwright manages a pinned
  Chromium build, so there is no chromedriver to match against a system browser,
  and `page.pdf()` replaces the private CDP call the old driver reached for.
- **`pdf()` is now `convert()` and `convert_many()`.** The old method was four
  near-identical branches returning `bytes | Iterable[bytes] | str |
  Iterable[str]`, which callers could not use without `isinstance`. `convert()`
  returns `bytes` without a destination and `Path` with one, through typed
  overloads.
- **Options are typed objects, not dicts.** `PdfOptions`, `BrowserOptions` and
  `RenderOptions` are frozen dataclasses that validate on construction, so a bad
  scale or a header template without `display_header_footer` fails immediately
  instead of at render time.
- **Waiting is explicit.** `wait_until`, `wait_for_selector` and `extra_wait`
  replace the `delay` argument, which was implemented by abusing Selenium's
  `staleness_of` condition.
- **Licence changed to MIT.** The `LICENSE` file held plain GPL-3.0 text while
  the metadata declared LGPL-3.0. Releases before 1.0.0 keep the licence they
  were published under.
- The exception hierarchy is flat under `WebSite2PDFError`. The aggregate
  `Errors` and `Drivers` classes are gone, as are `ClientAlreadyStarted` and
  `ClientAlreadyStopped` — `start()` and `close()` are idempotent now.
- Naming follows PEP 8: `pdfOptions` is `pdf_options`, `seleniumOptions` is
  `browser_options`.

### Added

- **`AsyncClient`**, an asyncio-native client that renders several pages at once
  in independent browser contexts sharing one browser process, bounded by
  `concurrency`.
- **A `website2pdf` command line**, behind the `cli` extra. Reads targets from
  arguments or stdin, writes to a file, a directory or stdout.
- Context-manager support on both clients, plus `start()`, `close()` and
  `is_running`.
- `py.typed`: type hints are visible to downstream type checkers.
- Cookies, extra headers, HTTP basic auth, viewport, locale and timezone through
  `BrowserOptions`.
- `emulate_media`, so a page can be rendered as it appears on screen rather than
  in print media.
- Filename de-duplication: pages sharing a title no longer overwrite each other.
- 197 tests, including browser-backed integration tests served over loopback,
  and a CI matrix across Python 3.10-3.14 on Linux, macOS and Windows.

### Fixed

- **A client could only be used once.** `stop_client()` called `quit()` but left
  the handle in place, so the next conversion raised `ClientAlreadyStarted`.
- **Filename sanitisation did not work.** The pattern
  `"(\/|\\|\?|%|\*|:|\||\"|<|>)"` was written in a non-raw string, where `\\`
  collapses to a single backslash that escapes the following `|`. Windows
  reserved device names were not handled at all.
- **Mutable default arguments** on the client constructor shared one dict and
  one list across every instance.
- **`delay=0` was silently ignored**, because the argument was selected with a
  falsy check rather than a `None` check.
- **Cookies never arrived.** They were added to the driver before navigation,
  which requires already being on the target domain. They now go on the browser
  context, where pre-navigation is the correct place.
- **The Firefox path could hang forever** on an unbounded `while not
  os.path.isfile(...)` loop, and depended on a `"Microsoft Print to PDF"`
  printer that does not exist outside Windows.
- URL validation no longer issues a separate `requests.get()`, which doubled
  traffic and failed against sites that reject non-browser user agents.

### Removed

- **Firefox support.** Only Chromium exposes a print-to-PDF command; the Firefox
  branch had never worked.
- The `delay` argument, `Errors`, `Drivers`, `ClientAlreadyStarted`,
  `ClientAlreadyStopped`, `setup.py`, `requirements.txt` and the `Makefile`.
- Python 3.7 to 3.9 support. The floor is 3.10.

[Unreleased]: https://github.com/uNickz/WebSite2PDF/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/uNickz/WebSite2PDF/releases/tag/v1.0.0
