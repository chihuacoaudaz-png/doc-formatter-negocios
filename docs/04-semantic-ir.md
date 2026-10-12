# 04 — Semantic IR

`SemanticIR` is the compiler's internal model of the document. It records **what
each element is**, never how it looks.

It is never authored by hand. It is produced by parsing `DocSource` and is the
input to every formatting stage. It is also the unit we persist and diff when we
want to compare two versions of a document's content.

## The one invariant

> **No formatting stage mutates the `SemanticIR`.**

Profiles, styles and layout rules read it and drive the lowering into a
`LayoutPlan`. They never write back into it.

The reason is concrete. The rule "each chapter starts on a new page" is
irresistible to implement as *insert a page-break node*. Do that and the IR
contains a page break — an idea with no meaning in HTML — and it is no longer a
format-independent model. Every backend beyond the first becomes a rewrite. The
discipline costs nothing now and preserves the LaTeX and HTML paths for free.

Practically, this means the IR contains **no**: font, size, colour, margin,
alignment, line spacing, indent, page break, section break, Word style name, or
any backend identifier.

## The exception boundary

"No visual information" is easy to state and easy to violate by accident, so the
boundary needs a test rather than a slogan. Three fields in the vocabulary below
look like violations, and the resolution is different in each case.

**The test: would a reader of a different medium understand the field as a
statement about the content?** A field survives if it means the same thing in
DOCX, LaTeX and HTML. It does not survive if it names a mechanism that only one
medium has.

| Field | Verdict | Resolution |
|---|---|---|
| `Paragraph.role: unindented` | **Violation.** "Unindented" describes appearance | Renamed to `standalone` — the semantic fact is that the paragraph does not continue the preceding flow. First-line indent is one medium's way of showing that |
| `Container.kind: landscape` | **Violation.** Landscape is a page concept; HTML has no pages | Renamed to `wide` — the semantic fact is that the content needs more width than the text block. The profile decides that means a landscape section in DOCX, `landscape` in LaTeX, a scroll container in HTML |
| `Figure.width` | **Declared exception, bounded** | Permitted **only as a fraction of the text block** (`100%`, `50%`) or the keyword `natural`. Absolute units — cm, pt, px, EMU — are rejected by validation |

Two of the three were not exceptions at all: they were correct concepts wearing
presentational names, and renaming them removed the problem. That is usually the
case, and it is worth trying before granting an exception.

`Figure.width` is a genuine exception and is granted deliberately. An author
does need to say "this diagram should occupy half the width"; that is authorial
intent, not styling. Restricting it to a **relative** value is what keeps it
medium-independent: 50% of the text block means the same thing everywhere, while
`8cm` means nothing in HTML and silently breaks when a profile changes its
margins.

**Enforced, not trusted.** The property test in
[Testing Strategy](09-testing-strategy.md) asserts that no IR node carries a
font, size, colour, margin, alignment, spacing, indent, style name or absolute
length. This invariant is what keeps the LaTeX and HTML backends reachable, and
it will be violated by someone under deadline unless a test notices.

## Node vocabulary

