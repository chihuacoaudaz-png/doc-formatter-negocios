import json
from pathlib import Path
import shutil

from lxml import etree as E
import pytest
import yaml

from doc_formatter import InvalidSource, parse_document, to_data
from doc_formatter.backends.docx import NS, emit, pack, q, unpack
from doc_formatter.build import build_document
from doc_formatter.conformance import inspect_docx
from doc_formatter.layout import plan_document

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures/uni-figmm-text-math/source"
PROFILE = ROOT / "profiles/uni-figmm/thesis@1.yaml"
requires_pandoc = pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc integration requires the external executable")


def sample_plan(profile=PROFILE):
    return plan_document(parse_document(SOURCE, profile), profile)


def test_layout_is_disposable_and_keeps_ir_unchanged():
    parsed = parse_document(SOURCE, PROFILE)
    before = to_data(parsed.document)
    plan = plan_document(parsed, PROFILE)
    assert to_data(parsed.document) == before
    assert plan == plan_document(parsed, PROFILE)
    assert [b.label for b in plan.blocks if b.kind == "equation" and b.label][:4] == ["(1)", "(2)", "(3)", "(4)"]
    assert plan.references["eq:profundidad-taladro"]["label"] == "(3)"
    assert plan.references["eq:avance"]["label"] == "(4)"
    assert plan.references["eq:raiz"]["label"] == "(36)"
    assert plan.references["tbl:fijacion-tajeos"]["label"] == "Tabla 1"
    assert plan.references["tbl:fijacion-contorno"]["label"] == "Tabla 2"
    assert plan.references["fig:sobrerotura"]["label"] == "Figura 1"
    assert plan.references["fig:perno-helicoidal"]["label"] == "Figura 2"
    assert [b.label for b in plan.blocks if b.kind == "table_label"] == ["Tabla 1", "Tabla 2"]
    assert [b.label for b in plan.blocks if b.kind == "figure_label"] == ["Figura 1", "Figura 2"]
    titles = [b.title for b in plan.blocks if b.kind in {"heading", "run_in_heading"}]
    assert titles[0] == "Resumen"
    assert titles[1] == "Abstract"
    assert titles[2] == "Capítulo I. Parte introductoria del trabajo"
    assert "1.1\tGeneralidades" in titles
    assert "1.2.1\tProblema general" in titles
    assert "Capítulo II. Marcos teórico y conceptual" in titles
    assert "2.1.5.2\tArranque de cuatro secciones." in titles
    assert "2.1.2.3.1\tPernos de anclaje." in titles
    assert "2.1.2.1\tSostenimiento con uso de madera." in titles
    assert "Capítulo III. Desarrollo del trabajo de investigación" in titles
    assert "Capítulo IV. Análisis e interpretación de resultados" in titles
    assert "Capítulo V. Pruebas matemáticas suplementarias" in titles
    assert "2.1\tMarco teórico" in titles
    assert any(b.kind == "run_in_heading" and b.level == 4 and b.inlines for b in plan.blocks)
    texts = ["".join(i.value for i in b.inlines) for b in plan.blocks if b.kind == "paragraph"]
    assert "Palabras clave — Mallas de perforación, sobrerotura, costos de sostenimiento, voladura de precorte, software de automatización, Python" in texts
    assert "Keywords — Drill grids, overburden, support costs, pre-cut blasting, automation software, Python" in texts
    assert plan.blocks[1].role == "body_standalone"
    with pytest.raises(TypeError):
        plan.styles["body"]["size"] = "12pt"


@pytest.mark.parametrize("change", [
    lambda p: p["styles"]["roles"]["body"].update({"size": "oops"}),
    lambda p: p["styles"]["roles"]["body"].update({"typo": True}),
    lambda p: p["styles"]["roles"]["body"].update({"inherits": "body"}),
    lambda p: next(r for r in p["layout"] if r["id"] == "caption-numbering")["sequences"]["equation"].update({"scope": "chapter"}),
    lambda p: next(r for r in p["layout"] if r["id"] == "caption-numbering")["sequences"]["equation"].update({"format": "{unknown}"}),
    lambda p: next(r for r in p["layout"] if r["id"] == "caption-numbering")["sequences"]["equation"].update({"field": "SEQ X \\r 9"}),
    lambda p: p["styles"]["roles"]["equation"].update({"docx_style": "PARRAFOS"}),
    lambda p: p["styles"]["page"]["margins"].update({"left": "100cm"}),
])
def test_unsupported_profile_values_fail_before_emission(tmp_path, change):
    config = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    change(config)
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    with pytest.raises(InvalidSource):
        sample_plan(path)


