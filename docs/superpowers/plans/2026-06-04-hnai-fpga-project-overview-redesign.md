# HNAI-FPGA Project Overview Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clear, editable 37-slide redesign of `HNAI-FPGA_项目讲解.pptx` without overwriting the original.

**Architecture:** Use the existing project overview Markdown and audited source PPT as content sources. Generate a new editable deck from structured slide data, render every slide to PNG, and inspect the contact sheet for readability issues.

**Tech Stack:** Artifact-tool presentation JSX, bundled Node.js runtime, bundled Python for contact sheet generation, local rendered source previews.

---

### Task 1: Prepare Content And Design System

**Files:**
- Read: `outputs/project-overview/HNAI-FPGA_项目介绍.md`
- Read: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/template-inspect/contact-sheet.png`
- Create: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/profile-plan.txt`
- Create: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/claim-spine.txt`
- Create: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/design-system.txt`

- [ ] **Step 1: Write profile plan**

Record task mode `create`, profile `engineering-platform`, source deck as content source, and the readability gates from the spec.

- [ ] **Step 2: Write claim spine**

List 37 slides with short claim titles and proof object types. Preserve the original chapter structure.

- [ ] **Step 3: Write design system**

Define slide size, color palette, typography, title grammar, table grammar, diagram grammar, and verification thresholds.

### Task 2: Generate Editable Slide Modules

**Files:**
- Create: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/slides/project_deck_data.mjs`
- Create: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/slides/slide-01.mjs` through `slide-37.mjs`
- Create: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/slides/render_helpers.mjs`

- [ ] **Step 1: Build reusable helpers**

Create helpers for cover slides, section dividers, content slides, flow diagrams, comparison tables, roadmap rows, and code snippets.

- [ ] **Step 2: Write slide data**

Convert the existing deck into structured slide data: kicker, title, subtitle, body bullets, proof object type, and footer.

- [ ] **Step 3: Write slide modules**

Each `slide-XX.mjs` imports the helpers and slide data, exports `slideXX`, and adds exactly one editable slide.

### Task 3: Render And Verify

**Files:**
- Output: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/output/HNAI-FPGA_项目讲解_清晰重排版.pptx`
- Output: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/preview/slide-01.png` through `slide-37.png`
- Output: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/preview/contact-sheet.png`
- Output: `outputs/manual-20260604-project-overview-redesign/presentations/project-overview-redesign/qa/readability-notes.txt`

- [ ] **Step 1: Build deck**

Run the Presentations build script with `--slide-count 37` and output the final PPTX plus previews.

- [ ] **Step 2: Verify priority slides**

Inspect slides 03, 10, 20, 25, and 37 in the preview set and record readability notes.

- [ ] **Step 3: Iterate**

Adjust slide data or helper layout when text is visibly cramped, misaligned, or too small in the rendered preview.

- [ ] **Step 4: Final check**

Confirm the final PPTX exists, has 37 slides, and the contact sheet shows nonblank slides with varied layout rhythm.
