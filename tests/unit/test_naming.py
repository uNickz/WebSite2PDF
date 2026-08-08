import pytest

from website2pdf._naming import (
    build_filename,
    deduplicate,
    ensure_pdf_suffix,
    resolve_destination,
    sanitize_filename,
)
from website2pdf.errors import OptionsError


class TestSanitizeFilename:
    @pytest.mark.parametrize("char", ["<", ">", ":", '"', "/", "\\", "|", "?", "*"])
    def test_strips_characters_windows_rejects(self, char):
        assert char not in sanitize_filename(f"before{char}after")

    def test_strips_control_characters(self):
        assert sanitize_filename("a\x00b\x08c\x7fd") == "abcd"

    def test_treats_unicode_separator_controls_as_whitespace(self):
        # Python's \s matches \x1c-\x1f, so these behave like the newline case
        # rather than being deleted outright.
        assert sanitize_filename("a\x1fb") == "a b"

    def test_collapses_whitespace_runs(self):
        assert sanitize_filename("too    many\n\tspaces") == "too many spaces"

    def test_turns_newlines_into_separators_rather_than_deleting_them(self):
        # Newlines and tabs sit in the control range; stripping them as illegal
        # characters would glue the surrounding words together.
        assert sanitize_filename("first\nsecond") == "first second"

    def test_strips_trailing_dots_and_spaces(self):
        # Windows drops these silently, which would rename the file behind the
        # caller's back.
        assert sanitize_filename("report. . ") == "report"

    def test_preserves_the_extension(self):
        assert sanitize_filename("quarterly report.pdf") == "quarterly report.pdf"

    def test_preserves_only_the_last_dot_as_extension(self):
        assert sanitize_filename("v1.2.3.pdf") == "v1.2.3.pdf"

    @pytest.mark.parametrize("name", ["CON", "nul", "Com1", "LPT9", "aux"])
    def test_defuses_windows_reserved_device_names(self, name):
        assert sanitize_filename(name) == f"_{name}"

    def test_defuses_reserved_names_that_carry_an_extension(self):
        assert sanitize_filename("CON.pdf") == "_CON.pdf"

    def test_falls_back_when_nothing_survives(self):
        assert sanitize_filename('<>:"/\\|?*', fallback="fallback") == "fallback"

    def test_falls_back_on_an_empty_name(self):
        assert sanitize_filename("", fallback="fallback") == "fallback"

    def test_falls_back_when_the_name_is_only_an_extension(self):
        assert sanitize_filename(".pdf", fallback="fallback") == "fallback.pdf"

    def test_truncates_the_stem_but_keeps_the_extension(self):
        result = sanitize_filename("x" * 500 + ".pdf", max_length=20)
        assert result == "x" * 20 + ".pdf"

    def test_keeps_non_ascii_characters(self):
        assert sanitize_filename("relazione annuale — città") == "relazione annuale — città"


class TestEnsurePdfSuffix:
    @pytest.mark.parametrize("name", ["report.pdf", "report.PDF", "report.Pdf"])
    def test_leaves_an_existing_suffix_alone(self, name):
        assert ensure_pdf_suffix(name) == name

    def test_appends_a_missing_suffix(self):
        assert ensure_pdf_suffix("report") == "report.pdf"


class TestBuildFilename:
    def test_uses_the_title_by_default(self):
        assert build_filename("My Page") == "My Page.pdf"

    def test_applies_a_custom_template(self):
        assert build_filename("My Page", "archive - {title}") == "archive - My Page.pdf"

    def test_sanitizes_the_title_before_substitution(self):
        assert build_filename('Q1/Q2: "x"') == "Q1Q2 x.pdf"

    def test_does_not_double_the_extension(self):
        assert build_filename("report.pdf") == "report.pdf"

    def test_strips_a_pdf_extension_from_the_title_before_templating(self):
        assert build_filename("report.PDF", "archive - {title}") == "archive - report.pdf"

    def test_keeps_a_non_pdf_extension_from_the_title(self):
        assert build_filename("data.csv") == "data.csv.pdf"

    def test_falls_back_on_an_empty_title(self):
        assert build_filename("") == "document.pdf"

    def test_rejects_an_unknown_placeholder(self):
        with pytest.raises(OptionsError, match="only placeholder"):
            build_filename("My Page", "{unknown}.pdf")


class TestDeduplicate:
    def test_passes_through_an_unused_name(self):
        assert deduplicate("a.pdf", set()) == "a.pdf"

    def test_numbers_a_collision(self):
        assert deduplicate("a.pdf", {"a.pdf"}) == "a (2).pdf"

    def test_keeps_counting_past_the_first_collision(self):
        assert deduplicate("a.pdf", {"a.pdf", "a (2).pdf"}) == "a (3).pdf"

    def test_handles_a_name_without_an_extension(self):
        assert deduplicate("a", {"a"}) == "a (2)"


class TestResolveDestination:
    def test_uses_a_literal_name_as_given(self, tmp_path):
        assert resolve_destination(tmp_path / "out.pdf", "Ignored") == tmp_path / "out.pdf"

    def test_appends_the_pdf_suffix_to_a_literal_name(self, tmp_path):
        assert resolve_destination(tmp_path / "out", "Ignored") == tmp_path / "out.pdf"

    def test_fills_the_title_placeholder(self, tmp_path):
        result = resolve_destination(tmp_path / "{title}.pdf", "My Page")
        assert result == tmp_path / "My Page.pdf"

    def test_writes_into_an_existing_directory(self, tmp_path):
        assert resolve_destination(tmp_path, "My Page") == tmp_path / "My Page.pdf"

    def test_sanitizes_a_literal_name(self, tmp_path):
        result = resolve_destination(tmp_path / 'a"b.pdf', "Ignored")
        assert result == tmp_path / "ab.pdf"
