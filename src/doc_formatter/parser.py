"""Lower Markdown tokens into our own content model, never a renderer AST."""
from pathlib import Path
import re
import unicodedata

from markdown_it import MarkdownIt

from .model import BulletList, Equation, Figure, Inline, ListItem, Paragraph, Section, Source, Table, TableCell, fail

ID = r"[A-Za-z0-9][A-Za-z0-9_-]*"
REF = re.compile(rf"@(eq|sec|tbl|fig):({ID})(?![\w:-])")
EQUATION = re.compile(rf":::equation\s+\{{#(eq:{ID})\}}\s*")
TABLE = re.compile(rf":::table\s+\{{#(tbl:{ID})\}}\s*")
FIGURE = re.compile(rf":::figure\s+\{{#(fig:{ID})\}}\s*")
FIGURE_WIDTH = re.compile(r"(?:100|[1-9][0-9]?)%|natural")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def find_fenced_close(state, start, end, closing, loc, code):
    stop = start + 1
    while stop < end:
        candidate = state.src[state.bMarks[stop]:state.eMarks[stop]].strip()
        if candidate == closing:
            return stop
        if candidate.startswith(":::"):
            fail(code, f"Expected closing {closing} before another block", loc)
        stop += 1
    fail(code, f"Missing closing {closing}", loc)


def parse_pipe_table(body, file, line, md):
    loc = Source(file, line)
    if not body.strip():
        fail("empty-table", "Table body must contain a pipe table", loc)
    tokens = MarkdownIt("commonmark").enable("table").parse(body)
    if not tokens or tokens[0].type != "table_open":
        fail("invalid-table", "Expected a Markdown pipe table after ---", loc)
    header, rows, current, in_header = [], [], None, False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        cell_loc = Source(file, (token.map[0] + line) if token.map else line)
        if token.type == "thead_open":
            in_header = True
            index += 1
            continue
        if token.type == "thead_close":
            in_header = False
            index += 1
            continue
        if token.type in ("tbody_open", "tbody_close", "table_open", "table_close"):
            index += 1
            continue
        if token.type == "tr_open":
            current = []
            index += 1
            continue
        if token.type == "tr_close":
            if current is None:
                fail("invalid-table", "Empty table row", cell_loc)
            (header if in_header else rows).append(tuple(current))
            current = None
            index += 1
            continue
        if token.type in ("th_open", "td_open"):
            inline = tokens[index + 1]
            if inline.type != "inline":
                fail("invalid-table", "Table cell must contain inline content", cell_loc)
            current.append(TableCell(inlines(md, inline.content, cell_loc), cell_loc))
            index += 3
            continue
        fail("invalid-table", f"Unexpected token in pipe table: {token.type}", cell_loc)
    if not header or not rows:
        fail("invalid-table", "Pipe table needs a header row and at least one body row", loc)
    width = len(header[0])
    if any(len(row) != width for row in (*header, *rows)):
        fail("invalid-table", "Table rows must have the same number of columns", loc)
    return tuple(header), tuple(rows)


def parse_table_meta(content, loc):
    if "\n---\n" not in content:
        fail("invalid-table", "Table requires metadata, a --- separator, and a pipe table", loc)
    meta_text, body = content.split("\n---\n", 1)
    meta = {}
    for raw in meta_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if ":" not in line:
            fail("invalid-table", "Table metadata lines must be key: value", loc)
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not key or key in meta:
            fail("invalid-table", f"Invalid or duplicate table metadata key: {key or '(empty)'}", loc)
        meta[key] = value
    if meta.keys() - {"title", "note", "header_repeat"}:
        fail("invalid-table", "Unknown table metadata: " + ", ".join(sorted(meta.keys() - {"title", "note", "header_repeat"})), loc)
    title = meta.get("title", "").strip()
    if not title:
        fail("invalid-table", "Table requires a title", loc)
    header_repeat = False
    if "header_repeat" in meta:
        if meta["header_repeat"] not in {"true", "false"}:
            fail("invalid-table", "header_repeat must be true or false", loc)
        header_repeat = meta["header_repeat"] == "true"
    note = meta["note"].strip() if meta.get("note", "").strip() else None
    return title, note, header_repeat, body


