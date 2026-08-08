"""End-to-end CLI runs against a real browser.

Kept away from the sync ``client`` fixture: the CLI calls ``asyncio.run()``,
which cannot start while a sync ``Client`` holds Playwright's greenlet driver
open on this thread.
"""

import pytest
from typer.testing import CliRunner

from website2pdf.__main__ import app

from .conftest import PDF_MAGIC, page_sizes, page_text

pytestmark = pytest.mark.browser

runner = CliRunner()


class TestWritingFiles:
    def test_writes_a_named_file(self, http_server, tmp_path):
        dest = tmp_path / "out.pdf"
        result = runner.invoke(app, [f"{http_server}/simple.html", "-o", str(dest)])
        assert result.exit_code == 0
        assert dest.read_bytes().startswith(PDF_MAGIC)

    def test_writes_into_a_directory_using_the_page_title(self, http_server, tmp_path):
        result = runner.invoke(app, [f"{http_server}/simple.html", "-o", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "Simple Fixture Page.pdf").is_file()

    def test_defaults_to_the_current_directory(self, http_server, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, [f"{http_server}/simple.html"])
        assert result.exit_code == 0
        assert (tmp_path / "Simple Fixture Page.pdf").is_file()

    def test_converts_several_targets(self, http_server, tmp_path):
        result = runner.invoke(
            app,
            [f"{http_server}/simple.html", f"{http_server}/paged.html", "-o", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert (tmp_path / "Simple Fixture Page.pdf").is_file()
        assert (tmp_path / "Paged Fixture.pdf").is_file()

    def test_applies_a_name_template(self, http_server, tmp_path):
        result = runner.invoke(
            app, [f"{http_server}/simple.html", "-o", str(tmp_path), "--name", "archive-{title}"]
        )
        assert result.exit_code == 0
        assert (tmp_path / "archive-Simple Fixture Page.pdf").is_file()

    def test_writes_the_pdf_to_stdout(self, http_server):
        result = runner.invoke(app, [f"{http_server}/simple.html", "-o", "-"])
        assert result.exit_code == 0
        assert result.stdout_bytes.startswith(PDF_MAGIC)

    def test_reads_targets_from_stdin(self, http_server, tmp_path):
        result = runner.invoke(
            app, ["-", "-o", str(tmp_path)], input=f"{http_server}/simple.html\n"
        )
        assert result.exit_code == 0
        assert (tmp_path / "Simple Fixture Page.pdf").is_file()


class TestOptions:
    def test_landscape_reaches_the_renderer(self, http_server, tmp_path):
        dest = tmp_path / "out.pdf"
        result = runner.invoke(app, [f"{http_server}/simple.html", "-o", str(dest), "--landscape"])
        assert result.exit_code == 0
        width, height = page_sizes(dest.read_bytes())[0]
        assert width > height

    def test_paper_format_reaches_the_renderer(self, http_server, tmp_path):
        a4 = tmp_path / "a4.pdf"
        a5 = tmp_path / "a5.pdf"
        runner.invoke(app, [f"{http_server}/simple.html", "-o", str(a4), "--format", "A4"])
        runner.invoke(app, [f"{http_server}/simple.html", "-o", str(a5), "--format", "A5"])
        assert page_sizes(a5.read_bytes())[0][0] < page_sizes(a4.read_bytes())[0][0]

    def test_pages_limits_the_output(self, http_server, tmp_path):
        dest = tmp_path / "out.pdf"
        result = runner.invoke(app, [f"{http_server}/paged.html", "-o", str(dest), "--pages", "1"])
        assert result.exit_code == 0
        assert len(page_sizes(dest.read_bytes())) == 1

    def test_media_screen_reaches_the_renderer(self, http_server, tmp_path):
        dest = tmp_path / "out.pdf"
        result = runner.invoke(
            app, [f"{http_server}/media.html", "-o", str(dest), "--media", "screen"]
        )
        assert result.exit_code == 0
        assert "SCREENMARKER" in page_text(dest.read_bytes())


class TestReporting:
    def test_lists_written_files_on_stderr(self, http_server, tmp_path):
        result = runner.invoke(app, [f"{http_server}/simple.html", "-o", str(tmp_path)])
        assert result.exit_code == 0
        assert "Simple Fixture Page.pdf" in result.output

    def test_quiet_suppresses_the_listing(self, http_server, tmp_path):
        result = runner.invoke(app, [f"{http_server}/simple.html", "-o", str(tmp_path), "-q"])
        assert result.exit_code == 0
        assert "Simple Fixture Page.pdf" not in result.output

    def test_reports_an_unreachable_target_and_exits_one(self, tmp_path):
        result = runner.invoke(app, ["http://127.0.0.1:1/nope.html", "-o", str(tmp_path)])
        assert result.exit_code == 1
        assert "error:" in result.output

    def test_reports_a_missing_local_file_and_exits_one(self, tmp_path):
        result = runner.invoke(app, [str(tmp_path / "nope.html"), "-o", str(tmp_path)])
        assert result.exit_code == 1
        assert "error:" in result.output
