# 07 — Numbering and Fields

This is the highest-value subsystem in the engine, and the one most likely to be
underestimated. It gets its own document because a design that treats numbering
as an afterthought produces documents that look right and fall apart the first
time a person edits them.

## The evidence

All three audited documents number everything by hand. All three are wrong — and
one of them is **approved**.

Heading numbers are literal text runs, not automatic numbering. In the
**approved** thesis the separator is not even consistent:

```
runs: ['1.2.1', '<TAB>', 'Problema general']     ← with a tab
runs: ['1.1',            'Generalidades']        ← no tab; renders "1.1Generalidades"
```

Zero of its 2,074 paragraphs use Word's automatic numbering. The consequences in
the **approved, submitted, accepted** document:

- **Equation tags run 1…44, then `6`, then 45, 46, 47, then `45`, `46` again** —
  50 tags for 47 numbers, with duplicates and one out of order.
- **"Marcos teórico y conceptual" is missing its `Capítulo II.` prefix** while
  chapters I, III and IV have theirs. It is wrong in the table of contents too.
- Two annex sub-items carry the annex style without an "Anexo N:" prefix, so
  they appear in the annex index as if they were annexes.
- A stray paragraph containing `88` carries the chapter-title style — a page
  number typed into the body.

The thesis proposal from the same faculty is worse in the same way: **three
consecutive headings numbered `1.1.2.1`**, `1.1.3` followed by `1.2.2` which
precedes `1.2`, and **tables labelled 2, 3, 4, 5, 9A, 9B** — 1, 6, 7 and 8 do
not exist, and `9A`/`9B` is a visible workaround for not renumbering downstream.

A third thesis, from a different university, had its table of contents converted
to static text, typed figure numbers, and two different figures both labelled
"Figura 2".

**This is not carelessness. It is the inevitable outcome of maintaining
numbering by hand across 134 pages while the content is still changing. The fact
that a document with these defects was approved tells us where the acceptance
bar sits — and that automation clears it comfortably.**

## Two consequences, and they point the same way

**First: automatic numbering is the single highest-value feature we ship.** Not
because it is technically interesting, but because it is the thing humans
reliably get wrong, and getting it right is unambiguous — a reader can check it.

**Second, and less obvious: numbering must be *field-backed*, not baked into
text.** This follows directly from the 90–95% target.

The engine will hand over a document with ~5% left to fix by hand. Suppose a
person inserts one table in the middle of chapter 3. If our numbers are static
text, every table label and every cross-reference after that point is now wrong,
and they must fix all of them by hand. The 5% became 30%, and we shipped the
same disease we set out to cure.

If the numbers are Word fields, they update. The person edits, presses F9, and
the document is correct.

> Static numbering is not a smaller version of automatic numbering.
> It is the defect, reintroduced at the last step.

## What the engine emits

| Element | Mechanism | Notes |
|---|---|---|
| Heading numbers | Multi-level list bound to the heading styles (`w:numPr` in `styles.xml`) | Levels 2 and 3; level 1 gets a `Capítulo {roman}.` prefix |
| Table labels | `SEQ Tabla` field in a `XTABLAS` paragraph | Renders "Tabla 5"; also produces the index entry |
| Figure labels | `SEQ Figura` field in a `XFIGURAS` paragraph | Same |
| Equation numbers | `SEQ` field in a centered paragraph, as `(n)` | **In scope** — the approved thesis numbers `(1)`…`(47)` |
| Cross-references | `REF` field to a bookmark on the target | "…como se observa en Tabla 5" |
| Page cross-references | `PAGEREF` field | |
| Tabla de Contenido | `TOC \h \z \t "TITU1;1;TITU2;1;TITU3;1"` | Style-driven; flat, all at level 1 |
| Índice de tablas | `TOC \h \z \t "XTABLAS;1"` | Style-driven |
| Índice de figuras | `TOC \h \z \t "XFIGURAS;1"` | Style-driven |
| Índice de anexos | `TOC \h \z \t "XANEXOS;1"` | Style-driven |
| Page numbers | `PAGE \* MERGEFORMAT` in the footer | Three regions via `w:pgNumType` |

