"""Helpers shared by the browser-backed tests."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from pypdf import PdfReader

from website2pdf import Client

if TYPE_CHECKING:
    from collections.abc import Iterator

PDF_MAGIC = b"%PDF-"


def page_sizes(data: bytes) -> list[tuple[float, float]]:
    """Return the ``(width, height)`` of every page, in PostScript points.

    Args:
        data: Raw PDF bytes.

    Returns:
        One ``(width, height)`` pair per page, in document order.
    """
    reader = PdfReader(BytesIO(data))
    return [(float(page.mediabox.width), float(page.mediabox.height)) for page in reader.pages]


def page_text(data: bytes) -> str:
    """Return the extractable text of every page, concatenated.

    Args:
        data: Raw PDF bytes.

    Returns:
        The text Chromium actually painted into the document.
    """
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() for page in reader.pages)


def page_count(data: bytes) -> int:
    """Return the number of pages in a PDF.

    Args:
        data: Raw PDF bytes.

    Returns:
        The page count.
    """
    return len(PdfReader(BytesIO(data)).pages)


@pytest.fixture(scope="module")
def client() -> Iterator[Client]:
    """Provide one browser shared by every test in the module.

    Scoped to the module, not the session, on purpose: a live sync ``Client``
    keeps Playwright's greenlet driver running on this thread, and
    ``asyncio.run()`` refuses to start while that loop is alive. Releasing the
    driver at each module boundary lets sync and async test modules coexist.

    The matching rule for new tests: never mix sync ``Client`` tests and async
    tests in the same module.

    Yields:
        A started client.
    """
    with Client() as started:
        yield started
