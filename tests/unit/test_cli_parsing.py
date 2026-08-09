"""CLI argument handling that never reaches the browser."""

import io

import pytest
import typer
from typer.testing import CliRunner

from website2pdf import __version__
from website2pdf.__main__ import _expand_targets, _parse_headers, app

runner = CliRunner()


class TestExpandTargets:
    def test_passes_plain_targets_through(self):
        assert _expand_targets(["a", "b"]) == ["a", "b"]

    def test_reads_one_target_per_line_from_stdin(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO("https://a\nhttps://b\n"))
        assert _expand_targets(["-"]) == ["https://a", "https://b"]

    def test_ignores_blank_stdin_lines(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO("https://a\n\n  \nhttps://b\n"))
        assert _expand_targets(["-"]) == ["https://a", "https://b"]

    def test_mixes_stdin_with_explicit_targets(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO("https://b\n"))
        assert _expand_targets(["https://a", "-"]) == ["https://a", "https://b"]

    def test_rejects_an_empty_result(self, monkeypatch):
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        with pytest.raises(typer.BadParameter, match="no targets"):
            _expand_targets(["-"])


class TestParseHeaders:
    def test_parses_a_name_and_value(self):
        assert _parse_headers(["Accept: text/html"]) == {"Accept": "text/html"}

    def test_keeps_colons_inside_the_value(self):
        assert _parse_headers(["Referer: https://example.com"]) == {
            "Referer": "https://example.com"
        }

    def test_parses_several_headers(self):
        assert _parse_headers(["A: 1", "B: 2"]) == {"A": "1", "B": "2"}

    def test_accepts_an_empty_value(self):
        assert _parse_headers(["X-Empty:"]) == {"X-Empty": ""}

    @pytest.mark.parametrize("header", ["no-colon", ": value"])
    def test_rejects_a_malformed_header(self, header):
        with pytest.raises(typer.BadParameter, match="expected"):
            _parse_headers([header])


class TestUsageErrors:
    def test_version_prints_and_exits_cleanly(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_missing_targets_is_a_usage_error(self):
        assert runner.invoke(app, []).exit_code == 2

    def test_an_invalid_scale_is_reported_before_a_browser_starts(self):
        result = runner.invoke(app, ["https://example.com", "--scale", "9"])
        assert result.exit_code == 2
        assert "scale must be between" in result.output

    def test_an_unknown_paper_format_is_rejected(self):
        assert runner.invoke(app, ["https://example.com", "--format", "A9"]).exit_code == 2

    def test_stdout_refuses_several_targets(self):
        result = runner.invoke(app, ["https://a", "https://b", "-o", "-"])
        assert result.exit_code == 2
        assert "single PDF to stdout" in result.output

    def test_a_file_destination_refuses_several_targets(self, tmp_path):
        result = runner.invoke(app, ["https://a", "https://b", "-o", str(tmp_path / "out.pdf")])
        assert result.exit_code == 2
        assert "must be an existing directory" in result.output

    def test_a_malformed_header_is_reported(self):
        result = runner.invoke(app, ["https://example.com", "-H", "nonsense"])
        assert result.exit_code == 2
        assert "expected" in result.output
