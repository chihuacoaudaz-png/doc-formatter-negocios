# UNI-FIGMM thesis fixture (text, math, tables, figures)

Working DocSource sample for profile `uni-figmm/thesis@1`: Resumen, Abstract,
complete Chapters I–II from the approved thesis, **skeleton** Chapters III–IV
(schema completeness), plus an optional supplemental math chapter for
equation regression.

Level-4/5 headings (`####` / `#####`) use a deeper tab stop, first-line
indent, and **run-in** body text on the same line as the title, matching the
approved thesis. Bullet lists, `:::table`, and `:::figure` (sample assets from
the thesis Word media) are supported. Ordered and nested lists remain
unsupported.

## Provenance

Source: `resources/TESIS PARA TURITIN.docx` (local, untracked).
SHA-256: `c380345d4fe88fe968db6ad6ce8305d9191ce5be3fd4978736be4e2e5cce2635`.

Paragraph locations below are one-based indices of direct `w:p` children of
`w:body` in `word/document.xml`, including empty paragraphs and TOC paragraphs.
They are stable for the source hash above and do not depend on pagination.

| Sample passage | Original location |
|---|---|
| Resumen | Heading 59; complete prose 60–62; keywords 63 |
| Abstract | Heading 66; complete prose 67–69; keywords 70 |
| Chapter I heading | Paragraph 248; manual chapter prefix removed |
| 1.1–1.6 | Headings and prose 249–305; empty 306 omitted |
| Chapter II | Marcos teórico y conceptual; `#####` + bullet lists |

Prose is preserved, with outer whitespace trimmed. Literal currency `$`
is escaped as `\$` so the math tokenizer does not consume it. Heading numbers and the
`Capítulo I.` prefix are removed because numbering belongs to the engine.
The profile inserts a tab between the number and the title, matching the
approved thesis (`w:tab`, default stop 1.25 cm).
"Variable dependiente/independiente" labels are bold in the source (`w:b`);
the sample keeps that as Markdown strong. The trailing period on "Justificación." is dropped. The Abstract keyword line
in the source ends with `PythonKeywords`; the sample stores `Python` in
`meta.keywords_en` and lets the profile render `Keywords — …`.

`05-pruebas-matematicas.md` is entirely supplemental test content. Its equations
are synthetic and must not be attributed to the thesis author. Do **not** add
that chapter to a real thesis DocSource.

## Profile and expectations

Use `profiles/uni-figmm/thesis@1.yaml` (`id: uni-figmm/thesis@1`). Page and text
styles are derived from `docs/reference/uni-figmm-profile.md`. FIGMM-specific
strings (`Capítulo`, `Palabras clave —`, Word style names) live in that
profile, not in `src/`.

The profile requires the two abstracts and body chapters I–IV with the exact
`#` titles in the schema. Resumen/Abstract body paragraphs bind to
`NORMALES`. Body chapter paragraphs bind to `PARRAFOS`. Numbered headings
restart from the body chapter index; the optional math chapter becomes
Capítulo V in this fixture only.

Agent brief for producing similar folders:
[`dialect/docsource.md`](../../dialect/docsource.md) +
[`playbooks/uni-figmm-thesis/PLAYBOOK.md`](../../playbooks/uni-figmm-thesis/PLAYBOOK.md).

`expected.json` records intended structural counts and equation-reference order.
The integration tests check these acceptance data against the parser and the
generated package. Holmberg displays in Chapter II use `:::equation` so the
engine assigns `(1)`…; in this partial fixture, profundidad/avance become
`(3)`/`(4)` as in the approved thesis excerpt. The supplemental math chapter
continues the global sequence. One unnumbered `$$…$$` remains only in that
math chapter.
