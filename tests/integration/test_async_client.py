import asyncio

import pytest

from website2pdf import AsyncClient, InvalidTargetError, PdfOptions

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

    async def test_renders_concurrently(self, http_server):
        # Four pages at concurrency 4 should not take four times one page.
        url = f"{http_server}/simple.html"
        async with AsyncClient(concurrency=4) as client:
            await client.convert(url)  # warm the browser up first

            start = asyncio.get_running_loop().time()
            await client.convert(url)
            sequential = asyncio.get_running_loop().time() - start

            start = asyncio.get_running_loop().time()
            await client.convert_many([url] * 4)
            concurrent = asyncio.get_running_loop().time() - start

        assert concurrent < sequential * 4


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
