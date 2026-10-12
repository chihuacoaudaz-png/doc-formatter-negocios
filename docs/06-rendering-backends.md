# 06 — Rendering Backends

A backend turns a `LayoutPlan` into a file. There is exactly one backend in v1:
DOCX.

## The DOCX backend is two stages, not one

The single most common mistake in this kind of project is assuming "run Pandoc
and you get a Word document." Pandoc does a large amount of valuable work and
cannot do several things the reference profile requires. So:

```
LayoutPlan
    ↓  emit
Pandoc AST (JSON)  +  reference.docx  (compiled from the profile's styles)
    ↓  pandoc
DOCX (structurally complete, layout incomplete)
    ↓  postprocess: OOXML passes          ← mandatory, not optional
DOCX (complete)
    ↓  refresh fields: headless LibreOffice
DOCX (delivered)
```

The post-processing stage is a required part of the pipeline. Designing as
though Pandoc is the whole backend leads to discovering this late, after the
architecture has hardened around the wrong assumption.

### What Pandoc handles well

Headings, paragraphs, lists, pipe tables, images, emphasis, hyperlinks,
**LaTeX math to OMML** (critical here — 141 equations in the approved thesis,
163 in the proposal), citation processing through its citation engine,
bibliography generation, and style application from a reference document.

For a math-heavy, image-heavy thesis this is most of the work, done correctly,
for free.

### What Pandoc cannot do, and we must

| Requirement | Why Pandoc cannot | Our pass |
|---|---|---|
| Multiple sections with different page-numbering formats (roman front matter, arabic body) | Not expressible in its document model | `postprocess:sections` |
| Landscape annex section | Same | `postprocess:sections` |
| `SEQ` fields for table, figure and equation numbers | Its cross-reference tooling resolves numbers to **static text** | `postprocess:fields` |
| `REF` fields for cross-references | Same | `postprocess:fields` |
| Four style-driven `TOC` fields (`\t "XTABLAS;1"` and friends) | `--toc` emits only a single outline-based TOC | `postprocess:fields` |
| Custom style names beyond the ones it knows | See below | `emit` (custom-style spans) |
| Byte-reproducible output | Emits timestamps and revision ids | `postprocess:normalize` |

### The reference document constraint

`reference.docx` is how Pandoc learns what things should look like. It is a
compiled artefact, produced deterministically from the profile's `styles`
block — not a hand-maintained file, and not part of the profile itself:

```
profile styles ──→ ReferenceDocBuilder ──→ reference.docx
               └──→ (future) CSS
               └──→ (future) LaTeX preamble
```

Keeping it out of the profile is what stops the profile from being coupled to
Word.

**The constraint that catches people:** Pandoc only applies styles it knows by
name — `Normal`, `Heading 1`–`9`, `Body Text`, `First Paragraph`, `Caption`,
`Table Caption`, `Source Code`, and a few others. A style defined in
`reference.docx` that Pandoc does not recognise is **silently ignored**.

The reference profile's styles are `PARRAFOS`, `NORMALES`, `TITU1`, `TITU2`,
`TITU3`, `XTABLAS`, `XFIGURAS`, `X1`, `X2`, `X3`, `XANEXOS`, `Dedicatoria`,
`TDC1` and `Piedepgina` — **Pandoc knows none of them.** So the `emit` pass must
wrap content in explicit custom-style markers:

```
Div  with custom-style = "TITU2"   for block-level styles
Span with custom-style = "X2"      for inline-level styles
```

This is why `docx_style` is a field on every style role in the profile: the
emitter needs the concrete target name, and the style binder is the only place
that knows it. The `SemanticIR` never does.

