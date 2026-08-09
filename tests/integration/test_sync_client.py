import pytest

from website2pdf import Client, InvalidTargetError, NavigationError, PdfOptions
from website2pdf._naming import build_filename

from .conftest import PDF_MAGIC, page_count, page_sizes

pytestmark = pytest.mark.browser


class TestConvert:
    def test_returns_pdf_bytes_when_no_destination_is_given(self, client, http_server):
        data = client.convert(f"{http_server}/simple.html")
        assert data.startswith(PDF_MAGIC)
        assert page_count(data) == 1

    def test_writes_to_an_explicit_path(self, client, http_server, tmp_path):
        dest = tmp_path / "out.pdf"
        result = client.convert(f"{http_server}/simple.html", dest)
        assert result == dest
        assert dest.read_bytes().startswith(PDF_MAGIC)

    def test_adds_the_pdf_suffix_when_missing(self, client, http_server, tmp_path):
        result = client.convert(f"{http_server}/simple.html", tmp_path / "out")
        assert result == tmp_path / "out.pdf"
        assert result.is_file()

    def test_creates_missing_parent_directories(self, client, http_server, tmp_path):
        result = client.convert(f"{http_server}/simple.html", tmp_path / "a" / "b" / "out.pdf")
        assert result.is_file()

    def test_fills_the_title_placeholder_from_the_page(self, client, http_server, tmp_path):
        result = client.convert(f"{http_server}/simple.html", tmp_path / "{title}.pdf")
        assert result.name == "Simple Fixture Page.pdf"

    def test_writes_into_an_existing_directory(self, client, http_server, tmp_path):
        result = client.convert(f"{http_server}/simple.html", tmp_path)
        assert result == tmp_path / "Simple Fixture Page.pdf"

    def test_sanitizes_a_hostile_page_title(self, client, http_server, tmp_path):
        result = client.convert(f"{http_server}/awkward-title.html", tmp_path / "{title}.pdf")
        # The raw title is: Q1/Q2: "Results" <draft> | 90%?
        assert result.name == "Q1Q2 Results draft 90%.pdf"
        assert result.is_file()

    def test_converts_a_local_file(self, client, tmp_path):
        source = tmp_path / "local.html"
        source.write_text("<title>Local</title><h1>Local</h1>", encoding="utf-8")
        assert client.convert(source).startswith(PDF_MAGIC)

    def test_rejects_a_missing_local_file(self, client, tmp_path):
        with pytest.raises(InvalidTargetError):
            client.convert(tmp_path / "nope.html")

    def test_reports_an_unreachable_host_as_a_navigation_error(self, client):
        with pytest.raises(NavigationError):
            client.convert("http://127.0.0.1:1/unreachable.html")


class TestPdfOptions:
    def test_landscape_swaps_the_page_dimensions(self, client, http_server):
        url = f"{http_server}/simple.html"
        portrait_width, portrait_height = page_sizes(client.convert(url))[0]
        landscape = client.convert(url, pdf_options=PdfOptions(landscape=True))
        landscape_width, landscape_height = page_sizes(landscape)[0]

        assert portrait_width < portrait_height
        assert landscape_width > landscape_height

    def test_paper_format_changes_the_page_size(self, client, http_server):
        url = f"{http_server}/simple.html"
        a4 = page_sizes(client.convert(url, pdf_options=PdfOptions(paper_format="A4")))[0]
        a5 = page_sizes(client.convert(url, pdf_options=PdfOptions(paper_format="A5")))[0]
        assert a5[0] < a4[0]
        assert a5[1] < a4[1]

    def test_page_ranges_limits_the_output(self, client, http_server):
        url = f"{http_server}/paged.html"
        assert page_count(client.convert(url)) == 3
        assert page_count(client.convert(url, pdf_options=PdfOptions(page_ranges="1-2"))) == 2

    def test_explicit_dimensions_override_the_named_format(self, client, http_server):
        options = PdfOptions(width="20cm", height="10cm")
        data = client.convert(f"{http_server}/simple.html", pdf_options=options)
        width, height = page_sizes(data)[0]
        assert width > height


