"""Navigation and context behaviour that the 0.x driver got wrong."""

import pytest

from website2pdf import BrowserOptions, Client, NavigationError, RenderOptions

from .conftest import page_text

pytestmark = pytest.mark.browser


class TestEmulateMedia:
    def test_defaults_to_print_media(self, client, http_server):
        text = page_text(client.convert(f"{http_server}/media.html"))
        assert "PRINTMARKER" in text
        assert "SCREENMARKER" not in text

    def test_can_reproduce_the_on_screen_appearance(self, client, http_server):
        text = page_text(
            client.convert(
                f"{http_server}/media.html",
                render_options=RenderOptions(emulate_media="screen"),
            )
        )
        assert "SCREENMARKER" in text
        assert "PRINTMARKER" not in text


class TestWaiting:
    def test_content_added_after_load_is_missed_by_default(self, client, http_server):
        text = page_text(client.convert(f"{http_server}/deferred.html"))
        assert "IMMEDIATEMARKER" in text
        assert "DEFERREDMARKER" not in text

    def test_wait_for_selector_catches_late_content(self, client, http_server):
        text = page_text(
            client.convert(
                f"{http_server}/deferred.html",
                render_options=RenderOptions(wait_for_selector="#late"),
            )
        )
        assert "DEFERREDMARKER" in text

    def test_extra_wait_catches_late_content(self, client, http_server):
        text = page_text(
            client.convert(
                f"{http_server}/deferred.html",
                render_options=RenderOptions(extra_wait=1500),
            )
        )
        assert "DEFERREDMARKER" in text

    def test_wait_for_a_selector_that_never_appears_times_out(self, client, http_server):
        with pytest.raises(NavigationError, match="timed out"):
            client.convert(
                f"{http_server}/simple.html",
                render_options=RenderOptions(wait_for_selector="#never", timeout=500),
            )


class TestCookies:
    def test_cookies_reach_the_page_before_it_loads(self, http_server):
        # Regression guard: 0.x called add_cookie() on the driver before
        # navigating, which Playwright's predecessor rejected outright.
        options = BrowserOptions(
            cookies=({"name": "w2p", "value": "marker", "domain": "127.0.0.1", "path": "/"},)
        )
        with Client(browser_options=options) as instance:
            text = page_text(instance.convert(f"{http_server}/cookies.html"))
        assert "w2p=marker" in text

    def test_no_cookies_by_default(self, client, http_server):
        assert "COOKIES[]" in page_text(client.convert(f"{http_server}/cookies.html"))