@requires_pandoc
def test_actual_docx_has_math_live_fields_and_named_styles(tmp_path):
    plan = sample_plan()
    path, _ = emit(plan, tmp_path)
    report = inspect_docx(path, plan)
    assert report["findings"] == []
    assert report["counts"] == {"paragraphs": 235, "tables": 2, "figures": 2, "math": 64, "numbered_equations": 36, "numbered_tables": 2, "numbered_figures": 2, "references": 5}
    root = E.fromstring(unpack(path)["word/document.xml"])
    for paragraph in root.findall("w:body/w:p", NS):
        if paragraph.xpath('.//w:instrText[contains(text(), "SEQ Ecuacion")]', namespaces=NS):
            assert len(paragraph.findall("m:oMath", NS)) == 1
    # Fraction, root, summation and exponents survive as editable math structures.
    assert root.findall(".//m:f", NS)
    assert root.findall(".//m:rad", NS)
    assert root.findall(".//m:nary", NS)
    assert root.findall(".//m:sSubSup", NS)
    heading_tabs = [p for p in root.findall("w:body/w:p", NS) if p.find("w:pPr/w:pStyle", NS) is not None and p.find("w:pPr/w:pStyle", NS).get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") in {"TITU2", "TITU3", "TITU4", "TITU5"}]
    assert heading_tabs and all(p.find(".//w:tab", NS) is not None for p in heading_tabs)
    styles = E.fromstring(unpack(path)["word/styles.xml"])
    assert styles.xpath('w:style[@w:styleId="TITU4"]/w:pPr/w:ind/@w:firstLine', namespaces=NS) == ["720"]
    assert styles.xpath('w:style[@w:styleId="TITU5"]/w:pPr/w:ind/@w:firstLine', namespaces=NS) == ["720"]
    assert styles.xpath('w:style[@w:styleId="TITU4"]/w:pPr/w:tabs/w:tab/@w:pos', namespaces=NS) == ["1701"]
    assert styles.xpath('w:style[@w:styleId="TITU5"]/w:pPr/w:tabs/w:tab/@w:pos', namespaces=NS) == ["1843"]
    assert styles.xpath('w:style[@w:styleId="TITU3"]/w:pPr/w:ind/@w:firstLine', namespaces=NS) == ["0"]
    assert styles.xpath('w:style[@w:styleId="Strong"]/w:rPr/w:b', namespaces=NS)
    assert styles.xpath('w:style[@w:styleId="XTABLAS"]/w:rPr/w:b', namespaces=NS)
    assert len(root.findall("w:body/w:tbl", NS)) == 2
    assert any(
        "Tabla" in "".join(p.itertext())
        and p.find("w:pPr/w:pStyle", NS) is not None
        and p.find("w:pPr/w:pStyle", NS).get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") == "XTABLAS"
        for p in root.findall("w:body/w:p", NS)
    )
    labels = [p for p in root.findall("w:body/w:p", NS) if "".join(p.itertext()).startswith("Variable ")]
    assert labels and all(p.find("w:r/w:rPr/w:rStyle", NS) is not None and p.find("w:r/w:rPr/w:rStyle", NS).get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") == "Strong" for p in labels)


@requires_pandoc
def test_profile_font_change_changes_styles_not_content(tmp_path):
    config = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    config["styles"]["roles"]["body"]["size"] = "12pt"
    profile = tmp_path / "profile.yaml"
    profile.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    plan = sample_plan(profile)
    path, _ = emit(plan, tmp_path)
    assert inspect_docx(path, plan)["findings"] == []
    styles = E.fromstring(unpack(path)["word/styles.xml"])
    assert styles.xpath('w:style[@w:styleId="PARRAFOS"]/w:rPr/w:sz/@w:val', namespaces=NS) == ["24"]
    assert parse_document(SOURCE, profile).document == parse_document(SOURCE, PROFILE).document


@requires_pandoc
def test_source_insertion_renumbers_later_equations_and_cached_refs(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(SOURCE, source)
    path = source / "sections/05-pruebas-matematicas.md"
    path.write_text(path.read_text().replace(":::equation {#eq:raiz}", ":::equation {#eq:inserted}\ny = 2\n:::\n\n:::equation {#eq:raiz}"))
    plan = plan_document(parse_document(source, PROFILE), PROFILE)
    assert [b.label for b in plan.blocks if b.kind == "equation" and b.number is not None][-3:] == ["(35)", "(36)", "(37)"]
    assert plan.references["eq:raiz"]["label"] == "(37)"
    assert plan.references["eq:inserted"]["label"] == "(36)"
    path, _ = emit(plan, tmp_path)
    assert inspect_docx(path, plan)["findings"] == []


@requires_pandoc
def test_corrupt_cached_field_is_detected(tmp_path):
    plan = sample_plan()
    path, _ = emit(plan, tmp_path)
    files = unpack(path)
    root = E.fromstring(files["word/document.xml"])
    for paragraph in root.findall("w:body/w:p", NS):
        if paragraph.xpath('.//w:instrText[contains(text(), "SEQ")]', namespaces=NS):
            cached = next(t for t in paragraph.findall(".//w:t", NS) if t.text == "1")
            cached.text = "99"
            break
    files["word/document.xml"] = E.tostring(root)
    pack(files, path)
    assert "equation-sequence" in [f["code"] for f in inspect_docx(path, plan)["findings"]]


@requires_pandoc
def test_build_publishes_bundle_and_overwrites_output(tmp_path):
    output = tmp_path / "bundle"
    report = build_document(SOURCE, PROFILE, output)
    assert {p.name for p in output.iterdir()} == {"document.docx", "layout-plan.json", "conformance.json"}
    assert json.loads((output / "conformance.json").read_text()) == report
    assert report["findings"][0]["code"] == "manual-field-refresh"
    marker = output / "stale.txt"
    marker.write_text("old")
    first_docx = (output / "document.docx").read_bytes()
    again = build_document(SOURCE, PROFILE, output)
    assert again["counts"] == report["counts"]
    assert not marker.exists()
    assert (output / "document.docx").is_file()
    assert (output / "document.docx").read_bytes() == first_docx


@requires_pandoc
def test_unsupported_latex_does_not_publish_document(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(SOURCE, source)
    md = source / "sections/05-pruebas-matematicas.md"
    md.write_text(md.read_text().replace(r"\bar{x}", r"\unknowncommand{x}"))
    output = tmp_path / "bundle"
    with pytest.raises(InvalidSource) as caught:
        build_document(source, PROFILE, output)
    assert caught.value.diagnostics[0].code == "renderer-error"
    assert not output.exists()
