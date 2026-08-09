import pytest

from website2pdf._targets import normalize_target
from website2pdf.errors import InvalidTargetError


class TestNormalizeTarget:
    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://example.com/page?q=1#frag",
            "file:///tmp/page.html",
            "about:blank",
            "data:text/html,<h1>hi</h1>",
        ],
    )
    def test_passes_navigable_urls_through_unchanged(self, url):
        assert normalize_target(url) == url

    def test_trims_surrounding_whitespace(self):
        assert normalize_target("  https://example.com  ") == "https://example.com"

    def test_accepts_an_uppercase_scheme(self):
        assert normalize_target("HTTPS://example.com") == "HTTPS://example.com"

    def test_converts_an_existing_path_object_to_a_file_uri(self, tmp_path):
        page = tmp_path / "page.html"
        page.write_text("<h1>hi</h1>", encoding="utf-8")
        assert normalize_target(page) == page.as_uri()

    def test_converts_an_existing_path_string_to_a_file_uri(self, tmp_path):
        page = tmp_path / "page.html"
        page.write_text("<h1>hi</h1>", encoding="utf-8")
        assert normalize_target(str(page)) == page.as_uri()

    def test_resolves_a_relative_path(self, tmp_path, monkeypatch):
        page = tmp_path / "page.html"
        page.write_text("<h1>hi</h1>", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        assert normalize_target("page.html") == page.resolve().as_uri()

    def test_rejects_an_empty_target(self):
        with pytest.raises(InvalidTargetError, match="must not be empty"):
            normalize_target("   ")

    def test_rejects_an_unsupported_scheme(self):
        with pytest.raises(InvalidTargetError, match="unsupported URL scheme"):
            normalize_target("ftp://example.com/page.html")

    def test_rejects_a_missing_local_file(self, tmp_path):
        with pytest.raises(InvalidTargetError, match="not found"):
            normalize_target(tmp_path / "nope.html")

    def test_rejects_a_directory(self, tmp_path):
        with pytest.raises(InvalidTargetError, match="not found"):
            normalize_target(tmp_path)

    def test_treats_a_drive_letter_as_a_path_not_a_scheme(self):
        # urlparse reports "c" as the scheme for "C:\\page.html"; a one-letter
        # scheme must fall through to filesystem handling.
        with pytest.raises(InvalidTargetError, match="not found"):
            normalize_target("C:\\definitely\\missing.html")
