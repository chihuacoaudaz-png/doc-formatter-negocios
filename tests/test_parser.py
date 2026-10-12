import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml

from doc_formatter import InvalidSource, parse_document, to_data
from doc_formatter.cli import main
from doc_formatter.model import Equation, Paragraph, Section, walk, walk_document, walk_inlines

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/uni-figmm-text-math"
PROFILE = ROOT / "profiles/uni-figmm/thesis@1.yaml"


def source(tmp_path, text="# Chapter\n\nText.\n", **overrides):
    (tmp_path / "section.md").write_text(text, encoding="utf-8")
    manifest = {"schema_version": 1, "profile": "test@1", "language": "es-PE", "meta": {"title": "Test"}, "body": ["section.md"]}
    manifest.update(overrides)
    (tmp_path / "document.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return tmp_path


def test_real_fixture_matches_acceptance_data():
    result = parse_document(FIXTURE / "source", PROFILE)
    expected = json.loads((FIXTURE / "expected.json").read_text())
    nodes = list(walk_document(result.document))
    from doc_formatter.model import BulletList, Figure, ListItem, Table, TableCell
    inline = []
    for n in nodes:
        if isinstance(n, (Paragraph, ListItem, TableCell)):
            inline.extend(walk_inlines(n.inlines))
    equations = [n for n in nodes if isinstance(n, Equation)]
    tables = [n for n in nodes if isinstance(n, Table)]
    figures = [n for n in nodes if isinstance(n, Figure)]
    assert len(result.document.frontmatter) == expected["frontmatter_sections"]
    assert len(result.document.body) == expected["chapters"]
    assert [s.kind for s in result.document.frontmatter] == ["top_level_section", "top_level_section"]
    assert result.document.body[0].kind == "chapter"
    assert {str(i): sum(isinstance(n, Section) and n.level == i for n in nodes) for i in (1, 2, 3, 4, 5)} == expected["headings_by_level"]
    assert sum(i.type == "math" for i in inline) == expected["math"]["inline"]
    assert sum(not e.numbered for e in equations) == expected["math"]["display_unnumbered"]
    assert [e.id for e in equations if e.numbered] == expected["equation_sequence"]
    assert [i.value for i in inline if i.type == "cross_ref"] == expected["cross_reference_targets"]
    assert [t.id for t in tables] == expected["table_sequence"]
    assert [f.id for f in figures] == expected["figure_sequence"]
    assert sum(isinstance(n, BulletList) for n in nodes) == expected["bullet_lists"]
    assert sum(isinstance(n, ListItem) for n in nodes) == expected["list_items"]
    assert len(tables) == expected["tables"]
    assert len(figures) == expected["figures"]
    assert expected["images"] == len(figures)
    assert result.diagnostics == ()
    numbered = {e.id: e for e in equations if e.numbered}
    assert numbered["eq:promedio"].latex == r"\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i"
    assert numbered["eq:profundidad-taladro"].latex.startswith("H = 0.15")
    assert result.references["eq:raiz"]["source"].line == 31
    assert result.document.body[1].title == "Marcos teórico y conceptual"


def test_ir_is_immutable_and_has_no_output_policy():
    result = parse_document(FIXTURE / "source", PROFILE)
    with pytest.raises(FrozenInstanceError):
        result.document.body[0].title = "Changed"
    with pytest.raises(TypeError):
        result.document.meta["title"] = "Changed"
    data = to_data(result.document)
    forbidden = {"profile", "renderer", "font", "size", "margin", "alignment", "docx_style", "label"}
    def check(node):
        if isinstance(node, dict):
            assert not forbidden.intersection(node)
            for value in node.values():
                check(value)
        elif isinstance(node, list):
            for value in node:
                check(value)
    check(data)
    assert to_data(parse_document(FIXTURE / "source", PROFILE).document) == data


@pytest.mark.parametrize(("text", "code", "line"), [
    ("# C\n\nSee @eq:missing.\n", "unresolved-reference", 3),
    ("# C\n\nFirst line\nthen @eq:missing.\n", "unresolved-reference", 4),
    ("# C\n\n:::equation {#eq:a}\nx\n:::\n\n:::equation {#eq:a}\ny\n:::\n", "duplicate-id", 7),
    ("# C\n\n:::unknown\nx\n:::\n", "unknown-block", 3),
    ("# C\n\n:::equation {#eq:a}\nx\n", "unclosed-equation", 3),
    ("# C\n\n:::equation\nx\n:::\n", "invalid-equation", 3),
    ("# C\n\n:::equation {#eq:a}\n:::\n", "empty-equation", 3),
    ("# C\n\n$$\nx\n", "unclosed-equation", 3),
    ("# C\n\n$x\n", "unclosed-math", 3),
    ("# C\n\n### Skipped\n", "heading-level", 3),
    ("## Missing chapter\n", "heading-level", 1),
    ("# C\n\n# Other\n", "chapter-count", 3),
    ("# C\n\n## 1.2 Numbered\n", "manual-numbering", 3),
    ("# C\n\n![Image](image.png)\n", "unsupported-inline", 3),
    ("# C\n\n```python\nx = 1\n```\n", "unsupported-block", 3),
    ("# C\n\n1. Ordered\n", "unsupported-block", 3),
    ("# C\n\n- outer\n  - nested\n", "unsupported-block", 4),
    ("# C\n\n| A | B |\n|---|---|\n| 1 | 2 |\n", "unsupported-block", 3),
    ("# C\n\n:::table {#tbl:a}\ntitle: T\n---\n| A |\n|---|\n| 1 |\n", "unclosed-table", 3),
    ("# C\n\n:::table {#tbl:a}\n---\n| A |\n|---|\n| 1 |\n:::\n", "invalid-table", 3),
    ("# C\n\n:::table\ntitle: T\n---\n| A |\n|---|\n| 1 |\n:::\n", "invalid-table", 3),
    ("# C\n\n:::figure {#fig:a}\ntitle: T\n:::\n", "invalid-figure", 3),
    ("# C\n\n:::figure {#fig:a}\nsrc: missing.png\ntitle: T\n:::\n", "missing-asset", 3),
    ("# C\n\n[@author2020]\n", "unsupported-citation", 3),
    ("# C\n\n<script>bad</script>\n", "unsupported-block", 3),
    ("# C\n\nA **reference @eq:missing**.\n", "unresolved-reference", 3),
])
def test_actionable_source_errors(tmp_path, text, code, line):
    with pytest.raises(InvalidSource) as caught:
        parse_document(source(tmp_path, text))
    error = caught.value.diagnostics[0]
    assert (error.code, error.source.file, error.source.line) == (code, "section.md", line)


def test_preserve_inline_semantics_and_escaped_literals(tmp_path):
    text = r"""# Chapter {#sec:chapter}

Text *emphasis* and **bold**, [link](https://example.org), $x_i^2$.

Escaped \$ and \@eq:literal; email author@example.org; see @sec:chapter.
"""
    result = parse_document(source(tmp_path, text))
    nodes = list(walk(result.document.body))
    inline = [i for n in nodes if isinstance(n, Paragraph) for i in walk_inlines(n.inlines)]
    assert {"emph", "strong", "link", "math", "cross_ref"} <= {i.type for i in inline}
    assert [i.value for i in inline if i.type == "cross_ref"] == ["sec:chapter"]
    assert next(i for i in inline if i.type == "link").value == "https://example.org"


def test_references_across_files_and_forward_references(tmp_path):
    source(tmp_path, "# First\n\nSee @eq:later.\n", body=["section.md", "second.md"])
    (tmp_path / "second.md").write_text("# Second\n\n:::equation {#eq:later}\nx=1\n:::\n")
    assert "eq:later" in parse_document(tmp_path).references


@pytest.mark.parametrize("override, code", [
    ({"schema_version": True}, "schema-version"),
    ({"schema_version": 2}, "schema-version"),
    ({"unknown": 1}, "unknown-key"),
    ({"body": []}, "invalid-manifest"),
    ({"body": [12]}, "invalid-manifest"),
    ({"body": ["missing.md"]}, "missing-section"),
    ({"body": ["../outside.md"]}, "invalid-path"),
    ({"body": ["section.md", "section.md"]}, "duplicate-section"),
    ({"meta": []}, "invalid-manifest"),
    ({"frontmatter": ["cover"]}, "unsupported-feature"),
    ({"bibliography": "references.bib"}, "unsupported-feature"),
])
def test_manifest_validation(tmp_path, override, code):
    with pytest.raises(InvalidSource) as caught:
        parse_document(source(tmp_path, **override))
    assert caught.value.diagnostics[0].code == code
    assert caught.value.diagnostics[0].source.file.endswith("document.yaml")


def test_duplicate_yaml_key_has_exact_location(tmp_path):
    source(tmp_path)
    with (tmp_path / "document.yaml").open("a") as f:
        f.write("profile: other\n")
    with pytest.raises(InvalidSource) as caught:
        parse_document(tmp_path)
    assert caught.value.diagnostics[0].code == "invalid-yaml"
    assert caught.value.diagnostics[0].source.line == len((tmp_path / "document.yaml").read_text().splitlines())


def test_authored_frontmatter_and_missing_required_slot(tmp_path):
    source(tmp_path, "# Resumen\n\nTexto.\n", frontmatter=[{"abstract_es": "section.md"}], body=["chapter.md"])
    (tmp_path / "chapter.md").write_text("# Chapter\n\nBody.\n")
    result = parse_document(tmp_path)
    assert result.document.frontmatter[0].kind == "top_level_section"
    assert result.document.frontmatter[0].slot == "abstract_es"
    assert result.document.frontmatter[0].title == "Resumen"
    profile = {"id": "test@1", "schema": {"frontmatter": {"required": ["abstract_es", "abstract_en"]}, "body": {}}}
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.safe_dump(profile))
    with pytest.raises(InvalidSource) as caught:
        parse_document(tmp_path, path)
    assert caught.value.diagnostics[0].code == "missing-slot"