def parse_figure_meta(content, loc, source_root: Path):
    meta = {}
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if ":" not in line:
            fail("invalid-figure", "Figure metadata lines must be key: value", loc)
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not key or key in meta:
            fail("invalid-figure", f"Invalid or duplicate figure metadata key: {key or '(empty)'}", loc)
        meta[key] = value
    if meta.keys() - {"src", "title", "note", "width"}:
        fail("invalid-figure", "Unknown figure metadata: " + ", ".join(sorted(meta.keys() - {"src", "title", "note", "width"})), loc)
    src = meta.get("src", "").strip()
    title = meta.get("title", "").strip()
    if not src or not title:
        fail("invalid-figure", "Figure requires src and title", loc)
    width = meta.get("width", "100%").strip() or "100%"
    if not FIGURE_WIDTH.fullmatch(width):
        fail("invalid-figure", "Figure width must be natural or a percentage from 1% to 100%", loc)
    note = meta["note"].strip() if meta.get("note", "").strip() else None
    path = Path(src)
    if path.is_absolute() or ".." in path.parts:
        fail("invalid-path", "Figure src must be a relative path inside DocSource", loc)
    asset = (source_root / path).resolve()
    if not asset.is_relative_to(source_root.resolve()):
        fail("invalid-path", "Figure src must stay inside DocSource", loc)
    if not asset.is_file():
        fail("missing-asset", f"Figure asset does not exist: {src}", loc)
    if asset.suffix.lower() not in IMAGE_SUFFIXES:
        fail("invalid-asset", f"Unsupported figure image type: {asset.suffix}", loc)
    return src, title, note, width


def block_rule(state, start, end, silent):
    line = state.src[state.bMarks[start] + state.tShift[start]:state.eMarks[start]].strip()
    if not (line.startswith(":::") or line.startswith("$$")):
        return False
    if silent:
        return True
    loc = Source(state.env["file"], start + 1)
    if line.startswith(":::figure"):
        match = FIGURE.fullmatch(line)
        if not match:
            fail("invalid-figure", "Expected :::figure {#fig:identifier}", loc)
        stop = find_fenced_close(state, start, end, ":::", loc, "unclosed-figure")
        content = state.src[state.bMarks[start + 1]:state.bMarks[stop]].strip()
        src, title, note, width = parse_figure_meta(content, loc, Path(state.env["source_root"]))
        token = state.push("doc_figure", "", 0)
        token.map = [start, stop + 1]
        token.meta = {"id": match[1], "src": src, "title": title, "note": note, "width": width}
        state.line = stop + 1
        return True
    if line.startswith(":::table"):
        match = TABLE.fullmatch(line)
        if not match:
            fail("invalid-table", "Expected :::table {#tbl:identifier}", loc)
        stop = find_fenced_close(state, start, end, ":::", loc, "unclosed-table")
        content = state.src[state.bMarks[start + 1]:state.bMarks[stop]].strip()
        title, note, header_repeat, body = parse_table_meta(content, loc)
        md = make_parser()
        header, rows = parse_pipe_table(body, state.env["file"], start + 2 + content[:content.index("---")].count("\n"), md)
        token = state.push("doc_table", "", 0)
        token.map = [start, stop + 1]
        token.meta = {"id": match[1], "title": title, "note": note, "header_repeat": header_repeat, "header": header, "rows": rows}
        state.line = stop + 1
        return True
    numbered = line.startswith(":::")
    equation_id = None
    if numbered:
        match = EQUATION.fullmatch(line)
        if not match:
            code = "invalid-equation" if line.startswith(":::equation") else "unknown-block"
            fail(code, "Expected :::equation {#eq:identifier}, :::table {#tbl:identifier}, or :::figure {#fig:identifier}; other fenced blocks are not supported yet", loc)
        equation_id = match[1]
        closing = ":::"
    else:
        closing = "$$"
    if not numbered and len(line) > 4 and line.endswith("$$"):
        content = line[2:-2].strip()
        next_line = start + 1
    else:
        if not numbered and line != "$$":
            fail("invalid-equation", "Display math must use $$…$$ or standalone $$ delimiters", loc)
        stop = find_fenced_close(state, start, end, closing, loc, "unclosed-equation")
        content = state.src[state.bMarks[start + 1]:state.bMarks[stop]].strip()
        next_line = stop + 1
    if not content:
        fail("empty-equation", "Equation must contain LaTeX", loc)
    token = state.push("doc_equation", "", 0)
    token.content = content
    token.map = [start, next_line]
    token.meta = {"id": equation_id, "numbered": numbered}
    state.line = next_line
    return True


