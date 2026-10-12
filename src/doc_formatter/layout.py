"""Resolve a profile into a disposable presentation plan; never modify the IR."""
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import math
import re

from .compiler import ParseResult, validate_profile
from .loader import freeze, read_yaml
from .model import BulletList, Equation, Figure, Inline, ListItem, Paragraph, Section, Source, Table, fail, to_data


@dataclass(frozen=True)
class PlannedBlock:
    kind: str
    role: str
    source: Source
    id: str | None = None
    title: str = ""
    inlines: tuple[Inline, ...] = ()
    latex: str = ""
    number: int | None = None
    label: str = ""
    level: int = 0
    rows: tuple[tuple[tuple[Inline, ...], ...], ...] = ()
    header_rows: int = 0
    header_repeat: bool = False
    asset: str = ""
    width: str = ""


@dataclass(frozen=True)
class LayoutPlan:
    profile: str
    target: str
    language: str
    page: Mapping
    styles: Mapping
    blocks: tuple[PlannedBlock, ...]
    references: Mapping
    sequences: Mapping

    @property
    def equation_sequence(self):
        return self.sequences.get("equation", {})


def length_points(value):
    if type(value) in (int, float) and math.isfinite(value) and value >= 0:
        return float(value)
    if isinstance(value, str):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)(pt|cm)", value)
        if match:
            return float(match[1]) * (72 / 2.54 if match[2] == "cm" else 1)
    raise ValueError(f"Expected a nonnegative pt/cm length, got {value!r}")


PLACEHOLDER = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
SECTION_TARGET = re.compile(r"section\[kind=([a-z_]+)\]")


def roman(value):
    if type(value) is not int or not 1 <= value <= 3999:
        raise ValueError(f"Roman numerals require an integer 1-3999, got {value!r}")
    digits = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    parts, remaining = [], value
    for amount, symbol in digits:
        while remaining >= amount:
            parts.append(symbol)
            remaining -= amount
    return "".join(parts)


def expand_template(template, values, list_join=", "):
    def replace(match):
        key = match.group(1)
        if key not in values:
            raise KeyError(key)
        value = values[key]
        if isinstance(value, (list, tuple)):
            return list_join.join(str(item) for item in value)
        return str(value)
    return PLACEHOLDER.sub(replace, template)


def format_heading_number(template, counters, level):
    text = template
    for index in range(1, 7):
        text = text.replace(f"{{n{index}}}", str(counters[index - 1]) if index <= level else "")
    return re.sub(r"[.\-/\s]+$", "", text)


