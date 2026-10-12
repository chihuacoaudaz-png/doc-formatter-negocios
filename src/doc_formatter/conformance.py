"""Checks on the actual generated package, separate from source validation."""
from lxml import etree as E

from .backends.docx import NS, bookmark_name, q, unpack
from .layout import length_points
from .model import walk_inlines


def inspect_docx(path, plan):
    files = unpack(path)
    document = E.fromstring(files["word/document.xml"])
    styles = E.fromstring(files["word/styles.xml"])
    checks, findings = [], []
    def check(name, passed, message):
        checks.append({"id": name, "passed": bool(passed)})
        if not passed:
            findings.append({"severity": "error", "code": name, "message": message})
    para_blocks = [b for b in plan.blocks if b.kind != "table"]
    paras = document.findall("w:body/w:p", NS)
    tables = document.findall("w:body/w:tbl", NS)
    check("paragraph-count", len(paras) == len(para_blocks), "Unexpected body paragraph count")
    check("table-count", len(tables) == sum(b.kind == "table" for b in plan.blocks), "Unexpected body table count")
    actual_styles = [p.find("w:pPr/w:pStyle", NS) for p in paras]
    check("style-bindings", [p.get(q("w:val")) if p is not None else None for p in actual_styles] == [plan.styles[b.role]["docx_style"] for b in para_blocks], "Paragraph styles differ from the layout plan")
    # Paragraph/run overrides outside named styles are forbidden, except the
    # cell-level alignment overrides that the approved thesis also uses inside tables.
    direct = document.xpath(
        "//w:p[not(ancestor::w:tbl)]/w:pPr/*[not(self::w:pStyle)]"
        " | //w:rPr/*[not(self::w:rStyle)][not(ancestor::m:oMath)][not(ancestor::w:tbl)]",
        namespaces=NS,
    )
    check("named-styles", len(direct) == 0, "Direct paragraph or text formatting remains outside math")
    # Table cells may carry jc (first column left) and header Strong; still require pStyle.
    table_paras = document.xpath("//w:tbl//w:p", namespaces=NS)
    check(
        "table-cell-styles",
        all(p.find("w:pPr/w:pStyle", NS) is not None for p in table_paras),
        "A table cell is missing its named paragraph style",
    )
    style_ids = {s.get(q("w:styleId")) for s in styles.findall("w:style", NS)}
    check("styles-present", all(s["docx_style"] in style_ids for s in plan.styles.values()), "A named style is missing")
    for role, config in plan.styles.items():
        style = next((s for s in styles.findall("w:style", NS) if s.get(q("w:styleId")) == config["docx_style"]), None)
        if style is None:
            continue
        for key, xpath, attr, expected in (
            ("font", "w:rPr/w:rFonts", "ascii", config.get("font")),
            ("size", "w:rPr/w:sz", "val", str(round(length_points(config["size"]) * 2)) if "size" in config else None),
            ("align", "w:pPr/w:jc", "val", "both" if config.get("align") == "justify" else config.get("align")),
            ("line_spacing", "w:pPr/w:spacing", "line", str(round(config["line_spacing"] * 240)) if "line_spacing" in config else None),
        ):
            if expected is not None:
                node = style.find(xpath, NS)
                check(f"style-{role}-{key}", node is not None and node.get(q("w:" + attr)) == expected, f"Style property {role}.{key} differs")
    page = document.find("w:body/w:sectPr/w:pgSz", NS)
    check("page-size", page is not None and (page.get(q("w:w")), page.get(q("w:h"))) == ("11906", "16838"), "Expected A4 page size")
    margins = document.find("w:body/w:sectPr/w:pgMar", NS)
    check("page-margins", margins is not None and all(margins.get(q("w:" + k)) == str(round(length_points(v) * 20)) for k, v in plan.page["margins"].items()), "Margins differ from profile")
    math_count = len(document.findall(".//m:oMath", NS))
    expected_math = sum(b.kind == "equation" for b in plan.blocks) + sum(i.type == "math" for b in plan.blocks for i in walk_inlines(b.inlines))
    for block in plan.blocks:
        if block.kind == "table":
            for row in block.rows:
                for cell in row:
                    expected_math += sum(i.type == "math" for i in walk_inlines(cell))
    check("editable-math", math_count == expected_math, "Expected editable OMML equations are missing")
    fields, active, malformed = [], None, False
    for element in document.iter():
        if element.tag == q("w:fldChar"):
            kind = element.get(q("w:fldCharType"))
            if kind == "begin":
                if active is not None:
                    malformed = True
                active = {"instruction": "", "cached": "", "separated": False}
            elif kind == "separate":
                if active is None:
                    malformed = True
                else:
                    active["separated"] = True
            elif kind == "end":
                if active is None:
                    malformed = True
                else:
                    fields.append(active)
                    active = None
        elif active is not None and element.tag == q("w:instrText"):
            active["instruction"] += element.text or ""
        elif active is not None and active["separated"] and element.tag == q("w:t"):
            active["cached"] += element.text or ""
    check("field-structure", not malformed and active is None and all(f["separated"] for f in fields), "Malformed or incomplete complex fields")
    eq_field = plan.sequences.get("equation", {}).get("field")
    tbl_field = plan.sequences.get("table", {}).get("field")
    fig_field = plan.sequences.get("figure", {}).get("field")
    eq_sequence = [f for f in fields if eq_field and f["instruction"].strip().startswith(eq_field)]
    tbl_sequence = [f for f in fields if tbl_field and f["instruction"].strip().startswith(tbl_field)]
    fig_sequence = [f for f in fields if fig_field and f["instruction"].strip().startswith(fig_field)]
    numbered_eq = [b for b in plan.blocks if b.kind == "equation" and b.number is not None]
    numbered_tbl = [b for b in plan.blocks if b.kind == "table_label" and b.number is not None]
    numbered_fig = [b for b in plan.blocks if b.kind == "figure_label" and b.number is not None]
    check(
        "equation-sequence",
        [f["cached"] for f in eq_sequence] == [str(b.number) for b in numbered_eq]
        and all(f["instruction"].strip() == eq_field + " \\* ARABIC" for f in eq_sequence),
        "Equation fields or cached sequence differ",
    )
    check(
        "table-sequence",
        [f["cached"] for f in tbl_sequence] == [str(b.number) for b in numbered_tbl]
        and all(f["instruction"].strip() == tbl_field + " \\* ARABIC" for f in tbl_sequence),
        "Table fields or cached sequence differ",
    )
    check(
        "figure-sequence",
        [f["cached"] for f in fig_sequence] == [str(b.number) for b in numbered_fig]
        and all(f["instruction"].strip() == fig_field + " \\* ARABIC" for f in fig_sequence),
        "Figure fields or cached sequence differ",
    )
    drawings = len(document.findall(".//w:drawing", NS))
    check("figure-images", drawings == sum(b.kind == "figure_image" for b in plan.blocks), "Expected embedded figure images are missing")
    references = [i for b in plan.blocks for i in walk_inlines(b.inlines) if i.type == "cross_ref"]
    # Cross-refs also appear as OOXML fields inside table cells (not PlannedBlock.inlines on the grid).
    for block in plan.blocks:
        if block.kind == "table":
            for row in block.rows:
                for cell in row:
                    references.extend(i for i in walk_inlines(cell) if i.type == "cross_ref")
    ref_fields = [f for f in fields if f["instruction"].strip().startswith("REF ")]
    check("reference-fields", [(f["instruction"].strip(), f["cached"]) for f in ref_fields] == [("REF " + bookmark_name(i.value) + " \\h", plan.references[i.value]["label"]) for i in references], "References or their cached values differ")
    bookmarks = document.findall(".//w:bookmarkStart", NS)
    names = [b.get(q("w:name")) for b in bookmarks]
    starts = [b.get(q("w:id")) for b in bookmarks]
    ends = [b.get(q("w:id")) for b in document.findall(".//w:bookmarkEnd", NS)]
    check("bookmarks", len(names) == len(set(names)) and len(starts) == len(set(starts)) and sorted(starts) == sorted(ends) and all(bookmark_name(key) in names for key in plan.references), "Missing, duplicate or unbalanced bookmarks")
    update = E.fromstring(files["word/settings.xml"]).find("w:updateFields", NS)
    check("update-fields", update is not None and update.get(q("w:val")) in {"1", "true"}, "Fields are not marked for refresh")
    return {
        "profile": plan.profile,
        "target": "docx",
        "checks": checks,
        "findings": findings,
        "counts": {
            "paragraphs": len(paras),
            "tables": len(tables),
            "figures": drawings,
            "math": math_count,
            "numbered_equations": len(eq_sequence),
            "numbered_tables": len(tbl_sequence),
            "numbered_figures": len(fig_sequence),
            "references": len(ref_fields),
        },
    }
