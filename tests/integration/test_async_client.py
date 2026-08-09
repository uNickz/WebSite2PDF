from pathlib import Path

import pytest

from website2pdf import AsyncClient, InvalidTargetError, PdfOptions, RenderOptions

from .conftest import PDF_MAGIC, page_count

pytestmark = pytest.mark.browser


@pytest.fixture
async def async_client():
    async with AsyncClient() as started:
        yield started


class TestAsyncConvert:
    async def test_returns_pdf_bytes(self, async_client, http_server):
        data = await async_client.convert(f"{http_server}/simple.html")
        assert data.startswith(PDF_MAGIC)

    async def test_writes_to_an_explicit_path(self, async_client, http_server, tmp_path):
        dest = tmp_path / "out.pdf"
        assert await async_client.convert(f"{http_server}/simple.html", dest) == dest
        assert dest.read_bytes().startswith(PDF_MAGIC)

    async def test_fills_the_title_placeholder(self, async_client, http_server, tmp_path):
        result = await async_client.convert(f"{http_server}/simple.html", tmp_path / "{title}.pdf")
        assert result.name == "Simple Fixture Page.pdf"

    async def test_honours_pdf_options(self, async_client, http_server):
        data = await async_client.convert(
            f"{http_server}/paged.html", pdf_options=PdfOptions(page_ranges="1")
        )
        assert page_count(data) == 1

    async def test_rejects_a_missing_local_file(self, async_client, tmp_path):
        with pytest.raises(InvalidTargetError):
            await async_client.convert(tmp_path / "nope.html")


class TestAsyncConvertMany:
    async def test_preserves_input_order(self, async_client, http_server):
        results = await async_client.convert_many(
            [
                f"{http_server}/simple.html",
                f"{http_server}/paged.html",
                f"{http_server}/simple.html",
            ]
        )
        assert [page_count(data) for data in results] == [1, 3, 1]

    async def test_writes_files_in_input_order(self, async_client, http_server, tmp_path):
        paths = await async_client.convert_many(
            [f"{http_server}/simple.html", f"{http_server}/paged.html"], tmp_path
        )
        assert [path.name for path in paths] == ["Simple Fixture Page.pdf", "Paged Fixture.pdf"]

    async def test_deduplicates_repeated_titles(self, async_client, http_server, tmp_path):
        url = f"{http_server}/simple.html"
        paths = await async_client.convert_many([url, url], tmp_path)
        assert [path.name for path in paths] == [
            "Simple Fixture Page.pdf",
            "Simple Fixture Page (2).pdf",
        ]

    async def test_renders_pages_at_the_same_time(self, http_server, monkeypatch):
        # Observing overlap directly, rather than timing the batch: wall-clock
        # assertions turn flaky the moment the runner is busy.
        client = AsyncClient(concurrency=3)
        original = client._render
        active = 0
        peak = 0

        async def tracked(
            target: str | Path,
            pdf_options: PdfOptions | None,
            render_options: RenderOptions | None,
        ) -> tuple[bytes, str]:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                return await original(target, pdf_options, render_options)
            finally:
                active -= 1

        monkeypatch.setattr(client, "_render", tracked)
        async with client:
            await client.convert_many([f"{http_server}/simple.html"] * 6)

        assert peak > 1, "pages were rendered one after another"
        assert peak <= 3, "the concurrency limit was not honoured"


class TestAsyncLifecycle:
    async def test_a_client_can_be_reused_after_being_closed(self, http_server):
        client = AsyncClient()
        try:
            assert (await client.convert(f"{http_server}/simple.html")).startswith(PDF_MAGIC)
            await client.close()
            assert not client.is_running
            assert (await client.convert(f"{http_server}/simple.html")).startswith(PDF_MAGIC)
        finally:
            await client.close()

    async def test_starting_and_closing_twice_are_no_ops(self):
        client = AsyncClient()
        await client.start()
        await client.start()
        assert client.is_running
        await client.close()
        await client.close()
        assert not client.is_running