It also matters more than a formatting detail here. The caption **label style is
the index source** — a label emitted with the wrong style silently drops out of
the Índice de tablas. So custom-style mapping is a correctness requirement, not
cosmetics. See
[Numbering and Fields](07-numbering-and-fields.md#the-indexes-are-style-driven-and-the-label-style-is-the-source).

### OOXML post-processing passes

Each is a small, independently testable transform over the unzipped package.

| Pass | Touches | Does |
|---|---|---|
| `sections` | `document.xml` | Insert `w:sectPr` at region boundaries; set `w:pgSz`, `w:pgMar`, orientation |
| `pagination` | `document.xml`, `footer*.xml` | Set `w:pgNumType` (`lowerRoman`, `decimal`, restart values); build footers with `PAGE` fields |
| `fields` | `document.xml` | Insert `SEQ`, `REF`, `PAGEREF`, `TOC` field structures; mark the document dirty so fields recalculate |
| `indexes` | `document.xml` | Insert the four style-driven `TOC` field structures at their slots |
| `cleanup` | `document.xml` | Remove empty paragraphs, strip stray direct formatting, collapse the numbering-definition explosion, remove any hand-placed page break |
| `normalize` | whole package | Strip timestamps and `w:rsid` attributes for reproducible output |

The `cleanup` pass has specific targets, all observed in the audited documents:
empty heading paragraphs, and stray paragraphs holding page numbers under the
chapter-title or TOC-heading styles. **Both audited UNI documents contain a
paragraph consisting of `88` styled as a chapter title**, which suggests a shared
source file or a shared habit. A generated document should not inherit that
class of artefact, and a cheap post-pass catches it.

`normalize` exists so that the same input produces the same bytes. Without it,
golden-file tests compare noise.

Note what is **not** in this list: a pass to insert page breaks. A page break
before a chapter, and keeping a caption with its object, are both **paragraph
style properties** (`w:pageBreakBefore`, `w:keepNext`), so they arrive through
`reference.docx` and need no post-processing at all. The approved thesis uses 32
hand-placed breaks instead; `cleanup` exists partly to ensure we never emit
one.

### Field refresh

Word fields store both an instruction and a cached result. A newly written
document has no cached results, so the four indexes and every `SEQ` number would
render as empty or as an error until someone opens the file and presses F9. The
approved thesis carries 162 fields and 207 bookmarks, so this is not a marginal
concern.

Headless LibreOffice resolves this:

```
soffice --headless --convert-to docx  (fields recalculate on load)
```

Two operational cautions:

- **Fonts must exist on the machine doing this.** Arial is not present on a
  stock Linux container; LibreOffice substitutes Liberation Sans, which is
  metrically compatible but not identical. Since the same step is used for PDF
  rendering and page counting, **font availability directly affects the reported
  page count**. Install the real fonts in the image, or accept the substitution
  as a deliberate decision and document it.
- **LibreOffice's DOCX round-trip is not lossless.** It must be evaluated
  against the golden fixtures before we depend on it, and specifically against
  the four nested style-driven `TOC` fields, which are the most fragile
  construct in the document. If it degrades the
  document, the fallback is to leave fields uncalculated and note in the
  conformance report that the recipient should press F9 once — acceptable, given
  the 90–95% target, but a worse experience.

## PDF

There is no PDF backend. PDF is produced by converting a rendered artefact:

```
DOCX → LibreOffice → PDF
```

PDF is used for visual validation and for delivery when the recipient does not
need to edit. It is never an editing target.

## Future backends

Neither is built now, and neither is free later. What the `SemanticIR`
invariant buys is narrower and worth stating precisely: adding one is
**additive work in one layer rather than a re-architecture**. No Word concept
enters the IR or the authoring format, so nothing upstream has to change.

**Known unfinished piece.** Every style role in a profile currently carries a
`docx_style` field — a Word identifier. It is correctly outside the IR, so the
invariant holds, but a second backend needs a parallel style-name mapping
(`latex_env`, `css_class`) that does not exist yet, plus a decision about
whether that lives in the profile or in a per-backend translation table. That is
real design work, not a rename.

**LaTeX.** For the third use case — generating documents for end users, where
typographic quality matters and no one needs to edit the source. The
`LayoutPlan` maps onto a LaTeX document class plus a preamble compiled from the
same profile styles. Math is native, so a document with 141 equations is
genuinely easier here than in Word. The hard parts are the reverse of Word's:
page geometry and floats are excellent, while reproducing one institution's
exact caption block and flat index takes more work than it does through a
reference document.

**HTML.** For in-app preview and for web delivery. The natural way to show a
draft to an author without producing a file.

## Template filling: a different architecture

Filling placeholders in a prepared DOCX is a legitimate technique for rigid,
high-volume, layout-fixed documents — contracts, certificates, forms. It
bypasses this entire pipeline: no IR, no layout rules, no style binding.

It is not needed for theses, and it is recorded here only to be explicit: if it
is ever added it is a **separate, clearly-labelled path**, never the default for
content that can be modelled semantically. Maintaining two architectures has a
real cost, and it should be paid knowingly.
