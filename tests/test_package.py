"""Smoke tests that validate the packaging setup itself."""

import importlib.metadata
from pathlib import Path

import website2pdf


def test_version_is_exposed():
    assert isinstance(website2pdf.__version__, str)
    assert website2pdf.__version__ != "0.0.0.dev0", (
        "package is not installed; run `uv sync` so tests exercise the built artifact"
    )


def test_version_matches_distribution_metadata():
    assert website2pdf.__version__ == importlib.metadata.version("website2pdf")


def test_py_typed_marker_is_present():
    """Guard the PEP 561 marker: without it downstream type checkers ignore our hints.

    This only proves the marker exists in the import tree. That it also lands
    inside the built wheel is asserted by the `build` CI job, because an editable
    install records just its import shim in the distribution RECORD.
    """
    module_file = website2pdf.__file__
    assert module_file is not None
    assert (Path(module_file).parent / "py.typed").is_file()