def inline_rule(state, silent):
    pos = state.pos
    char = state.src[pos]
    loc = Source(state.env["file"], state.env["line"] + state.src[:pos].count("\n"))
    if char == "$":
        end = pos + 1
        while end < state.posMax:
            if state.src[end] == "\n":
                break
            if state.src[end] == "\\":
                end += 2
                continue
            if state.src[end] == "$":
                break
            end += 1
        if end >= state.posMax or state.src[end] != "$":
            if silent:
                return False
            fail("unclosed-math", "Missing closing $ (escape literal currency as \\$)", loc)
        value = state.src[pos + 1:end]
        if not value.strip():
            if silent:
                return False
            fail("empty-equation", "Inline math cannot be empty; display math must be a separate block", loc)
        kind = "math"
        new_pos = end + 1
    elif char == "@" and (pos == 0 or not (state.src[pos-1].isalnum() or state.src[pos-1] in "_.+-")):
        match = REF.match(state.src, pos)
        if not match:
            if re.match(r"@[\w]", state.src[pos:]):
                if silent:
                    return False
                fail("unsupported-citation", "Citations are not implemented in this milestone; escape a literal @", loc)
            return False
        value = match[0][1:]
        kind = "cross_ref"
        new_pos = match.end()
    else:
        return False
    if not silent:
        token = state.push("doc_" + kind, "", 0)
        token.content = value
        token.meta["source"] = loc
    state.pos = new_pos
    return True


def make_parser():
    md = MarkdownIt("commonmark").enable("table")
    md.block.ruler.before("fence", "doc_equation", block_rule, {"alt": ["paragraph", "reference", "blockquote", "list"]})
    md.inline.ruler.before("text", "doc_inline", inline_rule)
    md.core.ruler.disable("inline")  # Parse each inline block with its own source line.
    return md


def inlines(md, content, loc, references=None):
    tokens = []
    md.inline.parse(content, md, {"file": loc.file, "line": loc.line, "references": references or {}}, tokens)
    root = []
    stack = [(None, root, "")]
    line = loc.line
    for token in tokens:
        source = token.meta.get("source", Source(loc.file, line))
        if token.type in ("em_open", "strong_open", "link_open"):
            stack.append(({"em_open": "emph", "strong_open": "strong", "link_open": "link"}[token.type], [], token.attrGet("href") or ""))
        elif token.type in ("em_close", "strong_close", "link_close"):
            kind, children, value = stack.pop()
            stack[-1][1].append(Inline(kind, source, value, tuple(children)))
        elif token.type in ("text", "text_special"):
            stack[-1][1].append(Inline("text", source, token.content))
            line += token.content.count("\n")
        elif token.type in ("softbreak", "hardbreak"):
            stack[-1][1].append(Inline("text" if token.type == "softbreak" else "line_break", source, " " if token.type == "softbreak" else ""))
            line += 1
        elif token.type in ("doc_math", "doc_cross_ref"):
            stack[-1][1].append(Inline(token.type.removeprefix("doc_"), source, token.content))
        else:
            fail("unsupported-inline", f"Inline construct not implemented: {token.type}", source)
    return tuple(root)


def slug(title):
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", title).strip("-") or "section"


