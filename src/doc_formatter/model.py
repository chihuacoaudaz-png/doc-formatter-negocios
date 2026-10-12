"""Immutable content nodes. No renderer, style or numbering policy lives here."""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True)
class Source:
    file: str
    line: int


@dataclass(frozen=True)
class Inline:
    type: str
    source: Source
    value: str = ""
    children: tuple[Inline, ...] = ()


@dataclass(frozen=True)
class Paragraph:
    inlines: tuple[Inline, ...]
    source: Source
    type: str = "paragraph"


@dataclass(frozen=True)
class Equation:
    latex: str
    numbered: bool
    source: Source
    id: str | None = None
    type: str = "equation"


@dataclass(frozen=True)
class ListItem:
    inlines: tuple[Inline, ...]
    source: Source
    type: str = "list_item"


@dataclass(frozen=True)
class BulletList:
    items: tuple[ListItem, ...]
    source: Source
    type: str = "bullet_list"


@dataclass(frozen=True)
class TableCell:
    inlines: tuple[Inline, ...]
    source: Source
    type: str = "table_cell"


@dataclass(frozen=True)
class Table:
    id: str
    title: str
    header: tuple[tuple[TableCell, ...], ...]
    rows: tuple[tuple[TableCell, ...], ...]
    source: Source
    note: str | None = None
    header_repeat: bool = False
    type: str = "table"


@dataclass(frozen=True)
class Figure:
    id: str
    title: str
    src: str
    source: Source
    note: str | None = None
    width: str = "100%"
    type: str = "figure"


@dataclass(frozen=True)
class Section:
    id: str
    level: int
    title: str
    children: tuple[Section | Paragraph | Equation | BulletList | Table | Figure, ...]
    source: Source
    kind: str = "subsection"
    slot: str | None = None
    type: str = "section"


@dataclass(frozen=True)
class Document:
    language: str
    meta: Mapping[str, Any]
    body: tuple[Section, ...]
    frontmatter: tuple[Section, ...] = ()
    schema_version: int = 1
    type: str = "document"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    source: Source
    severity: str = "error"


class InvalidSource(Exception):
    def __init__(self, *diagnostics: Diagnostic):
        self.diagnostics = diagnostics
        super().__init__("; ".join(d.message for d in diagnostics))


def fail(code: str, message: str, source: Source) -> None:
    raise InvalidSource(Diagnostic(code, message, source))


def to_data(value: Any) -> Any:
    if is_dataclass(value):
        return {f.name: to_data(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {k: to_data(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_data(v) for v in value]
    return value


def walk(nodes):
    for node in nodes:
        yield node
        if isinstance(node, Section):
            yield from walk(node.children)
        elif isinstance(node, BulletList):
            yield from walk(node.items)
        elif isinstance(node, Table):
            for row in (*node.header, *node.rows):
                yield from row


def walk_document(document):
    yield from walk(document.frontmatter)
    yield from walk(document.body)


def walk_inlines(nodes):
    for node in nodes:
        yield node
        yield from walk_inlines(node.children)
