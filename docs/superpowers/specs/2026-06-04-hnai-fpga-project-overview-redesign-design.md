# HNAI-FPGA Project Overview PPT Redesign Design

## Decision

Use approach A: keep the current 37-slide deep technical report and redesign each slide for readability.

## Source Deck

- Source PPTX: `outputs/project-overview/HNAI-FPGA_项目讲解.pptx`
- Rendered audit: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/template-inspect/contact-sheet.png`
- Output PPTX: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/output/HNAI-FPGA_项目讲解_清晰重排版.pptx`

## Audience And Use

The deck is for a formal HNAI-FPGA project explanation. It should preserve technical depth while making the material readable from a projector or shared screen.

## Design Goals

- Preserve all major chapters and the 37-slide coverage.
- Replace small dense prose with one claim title, one main proof object, and concise support notes.
- Keep the existing deep-blue academic technology identity, but reduce repeated title-bar monotony.
- Improve table, diagram, and code readability by enlarging text and simplifying visual grouping.
- Keep the deck editable in PowerPoint.

## Slide Grammar

- Slide size: 16:9, 1280 x 720 design surface.
- Backgrounds: dark ink chapter/cover slides; light technical canvas for content slides.
- Typography: Chinese sans-serif first, with fallback to system sans-serif; code uses monospace.
- Title system: each content slide uses a short kicker and a claim-style title.
- Body text: avoid paragraph blocks. Use 3-5 bullets or labeled callouts.
- Tables: cap visible rows per slide where possible; use larger header and alternating rows.
- Diagrams: show fewer but larger nodes, direct labels, and clear left-to-right reading order.
- Code: show only representative snippets or structured pseudo-code; never use code as dense decoration.

## High-Risk Slides

The audit identified these as priority pages:

- Slide 03: technical evolution overview has too many small stage cards.
- Slide 10: overall architecture is crowded and has many tiny labels.
- Slide 20: EDA feedback example mixes code, table, and diagnosis logic.
- Slide 25: tool module list table is too dense.
- Slide 37: team task allocation table is too small for presentation use.

## Output Requirements

- Produce a new PPTX only; leave the original PPTX unchanged.
- Render PNG previews for all slides and a contact sheet.
- Verify that the final deck renders without blank slides.
- Verify that priority slides have visibly larger text and cleaner hierarchy.

## Scope Boundaries

- Do not rewrite the research content or invent new technical claims.
- Do not add external logos or unverifiable identity assets.
- Do not remove chapters or compress the 37-slide structure.