def parse_section_file(path: Path, source_root: Path, *, kind="chapter", slot=None):
    file = path.relative_to(source_root.resolve()).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail("read-error", str(exc), Source(file, 1))
    md = make_parser()
    env = {"file": file, "source_root": str(source_root.resolve())}
    tokens = md.parse(text, env)
    references = env.get("references", {})
    # Link reference definitions are consumed into env by CommonMark, not body nodes.
    roots, stack = [], []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        loc = Source(file, token.map[0] + 1 if token.map else 1)
        if token.type == "heading_open":
            level = int(token.tag[1:])
            if not stack and level != 1:
                fail("heading-level", "A section file must start with a level-1 heading", loc)
            if stack and level > stack[-1]["level"] + 1:
                fail("heading-level", "Heading levels cannot skip", loc)
            if level == 1 and roots:
                fail("chapter-count", "Each body file must contain exactly one chapter", loc)
            title = tokens[index + 1].content
            match = re.search(rf"\s+\{{#(sec:{ID})\}}$", title)
            explicit_id = match[1] if match else None
            if match:
                title = title[:match.start()]
            if not title.strip():
                fail("empty-heading", "Heading title must not be empty", loc)
            if re.match(r"(?:\d+(?:\.\d+)*[.\s]|Capítulo\s+[IVXLCDM]+\.)", title, re.I):
                fail("manual-numbering", "Remove manually assigned heading numbering", loc)
            title_inlines = inlines(md, title, loc, references)
            if any(t.type != "text" for t in title_inlines):
                fail("unsupported-heading", "This milestone supports plain-text heading titles", loc)
            title = "".join(t.value for t in title_inlines)
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            parent_id = stack[-1]["id"].removeprefix("sec:") + "-" if stack else ""
            node = {"id": explicit_id or "sec:" + parent_id + slug(title), "level": level, "title": title, "children": [], "source": loc, "kind": kind if level == 1 else "subsection", "slot": slot if level == 1 else None}
            (stack[-1]["children"] if stack else roots).append(node)
            stack.append(node)
            index += 3
            continue
        if not stack:
            fail("missing-heading", "Content must follow a chapter heading", loc)
        if token.type == "paragraph_open":
            inner = tokens[index + 1]
            stack[-1]["children"].append(Paragraph(inlines(md, inner.content, loc, references), loc))
            index += 3
        elif token.type == "doc_equation":
            stack[-1]["children"].append(Equation(token.content, token.meta["numbered"], loc, token.meta["id"]))
            index += 1
        elif token.type == "doc_table":
            stack[-1]["children"].append(Table(token.meta["id"], token.meta["title"], token.meta["header"], token.meta["rows"], loc, token.meta["note"], token.meta["header_repeat"]))
            index += 1
        elif token.type == "doc_figure":
            stack[-1]["children"].append(Figure(token.meta["id"], token.meta["title"], token.meta["src"], loc, token.meta["note"], token.meta["width"]))
            index += 1
        elif token.type == "bullet_list_open":
            items = []
            index += 1
            while index < len(tokens) and tokens[index].type != "bullet_list_close":
                item = tokens[index]
                if item.type != "list_item_open":
                    fail("unsupported-block", f"Unexpected token inside bullet list: {item.type}", Source(file, item.map[0] + 1 if item.map else loc.line))
                item_loc = Source(file, item.map[0] + 1 if item.map else loc.line)
                index += 1
                item_inlines = None
                while index < len(tokens) and tokens[index].type != "list_item_close":
                    child = tokens[index]
                    child_loc = Source(file, child.map[0] + 1 if child.map else item_loc.line)
                    if child.type == "paragraph_open":
                        if item_inlines is not None:
                            fail("unsupported-block", "A list item may contain only one paragraph in this milestone", child_loc)
                        item_inlines = inlines(md, tokens[index + 1].content, child_loc, references)
                        index += 3
                    elif child.type in ("bullet_list_open", "ordered_list_open"):
                        fail("unsupported-block", "Nested lists are not implemented yet", child_loc)
                    else:
                        fail("unsupported-block", f"Unsupported content in list item: {child.type}", child_loc)
                if item_inlines is None:
                    fail("unsupported-block", "List item must contain a paragraph", item_loc)
                items.append(ListItem(item_inlines, item_loc))
                if index >= len(tokens) or tokens[index].type != "list_item_close":
                    fail("unsupported-block", "Unclosed list item", item_loc)
                index += 1
            if not items:
                fail("unsupported-block", "Bullet list must contain at least one item", loc)
            if index >= len(tokens) or tokens[index].type != "bullet_list_close":
                fail("unsupported-block", "Unclosed bullet list", loc)
            stack[-1]["children"].append(BulletList(tuple(items), loc))
            index += 1
        elif token.type == "ordered_list_open":
            fail("unsupported-block", "Ordered lists are not implemented yet; use a bullet list", loc)
        elif token.type == "table_open":
            fail("unsupported-block", "Bare pipe tables are not supported; wrap them in :::table {#tbl:…}", loc)
        else:
            fail("unsupported-block", f"Block construct not implemented: {token.type}", loc)
    if not roots:
        fail("missing-heading", "Section file contains no chapter", Source(file, 1))
    def finish(node):
        return Section(node["id"], node["level"], node["title"], tuple(finish(c) if isinstance(c, dict) else c for c in node["children"]), node["source"], node.get("kind", "subsection"), node.get("slot"))
    return tuple(finish(n) for n in roots)
