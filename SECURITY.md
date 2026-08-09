# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.x | Yes |
| 0.x | No |

0.x is unmaintained and depends on Selenium APIs that have been removed. Please
upgrade rather than reporting issues against it.

## Reporting a vulnerability

Report privately through GitHub's [security advisory
form](https://github.com/uNickz/WebSite2PDF/security/advisories/new), or by
email to <unickz.dev@gmail.com>.

Please do not open a public issue for a vulnerability.

Include what you can: affected version, a reproduction, and what an attacker
gains. You should get an acknowledgement within a few days, and a fix or an
explanation of why it is not one within thirty days.

## Scope

What this library does is fetch a URL with a real browser and print it. That
carries the risks you would expect, and a few worth stating outright:

- **Rendering an untrusted URL executes its JavaScript** in Chromium, in your
  process's browser. Treat conversion of user-supplied URLs as running untrusted
  code, and sandbox accordingly.
- **A `file://` target reads local files.** If URLs come from users, reject the
  `file` scheme before calling `convert()`; the library will happily open any
  path the process can read.
- **Local URLs are reachable.** A user-supplied URL can address your internal
  network or a cloud metadata endpoint. Filter targets if that matters to you.
- **`BrowserOptions(ignore_https_errors=True)` and the CLI's `--insecure` disable
  certificate validation.** They exist for testing against self-signed
  certificates. Do not enable them against hosts you do not control.

Reports about these behaviours as such will be closed as intended: they are
inherent to running a browser on someone else's content. Reports of ways to
escape the documented behaviour are very much in scope.
