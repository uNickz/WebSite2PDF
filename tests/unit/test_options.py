import pytest

from website2pdf.errors import OptionsError
from website2pdf.options import BrowserOptions, Margin, PdfOptions, RenderOptions


class TestMargin:
    def test_uniform_applies_one_value_to_every_side(self):
        assert Margin.uniform("1cm") == Margin(top="1cm", right="1cm", bottom="1cm", left="1cm")

    def test_to_playwright_uses_the_expected_keys(self):
        assert Margin.uniform("2mm").to_playwright() == {
            "top": "2mm",
            "right": "2mm",
            "bottom": "2mm",
            "left": "2mm",
        }


class TestPdfOptions:
    def test_is_immutable(self):
        options = PdfOptions()
        with pytest.raises(AttributeError):
            options.scale = 2.0  # type: ignore[misc]

    def test_defaults_to_a4_with_backgrounds(self):
        rendered = PdfOptions().to_playwright()
        assert rendered["format"] == "A4"
        assert rendered["print_background"] is True

    @pytest.mark.parametrize("scale", [0.09, 2.01, -1.0, 0.0])
    def test_rejects_an_out_of_range_scale(self, scale):
        with pytest.raises(OptionsError, match="scale must be between"):
            PdfOptions(scale=scale)

    @pytest.mark.parametrize("scale", [0.1, 1.0, 2.0])
    def test_accepts_the_range_boundaries(self, scale):
        assert PdfOptions(scale=scale).scale == scale

    def test_rejects_a_header_template_without_display_header_footer(self):
        with pytest.raises(OptionsError, match="display_header_footer"):
            PdfOptions(header_template="<span></span>")

    def test_accepts_a_header_template_with_display_header_footer(self):
        options = PdfOptions(display_header_footer=True, header_template="<span></span>")
        assert options.to_playwright()["header_template"] == "<span></span>"

    def test_explicit_dimensions_replace_the_named_format(self):
        rendered = PdfOptions(width="10cm", height="20cm").to_playwright()
        assert "format" not in rendered
        assert rendered["width"] == "10cm"
        assert rendered["height"] == "20cm"

    def test_omits_keys_it_does_not_constrain(self):
        rendered = PdfOptions().to_playwright()
        assert "margin" not in rendered
        assert "page_ranges" not in rendered
        assert "header_template" not in rendered

    def test_includes_a_margin_when_given(self):
        rendered = PdfOptions(margin=Margin.uniform("1in")).to_playwright()
        assert rendered["margin"]["top"] == "1in"


class TestBrowserOptions:
    def test_launch_kwargs_stay_separate_from_context_kwargs(self):
        options = BrowserOptions(headless=False, args=("--mute-audio",), user_agent="ua")
        launch = options.to_launch_kwargs()
        context = options.to_context_kwargs()
        assert launch["headless"] is False
        assert launch["args"] == ["--mute-audio"]
        assert "user_agent" not in launch
        assert context["user_agent"] == "ua"

    def test_viewport_is_expanded_into_width_and_height(self):
        assert BrowserOptions(viewport=(800, 600)).to_context_kwargs()["viewport"] == {
            "width": 800,
            "height": 600,
        }

    def test_no_viewport_is_requested_explicitly(self):
        context = BrowserOptions(viewport=None).to_context_kwargs()
        assert context["no_viewport"] is True
        assert "viewport" not in context

    def test_http_credentials_are_expanded_into_a_mapping(self):
        context = BrowserOptions(http_credentials=("alice", "secret")).to_context_kwargs()
        assert context["http_credentials"] == {"username": "alice", "password": "secret"}

    def test_omits_optional_launch_keys(self):
        launch = BrowserOptions().to_launch_kwargs()
        assert "args" not in launch
        assert "executable_path" not in launch
        assert "channel" not in launch


class TestRenderOptions:
    def test_defaults_to_waiting_for_load(self):
        assert RenderOptions().wait_until == "load"

    def test_rejects_a_negative_timeout(self):
        with pytest.raises(OptionsError, match="timeout must not be negative"):
            RenderOptions(timeout=-1)

    def test_rejects_a_negative_extra_wait(self):
        with pytest.raises(OptionsError, match="extra_wait must not be negative"):
            RenderOptions(extra_wait=-1)

    def test_allows_a_disabled_timeout(self):
        assert RenderOptions(timeout=0).timeout == 0
