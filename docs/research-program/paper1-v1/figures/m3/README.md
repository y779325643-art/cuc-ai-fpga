# M3 Method Figure Drafts

Status: IEEE/ACM-style explanatory drafts; awaiting user final approval

Backend: Python / matplotlib

Final width: 182 mm (IEEE two-column width)

Primary editable format: SVG (`svg.fonttype = none`)

## Figure contract

- Core conclusion: SR2FPGA separates requirement disposition, matched method
  treatments, public repair, immutable terminal selection and one-shot hidden
  evaluation without implying a method effect.
- Archetype: schematic-led composite split across one overview and two focused
  module figures.
- Evidence: v1.7 freeze, current method adapters, terminal selection,
  development hidden authority, artifact/cost contracts and M2 claim registry.
- Statistics/source data: none; these are explanatory, not result figures.
- Reviewer risk: do not imply G3/G4b closure, official VPP, hidden-feedback
  access, skeleton-only effect or general FPGA physical success.

## Outputs

### Figure 2

- `figure2_sr2fpga_overview.svg`
- `figure2_sr2fpga_overview.pdf`
- `figure2_sr2fpga_overview.png`
- `figure2_sr2fpga_overview.tiff`

**Fig. 2 | SR2FPGA matched project-generation and evaluator-separation
framework.** The independent RQ0 requirement-boundary audit classifies
requirements before project generation, while the ready-only VPP population
enters the matched M0-M5 method ladder. Public evaluation may drive bounded
repair only for M1 and M5. A declared terminal candidate is sealed before a
one-shot evaluator-private hidden final. Only an opaque reference and
reducer-bounded status cross the hidden boundary. Solid borders denote tested
development surfaces; the dashed orange gate denotes official G3/G4b authority
that remains incomplete. The figure depicts protocol and implementation
structure, not comparative results.

### Figure 3

- `figure3_matched_treatment_design.svg`
- `figure3_matched_treatment_design.pdf`
- `figure3_matched_treatment_design.png`
- `figure3_matched_treatment_design.tiff`

**Fig. 3 | Matched M0-M5 treatment design.** Shared immutable prerequisites
bind M0/M1 to the same Direct initial project (`S_D`), M3/M4/M5 to the same
generated System-HIS (`S_H`), and M4/M5 to the same skeleton-derived initial
project (`S_P`). The v1.7 RQ1 primary Holm family contains M4-M3 and M4-M0;
M3-M2 is a mandatory secondary representation-bundle estimate. The separate
RQ2 confirmatory family contains M5-M4 and the paired repair-policy probe.
Every block records actual campaign, standalone end-to-end and post-checkpoint
incremental cost. No comparison result is shown.

### Figure 4

- `figure4_evaluator_authority.svg`
- `figure4_evaluator_authority.pdf`
- `figure4_evaluator_authority.png`
- `figure4_evaluator_authority.tiff`

**Fig. 4 | Evaluator authority and immutable evidence lineage.** Generated
attempts cross into an evaluator-owned public channel that returns only public,
sanitized diagnosis to eligible M1/M5 repair. Terminal selection precedes an
exact content-bound terminal public rerun and consume-once hidden execution in
a physically separate evaluator store. Raw hidden records remain private;
reducers expose only bounded `pass`, `fail` or `not_run` status to the episode
ledger. The official hidden/VPP producer and G4b authorization gate remain
incomplete.

## Source and QA

- Source: `render_m3_method_figures.py`
- Static source validator: 14 pass, 0 warn, 0 fail
- Visual QA: two iterations; no remaining text overlap or clipped boxes in PNG
  previews at final aspect ratio
- SVG: editable text retained as text nodes
- Export: SVG, PDF, 300 dpi PNG and 600 dpi TIFF
- Data exclusion/simulation: not applicable; no quantitative data used

The files are drafts. Do not insert them into the manuscript or mark them final
until the user approves the rendered figures.

## Accessibility descriptions

### Figure 2 description

Two separate horizontal flows are shown. The upper flow routes requirement facts
through a requirement-envelope decision to either a clarification/capability stop
or a ready state. The lower flow sends ready requirements through a matched M0-M5
ladder, candidate project generation, public evaluation, terminal sealing and a
one-shot private hidden evaluator. Public and hidden outcomes feed an immutable
evidence plane, while a dashed orange box states that official G3/G4b authority is
incomplete.

### Figure 3 description

Three shared prerequisites on the left feed six method conditions in the center.
`S_D` is shared by M0/M1, `S_H` by M3/M4/M5, and `S_P` by M4/M5. The right column
lists the v1.7 RQ1 primary Holm family, mandatory secondary contrast and RQ2 Holm
family. A bottom box lists the three cost views.

### Figure 4 description

Three vertical authority zones separate the candidate/method side, public evaluator
and hidden evaluator. Public diagnosis can return only to M1/M5 repair. Terminal
selection precedes a content-bound public rerun and consume-once hidden evaluation.
The hidden evaluator emits an opaque reference to a reducer-only sanitized status;
a red stop marker denotes no hidden feedback. A dashed orange box marks incomplete
official hidden/VPP and G4b authority.
