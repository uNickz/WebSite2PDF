# Command line

Install the extra to get the `website2pdf` command:

```bash
pip install "website2pdf[cli]"
```

## Examples

```bash
# One page to a named file
website2pdf https://example.com -o report.pdf

# Several pages into a directory, named after their titles
website2pdf https://example.com https://example.org -o out/

# Straight to stdout, for piping
website2pdf https://example.com -o - > report.pdf

# One URL per line on stdin, eight at a time
cat urls.txt | website2pdf - -o out/ --concurrency 8

# A local file, in landscape A5 with margins
website2pdf report.html -o out.pdf --format A5 --landscape --margin 1cm

# A page that finishes loading after the load event
website2pdf https://example.com -o out.pdf --wait-for "#chart-ready"

# As the page looks on screen, not in print media
website2pdf https://example.com -o out.pdf --media screen
```

## Targets

Positional arguments are URLs or local HTML files. A `-` reads one target per
line from standard input, and can be mixed with explicit targets. Blank lines are
ignored.

## Output

| Form | Behaviour |
| --- | --- |
| *(omitted)* | Writes into the current directory using `--name` |
| `-o file.pdf` | Writes that file. Only valid with one target |
| `-o dir/` | Writes into an existing directory using `--name` |
| `-o -` | Writes the PDF to stdout. Only valid with one target |

Written paths are listed on **stderr**, so stdout stays a clean pipe. `--quiet`
suppresses the listing.

## Options

### Output

| Option | Default | Description |
| --- | --- | --- |
| `-o`, `--output` | current directory | File, directory, or `-` for stdout |
| `--name` | `{title}.pdf` | File name template. `{title}` is the only placeholder |
| `-q`, `--quiet` | off | Do not list written files |

### Page setup

| Option | Default | Description |
| --- | --- | --- |
| `--format` | `A4` | `Letter`, `Legal`, `Tabloid`, `Ledger`, `A0`–`A6` |
| `--landscape` | off | Landscape orientation |
| `--margin` | none | Margin on all four sides, in CSS units, e.g. `1cm` |
| `--scale` | `1.0` | Rendering scale, `0.1` to `2.0` |
| `--background` / `--no-background` | on | Paint background graphics |
| `--pages` | all | Pages to emit, e.g. `1-3,8` |
| `--prefer-css-page-size` | off | Let the page's `@page` CSS choose the size |

### Loading

| Option | Default | Description |
| --- | --- | --- |
| `--wait-until` | `load` | `commit`, `domcontentloaded`, `load`, `networkidle` |
| `--wait-for` | none | CSS selector to wait for before rendering |
| `--extra-wait` | `0` | Extra idle milliseconds after the page is ready |
| `--media` | Chromium's default | `print` or `screen` |
| `--timeout` | `30000` | Navigation timeout in milliseconds. `0` disables it |
| `-j`, `--concurrency` | `4` | Pages rendered at the same time |

### Browser

| Option | Default | Description |
| --- | --- | --- |
| `--user-agent` | Chromium's default | Override the `User-Agent` |
| `-H`, `--header` | none | Extra request header as `Name: value`. Repeatable |
| `--insecure` | off | Accept invalid TLS certificates |

### Other

| Option | Description |
| --- | --- |
| `--version` | Print the version and exit |
| `-h`, `--help` | Show the help and exit |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Every target was converted |
| `1` | A conversion failed, the page did not load, or could not be printed |
| `2` | The command was used incorrectly |

Usage errors are reported before a browser is launched, so a mistyped
invocation fails at once rather than after a Chromium start-up.