def test_profile_schema_checks_and_does_not_change_ir(tmp_path):
    source(tmp_path)
    profile = {"id": "test@1", "renderer": "unrelated-output", "schema": {"body": {"required_chapters": [{"title": "Chapter"}]}, "max_heading_depth": 1}}
    p = tmp_path / "profile.yaml"
    p.write_text(yaml.safe_dump(profile))
    result = parse_document(tmp_path, p)
    assert result.diagnostics == ()
    assert result.document == parse_document(tmp_path).document
    profile["schema"]["body"]["required_chapters"] = [{"title": "Absent"}]
    p.write_text(yaml.safe_dump(profile))
    with pytest.raises(InvalidSource) as caught:
        parse_document(tmp_path, p)
    assert caught.value.diagnostics[0].code == "missing-chapter"


def test_cli_writes_json_and_failure_leaves_no_output(tmp_path, capsys):
    target = tmp_path / "ir.json"
    assert main(["parse", str(FIXTURE / "source"), "--profile", str(PROFILE), "-o", str(target)]) == 0
    assert json.loads(target.read_text(encoding="utf-8"))["document"]["type"] == "document"
    assert capsys.readouterr().err == ""
    assert main(["parse", str(FIXTURE / "source"), "-o", str(target)]) == 1
    assert "File exists" in capsys.readouterr().err
    source(tmp_path, "# C\n\n@eq:missing\n")
    failed = tmp_path / "failed.json"
    assert main(["parse", str(tmp_path), "-o", str(failed)]) == 1
    assert not failed.exists()
    report = json.loads(capsys.readouterr().err)
    assert report["diagnostics"][0]["code"] == "unresolved-reference"


