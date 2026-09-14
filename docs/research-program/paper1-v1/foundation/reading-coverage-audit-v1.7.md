# Paper-1 v1.7 Reading Coverage Audit

Status: active M2 reading-coverage ledger

Updated: 2026-08-29

## 1. Scope

Reviewed material:

- `D:\Obsidian Vault\博士开题\硬件代码生成\文献\阅读总结.md`;
- 64 Markdown files under `文献\文献笔记`;
- PDFs and claim chains registered in
  [`canonical-citation-registry.md`](canonical-citation-registry.md);
- three primary PDFs re-read in the current M2 strengthening sequence.

This audit measures evidence coverage. It does not treat a note saying
“精读完成” as proof that the source PDF was read or that every numerical claim
was verified.

## 2. Summary document review

`阅读总结.md` was read completely in this audit. It is a useful historical map
of the broader doctoral/TCAD program, but it is not a current Paper-1 v1.7
literature authority.

### Useful retained content

- broad taxonomy of module generation, repair, IR, FPGA frameworks, DSE and
  physical evidence;
- early identification of VerilogEval, RTLLM, RTLFixer, AutoChip, CPPL,
  FIRRTL, RTL-Repo, CktEvo, ResBench and related lines;
- repeated distinction between module-level RTL and project-level artifacts;
- recognition that structure, oracle depth and physical evidence must be
  compared separately.

### Historical or unsafe content

| Location/topic | Problem | Current v1.7 disposition |
|---|---|---|
| Training trajectories and a unified trained SR2FPGA model | Described as a Paper-1 differentiator | Training is outside Paper-1; trajectories are audit/cost evidence only |
| GA/NSGA-II, QoR predictor and Architecture-IR search | Treated as core method lines | Outside minimum Paper-1 M0-M5; retain only as doctoral/future context |
| L5 board validation and general physical closure | Presented as a target differentiator | No current L5 pass; RQ4 is bounded OpenXC7 L4 characterization |
| “all benchmarks stop at simulation” or “all work is single-module/ASIC” | Field-wide categorical language | Replace with named-work, named-endpoint statements from the registry |
| “project-level” as the main novelty boundary | Superseded by RTL-Repo/HORIZON/Phoenix/CktEvo and other prior art | Use matched materialization and evaluator-separation questions |
| System-HIS as a novel front-end IR by itself | Too broad after CPPL/HINT/ChatCPU/AGON and compiler-IR ancestry | Use requirement/project contract and test its value empirically |
| “all pending items fully read” | Not supported by stable page-level records | Use the coverage classes below |

## 3. Note inventory audit

Automated inspection of the 64 Markdown notes found:

| Check | Count | Interpretation |
|---|---:|---|
| Total notes | 64 | Includes status reports and thematic notes, not only paper notes |
| YAML frontmatter | 61 | Useful identity metadata, not claim verification |
| Claims complete/full reading | 48 | Self-reported status only |
| Contains page/page-number anchors | 3 | Most notes cannot directly support page-level citation |
| Contains DOI or arXiv identifier | 35 | Identity coverage is incomplete |
| Uses `已核实/待核实/AI推断` | 1 | Historical notes predate the current evidence-label contract |
| Mentions WebSearch/search summaries | 9 | Discovery route must not be treated as primary-source proof |
| Filename-matched PDF found | 42 | Under-counts arXiv-number filenames but shows path mapping is incomplete |
| Reuses L0-L5 terminology | 53 | Strong evidence of project-oriented template reuse |
| Reuses “tool-verified trajectory” framing | 39 | Relationship-to-SR2FPGA prose is not necessarily a source-paper fact |

Therefore the 64-note collection is a research aid, not a 64-paper claim-ready
corpus.

## 4. Reading coverage classes

| Class | Definition | Current count | Allowed use |
|---|---|---:|---|
| `A claim-ready` | Full local reader/card/source-map/PDF-hash chain | 27 | Evidence-card-bounded claims |
| `B source-verified` | Primary PDF re-read with fixed hash and page-bounded claims | 3 | Claims listed in supplemental evidence only |
| `C historical-note-supported` | Note and often PDF exist, but no current claim chain or page audit | not frozen as a paper count | Discovery, prioritization and provisional interpretation |
| `D official-primary-page verified` | Current arXiv abstract/full HTML checked; no local PDF hash | 4 | Version-bounded claims in external primary-source evidence |
| `E discovery-only` | Mentioned in summary/note/search output without canonical identity chain | not frozen | Search lead only |

The three Class B works are HINT, RTLCoder and CVDP. Their evidence is in
[`supplemental-source-verified-evidence.md`](supplemental-source-verified-evidence.md).

## 5. High-priority coverage for Paper-1

### Current core with claim-ready chains

- Module benchmark: `verilogeval`, `rtllm`;
- Public repair: `rtlfixer`, `autochip`, `verilogcoder`;
- Structured representation/IR: `cppl`, `firrtl`, `formalrtl`, `chatcpu`,
  `agon`, `representation-bottleneck`;
- Repository/project boundary: `rtl-repo`, `phoenix-bench`, `cktevo`,
  `horizon`, `archxbench`;
- FPGA/physical boundary: `resbench`, `chip-chat`.

### Source-verified additions

- `hint`: closest executable-intent route comparator;
- `rtlcoder`: trained module-generation model baseline;
- `cvdp`: broad design/verification benchmark with explicit coverage limits.

### Remaining gaps

- `realbench`, `hwebench`, `closerbench`, `chipverilog`: official primary pages
  checked; local PDF/readers remain absent;
- OpenLLM-RTL, ChipBench, CIRCT and Spec-Driven Hardware Evolution: named in
  current/historical prose but not in the canonical claim chain;
- final-date incremental search remains unexecuted.

## 6. Use rules

1. Do not write “we read all PDFs” or “all notes are verified.”
2. Do not promote a historical note claim without returning to its registered
   evidence card or source PDF.
3. Treat all L0-L5, training, GA, QoR predictor and unified-model language in
   historical notes as project commentary unless the cited paper itself owns
   that claim.
4. Use the current v1.7 summary, not `阅读总结.md`, for Paper-1 positioning.
5. Preserve the historical notes unchanged.
