---
description: Install website2pdf with pip and download the Chromium build Playwright manages, including Linux server and container setups.
---

# Installation

## The package

```bash
pip install website2pdf
```

For the command line, install the extra too. Typer is not a core dependency, so
that importing the library from code does not pull a CLI framework with it:

```bash
pip install "website2pdf[cli]"
```

## The browser

**This step is required.** The library has nothing to render with until it has
run:

```bash
playwright install chromium
```

Or, if `playwright` is not on your `PATH`:

```bash
python -m playwright install chromium
```

The download is roughly 150 MB. It is shared by every project on the machine
that uses the same Playwright version, so you pay for it once, not once per
virtual environment.

If you skip it, the first conversion raises a
[`BrowserNotInstalledError`][website2pdf.BrowserNotInstalledError] that repeats
the command back to you.

!!! tip "Why a separate download"
    Playwright pins a Chromium build to each of its releases. That is what
    removes the version-matching problem that comes with driving whatever
    browser happens to be installed on the machine: the pair is always
    compatible, and upgrading the library upgrades the browser with it.

### On Linux servers and containers

A bare Linux image is usually missing the shared libraries Chromium links
against. Install them alongside the browser:

```bash
playwright install --with-deps chromium
```

`--with-deps` shells out to `apt`, so it needs root and only does anything on
Debian-derived distributions. On a workstation where you are not root, use
`playwright install chromium` and install the libraries through your own package
manager.

### Choosing where browsers live

Set `PLAYWRIGHT_BROWSERS_PATH` to keep the download inside your project, which
is what the CI workflow in this repository does so that one cache key works
across Linux, macOS and Windows:

```bash
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.playwright"
playwright install chromium
```

## Verifying

```bash
python -c "import website2pdf; print(website2pdf.__version__)"
website2pdf https://example.com -o /tmp/check.pdf
```

## Development install

The project uses [uv](https://docs.astral.sh/uv/), which manages the interpreter
as well as the dependencies:

```bash
git clone https://github.com/uNickz/WebSite2PDF
cd WebSite2PDF
uv sync --all-extras --all-groups
uv run playwright install chromium
uv run pytest
```

See [Contributing](contributing.md) for the rest.