def test_reference_style_link_preserves_destination(tmp_path):
    result = parse_document(source(tmp_path, "# C\n\nA [named link][ref].\n\n[ref]: https://example.org/path\n"))
    paragraph = result.document.body[0].children[0]
    link = next(i for i in paragraph.inlines if i.type == "link")
    assert link.value == "https://example.org/path"
    assert link.children[0].value == "named link"


@pytest.mark.parametrize("value", [".nan", ".inf", "2024-01-01"])
def test_non_json_metadata_is_rejected_at_manifest(tmp_path, value):
    source(tmp_path)
    path = tmp_path / "document.yaml"
    path.write_text(f"schema_version: 1\nprofile: test@1\nlanguage: es\nbody: [section.md]\nmeta:\n  value: {value}\n")
    with pytest.raises(InvalidSource) as caught:
        parse_document(tmp_path)
    assert caught.value.diagnostics[0].code == "invalid-manifest"
    assert caught.value.diagnostics[0].source.line == 5


def test_numbered_insertion_does_not_modify_existing_ids(tmp_path):
    original = "# C\n\n:::equation {#eq:first}\nx\n:::\n\n$$y$$\n\n:::equation {#eq:last}\nz\n:::\n"
    first = parse_document(source(tmp_path, original))
    changed = original.replace("$$y$$", ":::equation {#eq:inserted}\nw\n:::\n\n$$y$$")
    second = parse_document(source(tmp_path, changed))
    assert set(first.references) <= set(second.references)
    assert [e.id for e in walk(second.document.body) if isinstance(e, Equation) and e.numbered] == ["eq:first", "eq:inserted", "eq:last"]


@pytest.mark.parametrize("change, code", [
    ({"id": "different"}, "profile-mismatch"),
    ({"extends": "base"}, "unsupported-profile"),
    ({"schema": {"body": {}, "max_heading_depth": False}}, "invalid-profile"),
    ({"schema": {"body": {}, "typo": 1}}, "invalid-profile"),
    ({"schema": {"body": {}, "frontmatter": {"required": ["cover"]}}}, "unsupported-profile"),
    ({"schema": {"body": {}, "max_heading_depth": 1}}, "heading-depth"),
])
def test_profile_errors(tmp_path, change, code):
    source(tmp_path, "# Chapter\n\n## Subsection\n")
    profile = {"id": "test@1", "schema": {"body": {}}}
    profile.update(change)
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.safe_dump(profile))
    with pytest.raises(InvalidSource) as caught:
        parse_document(tmp_path, path)
    assert caught.value.diagnostics[0].code == code


def test_duplicate_ids_across_files(tmp_path):
    source(tmp_path, "# First {#sec:same}\n", body=["section.md", "second.md"])
    (tmp_path / "second.md").write_text("# Second {#sec:same}\n")
    with pytest.raises(InvalidSource) as caught:
        parse_document(tmp_path)
    assert caught.value.diagnostics[0].code == "duplicate-id"
    assert caught.value.diagnostics[0].source.file == "second.md"
