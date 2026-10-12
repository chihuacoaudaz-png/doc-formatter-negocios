# 11 — Decision Log

Each entry records a decision, why it was taken, and what was rejected. The
rejected alternatives matter more than the decisions: without them, a future
reader re-opens settled questions, and someone under deadline pressure quietly
reverses a choice whose reasoning was never written down.

Status values: **Accepted** · **Provisional** (needs evidence) · **Superseded**.

---

## D1 — Content generation and formatting are separate systems

**Accepted.**

The thesis agent writes content into a standardised format. A separate engine
formats it.

**Why:** different iteration speeds (content needs many review cycles;
formatting needs to be right once per institution), different failure modes
(probabilistic and human-judged vs. deterministic and machine-verifiable),
different reuse (per-institution vs. per-document), and testability — with a
standardised handoff the formatter has fixtures and can be regression-tested for
free.

**Rejected:** one agent that writes content and emits the DOCX. Every content
revision would re-run the expensive part, and the formatter could never be
tested in isolation.

---

## D2 — The authoring format is Markdown + YAML, not JSON

**Accepted.** Detail and arithmetic in
[Authoring Format](03-authoring-format.md#why-not-json).

**Why:** at the measured scale — 216–266 words/page, and 2,074 paragraphs in the
approved 134-page thesis, so ~33,000–40,000 words and ~2,300 paragraphs for a
150-page thesis — a nested JSON IR adds ~50,000 tokens of pure structure,
roughly doubling the agent's output. Worse, a JSON parse failure is global: one
bad escape in paragraph 2,000 loses the document, whereas a malformed Markdown
block loses one figure. Models are also far more reliable
emitting Markdown, and humans can review and correct it.

**Rejected:** the agent emitting the IR directly as JSON. The usual argument for
it — schema validation and constrained decoding — is satisfied by making the
*manifest* strict YAML and validating content after parsing, with errors that
point at a file and line.

**Consequence:** the JSON-shaped IR still exists, but it is internal to the
compiler and never authored by hand. Those are two different layers, and only
one is a human-facing contract.

---

## D3 — Three representations, and the IR is never mutated by formatting

**Accepted.** See [Semantic IR](04-semantic-ir.md).

`DocSource` → `SemanticIR` → `LayoutPlan` → backend.

**Why:** the rule "each chapter starts on a new page" is naturally implemented
by inserting a page-break node into the document model. The moment that happens,
the model contains a page break — meaningless in HTML — and is no longer
format-independent. The promise that one model serves many outputs is broken by
the first rule applied to it. Profiles therefore drive the *lowering* from
`SemanticIR` to `LayoutPlan` and never write back.

**Rejected:** a single mutable document model with rules applied in place.
Simpler on day one, and it forecloses every backend after the first.

**Cost:** one extra representation and a lowering pass. **Enforcement:** a
property test asserting no `SemanticIR` node carries a font, size, colour,
margin, alignment, spacing, indent, style name or **absolute length** — see
[Testing Strategy](09-testing-strategy.md). Without the test this decision will
be violated under deadline; it already was, three times, before the boundary was
written down explicitly
([D25](#d25--the-ir-has-one-declared-presentational-exception-and-it-is-relative)).

---

## D4 — Pandoc is a backend, not our data model

**Accepted.**

**Why:** Pandoc's AST is presentational rather than domain-semantic. It has
`Header` and `Table`, but no way to say "this is the methodology chapter" or
"these annexes are a landscape section" except as `Div` attributes — which are
stringly-typed and cannot be validated against a document schema. Concretely, it
cannot express the four-block APA caption (label / title / content / note, each
with its own style), the three page-numbering regions, or the four style-driven
index fields without degenerating into attribute strings. And `pandoc-types`
changes across major versions, so persisted documents would be tied to a Pandoc
release we do not control.

**Rejected:** adopting the Pandoc AST as the IR to save building one. It saves
less than it appears to and costs the schema layer.

**What we do use Pandoc for:** heading and paragraph structure, lists, tables,
images, **LaTeX-to-OMML math conversion** (critical — 141 equations in the
approved thesis, 163 in the proposal), citation processing, bibliography
generation, and style application from a reference document. That is most of the
work.

---

## D5 — The DOCX backend is Pandoc plus mandatory OOXML post-processing

**Accepted.** See [Rendering Backends](06-rendering-backends.md).

**Why:** Pandoc cannot produce several things the reference profile requires:
five sections with three different page-numbering formats, landscape annexes,
`SEQ`/`REF` fields, the **four style-driven `TOC` fields** (its `--toc` emits
only a single outline-based one), or reproducible bytes. Post-processing is
therefore a required pipeline stage, not an optional polish step.

**Rejected:** treating Pandoc as the whole backend. That assumption survives
until the first real document and then forces a late architectural change.

---

## D6 — Numbering is automatic and field-backed

**Accepted.** Evidence and mechanics in
[Numbering and Fields](07-numbering-and-fields.md).

**Why:** both audited theses number everything by hand, and both are wrong — the
reference thesis has three headings numbered `1.1.2.1` and tables labelled 2, 3,
4, 5, 9A, 9B. Automatic numbering is therefore the highest-value feature.

The *field-backed* part follows from the 90–95% target: we hand over a document
with ~5% left to fix. If numbering is static text, one manual insertion
invalidates every label and cross-reference after it, and the 5% becomes 30% —
we would have shipped the same defect we set out to cure. With Word fields, the
person edits and presses F9.

**Rejected:** static numbering resolved at build time, which is what Pandoc's
cross-reference tooling produces. It is not a smaller version of automatic
numbering; it is the defect reintroduced at the last step.

---

## D7 — Zero direct formatting in the output

**Accepted.**

Every visual property comes from a named style. No hard-coded font, size or
spacing on any paragraph or run we generate.

**Why:** this is what makes the manual 5% cheap. A person changes one style and
200 paragraphs follow. The reference thesis carries direct formatting on 41% of
its paragraphs; another audited thesis on 89% — adjusting line spacing there
means touching 1,250 paragraphs by hand.

**Enforcement:** a conformance assertion with a maximum of zero.

---

## D8 — One profile file with `extends`, not four registries

**Accepted, with a scheduled review at Phase 3.**

**Why:** the long-term argument for splitting schemas, styles, policies and
profiles into independent registries is correct — document variety is
combinatorial and factoring turns N×M into N+M+K. But it describes a state we
are not in. With one institution and one document kind, four cross-referencing
registries cost real machinery — reference resolution, inheritance semantics,
config-level validation, independent versioning — and return nothing. `extends`
is one inheritance mechanism instead of four.

**Rejected for now:** the four-registry design. Not wrong, just early. Deciding
the seams before the second and third profiles exist means guessing at them.

**Review:** Phase 3, when the second institution arrives.

---

## D9 — Style, Layout and Conformance are three different things

**Accepted.** See [Profiles](05-profiles-styles-policies.md#the-three-kinds-of-rule).

- **Style** — a property of a named style or the page setup. Does not change the
  node tree.
- **Layout** — a transform that inserts, moves, reorders or renumbers nodes.
- **Conformance** — a predicate that produces a finding and changes nothing.

**Why:** collapsing them produces a specific, hard-to-trace bug. "Each chapter
starts on a new page" is both a paragraph-style property (`w:pageBreakBefore`)
and a natural-sounding policy. If both layers can express it, eventually both
do, and the document gets two page breaks — with each layer looking correct in
isolation.

**The classification test:** does obeying the rule change the node tree? No →
style. Yes → layout. Only needs checking → conformance. The **resolver** applies
this test, not whoever writes the configuration.

### This design committed the bug it warns about

An earlier version of the reference profile classified `pageBreakBefore` as a
style in the table above **and** implemented "each chapter starts on a new page"
as a layout rule named `chapter-new-page` — in the same file, a hundred lines
apart. A human reviewer had both halves in front of them and did not notice.

That is the whole argument for the last sentence of the test: **the resolver
owns the classification.** A written rule that relies on the config author
remembering it will be violated, including by the person who wrote the rule.

**Resolution, and what it revealed.** Applying the test honestly moved the rule
out of `layout` entirely, and measurement then showed the correction was worth
more than the bug fix. The approved thesis sets `pageBreakBefore` on **no** style
and **no** paragraph; all 32 of its page breaks are hand-placed `<w:br>` runs,
serving two different intents:

| Intent | Author's mechanism | Correct mechanism | Kind |
|---|---|---|---|
| New page before a top-level division | ~7 manual breaks | `page_break_before` on the heading style | **Style** |
| Keep a caption with its figure or table | ~25 manual breaks | `keep_with_next` / `keep_together` | **Style** |

Both are properties, so both are styles, and neither needs a layout rule. Two
declarative style properties replace 32 hand-placed breaks and remove their
brittleness — any edit above a manual break leaves a half-empty page behind. See
the [audit, §6b](reference/reference-thesis-audit.md#6b-page-breaks-are-all-manual-and-they-serve-two-different-purposes).

---

## D10 — Citation style is delegated to CSL, never modelled

**Accepted.**

**Why:** APA 7 is not a list of our rules; it is a CSL style plus a processor,
freely available, correct, and maintained. Modelling citation rules ourselves
means reimplementing CSL, a multi-year project with no upside.

**What remains ours:** the parts of APA 7 that are document layout rather than
citation rendering — caption structure, double spacing, heading level formatting,
and the reference list's 1.27 cm hanging indent. Those live in `base/apa7` as
styles and layout rules.

**Resolved by the approved-thesis audit:** the bibliography style is **APA 7**.
IEEE appears only inside the front-matter "how to cite" table, which is a
faculty template for citing *this* thesis, not the bibliography style. A
citation processor also fixes a defect in the approved document, where each
entry's URL sits in a separate paragraph without the hanging indent.

---

## D11 — Captions are four slots, not one string

**Accepted.**

`Table` and `Figure` carry `label`, `title`, `content` and `note`.

**Why:** APA 7, as actually used in both audited documents, renders a caption as
separate blocks — "Tabla 2" / italic title / the object / "Nota. Adaptado de …".
A single `caption` string cannot express it.

**Also:** placement is a layout rule, not a content property. APA 7 puts label
and title above both tables and figures; other conventions put figure captions
below. Keeping placement in the profile means one IR renders correctly under
either. Baking it in would require a different IR per citation style.

**Concrete style bindings, measured from the approved thesis:**

```
Figura 1                                    XFIGURAS   label  (Arial bold)
Imagen representativa de la sobrerotura.    X1         title  (italic)
[IMAGE]                                     X2         content
Nota: El gráfico resalta…                   X3         note
```

Tables are identical with `XTABLAS` as the label style and the table replacing
the image. The note prefix is **`Nota:`** with a colon. `XFIGURAS`, `XTABLAS`
and `X1` are not present in the thesis proposal — without the approved document,
the caption model would have been bound to the wrong styles.

**And the label style doubles as the index source** — see
[D13](#d13--indexes-are-style-driven-toc-fields-not-outline-levels).

**Note on a common default:** the widely-repeated convention "figures captioned
below, tables captioned above" is Chicago/IEEE, **not** APA. Assuming it would
have been wrong for our primary target. This is the clearest case for deriving
profile defaults from measured documents rather than from intuition.

---

## D12 — Generation is one-way; no DOCX round-trip

**Accepted.**

**Why:** reading an edited DOCX back into the authoring format with fidelity is
disproportionately hard, and the alternative is cheaper: keep editing upstream
in `DocSource` and regenerate. Use case 2 (reformatting existing documents) is
not a counterexample — it is a one-time structure recovery with mandatory human
review, not a lossless round-trip.

**Stated as a constraint** so that nobody promises otherwise to a client.

---

## D13 — Indexes are style-driven TOC fields, not outline levels

**Accepted. Supersedes an earlier decision.**

The engine emits four live `TOC` fields, each driven by a paragraph style:

```
TOC \h \z \t "TITU1;1;TITU2;1;TITU3;1"     → Tabla de Contenido
TOC \h \z \t "XTABLAS;1"                   → Índice de tablas
TOC \h \z \t "XFIGURAS;1"                  → Índice de figuras
TOC \h \z \t "XANEXOS;1"                   → Índice de anexos
```

**Why:** this is measured from the **approved** thesis. An earlier version of
this decision was to add `outlineLvl` to the custom heading styles so that a
standard TOC field could see them. That was wrong in two ways:

1. **Unnecessary** — the `\t` style switch works without outline levels.
2. **Insufficient** — outline levels could never produce the table, figure or
   annex indexes, because those entries are not outline entries at all.

**The consequence that matters:** the caption **label style is the index
source**. Emitting "Tabla 5" with style `XTABLAS` both formats it bold *and*
produces its entry in the Índice de tablas. There is no separate index-building
step. This is why the template defines `XTABLAS`, `XFIGURAS` and `XANEXOS` as
distinct bold styles instead of folding them into `NORMALES`.

**Also measured:** the general index is **flat** — all three heading styles map
to TOC level 1, so every entry renders as `TDC1` with no depth indentation.
`TDC2` and `TDC3` exist in the template but are unused. We reproduce what was
approved rather than what looks better.

Setting `outlineLvl` anyway, purely so Word's navigation pane works, is harmless
and optional.

**Lesson recorded:** the earlier decision was derived from an unapproved draft.
Reading an *approved* document replaced a plausible invention with the
institution's actual accepted practice. Prefer approved documents as normative
sources.

---

## D14 — v1 omits footnotes, endnotes and code blocks. Equation numbering is IN scope

**Accepted, on measurement. Corrects an earlier version of this entry.**

**Out of scope, with strong evidence:** footnotes, endnotes and code blocks are
**zero in all three audited documents**.

**Back in scope:** **equation numbering**. An earlier version of this entry cut
it, based on the thesis proposal, which numbers none of its 163 equations. The
**approved** thesis numbers its equations `(1)` through `(47)`, globally
sequential.

**The good news in the detail:** the approved layout is a **centered paragraph
containing the equation followed by the tag as parenthesised text — no tab, no
right alignment**:

```
                    [ centered equation ]  (12)
```

That is markedly simpler than the classic right-margin-aligned tag, which needs
an invisible table or an OMML-plus-field construction. A `SEQ` field inside a
centered paragraph is sufficient.

**And it is worth doing:** the approved document's manual tags run 1…44, then
`6`, then 45, 46, 47, then `45`, `46` again — 50 tags for 47 numbers, with
duplicates and one out of order.

**Still out:** per-chapter numbering such as "Figura 3.2". All audited documents
number figures, tables and equations **globally**.

**Lesson recorded:** the same lesson as D13. A scope cut taken from a draft was
wrong; the approved document corrected it. Evidence quality matters as much as
evidence quantity.

---

## D15 — The conformance report is a product surface

**Accepted.** See [Validation](08-validation-and-conformance.md).

**Why:** we ship documents that are 90–95% correct, so the recipient needs to
know what is left — the report is their to-do list, not our debug log. Second,
the bottleneck may be *acceptance* rather than production; a report whose
findings are each traceable to a source is an argument, while a document alone
is a claim.

For UNI-FIGMM that source is the reference audit rather than a rulebook page,
since the faculty publishes neither — see
[D24](#d24--the-approved-thesis-is-the-specification).

**Consequence:** it is an output of every build, findings point at a `DocSource`
file and line, and a missing required section produces a document with a visible
placeholder plus a reported error rather than no document at all — because the
report is the feedback channel to the content agent, and a build that produces
nothing teaches nothing. `--strict` gives the fail-hard behaviour for final
submissions.

---

## D16 — Body text is 11pt

**Accepted.** Was provisional; now decided.

**Why:** `Normal` sets Arial and double spacing but declares **no size**, so it
inherits Word's document default of 11pt. Both audited UNI documents do this
identically. Most thesis rulebooks require 12pt — but this faculty publishes
neither a rulebook nor its template, so there is nothing to check against. The
approved document is the best authority available, and it renders at 11pt.

Two documents from the same template inheriting the same default is not
independent evidence of the faculty's *intent*. We are choosing 11pt knowing
that, because:

**The cost of being wrong is bounded, and nothing structural depends on it:**

| What changes if it turns out to be 12pt | Effort |
|---|---|
| `styles.roles.body.size` in `uni-figmm/base` | One value |
| The `body_size` conformance assertion | One value |
| The golden fixture's expected page count | Re-baseline once; expect ~10–15 more pages on a 134-page document |

No code changes, no schema changes, no structural changes. Phase 2's exit
criterion makes this explicit: **flip 11pt to 12pt by editing one value and
watch the suite re-baseline cleanly.** That turns an unresolved question into a
regression test, which is the right way to hold an assumption you cannot yet
verify.

**Lesson recorded:** an assumption whose correction cost is one config value
does not deserve to block a project. The mistake would have been leaving it open
as a blocker rather than deciding it and bounding the downside.

---

## D17 — Profiles are built by extracting them from an approved document

**Accepted. This is now the primary mechanism, not a secondary one.**

UNI-FIGMM publishes neither its template nor a written rulebook, so the approved
thesis *is* the specification. That was forced on us, and it turns out to be the
better path:

> An approved thesis tells you what the institution **accepted**. A rulebook
> tells you what it *says* it requires. When the two differ, the approved
> document is what your user will be judged against.

It is also far easier to obtain — every graduate has one; few have the rulebook.
**The onboarding story becomes: one approved thesis per institution.**

Most of the extraction is deterministic. Style definitions, fonts, sizes,
spacing, margins, page size, section properties, numbering and field
instructions are stored explicitly in OOXML; parsing them beats asking a model.
An LLM is needed only for semantic mapping — deciding that `XFIGURAS` is the
figure label style.

**Three rules the extractor must follow**, each because ignoring it would have
produced a wrong profile:

1. **Extract by statistical mode, never by first value seen.** The document with
   no template had 89% of paragraphs directly formatted, Arial mixed with
   Calibri, and line spacing spread across 0.83, 0.88, 0.94, 0.96, 1.01, 1.15,
   1.49, 1.50 and 1.52. Literal values there learn the noise. Report the spread;
   flag low-agreement properties for a human.
2. **Extract from an approved document, not a draft.** The proposal never used
   `XTABLAS`, `XFIGURAS` or `X1`, so extraction from it would bind the caption
   model to the wrong styles and conclude that equations are unnumbered. Both
   errors were in this design until the approved thesis was audited — see
   [D13](#d13--indexes-are-style-driven-toc-fields-not-outline-levels) and
   [D14](#d14--v1-omits-footnotes-endnotes-and-code-blocks-equation-numbering-is-in-scope).
3. **Prefer two documents from one template.** Where two authors agree on a
   property, it belongs to the **template**, not to one author's direct
   formatting. That is the entire value of the second audited document, and it
   is what the audit's *stable vs. drift* table records.

**Timing:** the profile is written by hand in Phase 0 from the existing audit.
The extractor becomes tooling in Phase 3, when there is a correct profile to
validate it against — running it on the UNI-FIGMM thesis must reproduce the
hand-written profile. Building the tool earlier would mean having no way to tell
whether its output was right.

---

## D18 — No template-filling engine in this architecture

**Accepted.**

Filling placeholders in a prepared DOCX is legitimate for rigid, high-volume,
fixed-layout documents, and it **bypasses this entire pipeline** — no IR, no
layout rules, no style binding.

It is not needed for theses. Recorded so that if it is ever added, it is a
separate and clearly-labelled path rather than the default for content that
could be modelled semantically. Two architectures have a real maintenance cost
and it should be paid knowingly.

---

## D19 — LLM use is bounded by ambiguity

**Accepted.** Table in [Architecture](02-architecture.md#where-the-llm-belongs-and-where-it-does-not).

A model is used where interpretation genuinely requires judgement: writing
content, recovering structure from an unformatted document, mapping extracted
styles to semantic roles, and reading a rulebook when one exists. It is not used
to read a value that is already stored explicitly, to apply a known rule, or —
ever — to generate formatting code per document.

The extraction path makes the boundary concrete: **everything measurable in
OOXML is parsed; only the semantic mapping is inferred.** See
[D17](#d17--profiles-are-built-by-extracting-them-from-an-approved-document).

**Two constraints when a model produces a profile from a rulebook:** output
restricted to a closed, enumerated rule vocabulary the engine can execute, and a
page-and-quote citation attached to every emitted rule. The first stops it
inventing rules that silently do nothing; the second turns an unverifiable
output into a reviewable artefact and lets the conformance report cite the
rulebook.

---

## D20 — Schema distinguishes `chapter` from `top_level_section`

**Accepted.**

Both bind to the same style, `TITU1`. A `chapter` receives a
`Capítulo {roman}.` prefix; a `top_level_section` does not.

**Why:** in the approved thesis, `TITU1` formats numbered chapters
("Capítulo I. Parte introductoria del trabajo") *and* unnumbered top-level
sections (Resumen, Abstract, Introducción, Conclusiones, Recomendaciones,
Referencias bibliográficas, Anexos). A model with only "heading level 1" cannot
express which ones get a prefix.

**Payoff:** the approved thesis is **missing the `Capítulo II.` prefix** on
"Marcos teórico y conceptual", while chapters I, III and IV have theirs — and
it is wrong in the table of contents too. Generating the prefix eliminates that
class of error by construction, and a conformance rule asserts it.

---

## D21 — The profile splits into a shared base plus per-document-kind schemas

**Accepted. This is D8's factorisation, validated rather than assumed.**

```
uni-figmm/base                    page setup · styles · captions · numbering · pagination
│                                 (derived from the approved thesis)
├── uni-figmm/thesis-final@2024       schema: chapters I-IV + closing sections   ← primary
└── uni-figmm/thesis-proposal@2026    schema: chapters I-V ending in schedule/budget/funding
```

**Why:** the two audited documents are different document kinds from the same
faculty sharing an **identical style layer** — every property marked *stable* in
the audit was identical in both. Only the required-section list differs.

This is the first real evidence that the schema/style split is the right seam,
and it arrived from measurement rather than from design taste. It does not
change [D8](#d8--one-profile-file-with-extends-not-four-registries): this is one
`extends` chain, not four registries.

**Note on sourcing.** The base layer is derived from the approved thesis alone
([D24](#d24--the-approved-thesis-is-the-specification)); the proposal
contributes nothing normative to it. The proposal's value here is twofold: it
confirmed that the *stable* properties belong to the template rather than to one
author, and it supplies the second schema — which Phase 2 adds as a
required-chapter list and nothing else, making it the cheapest available test of
this seam.

---

## D22 — ORCID iDs and the "how to cite" tables are out of scope

**Accepted.**

The approved thesis carries two front-matter elements we deliberately do not
build: **ORCID identifiers** with logo images next to the author and advisor on
the cover, and **two "Citar / How to cite" tables** giving the citation for the
thesis itself in IEEE and APA 7 format.

**Why:** all three of the following hold at once, which is what makes it an easy
call:

1. **Highly institution-specific.** Neither would transfer to another
   institution's profile; both would be dead weight in the shared layer.
2. **One-time boilerplate.** They never change across a document's revisions, so
   automating them saves no *repeated* work — which is the only work worth
   automating here.
3. **Under a minute by hand.** They fall naturally into the manual 5% that the
   90–95% target explicitly plans for.

Building them would mean carrying an ORCID logo asset, wiring in a second
citation style purely to render a front-matter table, and implementing a bespoke
two-table layout — for no saving.

**Recorded so their absence reads as a decision, not an oversight.** They are
measured and documented in the
[audit](reference/reference-thesis-audit.md#8-document-structure--a-complete-approved-thesis),
so adding them later is a small, well-specified task rather than a rediscovery.

---

## D23 — We reproduce the flat general index

**Accepted.**

The approved thesis maps all three heading styles to TOC level 1
(`TITU1;1;TITU2;1;TITU3;1`), so every index entry renders as `TDC1` with no
indentation by depth. `TDC2` and `TDC3` are defined in the template but unused.

**Why:** indenting by depth would look better. It would also differ visibly from
the document the faculty accepted, and with no rulebook to appeal to we have no
grounds for the change.

**The distinction that governs this:** an approved document is our specification
for *format*, not for *errors*. The test is **does this depart from the
template's own evident intent?**

- A chapter missing its `Capítulo II.` prefix while three others have theirs is
  an **error** — we fix it ([D20](#d20--schema-distinguishes-chapter-from-top_level_section)).
- A flat table of contents, where the author used neither `TDC2` nor `TDC3`
  across 158 entries, is a consistent **layout choice** — we reproduce it.

Consistency is the signal. One chapter out of four is a slip; 158 entries out of
158 is a decision.

---

## D24 — The approved thesis is the specification

**Accepted. This reframes several earlier entries.**

UNI-FIGMM publishes neither its template nor a written rulebook. The profile is
therefore derived **~100% from one approved thesis**, with a second document from
the same template used only as a stability check.

**Why this is sound:**

- An approved document is evidence of what the faculty **accepted in practice**,
  which is closely related to the standard our users are judged against.
- Where two documents by different authors from one template agree, the property
  belongs to the **template**, not to an author. That check is what the audit's
  *stable vs. drift* table performs, and it is why the second document was worth
  auditing even though it is only a proposal.
- It is far easier to obtain. Every graduate has an approved thesis.

**It is not strictly better than a rulebook.** An earlier version of this entry
implied it was; that overclaimed. A rulebook wins where it is **current** and the
thesis is not, where the rule is a **prohibition**, where the **reviewer
actually checks against it**, or where the approved document contains **tolerated
deviations**. On the last point our own reference thesis is the example: it was
accepted with a missing chapter prefix and duplicate equation numbers, which
proves those were tolerated once, not that they are permitted.

The accurate claim is narrower: **where no rulebook is available, an approved
document is a sufficient and defensible basis. Where both exist and conflict,
that conflict needs a human decision, not an automatic winner.**

**What extraction cannot give us:** prohibition-type rules leave no trace in a
compliant document — "tables may not exceed the text width" is invisible in a
thesis with no oversized tables. We derive those from geometry (text width
follows from the margins) and mark them as **our inference**, not measured fact.
Conformance findings that rest on an inference say so.

**Consequences elsewhere:**

- Conformance findings cite the reference audit, not a rulebook page
  ([D15](#d15--the-conformance-report-is-a-product-surface)).
- [D16](#d16--body-text-is-11pt) (11pt) is decided rather than verified, because
  there is nothing to verify against.
- [D17](#d17--profiles-are-built-by-extracting-them-from-an-approved-document)
  makes extraction the primary mechanism, and the onboarding story becomes *one
  approved thesis per institution*.

---

## D25 — The IR has one declared presentational exception, and it is relative

**Accepted.** Closes a contradiction that stood in three places.

[D3](#d3--three-representations-and-the-ir-is-never-mutated-by-formatting) states
that the `SemanticIR` carries no visual information. Three fields violated it:
`Paragraph.role: unindented`, `Container.kind: landscape`, and `Figure.width`.

**The test: would a reader of a different medium understand the field as a
statement about the content?** It survives if it means the same thing in DOCX,
LaTeX and HTML. It fails if it names a mechanism only one medium has.

| Field | Verdict | Resolution |
|---|---|---|
| `role: unindented` | Violation — describes appearance | Renamed **`standalone`**: the paragraph does not continue the preceding flow. Removing a first-line indent is one medium's way of showing that |
| `kind: landscape` | Violation — pages are a Word/print concept | Renamed **`wide`**: the content needs more width than the text block. The profile decides that means a landscape section in DOCX |
| `Figure.width` | **Declared exception, bounded** | Permitted only as a **fraction of the text block** (`100%`, `50%`) or `natural`. Absolute units are rejected by validation |

**Two of the three were not exceptions at all** — they were correct concepts
wearing presentational names, and renaming them dissolved the problem. That is
usually the case, and it is worth attempting before granting an exception.

`Figure.width` is a genuine exception, granted deliberately. An author does need
to say "this diagram should occupy half the width"; that is authorial intent.
Restricting it to a **relative** value is what keeps it medium-independent: 50%
of the text block means the same thing everywhere, while `8cm` means nothing in
HTML and breaks silently when a profile changes its margins.

**Lesson recorded:** an invariant stated as a slogan gets violated. Stated as a
test, with the exceptions enumerated and a property test enforcing them, it
holds. The violations were introduced by the same design that declared the
invariant.

---

## D26 — Four severities: `fatal` cannot produce, `error` produces a placeholder

**Accepted.** Closes a direct self-contradiction.

An earlier version of
[Validation](08-validation-and-conformance.md#severity-and-build-semantics)
stated in a table that an `error` produced no file, and in the prose immediately
below that the default was to produce a file with placeholders. Both sentences
were defensible; they were describing two different things under one name.

| Severity | Meaning | File? | Exit |
|---|---|---|---|
| `fatal` | The build **cannot** proceed | No | non-zero |
| `error` | A hard requirement is unmet, but a document is still producible | Yes, with a visible placeholder | non-zero |
| `warning` | Produced; a human must decide | Yes | zero |
| `info` | Worth knowing | Yes | zero |

**`fatal` is a capability limit, not a judgement** — an unparseable manifest, a
missing section file, an undecodable asset, a profile failing its own schema. No
policy is involved; there is physically nothing to emit.

**`error` is a conformance judgement and does not stop the build.** A missing
required chapter yields `[MISSING: Capítulo III. …]` in the output, an `error`
finding, and a non-zero exit code.

**Why `error` still produces a file:** the report is an interface to the content
agent, and a build that produces nothing teaches nothing. The **non-zero exit
code** is what keeps this safe — automation that treats exit 0 as "ready to
submit" will not be fooled by a document full of placeholders. `--strict`
promotes every `error` to `fatal` for final submission.

**Lesson recorded:** when a table and its surrounding prose disagree, the usual
cause is one name covering two concepts. The fix is a new name, not a reworded
sentence.

---

## D27 — LibreOffice field refresh is rejected; computed values ship inline

**Accepted, on measurement.** Answers a question this log tracked as open.

Measured on the text-and-math fixture, Pandoc 3.11 and LibreOffice 26.8:

| Property | Ours | After LibreOffice round-trip |
|---|---|---|
| Paragraphs | 25 | 25 |
| OMML equations | 7 | **7 — preserved** |
| Field instructions | 12 | **12 — preserved** |
| Direct paragraph formatting | **0** | **1 — injected** |
| `w:updateFields` flag | **set** | **stripped** |

**The good news is the part we feared most:** LibreOffice preserves every
equation and every field structure. The math and the `SEQ`/`REF` machinery
survive a round-trip intact.

**Two real regressions, both small:** it injects one direct paragraph-formatting
override, which violates
[D7](#d7--zero-direct-formatting-in-the-output), and it strips
`w:updateFields`, which is the flag telling Word to recalculate on open.

`build` therefore **rejects** the refreshed package and keeps the original,
recording a `manual-field-refresh` warning. That is the fallback the design
anticipated, and it works.

**The reframing that matters.** The question was "does refresh degrade the
document?" The more useful answer is that **refresh is not needed yet**. Our
emitter already writes computed field values alongside the instructions, so the
document reads correctly before any refresh. A refresh only buys something a
generator cannot compute itself — and for this sample there is nothing in that
category: `SEQ` and `REF` values are ours to assign.

**When it will matter:** a real table of contents. Page numbers genuinely
cannot be computed without laying out the pages, so the four style-driven index
fields of the full thesis will need either a working refresh or an accepted
"press F9 once" instruction. At that point the two regressions above have to be
handled, not merely detected. Until then, `--refresh` is a net negative and the
default of not using it is correct.

**One check to revisit then:** `update-fields` currently fails whenever the flag
is absent. After a *successful* refresh the flag is legitimately unnecessary,
because the values are already computed. The check is right for our own output
and slightly over-strict for a post-refresh package; it is not urgent, since the
direct-formatting regression rejects the refresh anyway.

---

## Open questions

| # | Question | How it gets answered |
|---|---|---|
| Q2 | Can the content agent hold structure across ~20 calls and ~29,000 words? | One hour: ask it for one section with two figures and a table |
| Q3 | Is the bottleneck production or acceptance? | One conversation with someone who has submitted a thesis |
| Q4 | Do we install real fonts in the render image, or accept metric substitutes? | Phase 1, once page-count sensitivity is measured |
| Q5 | Do we split the profile into four registries? | Phase 3, deliberately ([D8](#d8--one-profile-file-with-extends-not-four-registries)) |
| Q6 | Would a second approved thesis from this faculty disagree on any *stable* property? | Audit one when available; cheap once the extractor exists |

### Answered

| Question | Answer |
|---|---|
| Body font size — 11pt or 12pt? | **11pt** ([D16](#d16--body-text-is-11pt)). Correction cost is one config value |
| Is 134 pages representative for an undergraduate thesis? | **Yes.** Plan ~29,000 words, not ~16,000 |
| Reproduce the flat general index, or indent by depth? | **Reproduce** ([D23](#d23--we-reproduce-the-flat-general-index)) |
| Are ORCID iDs and the how-to-cite tables required? | **Out of scope** ([D22](#d22--orcid-ids-and-the-how-to-cite-tables-are-out-of-scope)) |
| The missing `Capítulo II.` prefix — fix or replicate? | **Fix** ([D20](#d20--schema-distinguishes-chapter-from-top_level_section)) |
| Does the faculty publish its template or a rulebook? | **No.** The approved thesis is the specification ([D24](#d24--the-approved-thesis-is-the-specification)) |
| Is the bibliography style APA 7 or IEEE? | **APA 7**, 1.27 cm hanging indent ([D10](#d10--citation-style-is-delegated-to-csl-never-modelled)) |
| Are equations numbered? | **Yes**, global `(1)`…`(47)` ([D14](#d14--v1-omits-footnotes-endnotes-and-code-blocks-equation-numbering-is-in-scope)) |
| How are the indexes built? | Four style-driven `TOC` fields ([D13](#d13--indexes-are-style-driven-toc-fields-not-outline-levels)) |
| Does LibreOffice's field refresh degrade the DOCX? | **Yes, slightly** — equations and fields survive, but it injects direct formatting and strips `updateFields`. Rejected; refresh is not needed until a real TOC exists ([D27](#d27--libreoffice-field-refresh-is-rejected-computed-values-ship-inline)) |

### Self-corrections from internal review

Four contradictions and four overclaims found by reviewing this documentation
against itself, all now resolved. Recorded because the pattern is more useful
than the individual fixes.

| Problem | Resolution |
|---|---|
| IR forbade visual data but carried `width`, `landscape`, `unindented` | [D25](#d25--the-ir-has-one-declared-presentational-exception-and-it-is-relative) — two renamed, one bounded exception |
| `pageBreakBefore` classified as style, implemented as layout | [D9](#d9--style-layout-and-conformance-are-three-different-things) — reclassified; revealed `keep_with_next` too |
| `error` both blocked and did not block the build | [D26](#d26--four-severities-fatal-cannot-produce-error-produces-a-placeholder) — four severities |
| README cited the 73-page proposal as the reference | Corrected to the approved 134-page thesis |
| "A LaTeX backend is a few days of work" | Unestimated. Claim narrowed to *additive rather than a re-architecture*; the unfinished `docx_style` mapping is named |
| "Any engine code for a second university is a design failure" | Only for *the same capability with different values*. A genuinely new capability is the engine growing as intended |
| "An approved thesis is the better authority than a rulebook" | Narrowed: sufficient where no rulebook exists; a conflict between the two needs a human decision ([D24](#d24--the-approved-thesis-is-the-specification)) |
| "Future backends possible at close to zero cost" | Narrowed to *cost contained in one layer* |

**The pattern in the four contradictions:** each one held a correct principle in
one place and violated it in another, and in three of the four cases the
violation was in a document that *stated* the principle. Written principles do
not enforce themselves. Every one of these is now either enforced by a test
(D25, D7), owned by the resolver rather than the config author (D9), or encoded
in the type system as separate names (D26).