class TestConvertMany:
    def test_returns_one_pdf_per_target_in_order(self, client, http_server):
        results = client.convert_many([f"{http_server}/simple.html", f"{http_server}/paged.html"])
        assert [page_count(data) for data in results] == [1, 3]

    def test_writes_every_pdf_into_the_destination_directory(self, client, http_server, tmp_path):
        paths = client.convert_many(
            [f"{http_server}/simple.html", f"{http_server}/paged.html"],
            tmp_path,
        )
        assert [path.name for path in paths] == ["Simple Fixture Page.pdf", "Paged Fixture.pdf"]
        assert all(path.read_bytes().startswith(PDF_MAGIC) for path in paths)

    def test_does_not_let_identical_titles_overwrite_each_other(
        self, client, http_server, tmp_path
    ):
        url = f"{http_server}/simple.html"
        paths = client.convert_many([url, url, url], tmp_path)
        assert [path.name for path in paths] == [
            "Simple Fixture Page.pdf",
            "Simple Fixture Page (2).pdf",
            "Simple Fixture Page (3).pdf",
        ]
        assert len({path.read_bytes()[:5] for path in paths}) == 1

    def test_applies_a_filename_template(self, client, http_server, tmp_path):
        paths = client.convert_many(
            [f"{http_server}/simple.html"], tmp_path, filename_template="archive - {title}"
        )
        assert paths[0].name == build_filename("Simple Fixture Page", "archive - {title}")

    def test_creates_the_destination_directory(self, client, http_server, tmp_path):
        target = tmp_path / "new" / "nested"
        paths = client.convert_many([f"{http_server}/simple.html"], target)
        assert paths[0].parent == target


class TestLifecycle:
    def test_a_client_can_be_reused_after_being_closed(self, http_server):
        # Regression guard: in 0.x, stop_client() left a stale handle behind, so
        # the second conversion raised ClientAlreadyStarted.
        instance = Client()
        try:
            assert instance.convert(f"{http_server}/simple.html").startswith(PDF_MAGIC)
            instance.close()
            assert not instance.is_running
            assert instance.convert(f"{http_server}/simple.html").startswith(PDF_MAGIC)
        finally:
            instance.close()

    def test_starting_twice_is_a_no_op(self, http_server):
        with Client() as instance:
            instance.start()
            instance.start()
            assert instance.is_running
            assert instance.convert(f"{http_server}/simple.html").startswith(PDF_MAGIC)

    def test_closing_twice_is_a_no_op(self):
        instance = Client()
        instance.start()
        instance.close()
        instance.close()
        assert not instance.is_running

    def test_two_clients_can_coexist_on_one_thread(self, http_server):
        # Playwright's sync driver is greenlet-based and refuses a second
        # start() on the same thread, blaming asyncio. The driver is shared and
        # reference counted so independent clients still work.
        url = f"{http_server}/simple.html"
        with Client() as first, Client(pdf_options=PdfOptions(landscape=True)) as second:
            portrait = page_sizes(first.convert(url))[0]
            landscape = page_sizes(second.convert(url))[0]
        assert portrait[0] < portrait[1]
        assert landscape[0] > landscape[1]

    def test_closing_one_client_does_not_break_another(self, http_server):
        url = f"{http_server}/simple.html"
        first = Client()
        second = Client()
        try:
            first.convert(url)
            second.convert(url)
            first.close()
            # The shared driver must still be alive for the second client.
            assert second.convert(url).startswith(PDF_MAGIC)
        finally:
            first.close()
            second.close()

    def test_convert_starts_the_browser_implicitly(self, http_server):
        instance = Client()
        try:
            assert not instance.is_running
            instance.convert(f"{http_server}/simple.html")
            assert instance.is_running
        finally:
            instance.close()
