"""Client configuration that can be checked without launching a browser."""

import pytest

from website2pdf import AsyncClient, Client, PdfOptions, RenderOptions
from website2pdf.errors import OptionsError


class TestDefaults:
    @pytest.mark.parametrize("factory", [Client, AsyncClient])
    def test_a_fresh_client_is_not_running(self, factory):
        assert factory().is_running is False

    @pytest.mark.parametrize("factory", [Client, AsyncClient])
    def test_options_default_to_shared_immutable_instances(self, factory):
        # Frozen dataclasses make this safe, unlike the 0.x mutable defaults.
        assert factory().pdf_options == PdfOptions()
        assert factory().render_options == RenderOptions()

    @pytest.mark.parametrize("factory", [Client, AsyncClient])
    def test_two_clients_do_not_share_mutable_state(self, factory):
        first = factory()
        second = factory(pdf_options=PdfOptions(landscape=True))
        assert first.pdf_options.landscape is False
        assert second.pdf_options.landscape is True


class TestAsyncConcurrency:
    def test_defaults_to_a_bounded_value(self):
        assert AsyncClient().concurrency >= 1

    @pytest.mark.parametrize("value", [0, -1])
    def test_rejects_a_non_positive_concurrency(self, value):
        with pytest.raises(OptionsError, match="concurrency must be at least 1"):
            AsyncClient(concurrency=value)
