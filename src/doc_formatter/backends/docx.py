"""Pandoc emission, named-style compilation and live Word fields."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import json
import re
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

from ..layout import length_points
from ..model import Source, fail, walk_inlines

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main", "m": "http://schemas.openxmlformats.org/officeDocument/2006/math", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
XML = "http://www.w3.org/XML/1998/namespace"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def q(name):
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def element(tag, **attrs):
    return E.Element(q(tag), {q("w:" + k): str(v) for k, v in attrs.items()})


def xml_bytes(root):
    return E.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def unpack(path_or_bytes):
    with ZipFile(BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def pack(files, path):
    # Stable archive metadata. XML normalization is intentionally limited here.
    from zipfile import ZipInfo
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, files[name])


def run_tool(command, *, input=None):
    try:
        result = subprocess.run(command, input=input, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail("renderer-error", str(exc), Source(str(command[0]), 1))
    if result.returncode:
        fail("renderer-error", result.stderr.decode(errors="replace") or f"Tool exited with {result.returncode}", Source(str(command[0]), 1))
    return result


def pandoc_executable():
    executable = shutil.which("pandoc")
    if executable is None:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            Path(local_app_data) / "Pandoc" / "pandoc.exe" if local_app_data else None,
            Path(r"C:\Program Files\Pandoc\pandoc.exe"),
            Path(r"C:\Program Files (x86)\Pandoc\pandoc.exe"),
            Path("/usr/bin/pandoc"),
            Path("/usr/local/bin/pandoc"),
        ]
        for c in candidates:
            if c and c.exists():
                return str(c)
        fail("missing-pandoc", "Install Pandoc and make it available on PATH", Source("pandoc", 1))
    return executable


def style_properties(role, config, plan):
    ppr = element("w:pPr")
    if role.startswith("heading_") or role in {"chapter_title", "top_level_section_title"}:
        ppr.append(element("w:keepNext"))
        ppr.append(element("w:keepLines"))
    if config.get("keep_next") and ppr.find(q("w:keepNext")) is None:
        ppr.append(element("w:keepNext"))
    if "line_spacing" in config or "space_after" in config:
        spacing = element("w:spacing")
        if "line_spacing" in config:
            spacing.set(q("w:line"), str(round(config["line_spacing"] * 240)))
            spacing.set(q("w:lineRule"), "auto")
        if "space_after" in config:
            spacing.set(q("w:after"), str(round(length_points(config["space_after"]) * 20)))
        ppr.append(spacing)
    if "first_line_indent" in config or "left_indent" in config or "hanging_indent" in config:
        ind = {}
        if "left_indent" in config:
            ind["left"] = round(length_points(config["left_indent"]) * 20)
        if "hanging_indent" in config:
            ind["hanging"] = round(length_points(config["hanging_indent"]) * 20)
        if "first_line_indent" in config and "hanging_indent" not in config:
            ind["firstLine"] = round(length_points(config["first_line_indent"]) * 20)
        ppr.append(element("w:ind", **ind))
    if "tab_stop" in config:
        tabs = element("w:tabs")
        tabs.append(element("w:tab", val="left", pos=round(length_points(config["tab_stop"]) * 20)))
        ppr.append(tabs)
    if "align" in config:
        ppr.append(element("w:jc", val="both" if config["align"] == "justify" else config["align"]))
    if role in {"chapter_title", "top_level_section_title"} or role.startswith("heading_"):
        level = 1 if role in {"chapter_title", "top_level_section_title"} else int(role.split("_")[1])
        ppr.append(element("w:outlineLvl", val=level - 1))
    rpr = element("w:rPr")
    if "font" in config:
        rpr.append(element("w:rFonts", ascii=config["font"], hAnsi=config["font"], cs=config["font"], eastAsia=config["font"]))
    for key, tag in (("bold", "b"), ("italic", "i")):
        if key in config:
            rpr.append(element("w:" + tag, val="1" if config[key] else "0"))
    if "size" in config:
        size = round(length_points(config["size"]) * 2)
        rpr.extend([element("w:sz", val=size), element("w:szCs", val=size)])
    rpr.append(element("w:lang", val=plan.language))
    return ppr, rpr


def compile_style(styles, role, config, plan):
    sid = config["docx_style"]
    existing = styles.xpath("w:style[@w:styleId=$sid]", namespaces=NS, sid=sid)
    ppr, rpr = style_properties(role, config, plan)
    if sid == "Normal" and existing:
        style = existing[0]
        for child in list(style):
            if child.tag in {q("w:pPr"), q("w:rPr")}:
                style.remove(child)
        style.append(ppr)
        style.append(rpr)
        return
    for node in existing:
        styles.remove(node)
    style = element("w:style", type="paragraph", customStyle="1", styleId=sid)
    style.append(element("w:name", val=sid))
    style.append(element("w:basedOn", val="Normal"))
    style.append(element("w:next", val=plan.styles.get("body", config)["docx_style"]))
    style.append(element("w:qFormat"))
    style.append(ppr)
    style.append(rpr)
    styles.append(style)


def compile_character_styles(styles):
    marks = (("Strong", "b"), ("Emphasis", "i"))
    for sid, tag in marks:
        for existing in styles.xpath("w:style[@w:styleId=$sid]", namespaces=NS, sid=sid):
            styles.remove(existing)
        style = element("w:style", type="character", customStyle="1", styleId=sid)
        style.append(element("w:name", val=sid))
        rpr = element("w:rPr")
        rpr.append(element("w:" + tag, val="1"))
        style.append(rpr)
        styles.append(style)


def add_page_footer(files, plan):
    footer = plan.page.get("footer")
    if not footer:
        return
    role = plan.styles[footer["role"]]
    ftr = E.Element(q("w:ftr"))
    paragraph = element("w:p")
    ppr = element("w:pPr")
    ppr.append(element("w:pStyle", val=role["docx_style"]))
    paragraph.append(ppr)
    paragraph.extend(field("PAGE", "1"))
    ftr.append(paragraph)
    files["word/footer1.xml"] = xml_bytes(ftr)
    rels = E.fromstring(files["word/_rels/document.xml.rels"])
    rel = E.Element("{%s}Relationship" % REL)
    rel.set("Id", "rIdDocFormatterFooter")
    rel.set("Type", OFFICE_REL + "/footer")
    rel.set("Target", "footer1.xml")
    rels.append(rel)
    files["word/_rels/document.xml.rels"] = xml_bytes(rels)
    types = E.fromstring(files["[Content_Types].xml"])
    override = E.Element("{%s}Override" % CT)
    override.set("PartName", "/word/footer1.xml")
    override.set("ContentType", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml")
    types.append(override)
    files["[Content_Types].xml"] = xml_bytes(types)
    document = E.fromstring(files["word/document.xml"])
    for sect in document.findall(".//w:sectPr", NS):
        for old in sect.findall("w:footerReference", NS):
            sect.remove(old)
        ref = element("w:footerReference", type="default")
        ref.set("{%s}id" % OFFICE_REL, "rIdDocFormatterFooter")
        sect.insert(0, ref)
    files["word/document.xml"] = xml_bytes(document)


def compile_reference(plan, pandoc, path):
    files = unpack(run_tool([pandoc, "--print-default-data-file", "reference.docx"]).stdout)
    styles = E.fromstring(files["word/styles.xml"])
    for role, config in plan.styles.items():
        compile_style(styles, role, config, plan)
    compile_character_styles(styles)
    files["word/styles.xml"] = xml_bytes(styles)
    document = E.fromstring(files["word/document.xml"])
    for sect in document.findall(".//w:sectPr", NS):
        for tag in ("pgSz", "pgMar"):
            for child in sect.findall("w:" + tag, NS):
                sect.remove(child)
        sect.insert(0, element("w:pgSz", w=11906, h=16838))
        sect.insert(1, element("w:pgMar", **{k: round(length_points(v) * 20) for k, v in plan.page["margins"].items()}, header=720, footer=720, gutter=0))
    files["word/document.xml"] = xml_bytes(document)
    add_page_footer(files, plan)
    pack(files, path)


def bookmark_name(identifier):
    return "df_" + sha256(identifier.encode()).hexdigest()[:32]


def raw(elements):
    return {"t": "RawInline", "c": ["openxml", "".join(E.tostring(e, encoding="unicode") for e in elements)]}


def text_run(value):
    run = element("w:r")
    text = element("w:t")
    text.set(f"{{{XML}}}space", "preserve")
    text.text = value
    run.append(text)
    return run


def field(instruction, cached):
    begin = element("w:r")
    begin.append(element("w:fldChar", fldCharType="begin", dirty="true"))
    code = element("w:r")
    text = element("w:instrText")
    text.set(f"{{{XML}}}space", "preserve")
    text.text = " " + instruction + " "
    code.append(text)
    separate = element("w:r")
    separate.append(element("w:fldChar", fldCharType="separate"))
    end = element("w:r")
    end.append(element("w:fldChar", fldCharType="end"))
    return [begin, code, separate, text_run(cached), end]


def ast_inlines(nodes, plan):
    result = []
    for node in nodes:
        if node.type == "text":
            # Preserve word boundaries without Markdown escaping/reparsing.
            result.extend({"t": "Space"} if s.isspace() else {"t": "Str", "c": s} for s in re.split(r"(\s+)", node.value) if s)
        elif node.type == "math":
            result.append({"t": "Math", "c": [{"t": "InlineMath"}, node.value]})
        elif node.type in ("emph", "strong"):
            style = "Emphasis" if node.type == "emph" else "Strong"
            result.append({"t": "Span", "c": [["", [], [["custom-style", style]]], ast_inlines(node.children, plan)]})
        elif node.type == "link":
            result.append({"t": "Link", "c": [["", [], []], ast_inlines(node.children, plan), [node.value, ""]]})
        elif node.type == "line_break":
            result.append({"t": "LineBreak"})
        elif node.type == "cross_ref":
            result.append(raw(field("REF " + bookmark_name(node.value) + " \\h", plan.references[node.value]["label"])))
        else:
            fail("unsupported-inline", f"DOCX does not support {node.type}", node.source)
    return result


def strong_or_emph(nodes, *, strong=True, emph=False):
    result = nodes
    if strong:
        result = [{"t": "Span", "c": [["", [], [["custom-style", "Strong"]]], result]}]
    if emph:
        result = [{"t": "Span", "c": [["", [], [["custom-style", "Emphasis"]]], result]}]
    return result


def ooxml_inlines(nodes, plan, pandoc, omml_cache):
    """Render cell inlines to OOXML runs / OMML (table body)."""
    runs = []
    for node in nodes:
        if node.type == "text":
            runs.append(text_run(node.value))
        elif node.type in ("emph", "strong"):
            for child in ooxml_inlines(node.children, plan, pandoc, omml_cache):
                if child.tag != q("w:r"):
                    runs.append(child)
                    continue
                rpr = child.find(q("w:rPr"))
                if rpr is None:
                    rpr = element("w:rPr")
                    child.insert(0, rpr)
                rpr.append(element("w:rStyle", val="Emphasis" if node.type == "emph" else "Strong"))
                runs.append(child)
        elif node.type == "line_break":
            run = element("w:r")
            run.append(element("w:br"))
            runs.append(run)
        elif node.type == "cross_ref":
            runs.extend(field("REF " + bookmark_name(node.value) + " \\h", plan.references[node.value]["label"]))
        elif node.type == "math":
            runs.append(inline_omml(pandoc, node.value, node.source, omml_cache))
        elif node.type == "link":
            fail("unsupported-inline", "Links inside table cells are not implemented yet", node.source)
        else:
            fail("unsupported-inline", f"DOCX does not support {node.type} in table cells", node.source)
    return runs


def inline_omml(pandoc, latex, source, cache):
    if latex not in cache:
        result = run_tool([pandoc, "-f", "markdown", "-t", "docx", "-o", "-"], input=f"${latex}$\n".encode())
        root = E.fromstring(unpack(result.stdout)["word/document.xml"])
        maths = root.findall(".//m:oMath", NS)
        if len(maths) != 1:
            fail("renderer-error", f"Could not convert inline math to OMML: {latex}", source)
        cache[latex] = maths[0]
    # Fresh copy: the same formula may appear in several cells.
    return E.fromstring(E.tostring(cache[latex]))


def cell_plain_width(inlines):
    size = 0
    for node in walk_inlines(inlines):
        if node.type == "text":
            size += max(len(node.value), 1)
        elif node.type == "math":
            size += max(len(node.value), 3)
    return size


def column_widths_dxa(rows, cols):
    # Content-sized columns, capped near the approved thesis Tabla 1 total (~6377 twips).
    weights = [1] * cols
    for row in rows:
        for index, cell in enumerate(row):
            weights[index] = max(weights[index], cell_plain_width(cell))
    total = sum(weights) or 1
    target = 6400
    widths = [max(900, round(target * weight / total)) for weight in weights]
    scale = target / sum(widths)
    return [max(900, round(width * scale)) for width in widths]


def build_table_xml(block, plan, pandoc, omml_cache):
    if "table_header" not in plan.styles:
        fail("unsupported-profile", "Tables require a table_header style role", block.source)
    cols = len(block.rows[0]) if block.rows else 0
    widths = column_widths_dxa(block.rows, cols)
    tbl = element("w:tbl")
    tbl_pr = element("w:tblPr")
    # Auto width + fixed preferred columns: centered content box, not full text width.
    tbl_pr.append(element("w:tblW", w=str(sum(widths)), type="dxa"))
    tbl_pr.append(element("w:jc", val="center"))
    borders = element("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge in {"top", "bottom", "insideH"}:
            borders.append(element(f"w:{edge}", val="single", sz="4", space="0", color="auto"))
        else:
            borders.append(element(f"w:{edge}", val="nil", sz="0", space="0", color="auto"))
    tbl_pr.append(borders)
    tbl_pr.append(element("w:tblLook", val="04A0", firstRow="1", lastRow="0", firstColumn="1", lastColumn="0", noHBand="0", noVBand="1"))
    tbl.append(tbl_pr)
    grid = element("w:tblGrid")
    for width in widths:
        grid.append(element("w:gridCol", w=str(width)))
    tbl.append(grid)
    for row_index, row in enumerate(block.rows):
        tr = element("w:tr")
        tr_pr = element("w:trPr")
        # ~0.8 cm row height from the approved thesis tables.
        tr_pr.append(element("w:trHeight", val="454"))
        tr_pr.append(element("w:jc", val="center"))
        if row_index < block.header_rows and block.header_repeat:
            tr_pr.append(element("w:tblHeader"))
        tr.append(tr_pr)
        is_header = row_index < block.header_rows
        role = "table_header" if is_header else "table_cell"
        style = plan.styles[role]["docx_style"]
        for col_index, cell in enumerate(row):
            tc = element("w:tc")
            tc_pr = element("w:tcPr")
            tc_pr.append(element("w:tcW", w=str(widths[col_index]), type="dxa"))
            tc_pr.append(element("w:vAlign", val="center"))
            tc.append(tc_pr)
            paragraph = element("w:p")
            ppr = element("w:pPr")
            ppr.append(element("w:pStyle", val=style))
            # First body column is left-aligned in the reference thesis.
            if not is_header and col_index == 0:
                ppr.append(element("w:jc", val="left"))
            paragraph.append(ppr)
            runs = ooxml_inlines(cell, plan, pandoc, omml_cache)
            if is_header:
                for run in runs:
                    if run.tag != q("w:r"):
                        continue
                    rpr = run.find(q("w:rPr"))
                    if rpr is None:
                        rpr = element("w:rPr")
                        run.insert(0, rpr)
                    if rpr.find(q("w:rStyle")) is None:
                        rpr.append(element("w:rStyle", val="Strong"))
            paragraph.extend(runs)
            tc.append(paragraph)
            tr.append(tc)
        tbl.append(tr)
    return tbl


def to_pandoc(plan, version, pandoc):
    blocks = []
    bookmark_ids = {key: index for index, key in enumerate(plan.references, 1)}
    omml_cache = {}
    for block in plan.blocks:
        content = []
        if block.kind == "heading":
            content.append(raw([element("w:bookmarkStart", id=bookmark_ids[block.id], name=bookmark_name(block.id))]))
            title_nodes = []
            for index, part in enumerate(block.title.split("\t")):
                if index:
                    run = element("w:r")
                    run.append(element("w:tab"))
                    title_nodes.append(raw([run]))
                if part:
                    title_nodes.append({"t": "Str", "c": part})
            if block.level >= 4:
                content.extend(strong_or_emph(title_nodes, strong=True, emph=block.level >= 5))
            else:
                content.extend(title_nodes)
            content.append(raw([element("w:bookmarkEnd", id=bookmark_ids[block.id])]))
        elif block.kind == "run_in_heading":
            content.append(raw([element("w:bookmarkStart", id=bookmark_ids[block.id], name=bookmark_name(block.id))]))
            title_nodes = []
            for index, part in enumerate(block.title.split("\t")):
                if index:
                    run = element("w:r")
                    run.append(element("w:tab"))
                    title_nodes.append(raw([run]))
                if part:
                    title_nodes.append({"t": "Str", "c": part})
            # Level 5 in the reference thesis often marks the run-in title in bold+italic.
            content.extend(strong_or_emph(title_nodes, strong=True, emph=block.level >= 5))
            content.append(raw([element("w:bookmarkEnd", id=bookmark_ids[block.id])]))
            body = ast_inlines(block.inlines, plan)
            if body:
                content.append({"t": "Space"})
                content.extend(body)
        elif block.kind in ("paragraph", "list_item", "table_title", "table_note", "figure_title", "figure_note"):
            content = ast_inlines(block.inlines, plan)
            if block.kind == "list_item":
                content = [{"t": "Str", "c": "▪"}, {"t": "Space"}] + content
        elif block.kind in ("table_label", "figure_label"):
            sequence = plan.sequences["table" if block.kind == "table_label" else "figure"]
            prefix, suffix = sequence["format"].split("{n}")
            content.append(raw([element("w:bookmarkStart", id=bookmark_ids[block.id], name=bookmark_name(block.id))]))
            if prefix:
                content.append({"t": "Str", "c": prefix})
            content.append(raw(field(sequence["field"] + " \\* ARABIC", str(block.number))))
            if suffix:
                content.append({"t": "Str", "c": suffix})
            content.append(raw([element("w:bookmarkEnd", id=bookmark_ids[block.id])]))
        elif block.kind == "figure_image":
            attrs = []
            if block.width and block.width != "natural":
                attrs.append(["width", block.width])
            content = [{"t": "Image", "c": [["", [], attrs], [{"t": "Str", "c": block.title or "figure"}], [block.asset, ""]]}]
        elif block.kind == "table":
            blocks.append({"t": "RawBlock", "c": ["openxml", E.tostring(build_table_xml(block, plan, pandoc, omml_cache), encoding="unicode")]})
            continue
        elif block.kind == "equation":
            content.append({"t": "Math", "c": [{"t": "DisplayMath"}, block.latex]})
            if block.number is not None:
                eq_sequence = plan.sequences["equation"]
                prefix, suffix = eq_sequence["format"].split("{n}")
                label = [text_run("  "), element("w:bookmarkStart", id=bookmark_ids[block.id], name=bookmark_name(block.id)), text_run(prefix)]
                label += field(eq_sequence["field"] + " \\* ARABIC", str(block.number))
                label += [text_run(suffix), element("w:bookmarkEnd", id=bookmark_ids[block.id])]
                content.append(raw(label))
        else:
            fail("unsupported-block", f"DOCX does not support planned block {block.kind}", block.source)
        blocks.append({"t": "Div", "c": [["", [], [["custom-style", plan.styles[block.role]["docx_style"]]]], [{"t": "Para", "c": content}]]})
    return {"pandoc-api-version": version, "meta": {}, "blocks": blocks}


def emit(plan, directory):
    pandoc = pandoc_executable()
    reference = directory / "reference.docx"
    compile_reference(plan, pandoc, reference)
    version = json.loads(run_tool([pandoc, "-f", "markdown", "-t", "json"], input=b"").stdout)["pandoc-api-version"]
    output = directory / "document.docx"
    run_tool([pandoc, "-f", "json", "-t", "docx", "--fail-if-warnings", "--reference-doc", str(reference), "-o", str(output)], input=json.dumps(to_pandoc(plan, version, pandoc)).encode())
    files = unpack(output)
    if plan.page.get("footer") and "word/footer1.xml" not in files:
        add_page_footer(files, plan)
    doc = E.fromstring(files["word/document.xml"])
    body = doc.find("w:body", NS)
    items = [child for child in body if child.tag in {q("w:p"), q("w:tbl")}]
    # Pandoc emits display math and following raw fields as separate paragraphs.
    # Join only the known equation/label pair from the plan, preserving OMML.
    cursor = 0
    for block in plan.blocks:
        if cursor >= len(items):
            fail("unexpected-docx", "Pandoc omitted an expected body element", block.source)
        item = items[cursor]
        if block.kind == "table":
            if item.tag != q("w:tbl"):
                fail("unexpected-docx", "Expected a Word table for a planned table block", block.source)
            cursor += 1
            continue
        if item.tag != q("w:p"):
            fail("unexpected-docx", "Expected a paragraph for a planned text block", block.source)
        paragraph = item
        cursor += 1
        if block.kind == "equation" and block.number is not None and not paragraph.findall(".//w:instrText", NS):
            if cursor >= len(items) or items[cursor].tag != q("w:p"):
                fail("unexpected-docx", "Expected an equation followed by its sequence field", block.source)
            label = items[cursor]
            instructions = "".join(label.xpath(".//w:instrText/text()", namespaces=NS))
            if not paragraph.findall(".//m:oMath", NS) or plan.sequences["equation"]["field"] not in instructions:
                fail("unexpected-docx", "Expected an equation followed by its sequence field", block.source)
            for child in list(label):
                if child.tag != q("w:pPr"):
                    paragraph.append(child)
            label.getparent().remove(label)
            items.pop(cursor)
    if cursor != len(items):
        fail("unexpected-docx", "Pandoc changed the expected body structure", Source(str(output), 1))
    para_blocks = [b for b in plan.blocks if b.kind != "table"]
    paragraphs = [c for c in body if c.tag == q("w:p")]
    if len(paragraphs) != len(para_blocks):
        fail("unexpected-docx", "Pandoc changed the expected paragraph structure", Source(str(output), 1))
    for index, (paragraph, block) in enumerate(zip(paragraphs, para_blocks)):
        ppr = paragraph.find("w:pPr", NS)
        if ppr is None:
            ppr = element("w:pPr")
            paragraph.insert(0, ppr)
        # All paragraph appearance belongs to its named style.
        for child in list(ppr):
            ppr.remove(child)
        ppr.append(element("w:pStyle", val=plan.styles[block.role]["docx_style"]))
        if index and plan.styles[block.role].get("page_break_before"):
            run = element("w:r")
            run.append(element("w:br", type="page"))
            paragraph.insert(1, run)
        if block.kind == "equation" and block.number is not None:
            for display in paragraph.findall("m:oMathPara", NS):
                position = paragraph.index(display)
                maths = display.findall("m:oMath", NS)
                paragraph.remove(display)
                for math in maths:
                    paragraph.insert(position, math)
                    position += 1
    files["word/document.xml"] = xml_bytes(doc)
    settings = E.fromstring(files["word/settings.xml"])
    update = settings.find("w:updateFields", NS)
    if update is None:
        update = element("w:updateFields")
        settings.append(update)
    update.set(q("w:val"), "true")
    if "default_tab_stop" in plan.page:
        stop = settings.find("w:defaultTabStop", NS)
        if stop is None:
            stop = element("w:defaultTabStop")
            settings.append(stop)
        stop.set(q("w:val"), str(round(length_points(plan.page["default_tab_stop"]) * 20)))
    files["word/settings.xml"] = xml_bytes(settings)
    # Pandoc uses build-time timestamps; keep package metadata stable.
    core = E.fromstring(files["docProps/core.xml"])
    for child in core:
        if E.QName(child).localname in {"created", "modified"}:
            child.text = "2000-01-01T00:00:00Z"
    files["docProps/core.xml"] = xml_bytes(core)
    pack(files, output)
    return output, run_tool([pandoc, "--version"]).stdout.decode().splitlines()[0]