Closed on purpose, and derived from measurement rather than from imagining what
a document might contain. See the
[audit](reference/reference-thesis-audit.md#2-element-census).

The rule for growth: **a node type is added when a profile genuinely requires
it, and then it is available to every profile.** Code grows by capability, never
by document type.

### Document

| Node | Fields | Notes |
|---|---|---|
| `Document` | `meta`, `frontmatter[]`, `body[]`, `backmatter[]`, `bibliography` | Root |
| `Section` | `id`, `level`, `title`, `kind`, `children[]` | `kind` is one of `chapter`, `top_level_section`, `subsection`, `annex` |
| `Slot` | `name` | A generated region — the full set is below |

**`chapter` and `top_level_section` are deliberately distinct** even though both
render as a level-1 heading. A `chapter` receives a `Capítulo {roman}.` prefix;
a `top_level_section` (Resumen, Abstract, Introducción, Conclusiones,
Recomendaciones, Referencias, Anexos) does not. In the approved thesis both use
the same Word style, so a model with only "heading level 1" could not express
which ones get a prefix — and that document is in fact **missing the
`Capítulo II.` prefix** on one chapter. See
[D20](11-decision-log.md#d20--schema-distinguishes-chapter-from-top_level_section).

`Slot` is how the IR expresses "a table of contents belongs here" without
containing one. The contents are produced during lowering, from the document
itself.

The slot vocabulary, measured from the approved thesis:

```
cover              institution · faculty · logo · title · degree statement ·
                   author · advisor · place · year
dedication         style Dedicatoria — italic, right-aligned
acknowledgements
abstract_es        "Resumen" + body + "Palabras clave — …"
abstract_en        "Abstract" + body + "Keywords — …"
toc                Tabla de Contenido
list_of_tables     Índice de tablas
list_of_figures    Índice de figuras
list_of_annexes    Índice de anexos
references         the bibliography
```

`cover` is filled from `Document.meta`; the four index slots are computed from
the document itself; the rest hold authored prose.

The approved thesis also carries ORCID identifiers on the cover and a pair of
"how to cite" tables. Both are **deliberately excluded** — institution-specific
boilerplate assigned to the manual 5%, see
[D22](11-decision-log.md#d22--orcid-ids-and-the-how-to-cite-tables-are-out-of-scope).

### Block

Evidence counts are from the **approved** 134-page thesis, with the 73-page
proposal in parentheses.

| Node | Fields | Evidence |
|---|---|---|
| `Paragraph` | `inlines[]`, `role` | 2,074 (1,157) |
| `List` | `ordered`, `items[]` (nestable) | 74 (119) list items |
| `Table` | `id`, `label`, `title`, `note`, `header_rows`, `rows[][]`, `header_repeat` | **37** (8) tables |
| `Figure` | `id`, `label`, `title`, `note`, `asset`, `width` (relative only) | **107** (4) images, 93 media files, 11 MB |
| `Equation` | `id`, `label`, `latex`, `display`, `numbered` | **141** (163) — the dominant element; **numbered** in the approved thesis |
| `Blockquote` | `children[]` | |
| `Container` | `kind`, `children[]` | Structural groupings. `kind: wide` means "needs more width than the text block" |
| `Raw` | `target`, `content` | Escape hatch; every use is a reported finding |

`Paragraph.role` carries semantic intent — `body`, `standalone`,
`caption_label`, `caption_title`, `caption_note`, `equation`,
`bibliography_entry`, `dedication`, `keywords` — which the style binder maps to
concrete named styles. It is a semantic role, not a style name: `standalone`
says the paragraph does not continue the preceding flow; `NORMALES` is one
institution's name for how that is shown, and removing its first-line indent is
one medium's way of showing it.

### Inline

| Node | Fields |
|---|---|
| `Text` | `value` |
| `Emph` / `Strong` | `inlines[]` |
| `Math` | `latex` (inline form) |
| `Citation` | `keys[]`, `locator`, `style` (parenthetical or narrative) |
| `CrossRef` | `target_id`, `kind` |
| `Link` | `url`, `inlines[]` |
| `LineBreak` | — |

### Not in v1

`Footnote`, `Endnote`, `CodeBlock`, `Chart`, `Metric`, `Callout`, `Clause`,
`SignatureBlock`.

The first three have **zero occurrences in all three audited documents**. The
rest belong to document families we are not building yet. Adding any of them later is additive
and does not disturb existing profiles — that property is the point of the
design.

## The caption model

The one place a naive IR design fails outright.

APA 7, as actually used in the approved thesis, treats a table or figure
caption as **separate blocks around the object**, each with its own Word style:

```
Figura 1                                      XFIGURAS   ← label   (Arial bold)
Imagen representativa de la sobrerotura.      X1         ← title   (italic)
[IMAGE]                                       X2         ← content
Nota: El gráfico resalta la zona roja como…   X3         ← note
```

Tables are identical, with `XTABLAS` as the label style and the table in place
of the image. The note prefix is `Nota:` with a colon.

So `Table` and `Figure` carry four distinct slots — `label`, `title`,
`content`, `note` — and not one `caption` string.

**A third reason the four slots matter:** the `label` style is also the source
for the Índice de tablas and Índice de figuras, which are style-driven `TOC`
fields. A merged caption string would produce index entries containing the
title as well as the label.

Two further points:

- **`label` is computed, never authored.** `Tabla 5` comes from the `number`
  pass. The proposal labels its tables 2, 3, 4, 5, 9A, 9B because a human
  maintained them by hand; the approved thesis mislabels equations the same way.
- **Where the blocks go is a layout decision, not a content one.** APA 7 puts
  label and title above both tables and figures. Other conventions put figure
  captions below. That placement lives in the profile's layout rules, so the
  same IR renders correctly under either. A design that bakes placement into the
  IR needs a different IR per citation style.

## Identity and references

Every referenceable node has a stable `id`, either authored (`{#tbl:props}`) or
derived from its content. The `number` pass builds a reference map:

```
tbl:props     → { kind: table,    label: "Tabla 5",   section: "2.1.5" }
fig:mapa      → { kind: figure,   label: "Figura 12", section: "3.1.2" }
eq:holmberg   → { kind: equation, label: "(12)",      section: "2.1.5" }
sec:marco     → { kind: section,  label: "2.1",       title: "Marco teórico" }
```

An unresolvable reference is a validation error, not a rendered `??`. The
reference map is what pass 11 turns into live Word fields — see
[Numbering and Fields](07-numbering-and-fields.md).

## Versioning

The IR carries `schema_version`. A document persisted today must remain
readable after the vocabulary grows. Two commitments:

- Adding an optional field or a new node type is a minor version and is
  backward-compatible.
- Removing or repurposing a field is a major version and requires a migration.

This is also the reason we do not adopt an external AST as our model: its version
lifecycle would not be ours to control.
