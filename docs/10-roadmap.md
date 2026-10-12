# 10 — Roadmap

Phases are ordered by risk, not by architectural tidiness. Each has an exit
criterion that can be checked, not a feeling of completeness.

The approved 134-page thesis remains the reference for UNI-FIGMM formatting
and the eventual full-document acceptance test. **The first implementation uses
Resumen, Abstract, complete Chapter I and a supplemental math chapter. Images,
cover and indexes are deferred.**
The full thesis is not a prerequisite for starting or completing the first
small end-to-end test.

---

## Phase 0 — A small DocSource sample from the approved thesis

Two deliverables, **no engine code**.

**a) A minimal profile for the sample.** Transcribe the relevant measurements
from [UNI-FIGMM Profile](reference/uni-figmm-profile.md) into a concrete YAML
profile: page setup, body and heading styles, and equation numbering. Give the
sample profile a distinct test identity and require only the selected sections;
it must not claim that a partial document satisfies the full thesis schema.
Inheritance support and the complete institutional profile can wait.

**b) Selected sections in `DocSource`.** Choose two or three short sections from
the approved thesis that exercise headings, subheadings and ordinary paragraphs.
Create `document.yaml` and `sections/*.md`, with a fixture README recording the
original section titles and source locations. Retain bibliography entries if
selected text contains citations; do not silently remove citations.

Include a small equation set:

- Inline math (`$…$`), including subscripts and superscripts.
- An unnumbered display equation (`$$…$$`).
- At least two numbered equations (`:::equation {#eq:…}`), including a fraction
  and a more complex expression such as a sum or a root.
- Cross-references to those equations from the prose.

Reuse equations from the thesis where practical. Additional equations may be
added specifically for testing; identify them in a separate test section and in
the fixture README so they cannot be mistaken for original thesis content.
Authors supply stable IDs, never manually assigned equation numbers.

**Not required for this sample:** images, asset extraction, tables, a cover,
indexes, landscape annexes, or transcription of the remaining thesis. Select
self-contained passages; document any omitted material or dependencies. If
citations are retained, resolve their bibliography keys in the sample.

**Exit criterion:** the sample and its minimal profile exist as real files;
each selected passage is traceable to the thesis; added test content is clearly
identified; all equation IDs and references are consistent; and the sample uses
no `raw` blocks. Record the expected equation counts by kind and reference
targets for later assertions. A complete thesis and a 134-page output are not
required.

**Risk this retires:** ambiguity in the authoring contract for text and math,
before expanding the fixture or building the engine around it.

---

## Phase 1 — Render the small sample end to end

Build `DocSource → SemanticIR → LayoutPlan → DOCX` incrementally against the
Phase 0 sample.

### 1a — Load, parse and validate

**Implemented for the current sample, including authored frontmatter.** The CLI,
supported subset and dependency choices are documented in
[Implementation Stack](12-implementation-stack.md). Citation support remains
pending; cited passages are rejected explicitly until that capability is added.


- Read the manifest, authored frontmatter files and selected Markdown files.
- Parse chapters, top-level sections, paragraphs, inline math, display equations and cross-references.
- Validate the sample schema, supported block vocabulary, unique IDs and
  reference targets, with errors pointing to source files and lines.
- Preserve citations and validate bibliography keys when present in the sample.
- Produce inspectable `SemanticIR` and a reference map.

**Exit criterion:** the sample parses with the expected structure and equation
counts. Small invalid variants detect a duplicate equation ID, an unresolved
reference and an unknown block, each with an actionable source location.

### 1b — Emit an editable Word document

**Implemented for the current sample.** `doc-formatter build`
produces the DOCX, an optional PDF preview and a conformance report. Citation
rendering is still pending, in step with 1a.

- Implement only the profile styles and layout capabilities used by the sample
  (`prefix_heading`, `number_headings`, `append_paragraph`, `bind_role`,
  equation `number_labels`).
- Build `reference.docx` from those styles and apply the custom-style mapping.
- Render text and equations through Pandoc, producing editable OMML math.
- Insert live `SEQ` equation labels and `REF` cross-references through OOXML
  post-processing. Inline and unnumbered display math do not advance the sequence.
