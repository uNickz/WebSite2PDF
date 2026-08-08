"""Normalisation of conversion targets into URLs the browser can navigate to."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .errors import InvalidTargetError

#: Schemes handed to the browser untouched.
NAVIGABLE_SCHEMES = frozenset({"about", "data", "file", "http", "https"})


def normalize_target(target: str | Path) -> str:
    """Turn a user-supplied target into a URL the browser can navigate to.

    Accepts an ``http(s)`` URL, a ``file://`` URL, or a path to a local file,
    given either as a :class:`~pathlib.Path` or as a plain string.

    Args:
        target: URL or local filesystem path.

    Returns:
        A URL suitable for ``page.goto()``.

    Raises:
        InvalidTargetError: If the target is empty, uses an unsupported scheme,
            or points at a local file that does not exist.
    """
    if isinstance(target, Path):
        return _file_to_uri(target)

    stripped = target.strip()
    if not stripped:
        message = "target must not be empty"
        raise InvalidTargetError(message)

    scheme = urlparse(stripped).scheme.lower()
    if scheme in NAVIGABLE_SCHEMES:
        return stripped

    # A single-letter scheme is a Windows drive letter ("C:\\page.html"),
    # not a URL scheme.
    if len(scheme) > 1:
        message = (
            f"unsupported URL scheme {scheme!r} in {stripped!r}; "
            f"expected one of {', '.join(sorted(NAVIGABLE_SCHEMES))}, or a local file path"
        )
        raise InvalidTargetError(message)

    return _file_to_uri(Path(stripped))


def _file_to_uri(path: Path) -> str:
    """Resolve a local file and convert it to a ``file://`` URI.

    Args:
        path: Path to an existing HTML file.

    Returns:
        The absolute ``file://`` URI for ``path``.

    Raises:
        InvalidTargetError: If ``path`` does not point at an existing file.
    """
    resolved = path.expanduser()
    try:
        resolved = resolved.resolve()
    except OSError as exc:  # pragma: no cover - platform dependent
        message = f"could not resolve local path {path}: {exc}"
        raise InvalidTargetError(message) from exc

    if not resolved.is_file():
        message = f"local file not found: {path}"
        raise InvalidTargetError(message)

    return resolved.as_uri()
