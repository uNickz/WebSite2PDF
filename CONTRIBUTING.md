# Contributing

Thanks for taking the time. Issues, questions and pull requests are all welcome.

## Getting set up

The project uses [uv](https://docs.astral.sh/uv/). It manages the interpreter as
well as the dependencies, so there is nothing to install first beyond uv itself.

```bash
git clone https://github.com/uNickz/WebSite2PDF
cd WebSite2PDF
uv sync --all-extras --all-groups
uv run playwright install chromium
```

Install the git hooks so the same checks CI runs also run before each commit:

```bash
uv run pre-commit install
```

## The checks

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy                  # types, strict
uv run pytest                # tests
uv run pytest --cov          # tests with the coverage gate
```

`uv run pre-commit run --all-files` runs the lot in one go.

CI requires all of them, plus a coverage floor of 85%.

## Tests

Tests split in two:

- `tests/unit/` never launches a browser and runs in well under a second.
- `tests/integration/` drives real Chromium against fixtures served over
  loopback from `tests/fixtures/`. **No test may reach the public internet**,
  the 0.x suite converted `pypi.org` on every run, which made a red build
  ambiguous and a green one close to meaningless.

Skip the browser-backed tests when you are iterating on pure logic:

```bash
uv run pytest -m "not browser"
```

### One rule that is easy to trip over

**Do not mix synchronous `Client` tests and async tests in the same module.**

Playwright's synchronous driver runs an event loop on the calling thread using
greenlets. While a sync `Client` is open, `asyncio.run()` on that thread fails
with a message about asyncio that has nothing to do with your test. The shared
`client` fixture is therefore module-scoped rather than session-scoped, so the
driver is released at each module boundary.

If you add async tests to a module that already exercises the sync client, split
them into their own file, as `test_render_options.py` and
`test_render_options_async.py` do.

## Coverage and greenlets

`pyproject.toml` sets `concurrency = ["thread", "greenlet"]` for coverage. Do not
remove it. Without it coverage.py loses its tracer at Playwright's first greenlet
switch, and the synchronous client reports around 65% while its tests are in fact
exercising every line.

## Style

Ruff and mypy decide almost everything, so there is little left to argue about.
Beyond them:

- Docstrings follow the Google convention; mkdocstrings builds the API reference
  from them.
- Explain *why* in comments, not *what*. The code already says what.
- Public API lives in `website2pdf/__init__.py` and `__all__`. Modules starting
  with `_` are private and may change without notice.

## Commits and pull requests

Commit messages follow [Conventional
Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`,
`test:`, `ci:`, `chore:`, with `!` for a breaking change.

Say what changed and why in the body. If you fixed a bug, describe the failure
someone would have seen, that is what a future reader needs.

Add an entry to `CHANGELOG.md` under `Unreleased` for anything user-visible.

## Releasing

Maintainers only:

1. Move the `Unreleased` entries into a new version section in `CHANGELOG.md`.
2. Bump `version` in `pyproject.toml`.
3. Merge to `main`, then push a matching tag: `git tag v1.2.3 && git push origin v1.2.3`.

`release.yml` refuses to publish if the tag and the version in `pyproject.toml`
disagree, then builds and publishes to PyPI through Trusted Publishing. There is
no API token to manage.
