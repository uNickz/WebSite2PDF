## What this changes

<!-- What the change does, and why it is worth making. If it fixes a bug,
describe the failure someone would have seen. -->

## Related issues

<!-- Fixes #123 -->

## Checklist

- [ ] `uv run pre-commit run --all-files` passes
- [ ] `uv run pytest` passes
- [ ] Tests cover the change (a regression test for a bug fix)
- [ ] `CHANGELOG.md` has an entry under `Unreleased`, if this is user-visible
- [ ] Docstrings and docs updated, if the public API changed

<!-- If you added async tests, check they are not in a module that also uses the
synchronous `Client` fixture. See CONTRIBUTING.md. -->
