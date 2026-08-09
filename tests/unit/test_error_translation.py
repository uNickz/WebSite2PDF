"""Mapping of Playwright's single Error type onto this library's hierarchy."""

import pytest

from website2pdf._browser import (
    navigation_failed,
    navigation_timeout,
    render_failed,
    translate_launch_error,
)
from website2pdf.errors import (
    BrowserLaunchError,
    BrowserNotInstalledError,
    NavigationError,
    RenderError,
    WebSite2PDFError,
)


class TestTranslateLaunchError:
    @pytest.mark.parametrize(
        "text",
        [
            "Executable doesn't exist at /home/u/.cache/ms-playwright/chromium-1234/chrome",
            "Please run the following command to download new browsers: playwright install",
            "Looks like Playwright was just installed or updated.",
        ],
    )
    def test_recognises_a_missing_browser(self, text):
        assert isinstance(translate_launch_error(Exception(text)), BrowserNotInstalledError)

    def test_missing_browser_error_names_the_install_command(self):
        assert "playwright install chromium" in str(
            translate_launch_error(Exception("playwright install"))
        )

    def test_falls_back_to_a_generic_launch_error(self):
        result = translate_launch_error(Exception("Target page crashed"))
        assert isinstance(result, BrowserLaunchError)
        assert "Target page crashed" in str(result)

    def test_every_translation_stays_inside_the_library_hierarchy(self):
        assert isinstance(translate_launch_error(Exception("boom")), WebSite2PDFError)


class TestNavigationErrors:
    def test_timeout_reports_the_budget_and_the_url(self):
        error = navigation_timeout("https://example.com", 5000)
        assert isinstance(error, NavigationError)
        assert "5000 ms" in str(error)
        assert "https://example.com" in str(error)

    def test_timeout_suggests_what_to_change(self):
        assert "timeout" in str(navigation_timeout("https://example.com", 1000))

    def test_failure_keeps_the_underlying_explanation(self):
        error = navigation_failed("https://example.com", Exception("net::ERR_CONNECTION_REFUSED"))
        assert isinstance(error, NavigationError)
        assert "ERR_CONNECTION_REFUSED" in str(error)


class TestRenderErrors:
    def test_failure_keeps_the_underlying_explanation(self):
        error = render_failed("https://example.com", Exception("PDF generation is not supported"))
        assert isinstance(error, RenderError)
        assert "not supported" in str(error)
        assert "https://example.com" in str(error)


class TestHierarchy:
    @pytest.mark.parametrize(
        "error",
        [
            BrowserNotInstalledError(),
            BrowserLaunchError("x"),
            NavigationError("x"),
            RenderError("x"),
        ],
    )
    def test_one_except_clause_catches_everything(self, error):
        assert isinstance(error, WebSite2PDFError)

    def test_the_missing_browser_message_can_name_another_browser(self):
        assert "firefox" in str(BrowserNotInstalledError("firefox"))