### The indexes are style-driven, and the label style is the source

All four index fields are driven by a **paragraph style**, not by outline levels.
This is measured from the approved thesis, and it has a consequence worth stating
plainly:

**Emitting a table label with style `XTABLAS` both formats it bold and produces
its entry in the Índice de tablas.** There is no separate index-building step.
Same for `XFIGURAS` and `XANEXOS`. That is why the university's template defines
those as distinct bold styles rather than folding them into `NORMALES`.

An earlier version of this document planned to add `outlineLvl` to the heading
styles so a standard TOC field could see them. That was unnecessary — the `\t`
switch needs no outline levels — and insufficient, since outline levels cannot
produce table, figure or annex indexes at all. See
[D13](11-decision-log.md#d13--indexes-are-style-driven-toc-fields-not-outline-levels).

### Equation numbering is simpler than feared

The approved layout is a **centered paragraph holding the equation followed by
the tag in parentheses — no tab, no right alignment**:

```
                    [ centered equation ]  (12)
```

The classic right-margin-aligned tag needs an invisible table or an
OMML-plus-field construction. This does not: a `SEQ` field at the end of a
centered paragraph is enough. Numbering is global and sequential, not per
chapter.

Every referenceable object also gets a bookmark, because a `REF` field points at
a bookmark rather than at a position.

## The two-representation problem

Numbering exists twice, in two different forms, and the distinction is easy to
lose.

**In the `SemanticIR`, numbering is logical.** The `number` pass computes a
reference map:

```
tbl:props     → { kind: table,    label: "Tabla 5",  section: "2.1.5" }
fig:mapa      → { kind: figure,   label: "Figura 12", section: "3.1.2" }
eq:holmberg   → { kind: equation, label: "(12)",     section: "2.1.5" }
sec:marco     → { kind: section,  label: "2.1" }
```

This is needed because the engine must *know* the numbers: to validate that
every cross-reference resolves, to build the conformance report, and to render
correctly for backends that have no field mechanism at all. LaTeX and HTML
resolve references at build time; only Word defers them.

**In the DOCX, numbering is deferred.** The `postprocess:fields` pass replaces
the computed labels with field structures, so Word owns them from then on.

The logical numbers are still not wasted: they are what the conformance report
quotes, and they are the expected values the golden tests assert against after
field refresh. If Word's computed numbers and ours disagree, that is a bug worth
catching — and given that every audited document has numbering errors, it is
exactly the bug class we exist to eliminate.

## Field mechanics

A Word field is a small structure, not an attribute:

```xml
<w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText xml:space="preserve"> SEQ Tabla \* ARABIC </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:t>2</w:t></w:r>              <!-- cached result -->
<w:r><w:fldChar w:fldCharType="end"/></w:r>
```

Three practical consequences:

1. **The cached result must be written.** If it is omitted, the field shows
   blank or an error until someone opens the document. We write our computed
   value there, so the document reads correctly even before any refresh.
2. **The document must be marked dirty** (`w:updateFields` in `settings.xml`) so
   Word recalculates on open.
3. **A refresh pass should run before delivery**, because a table of contents
   cannot be computed without laying out the pages. See
   [Rendering Backends](06-rendering-backends.md#field-refresh).

## Scope for v1

**In:** heading numbering; `SEQ` labels for tables, figures **and equations**;
`REF` cross-references; all four style-driven index fields; three-region `PAGE`
numbering; bookmarks on every referenceable object.

**Out:** per-chapter numbering such as "Figura 3.2" — all three audited
documents number globally — and footnote numbering, since all three contain zero
footnotes.

Both are additive later and neither affects the design of what is in scope.

> **Equation numbering was previously cut and is now back in.** The cut was
> based on the thesis *proposal*, which numbers none of its 163 equations. The
> *approved* thesis numbers its equations. Evidence from an approved document
> outranks evidence from a draft — see
> [D14](11-decision-log.md#d14--v1-omits-footnotes-endnotes-and-code-blocks-equation-numbering-is-in-scope).
