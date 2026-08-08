"""Render web pages and local HTML files to PDF.

The public API is built in phase 2; for now this module only exposes the
package version so that packaging and tooling can be validated end to end.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("website2pdf")
except PackageNotFoundError:  # pragma: no cover - only hit when running from a raw checkout
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
