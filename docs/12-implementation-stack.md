# 12 — Implementation stack

The engine will be implemented in **Python**. This is the language decision for
the initial text-and-equation implementation; earlier design documents specified
the architecture and rendering tools, but did not select an engine language.

| Component | Decision |
|---|---|
| Engine, validation, IR and layout passes | Python |
| Authoring input | Markdown section files and a YAML manifest |
| Profile configuration | YAML |
| Word emission and LaTeX math conversion | External Pandoc executable |
| DOCX post-processing | Python manipulating the ZIP/XML package |
| Field refresh and PDF conversion | External LibreOffice executable, subject to fixture validation |

Python does not replace Pandoc or LibreOffice. They remain separate runtime
dependencies of the rendering stages.

## Selected Python tooling

- Python 3.11+, using `venv` and `pip`.
- `markdown-it-py` for Markdown tokenization, with small DocSource rules for
  equations and cross-references. Token maps preserve block source locations;
  custom reference tokens also retain their actual line within a paragraph.
  See the [token API](https://markdown-it-py.readthedocs.io/en/latest/api/markdown_it.token.html).
- PyYAML's safe loader with duplicate-key rejection for manifests and profiles.
- Frozen dataclasses, tuples and immutable metadata mappings for the content IR.
- `pytest` for fixture integration, CLI behavior and malformed-input tests.

- `lxml` for OOXML post-processing, and Python's `zipfile` for the package.

`pyproject.toml` declares compatible dependency ranges; `requirements-dev.txt`
records the tested direct and transitive versions. Install it inside `.venv`.

**External tools.** `parse` needs neither Pandoc nor LibreOffice. `build`
requires Pandoc; LibreOffice is optional and used only for `--refresh` and
`--pdf`. No minimum versions are pinned yet — the build records which tools it
found in its report, and falls back with a `manual-field-refresh` warning when
refresh is unavailable or does not survive the package checks.

**`--refresh` currently always falls back**, measured with Pandoc 3.11 and
LibreOffice 26.8: the round-trip preserves all 7 equations and all 12 field
structures, but injects one direct paragraph-formatting override and strips
`w:updateFields`. The build rejects it and keeps the original. This costs
nothing today because computed field values are already written inline; it will
matter once a real table of contents exists, whose page numbers cannot be
computed without layout. See
[D27](11-decision-log.md#d27--libreoffice-field-refresh-is-rejected-computed-values-ship-inline).

## Implemented contract and limits

`doc-formatter parse SOURCE --profile PROFILE.yaml` produces a JSON envelope:

- `document`: content-only SemanticIR, schema version 1.
- `profile`: the requested profile ID, outside the IR.
- `references`: IDs mapped to semantic kinds and source locations. No rendered
  labels or numbering policy are assigned in this phase.
- `diagnostics`: warnings; invalid input instead returns diagnostics on stderr
  with exit code 1 and does not publish an IR file.

The CLI accepts a source directory or manifest path. `--output` writes a new
file; omitting it prints JSON. A profile is optional, but omission produces a
`profile-not-checked` warning. Supplying one validates its ID, required authored frontmatter slots, required
chapter titles/order and maximum heading depth. Rendering styles and layout
rules are not interpreted by the parser, and profile inheritance is not
implemented.

The current input is one top-level heading per Markdown file. Body files are
`chapter`; authored frontmatter files (`abstract_es`, `abstract_en`, and the
other authored slots) are `top_level_section`. Generated slots (`cover`,
`toc`, indexes) and back matter are still rejected. Supported content:
headings, paragraphs, emphasis/strong text, links, line breaks, inline math,
display math and equation/section references. Heading IDs may be explicit
(`{#sec:name}`) or derived from the title and heading ancestry. Derived IDs change
when titles change; use explicit IDs for externally referenced stable sections.
Duplicate IDs, skipped heading levels, invalid delimiters and unresolved
references fail with a source location.

The compact inline nodes use `type`, `value` and `children`: for math, `value`
is LaTeX; for a cross-reference it is the target ID; for a link it is the URL.
These are semantic values with no rendering instructions. Display equations
store `latex`, `numbered` and an optional ID. A separate block source map
identifies the authored file and one-based line.

Dollar-delimited inline math is single-line; escape literal dollars as `\$`.
Display math uses a standalone `$$…$$` block (one or multiple lines), or the
numbered `:::equation {#eq:name}` form. The parser checks delimiters and nonempty
content, not the validity of LaTeX commands or mathematical statements.

Unsupported constructs fail rather than disappear: images, tables, lists,
code, raw HTML, citations/bibliographies, generated front-matter slots and
back matter. Selected sample passages contain no citation syntax. Citation
processing is deferred and must be implemented before extending the sample
with `[@cite]` keys. Full schema coverage, draft placeholders and complete
document conformance are later work; this command validates the supported
source subset only.

## Implemented rendering contract

`doc-formatter build SOURCE --profile PROFILE.yaml --output DIR` writes the DOCX
and a conformance report into a **new** directory, and prints the artifact path,
structural counts and findings. `--refresh` attempts a headless LibreOffice
field refresh, keeping the original package if the post-refresh checks fail.
`--pdf` additionally renders a preview.

The pipeline is `SemanticIR → LayoutPlan → Pandoc + reference.docx → OOXML
post-processing`. The `LayoutPlan` is where styles are bound and numbering is
assigned from profile rules (`prefix_heading`, `number_headings`,
`append_paragraph`, `bind_role`, `number_labels`); the `SemanticIR` stays free
of fonts, sizes, margins and style names. Institution-specific strings such as
`Capítulo {roman}. {title}` and `Palabras clave —` live in the profile.
`reference.docx` is generated from the profile's styles rather than maintained
by hand, and the emitter wraps content in explicit custom-style markers because
Pandoc ignores style names it does not know.

Post-processing inserts `SEQ` equation labels, `REF` cross-references and their
bookmarks, and joins the equation paragraph with its label field — Pandoc emits
those separately. Computed field values are written alongside the instructions,
so the document reads correctly before any refresh. Numbering is global and
sequential; inline and unnumbered display math do not advance the sequence.

Conformance runs against the generated package, not the source. Not yet
implemented: images, tables, citations, cover, indexes, back matter,
page-count assertions and visual checks.

## First concrete input

The working fixture is
[`fixtures/uni-figmm-text-math`](../fixtures/uni-figmm-text-math/README.md):
Resumen, Abstract, complete Chapters I–II, skeleton III–IV, plus an optional
synthetic math chapter. Its profile is
[`thesis@1.yaml`](../profiles/uni-figmm/thesis@1.yaml)
(`id: uni-figmm/thesis@1`). Keywords come from `meta`; heading numbers use a
Word tab, matching the approved document. Agent brief:
[`dialect/docsource.md`](../dialect/docsource.md) +
[`playbooks/uni-figmm-thesis/`](../playbooks/uni-figmm-thesis/).

This sample parses into inspectable SemanticIR, and its IDs, references and
counts are tested against the expected data. It also builds to a DOCX with
named styles, chapter prefixes, numbered headings, editable OMML math, `SEQ`
equation labels and working `REF` cross-references.
