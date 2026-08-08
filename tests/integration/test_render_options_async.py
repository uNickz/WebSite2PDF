"""Async counterparts of the render-option tests.

Kept in their own module because a sync ``Client`` holds Playwright's greenlet
driver open, which makes ``asyncio.run()`` unusable on the same thread. See
``tests/integration/conftest.py``.
"""

import pytest

from website2pdf import AsyncClient, BrowserOptions, NavigationError, RenderOptions

from .conftest import page_text

pytestmark = pytest.mark.browser


class TestAsyncRenderOptions:
    async def test_emulate_media_applies(self, http_server):
        async with AsyncClient() as instance:
            data = await instance.convert(
                f"{http_server}/media.html",
                render_options=RenderOptions(emulate_media="screen"),
            )
        assert "SCREENMARKER" in page_text(data)

    async def test_wait_for_selector_applies(self, http_server):
        async with AsyncClient() as instance:
            data = await instance.convert(
                f"{http_server}/deferred.html",
                render_options=RenderOptions(wait_for_selector="#late"),
            )
        assert "DEFERREDMARKER" in page_text(data)

    async def test_extra_wait_applies(self, http_server):
        async with AsyncClient() as instance:
            data = await instance.convert(
                f"{http_server}/deferred.html",
                render_options=RenderOptions(extra_wait=1500),
            )
        assert "DEFERREDMARKER" in page_text(data)

    async def test_cookies_reach_the_page(self, http_server):
        options = BrowserOptions(
            cookies=({"name": "w2p", "value": "async", "domain": "127.0.0.1", "path": "/"},)
        )
        async with AsyncClient(browser_options=options) as instance:
            data = await instance.convert(f"{http_server}/cookies.html")
        assert "w2p=async" in page_text(data)

    async def test_navigation_failure_is_translated(self):
        async with AsyncClient() as instance:
            with pytest.raises(NavigationError):
                await instance.convert("http://127.0.0.1:1/unreachable.html")