- Preserve and render citations if the selected passages contain them.
- Produce a basic conformance report for the supported sample checks.
- Evaluate field refresh with headless LibreOffice on this small document; if
  it degrades fields or math, document the fallback requiring refresh in Word.

**Exit criterion:** the sample opens in Word with the expected headings and
named styles, editable math, sequential equation labels and working reference
fields. Insert a numbered equation between existing ones and refresh fields:
subsequent numbers and cross-references must update. Also verify that regeneration
from the changed source produces the expected sequence. Review the rendered math
visually and check that the conformance report matches any remaining limitations.
There is no fixed page-count target for this first sample.

**Risk this retires:** that the backend cannot preserve editable equations and
live numbering in an otherwise simple document. Images and full-thesis layout
remain outside this milestone.

---

## Phase 1c — Expand coverage towards the full thesis, after the sample works

This is deferred work. Authored abstracts and heading numbering already landed
in the small sample; the items below are still outstanding. Add small fixtures
for each capability before combining them into the complete reference thesis:

- Tables and their captions, numbering and references.
- Cover, the four style-driven indexes and page-numbering regions.
- Landscape annexes and section boundaries.
- Images, asset resolution, sizing, captions and figure references.
- The remaining sections, bibliography and equations of the approved thesis.

Complete the institutional profile as coverage grows. Keep the original small
sample as a fast regression test. ORCID identifiers and the “how to cite” tables
remain assigned to the manual remainder under
[D22](11-decision-log.md#d22--orcid-ids-and-the-how-to-cite-tables-are-out-of-scope).

**Exit criterion:** the complete fixture exercises the audited document's
capabilities: all equations and assets accounted for, tables and figures with
live labels, four populated indexes, correct pagination and landscape annexes.
Reconcile the audited equation tags with the transcribed equations explicitly;
do not assume that the count of display OMML objects equals the count of
numbered equations. Check the full output against the existing **134 pages ±3**
target and investigate differences caused by deliberate corrections or omitted
boilerplate before establishing the reviewed baseline.

Only this expanded milestone claims full-reference coverage. Field-refresh
compatibility with all four indexes must be checked here even if the small
sample passed.

---

## Phase 2 — Make the profile real configuration

Phase 1 is allowed to cheat wherever cheating is faster. Phase 2 removes the
cheating.

- Formalise the three rule kinds — style, layout, conformance — with a declared
  execution order and conflict detection
- `extends` inheritance, with `base/apa7` and `uni-figmm/base` factored out
- Add `thesis-proposal` as a second document kind — a different
  required-chapter list and nothing else. Cheap, and it is the first real test of
  the schema/style seam without needing a second institution
- Full conformance report, findings traceable to the reference audit
- The golden-file test harness, DOCX normalisation, page-count assertions,
  idempotency tests, and the IR-invariant property test

**Exit criterion:** every value in the profile comes from configuration; the
test suite runs in continuous integration; changing a style in the profile
changes the output with no code edit. The concrete test: **switch the body font
from 11pt to 12pt by editing one value**, and watch the page count move and the
suite re-baseline cleanly. That is the open question from
[D16](11-decision-log.md#d16--body-text-is-11pt) turned into a regression test.

---

## Phase 3 — The second institution

The only real test of whether the factorisation works.

Add a second profile for a different university, and build the **style
extractor** that produces it.

This is where extraction stops being a manual audit and becomes tooling:

```
approved-thesis.docx → OOXML parse (deterministic) → measurements
                     → semantic mapping (LLM) → human review → profile.yaml
```

The reason it belongs here rather than earlier is that we now know what a
correct profile looks like, so the extractor has a target to be validated
against: **run it on the UNI-FIGMM thesis and it must reproduce the
hand-written profile.** Building it before Phase 0 would have meant building a
tool with no way to tell whether its output was right.

Everything that turns out to be shared moves into a base profile.

**On what counts as a failure here.** An earlier version of this roadmap said
any engine code needed for a second institution was a design failure. That is
too absolute, and it contradicts our own principle that **code grows by
capability, not by document type**. Two cases have to be separated:

| New code needed for | Verdict |
|---|---|
| A genuinely new **capability** — per-chapter numbering ("Figura 3.2"), footnotes, a signature block | **Expected and correct.** Add it once; every profile can then use it |
| The **same capability with different values** — a different font, margin, caption order, chapter list | **A design failure.** This is what configuration is for |

Only the second kind gets recorded as a failure in the
[Decision Log](11-decision-log.md). The first is the engine growing as intended,
and the measure of success is that the capability lands in the shared core
rather than in an institution-specific branch.

This also settles the product story for onboarding: **one approved thesis per
institution**, which is far easier to obtain than a rulebook — every graduate
has one, and faculties frequently publish neither.

**This is also the moment to decide whether to split the single profile file
into separate schema, style, policy and profile registries.** Not before. By
this point we will know where the seams actually are rather than guessing at
them.

**Exit criterion:** the second profile needs **no engine code for anything the
first profile already does**; any new code implements a named new capability in
the shared core; the extractor reproduces the hand-written UNI-FIGMM profile;
and the time it took is recorded. That number is the success metric from
[Goals and Scope](01-goals-and-scope.md#success-metrics).

---

## Phase 4 — The reformatting front end

The funded near-term work: documents whose content exists but whose formatting
does not.

```
unformatted.docx → extract → detect structure → DocSource
                                    ↓
                       ┌────────────────────────────┐
                       │  HUMAN REVIEWS THE OUTLINE │
                       └────────────────────────────┘
                                    ↓
                          Phase 1-3 pipeline
```

The human review step is part of the deliverable, not a workaround. Structure
detection will confuse a bold paragraph with a heading; correcting three lines
of an outline is far cheaper than correcting forty pages of output.

**Exit criterion:** a real unformatted client document is reformatted
end-to-end, and the person-hours are compared against doing it by hand. That
comparison is the business case.

---

## Phase 5 — Additional backends, on demand

LaTeX and HTML. **Do not build these until something needs them.** The
architecture keeps them cheap; building them early buys nothing and adds surface
to maintain.

When one is needed, the work is a `LayoutPlan` emitter plus a second target for
the style compiler. If it turns out to be more than that, the `SemanticIR`
invariant was violated somewhere and the property test from
[Testing Strategy](09-testing-strategy.md) should have caught it.

---

## Phase 6 — Visual validation

Geometric checks first — bounding boxes against the text area, orphaned
headings, captions separated from their objects. These are deterministic and
need no model.

Perceptual checks with a vision model afterwards, if the geometric ones prove
insufficient.

---

## Sequencing rationale

| Phase | Retires which risk |
|---|---|
| 0 | The text and equation authoring contract is ambiguous |
| 1a–1b | Parsing, editable math or live equation references fail on a small sample |
| 1c | The backend cannot handle the full thesis and its remaining capabilities |
| 2 | The engine is not actually configurable |
| 3 | The factorisation does not generalise; extraction cannot be automated |
| 4 | The second revenue stream does not fit the architecture |
| 5–6 | — (capability expansion, no architectural risk) |

Phases 0 and 1a–1b establish the first working text-and-equation path. Phase 1c
tests full-document coverage. Phase 3 tests whether the architecture generalises
to another institution.

## Two things worth testing in parallel, cheaply

Neither blocks the roadmap, and each is a hypothesis that could change
priorities if it turns out differently than assumed.

**Can the content agent actually hold structure over 150 pages?** Writing prose
is easy for a model; maintaining consistent structure, asset numbering and
citation keys across ~20 calls is not. **Cost to test: one hour.** Ask it for a
short section containing inline math, two numbered equations and cross-references
in the `DocSource` format, and check whether it respects the vocabulary. This
checks local correctness only; test sustained multi-section consistency later. If it cannot, the handoff format
needs to be even simpler, and we want to know that before Phase 1.

**Is the real bottleneck producing the document, or getting it accepted?** If
advisors return theses three or more times for formatting alone, then the
conformance report with rulebook citations is the product and its priority
should rise above parts of Phase 2. **Cost to test: one conversation** with
someone who has been through the process.

There is now a data point worth weighing here: the approved thesis was accepted
carrying a missing chapter prefix, duplicated equation numbers, two mislabelled
annexes, a page number typed into the body as a chapter title, and three fonts
against a one-font template. **Formatting rigour is evidently not what gates
approval at this faculty**, which argues that the conformance report's value is
in saving the author's time rather than in clearing a reviewer's bar. Worth
confirming before over-investing in it.
