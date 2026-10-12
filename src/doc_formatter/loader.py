"""Strict loading for the Phase 1a body-only DocSource subset."""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
import math
import yaml

from .model import Source, fail

AUTHORING_SLOTS = {"abstract_es", "abstract_en", "dedication", "acknowledgements", "introduction"}
GENERATED_SLOTS = {"cover", "toc", "list_of_tables", "list_of_figures", "list_of_annexes"}


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.constructor.ConstructorError(None, None, "Keys must be strings", key_node.start_mark)
            if key in result:
                raise yaml.constructor.ConstructorError(None, None, f"Duplicate key: {key}", key_node.start_mark)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def read_yaml(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
        value = yaml.load(text, Loader=UniqueLoader)
        tree = yaml.compose(text, Loader=UniqueLoader)
    except (OSError, UnicodeError) as exc:
        fail("read-error", str(exc), Source(str(path), 1))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        fail("invalid-yaml", str(exc), Source(str(path), mark.line + 1 if mark else 1))
    if not isinstance(value, dict):
        fail("invalid-manifest", "Expected a YAML mapping", Source(str(path), 1))
    lines = {k.value: k.start_mark.line + 1 for k, _ in tree.value}
    return value, lines, tree


@dataclass(frozen=True)
class LoadedSource:
    profile: str
    language: str
    meta: object
    files: tuple[Path, ...]
    manifest: Path
    frontmatter: tuple[tuple[str, Path], ...] = ()


def freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Metadata numbers must be finite")
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError("Metadata must contain JSON-compatible values (quote dates)")


def load_source(path: Path) -> LoadedSource:
    path = path / "document.yaml" if path.is_dir() else path
    data, lines, tree = read_yaml(path)
    def error(code, message, key):
        fail(code, message, Source(str(path), lines.get(key, 1)))
    allowed = {"schema_version", "profile", "language", "meta", "body", "frontmatter", "backmatter", "bibliography", "citation_style"}
    for key in data.keys() - allowed:
        error("unknown-key", f"Unknown manifest key: {key}", key)
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        error("schema-version", "schema_version must be 1", "schema_version")
    for key in ("profile", "language"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            error("invalid-manifest", f"{key} must be a nonempty string", key)
    if data.get("backmatter", []) != []:
        error("unsupported-feature", "backmatter is not implemented in this milestone", "backmatter")
    for key in ("bibliography", "citation_style"):
        if key in data:
            error("unsupported-feature", "Bibliography and citation processing are not implemented yet", key)
    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        error("invalid-manifest", "meta must be a mapping", "meta")
    try:
        meta = freeze(meta)
    except (ValueError, RecursionError) as exc:
        error("invalid-manifest", str(exc), "meta")
    body = data.get("body")
    if not isinstance(body, list) or not body:
        error("invalid-manifest", "body must be a nonempty list of Markdown paths", "body")
    body_node = next(v for k, v in tree.value if k.value == "body")
    files = []
    for item, node in zip(body, body_node.value):
        loc = Source(str(path), node.start_mark.line + 1)
        if not isinstance(item, str) or not item:
            fail("invalid-manifest", "Each body item must be a file path", loc)
        target = (path.parent / item).resolve()
        if not target.is_relative_to(path.parent.resolve()):
            fail("invalid-path", "Section paths must stay inside DocSource", loc)
        if target.suffix.lower() != ".md" or not target.is_file():
            fail("missing-section", f"Markdown section does not exist: {item}", loc)
        if target in files:
            fail("duplicate-section", f"Section listed twice: {item}", loc)
        files.append(target)
    frontmatter = resolve_frontmatter(data.get("frontmatter", []), path, lines, tree, files)
    return LoadedSource(data["profile"], data["language"], meta, tuple(files), path, frontmatter)


def resolve_section_path(item, loc, manifest):
    if not isinstance(item, str) or not item:
        fail("invalid-manifest", "Each section item must be a file path", loc)
    target = (manifest.parent / item).resolve()
    if not target.is_relative_to(manifest.parent.resolve()):
        fail("invalid-path", "Section paths must stay inside DocSource", loc)
    if target.suffix.lower() != ".md" or not target.is_file():
        fail("missing-section", f"Markdown section does not exist: {item}", loc)
    return target


def resolve_frontmatter(items, manifest, lines, tree, body_files):
    if items == []:
        return ()
    if not isinstance(items, list):
        fail("invalid-manifest", "frontmatter must be a list of slot mappings", Source(str(manifest), lines.get("frontmatter", 1)))
    node = next(value for key, value in tree.value if key.value == "frontmatter")
    resolved, seen = [], set()
    used = set(body_files)
    for item, child in zip(items, node.value):
        loc = Source(str(manifest), child.start_mark.line + 1)
        if isinstance(item, str):
            fail("unsupported-feature", f"Generated frontmatter slot is not implemented: {item}", loc)
        if not isinstance(item, dict) or len(item) != 1:
            fail("invalid-manifest", "Each frontmatter item must be a single slot: path mapping", loc)
        slot, rel = next(iter(item.items()))
        if slot in GENERATED_SLOTS:
            fail("unsupported-feature", f"Generated frontmatter slot is not implemented: {slot}", loc)
        if slot not in AUTHORING_SLOTS:
            fail("unknown-key", f"Unknown frontmatter slot: {slot}", loc)
        if slot in seen:
            fail("duplicate-section", f"Frontmatter slot listed twice: {slot}", loc)
        target = resolve_section_path(rel, loc, manifest)
        if target in used:
            fail("duplicate-section", f"Section listed twice: {rel}", loc)
        seen.add(slot)
        used.add(target)
        resolved.append((slot, target))
    return tuple(resolved)
