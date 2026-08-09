"""Derive filesystem-safe file names from page titles.

The rules here are deliberately the strictest common denominator across
Windows, macOS and Linux, so that a name produced on one platform is valid on
all of them.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import OptionsError

if TYPE_CHECKING:
    from collections.abc import Container

#: Characters Windows rejects outright, plus the C0 control range.
_ILLEGAL_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')

_WHITESPACE_RUN = re.compile(r"\s+")

#: Device names Windows reserves regardless of extension.
_RESERVED_STEMS = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)

DEFAULT_TEMPLATE = "{title}.pdf"
DEFAULT_FALLBACK = "document"

#: Leaves room for a de-duplication suffix inside the common 255-byte limit.
MAX_STEM_LENGTH = 200


def sanitize_filename(
    name: str,
    *,
    fallback: str = DEFAULT_FALLBACK,
    max_length: int = MAX_STEM_LENGTH,
) -> str:
    """Make `name` safe to use as a single path component.

    Strips characters that are illegal on any mainstream filesystem, collapses
    whitespace, defuses Windows reserved device names, and truncates the stem
    while preserving the extension.

    Args:
        name: Raw name, typically a page title.
        fallback: Stem to use when nothing usable survives sanitisation.
        max_length: Maximum length of the stem, extension excluded.

    Returns:
        A safe single path component. Never empty.
    """
    # Whitespace is normalised first: newlines and tabs also live in the control
    # range, and deleting them would glue neighbouring words together.
    cleaned = _WHITESPACE_RUN.sub(" ", name)
    cleaned = _ILLEGAL_CHARACTERS.sub("", cleaned)
    cleaned = _WHITESPACE_RUN.sub(" ", cleaned).strip()
    # Windows silently drops trailing dots and spaces, which would turn
    # "report." into "report" behind the caller's back.
    cleaned = cleaned.rstrip(". ")

    stem, dot, suffix = cleaned.rpartition(".")
    if not dot:
        stem, suffix = cleaned, ""

    if not stem:
        stem = fallback
    if stem.upper() in _RESERVED_STEMS:
        stem = f"_{stem}"
    if len(stem) > max_length:
        stem = stem[:max_length].rstrip(". ") or fallback

    return f"{stem}.{suffix}" if suffix else stem


def ensure_pdf_suffix(name: str) -> str:
    """Append a `.pdf` extension unless one is already present.

    Args:
        name: File name, with or without extension.

    Returns:
        `name` guaranteed to end in `.pdf` (case-insensitively).
    """
    return name if name.lower().endswith(".pdf") else f"{name}.pdf"


def build_filename(
    title: str,
    template: str = DEFAULT_TEMPLATE,
    *,
    fallback: str = DEFAULT_FALLBACK,
) -> str:
    """Render a file name from a page title and a template.

    Args:
        title: Page title, used to fill the `{title}` placeholder.
        template: Format string. `{title}` is the only supported placeholder.
        fallback: Stem to use when the title sanitises down to nothing.

    Returns:
        A safe file name ending in `.pdf`.

    Raises:
        OptionsError: If `template` references an unsupported placeholder.
    """
    safe_title = sanitize_filename(title, fallback=fallback)
    # The template owns the extension, so a page literally titled "report.pdf"
    # must not become "report.pdf.pdf".
    if safe_title.lower().endswith(".pdf"):
        safe_title = safe_title[: -len(".pdf")]

    try:
        rendered = template.format(title=safe_title)
    except (KeyError, IndexError) as exc:
        message = f"invalid filename template {template!r}: {{title}} is the only placeholder"
        raise OptionsError(message) from exc

    return ensure_pdf_suffix(sanitize_filename(rendered, fallback=fallback))


def resolve_destination(
    dest: str | Path,
    title: str,
    *,
    fallback: str = DEFAULT_FALLBACK,
) -> Path:
    """Work out which file a single conversion should be written to.

    Three shapes are supported, checked in order:

    1. A name containing `{title}`, which is filled in from the page title.
    2. An existing directory, which receives `<title>.pdf`.
    3. Anything else, treated as the literal file name.

    Args:
        dest: Destination supplied by the caller.
        title: Title of the rendered page.
        fallback: Stem to use when the title sanitises down to nothing.

    Returns:
        The path to write, always ending in `.pdf`.
    """
    path = Path(dest)

    if "{title}" in path.name:
        return path.with_name(build_filename(title, path.name, fallback=fallback))
    if path.is_dir():
        return path / build_filename(title, fallback=fallback)

    return path.with_name(ensure_pdf_suffix(sanitize_filename(path.name, fallback=fallback)))


def deduplicate(name: str, taken: Container[str]) -> str:
    """Return `name`, or a numbered variant that is not already in `taken`.

    Two different pages routinely share a title; without this they would
    silently overwrite each other.

    Args:
        name: Desired file name.
        taken: Names already in use.

    Returns:
        `name` if free, otherwise `"name (2).pdf"`, `"name (3).pdf"`, ...
    """
    if name not in taken:
        return name

    stem, dot, suffix = name.rpartition(".")
    if not dot:
        stem, suffix = name, ""

    counter = 2
    while True:
        candidate = f"{stem} ({counter}).{suffix}" if suffix else f"{stem} ({counter})"
        if candidate not in taken:
            return candidate
        counter += 1
