"""Phase 1a orchestration: load, parse, structural validation, reference index."""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from .loader import GENERATED_SLOTS, load_source, read_yaml
from .model import Diagnostic, Document, Equation, Figure, InvalidSource, ListItem, Paragraph, Section, Source, Table, TableCell, fail, walk_document, walk_inlines
from .parser import parse_section_file


@dataclass(frozen=True)
class ParseResult:
    document: Document
    profile: str
    references: object
    diagnostics: tuple[Diagnostic, ...]
    source_root: str | None = None


def validate_references(document):
    refs, diagnostics = {}, []
    nodes = list(walk_document(document))
    for node in nodes:
        if isinstance(node, (Section, Equation, Table, Figure)) and node.id:
            if node.id in refs:
                first = refs[node.id]["source"]
                diagnostics.append(Diagnostic("duplicate-id", f"Duplicate ID {node.id}; first declared at {first.file}:{first.line}", node.source))
            else:
                if isinstance(node, Section):
                    kind = "section"
                elif isinstance(node, Equation):
                    kind = "equation"
                elif isinstance(node, Table):
                    kind = "table"
                else:
                    kind = "figure"
                refs[node.id] = {"kind": kind, "source": node.source}
    for node in nodes:
        if isinstance(node, (Paragraph, ListItem, TableCell)):
            for inline in walk_inlines(node.inlines):
                if inline.type == "cross_ref":
                    target = refs.get(inline.value)
                    if target is None:
                        diagnostics.append(Diagnostic("unresolved-reference", f"Unknown reference: {inline.value}", inline.source))
    if diagnostics:
        raise InvalidSource(*diagnostics)
    return MappingProxyType({key: MappingProxyType(value) for key, value in refs.items()})


def validate_profile(document, profile_path, requested):
    profile, lines, _ = read_yaml(profile_path)
    loc = Source(str(profile_path), lines.get("schema", 1))
    if profile.get("id") != requested:
        fail("profile-mismatch", f"Profile id must match manifest: {requested}", Source(str(profile_path), lines.get("id", 1)))
    if "extends" in profile:
        fail("unsupported-profile", "Profile inheritance is not implemented yet", loc)
    schema = profile.get("schema")
    if not isinstance(schema, dict):
        fail("invalid-profile", "Profile must declare a schema mapping", loc)
    allowed = {"frontmatter", "body", "backmatter", "max_heading_depth"}
    if schema.keys() - allowed:
        fail("invalid-profile", "Unknown schema keys: " + ", ".join(sorted(schema.keys() - allowed)), loc)
    for region in ("frontmatter", "backmatter"):
        region_schema = schema.get(region, {})
        if not isinstance(region_schema, dict) or region_schema.keys() - {"required", "optional"}:
            fail("invalid-profile", f"Invalid {region} schema", loc)
        if any(not isinstance(region_schema.get(k, []), list) for k in ("required", "optional")):
            fail("invalid-profile", f"{region} required and optional must be lists", loc)
        required_slots = region_schema.get("required", [])
        if any(not isinstance(item, str) or not item for item in required_slots + region_schema.get("optional", [])):
            fail("invalid-profile", f"{region} required and optional must contain slot names", loc)
        if region == "backmatter" and required_slots:
            fail("unsupported-profile", "This milestone cannot satisfy required backmatter", loc)
        if region == "frontmatter" and any(slot in GENERATED_SLOTS for slot in required_slots):
            fail("unsupported-profile", "Generated frontmatter slots are not implemented yet", loc)
    body = schema.get("body")
    if not isinstance(body, dict) or body.keys() - {"ordered", "required_chapters"}:
        fail("invalid-profile", "Invalid body schema", loc)
    required = body.get("required_chapters", [])
    if not isinstance(required, list) or any(not isinstance(c, dict) or c.keys() - {"id", "title"} or not isinstance(c.get("title"), str) for c in required):
        fail("invalid-profile", "required_chapters must contain chapter titles", loc)
    if type(body.get("ordered", False)) is not bool:
        fail("invalid-profile", "ordered must be a boolean", loc)
    depth = schema.get("max_heading_depth", 6)
    if type(depth) is not int or not 1 <= depth <= 6:
        fail("invalid-profile", "max_heading_depth must be an integer from 1 to 6", loc)
    titles = [c.title for c in document.body]
    expected = [c["title"] for c in required]
    diagnostics = []
    if any(title not in titles for title in expected):
        diagnostics.append(Diagnostic("missing-chapter", "Missing required chapters: " + ", ".join(t for t in expected if t not in titles), loc))
    elif body.get("ordered") and [titles.index(t) for t in expected] != sorted(titles.index(t) for t in expected):
        diagnostics.append(Diagnostic("chapter-order", "Required chapters are out of order", loc))
    authored = [section.slot for section in document.frontmatter]
    for slot in schema.get("frontmatter", {}).get("required", []):
        if slot not in authored:
            diagnostics.append(Diagnostic("missing-slot", f"Missing required frontmatter slot: {slot}", loc))
    for node in walk_document(document):
        if isinstance(node, Section) and node.level > depth:
            diagnostics.append(Diagnostic("heading-depth", f"Profile allows at most {depth} heading levels", node.source))
    if diagnostics:
        raise InvalidSource(*diagnostics)


def parse_document(path: Path, profile_path: Path | None = None) -> ParseResult:
    loaded = load_source(Path(path))
    root = loaded.manifest.parent
    frontmatter = []
    for slot, section in loaded.frontmatter:
        frontmatter.extend(parse_section_file(section, root, kind="top_level_section", slot=slot))
    body = []
    for section in loaded.files:
        body.extend(parse_section_file(section, root, kind="chapter"))
    document = Document(loaded.language, loaded.meta, tuple(body), tuple(frontmatter))
    refs = validate_references(document)
    diagnostics = ()
    if profile_path is not None:
        validate_profile(document, Path(profile_path), loaded.profile)
    else:
        diagnostics = (Diagnostic("profile-not-checked", "Only source structure checked; pass --profile for profile schema validation", Source(str(loaded.manifest), 1), "warning"),)
    return ParseResult(document, loaded.profile, refs, diagnostics, str(root))