def plan_document(parsed: ParseResult, profile_path: Path) -> LayoutPlan:
    validate_profile(parsed.document, profile_path, parsed.profile)
    profile, _, _ = read_yaml(profile_path)
    loc = Source(str(profile_path), 1)
    def error(message):
        fail("unsupported-profile", message, loc)
    if profile.get("renderer") != "docx-pandoc":
        error("This build command implements only the docx-pandoc backend")
    if profile.keys() - {"id", "renderer", "schema", "styles", "layout", "conformance"}:
        error("Profile contains unsupported top-level settings")
    styles = profile.get("styles", {})
    if not isinstance(styles, dict) or styles.keys() - {"page", "roles"}:
        error("Expected styles.page and styles.roles")
    page = styles.get("page", {})
    if not isinstance(page, dict) or page.keys() - {"size", "margins", "footer", "default_tab_stop"} or page.get("size") != "A4":
        error("This sample backend supports A4 page size and margins")
    if "default_tab_stop" in page:
        try:
            if length_points(page["default_tab_stop"]) <= 0:
                error("default_tab_stop must be a positive length")
        except ValueError as exc:
            error(str(exc))
    margins = page.get("margins", {})
    if not isinstance(margins, dict) or set(margins) != {"top", "bottom", "left", "right"}:
        error("Specify all four page margins")
    try:
        margin_points = {k: length_points(v) for k, v in margins.items()}
    except ValueError as exc:
        error(str(exc))
    if margin_points["left"] + margin_points["right"] >= 210 * 72 / 25.4 or margin_points["top"] + margin_points["bottom"] >= 297 * 72 / 25.4:
        error("Margins leave no printable area")
    roles = styles.get("roles", {})
    if not isinstance(roles, dict):
        error("styles.roles must be a mapping")
    resolved = {}
    allowed = {"inherits", "font", "size", "line_spacing", "align", "first_line_indent", "left_indent", "hanging_indent", "tab_stop", "space_after", "bold", "italic", "docx_style", "page_break_before", "keep_next", "keep_with_next"}
    def resolve(name, active=()):
        if name in resolved:
            return resolved[name]
        if name in active or name not in roles:
            error(f"Missing or cyclic style role: {name}")
        own = roles[name]
        if not isinstance(own, dict) or own.keys() - allowed:
            error(f"Unknown style properties for role {name}")
        values = dict(resolve(own["inherits"], active + (name,))) if "inherits" in own else {}
        values.update({k: v for k, v in own.items() if k != "inherits"})
        if "keep_with_next" in values:
            values["keep_next"] = values.pop("keep_with_next")
        style_name = values.get("docx_style")
        if not isinstance(style_name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", style_name):
            error(f"Role {name} needs an ASCII docx_style identifier")
        if "font" in values and (not isinstance(values["font"], str) or not values["font"]):
            error(f"Invalid font for {name}")
        for key in ("bold", "italic", "page_break_before", "keep_next"):
            if key in values and type(values[key]) is not bool:
                error(f"{name}.{key} must be boolean")
        if "align" in values and values["align"] not in {"left", "right", "center", "justify"}:
            error(f"Invalid alignment for {name}")
        if "line_spacing" in values and (type(values["line_spacing"]) not in (int, float) or not math.isfinite(values["line_spacing"]) or values["line_spacing"] <= 0):
            error(f"Invalid line spacing for {name}")
        try:
            for key in ("size", "space_after", "first_line_indent", "left_indent", "hanging_indent", "tab_stop"):
                if key in values:
                    length_points(values[key])
        except ValueError as exc:
            error(str(exc))
        resolved[name] = values
        return values
    for name in roles:
        resolve(name)
    by_style = {}
    for name, values in resolved.items():
        style_id = values["docx_style"]
        if style_id in by_style and by_style[style_id] != values:
            error(f"Conflicting definitions for Word style {style_id}")
        by_style[style_id] = values
    footer = page.get("footer")
    if footer is not None:
        if not isinstance(footer, dict) or footer.keys() - {"role", "field"} or footer.get("field") != "PAGE" or footer.get("role") not in resolved:
            error("page.footer requires field PAGE and a declared style role")
    sequence = None
    sequences = None
    prefix_rule = None
    heading_rule = None
    bind_rules = []
    append_rules = []
    layout = profile.get("layout", [])
    if not isinstance(layout, list):
        error("layout must be a list")
    phases = {"structure", "numbering", "placement", "pagination"}
    for rule in layout:
        if not isinstance(rule, dict) or rule.get("phase") not in phases or not isinstance(rule.get("id"), str) or not rule["id"]:
            error("Each layout rule needs an id and a known phase")
        kind = rule.get("rule")
        if kind == "number_labels":
            if rule.keys() - {"id", "phase", "rule", "sequences"} or sequences is not None:
                error("Declare exactly one number_labels rule")
            raw_sequences = rule.get("sequences", {})
            if not isinstance(raw_sequences, dict) or not raw_sequences or raw_sequences.keys() - {"equation", "table", "figure"}:
                error("number_labels sequences may only include equation, table and/or figure")
            resolved_sequences = {}
            for name, sequence in raw_sequences.items():
                allowed = {"format", "scope", "field"} | ({"note_template", "note_label"} if name in {"table", "figure"} else set())
                if not isinstance(sequence, dict) or sequence.keys() - allowed or not {"format", "scope", "field"} <= sequence.keys():
                    error(f"{name} sequence requires format, scope and field")
                fmt = sequence["format"]
                if sequence["scope"] != "global" or not isinstance(fmt, str) or fmt.count("{n}") != 1 or "{" in fmt.replace("{n}", "") or "}" in fmt.replace("{n}", ""):
                    error(f"{name} numbering requires global scope and a single {{n}} placeholder")
                if not isinstance(sequence["field"], str) or not re.fullmatch(r"SEQ [A-Za-z][A-Za-z0-9_]*", sequence["field"]):
                    error(f"Invalid {name} field sequence name")
                if name in {"table", "figure"} and "note_template" in sequence:
                    if not isinstance(sequence["note_template"], str) or "{note}" not in sequence["note_template"]:
                        error(f"{name} note_template must include {{note}}")
                if name in {"table", "figure"} and "note_label" in sequence:
                    if not isinstance(sequence["note_label"], str) or not sequence["note_label"].strip():
                        error(f"{name} note_label must be a nonempty string")
                resolved_sequences[name] = sequence
            sequences = resolved_sequences
            sequence = resolved_sequences.get("equation")
        elif kind == "prefix_heading":
            if prefix_rule is not None or rule.keys() - {"id", "phase", "rule", "target", "template"}:
                error("prefix_heading requires a single target and template")
            match = SECTION_TARGET.fullmatch(rule.get("target", ""))
            if match is None or not isinstance(rule.get("template"), str) or "{title}" not in rule["template"]:
                error("prefix_heading target must be section[kind=…] and the template must include {title}")
            prefix_rule = {"kind": match[1], "template": rule["template"]}
        elif kind == "number_headings":
            if heading_rule is not None or rule.keys() - {"id", "phase", "rule", "levels", "format", "separator", "run_in_levels", "run_in_title_period"}:
                error("number_headings requires levels, format and separator")
            levels = rule.get("levels")
            fmt = rule.get("format")
            separator = rule.get("separator", " ")
            if separator == "tab":
                separator = "\t"
            run_in_levels = rule.get("run_in_levels", [])
            run_in_title_period = rule.get("run_in_title_period", False)
            if not isinstance(levels, list) or any(type(level) is not int or not 2 <= level <= 6 for level in levels):
                error("number_headings levels must be integers from 2 to 6")
            if not isinstance(fmt, str) or "{n1}" not in fmt or not isinstance(separator, str):
                error("number_headings format must include {n1}")
            if not isinstance(run_in_levels, list) or any(type(level) is not int or level not in levels for level in run_in_levels):
                error("run_in_levels must be a subset of number_headings levels")
            if type(run_in_title_period) is not bool:
                error("run_in_title_period must be boolean")
            heading_rule = {"levels": tuple(levels), "format": fmt, "separator": separator, "run_in_levels": tuple(run_in_levels), "run_in_title_period": run_in_title_period}
        elif kind == "bind_role":
            target = rule.get("target")
            if rule.keys() - {"id", "phase", "rule", "target", "role"} or not isinstance(target, dict) or target.keys() - {"region", "node"}:
                error("bind_role requires target.region, target.node and role")
            if target.get("region") not in {"frontmatter", "body", "backmatter"} or target.get("node") != "paragraph" or rule.get("role") not in resolved:
                error("bind_role can assign a declared role to paragraphs in one region")
            bind_rules.append(target | {"role": rule["role"]})
        elif kind == "append_paragraph":
            target = rule.get("target")
            if rule.keys() - {"id", "phase", "rule", "target", "template", "role", "list_join"} or not isinstance(target, dict) or set(target) != {"slot"}:
                error("append_paragraph requires target.slot, template and role")
            join = rule.get("list_join", ", ")
            if not isinstance(rule.get("template"), str) or rule.get("role") not in resolved or not isinstance(join, str):
                error("append_paragraph template and role must be valid")
            append_rules.append({"slot": target["slot"], "template": rule["template"], "role": rule["role"], "list_join": join})
        else:
            error(f"Unsupported layout rule: {kind}")
    # Implement only the conformance predicates advertised by the sample profile.
    for rule in profile.get("conformance", []):
        targets = rule.get("targets")
        if not isinstance(rule, dict) or not (
            rule.get("rule") == "sequences_gapless" and isinstance(targets, list) and targets and set(targets) <= {"equation", "table", "figure"}
            or rule.get("rule") == "no_node" and rule.get("node") == "Raw"
        ):
            error("Unsupported conformance rule in sample backend")

    def heading_role(section):
        if section.kind == "chapter":
            return "chapter_title" if "chapter_title" in resolved else f"heading_{section.level}"
        if section.kind == "top_level_section":
            if "top_level_section_title" in resolved:
                return "top_level_section_title"
            return "chapter_title" if "chapter_title" in resolved else f"heading_{section.level}"
        return f"heading_{section.level}"

    def paragraph_role(region):
        for rule in bind_rules:
            if rule["region"] == region:
                return rule["role"]
        return "body"

    blocks, refs, number, table_number, figure_number, chapter_n = [], {}, 0, 0, 0, 0
    counters = [0, 0, 0, 0, 0, 0]
    sequences = sequences or {}

    def add(block):
        resolve(block.role)
        blocks.append(block)

    def caption_note(sequence, note, source):
        label = sequence.get("note_label")
        if label:
            return (
                Inline("emph", source, children=(Inline("text", source, label),)),
                Inline("text", source, f": {note}"),
            )
        try:
            note_text = expand_template(sequence.get("note_template", "{note}"), {"note": note})
        except KeyError as exc:
            error(f"Unknown placeholder in note_template: {exc}")
        return (Inline("text", source, note_text),)

    def emit_equation(node):
        nonlocal number
        eq_sequence = sequences.get("equation")
        if node.numbered:
            if eq_sequence is None:
                error("Numbered equations require an equation numbering rule")
            number += 1
        label = eq_sequence["format"].replace("{n}", str(number)) if node.numbered else ""
        add(PlannedBlock("equation", "equation", node.source, node.id, latex=node.latex, number=number if node.numbered else None, label=label))
        if node.id:
            refs[node.id] = {"kind": "equation", "label": label, "number": number, "source": node.source}

    def emit_table(node):
        nonlocal table_number
        tbl_sequence = sequences.get("table")
        if tbl_sequence is None:
            error("Tables require a table numbering sequence")
        for role in ("table_label", "table_title", "table_header", "table_cell"):
            if role not in resolved:
                error(f"Tables require a {role} style role")
        if node.note and "table_note" not in resolved:
            error("Tables with notes require a table_note style role")
        table_number += 1
        label = tbl_sequence["format"].replace("{n}", str(table_number))
        add(PlannedBlock("table_label", "table_label", node.source, node.id, number=table_number, label=label))
        refs[node.id] = {"kind": "table", "label": label, "number": table_number, "source": node.source}
        add(PlannedBlock("table_title", "table_title", node.source, title=node.title, inlines=(Inline("text", node.source, node.title),)))
        grid = tuple(tuple(cell.inlines for cell in row) for row in (*node.header, *node.rows))
        add(PlannedBlock("table", "table_cell", node.source, rows=grid, header_rows=len(node.header), header_repeat=node.header_repeat))
        if node.note:
            add(PlannedBlock("table_note", "table_note", node.source, inlines=caption_note(tbl_sequence, node.note, node.source)))

    def emit_figure(node):
        nonlocal figure_number
        fig_sequence = sequences.get("figure")
        if fig_sequence is None:
            error("Figures require a figure numbering sequence")
        for role in ("figure_label", "figure_title", "figure_image"):
            if role not in resolved:
                error(f"Figures require a {role} style role")
        if node.note and "figure_note" not in resolved:
            error("Figures with notes require a figure_note style role")
        figure_number += 1
        label = fig_sequence["format"].replace("{n}", str(figure_number))
        add(PlannedBlock("figure_label", "figure_label", node.source, node.id, number=figure_number, label=label))
        refs[node.id] = {"kind": "figure", "label": label, "number": figure_number, "source": node.source}
        add(PlannedBlock("figure_title", "figure_title", node.source, title=node.title, inlines=(Inline("text", node.source, node.title),)))
        if parsed.source_root is None:
            error("Figures require a resolved DocSource root")
        root = Path(parsed.source_root)
        asset = (root / node.src).resolve()
        if not asset.is_file() or not asset.is_relative_to(root.resolve()):
            error(f"Figure asset is missing or outside DocSource: {node.src}")
        add(PlannedBlock("figure_image", "figure_image", node.source, title=node.title, asset=str(asset), width=node.width))
        if node.note:
            add(PlannedBlock("figure_note", "figure_note", node.source, inlines=caption_note(fig_sequence, node.note, node.source)))

    def emit_section(section, region):
        nonlocal chapter_n
        title = section.title
        run_in = False
        if section.kind == "chapter":
            chapter_n += 1
            counters[0] = chapter_n
            for index in range(1, 6):
                counters[index] = 0
            if prefix_rule and prefix_rule["kind"] == "chapter":
                try:
                    title = expand_template(prefix_rule["template"], {"title": section.title, "n": chapter_n, "roman": roman(chapter_n)})
                except (KeyError, ValueError) as exc:
                    error(f"Invalid chapter prefix template: {exc}")
        elif heading_rule and section.level in heading_rule["levels"]:
            counters[section.level - 1] += 1
            for index in range(section.level, 6):
                counters[index] = 0
            display = section.title
            run_in = section.level in heading_rule["run_in_levels"]
            if run_in and heading_rule["run_in_title_period"] and display and display[-1] not in ".!?…":
                display = display + "."
            title = format_heading_number(heading_rule["format"], counters, section.level) + heading_rule["separator"] + display
        role = heading_role(section)
        children = list(section.children)
        if run_in and children and isinstance(children[0], Paragraph):
            first = children.pop(0)
            add(PlannedBlock("run_in_heading", role, section.source, section.id, title=title, inlines=first.inlines, level=section.level))
        else:
            add(PlannedBlock("heading", role, section.source, section.id, title=title, level=section.level))
        refs[section.id] = {"kind": "section", "label": title, "source": section.source}
        for child in children:
            if isinstance(child, Section):
                emit_section(child, region)
            elif isinstance(child, Paragraph):
                add(PlannedBlock("paragraph", paragraph_role(region), child.source, inlines=child.inlines))
            elif isinstance(child, Equation):
                emit_equation(child)
            elif isinstance(child, Table):
                emit_table(child)
            elif isinstance(child, Figure):
                emit_figure(child)
            elif isinstance(child, BulletList):
                if "list_item" not in resolved:
                    error("Bullet lists require a list_item style role")
                for item in child.items:
                    add(PlannedBlock("list_item", "list_item", item.source, inlines=item.inlines))
            else:
                error(f"Unsupported content node: {child.type}")
        for rule in append_rules:
            if rule["slot"] != section.slot:
                continue
            try:
                text = expand_template(rule["template"], dict(parsed.document.meta), rule["list_join"])
            except KeyError as exc:
                error(f"Unknown placeholder in append_paragraph: {exc}")
            generated = Source(str(profile_path), 1)
            add(PlannedBlock("paragraph", rule["role"], generated, inlines=(Inline("text", generated, text),)))

    for section in parsed.document.frontmatter:
        emit_section(section, "frontmatter")
    for section in parsed.document.body:
        emit_section(section, "body")
    return LayoutPlan(parsed.profile, "docx", parsed.document.language, freeze(page), freeze(resolved), tuple(blocks), freeze(to_data(refs)), freeze(sequences))
