# Paper-1 v1.7 Literature Search Plan and Execution Ledger

Status: active M2 search ledger

Updated: 2026-08-29

Rule: planned searches and executed searches are recorded separately.

## 1. Search plan

The following table records intended searches. A row marked `待执行` is not
evidence that the database was searched.

| Plan ID | Platform | Query family | Intended window | Required filters/fields | Status |
|---|---|---|---|---|---|
| `PLAN-SCOPUS-01` | Scopus | LLM/agent + RTL/HDL + project/repository/FPGA | 2022-01-01 to execution date | title/abstract/keywords; English; article/conference/preprint identity reconciliation | 待执行 |
| `PLAN-WOS-01` | Web of Science | hardware code generation + structured representation + verification | 2022-01-01 to execution date | topic field; document type; cited-reference follow-up | 待执行 |
| `PLAN-IEEE-01` | IEEE Xplore | RTL generation/repair, hardware intent, FPGA physical evidence | 2022-01-01 to execution date | metadata, publication status, DOI, venue | 待执行 |
| `PLAN-ACM-01` | ACM Digital Library | Verilog/RTL agent, repository repair, EDA feedback | 2022-01-01 to execution date | title/abstract; proceedings/journal; DOI | 待执行 |
| `PLAN-ARXIV-01` | arXiv | newest CS.AR/CS.AI/CS.SE hardware-agent neighbors | 2026-07-18 to execution date | exact arXiv version, authors, update date | 待执行 |
| `PLAN-GSCHOLAR-01` | Google Scholar | exact-title, cited-by and related-article follow-up for closest works | 2026-07-18 to execution date | exact title, year sort; T3 source warning | 待执行 |
| `PLAN-CNKI-01` | CNKI | 中文 FPGA/Verilog 代码生成与智能 EDA | 2022-01-01 to execution date | 主题/篇名/关键词；学位论文与期刊分开 | 待执行 |

Detailed historical query strings remain in
`D:\Obsidian Vault\博士开题\硬件代码生成\日志\26.08.27 文献综述.md`.
They are plan inputs, not execution evidence.

### Inclusion contract

Include a work when it materially informs at least one of:

1. requirement/specification to RTL/project generation;
2. multi-file/project/repository task unit;
3. structured/typed/executable representation;
4. tool-feedback repair and evaluator privilege;
5. hidden/held-out verification, leakage or reward hacking;
6. FPGA resource, timing, P&R or target-profile evidence;
7. artifact, license, budget and reproducibility boundaries.

Exclude or separate analog/PCB-only work, reverse RTL-to-specification tasks,
HLS/DSE-only work without a relevant boundary role, duplicate versions, and
LLM-judge-only correctness claims without executable evidence.

## 2. Executed search ledger

Only rows with actual returned records and a retained log appear here.

| Run ID | Actual source | Execution date | Query IDs | Returned/screened | Deduplication | Outcome | Evidence status |
|---|---|---|---|---|---|---|---|
| `RUN-OA-20260716-01` | OpenAlex fallback | 2026-07-16 | Q1–Q6 | 20 records inspected per broad family; stable database-wide totals unavailable | DOI → arXiv ID → normalized title → author/year | broad discovery; refined exact-title searches required | 已核实 |
| `RUN-REFINE-20260716-17` | OpenAlex plus exact-title arXiv/Crossref/IEEE/ACM/AAAI and author-artifact checks | 2026-07-16 to 2026-07-17 | R1–R4 | Counts recorded by promoted/candidate works, not as database totals | same canonical-ID rules | promoted AGON, ChatCPU, Chip-Chat, GPT4AIGChip, HiVeGen, ChipCraftBrain, VerilogCoder, Dr. RTL, Alpha-RTL and ChipMATE; lower-priority candidates retained | 已核实 |
| `RUN-LOCAL-MAP-20260812` | Local PDF/reader/card inventory | through 2026-08-12 | canonical mapping | 45 local PDFs → 43 canonical local works; 19 gap candidates; 62 discovered works; 27 claim-ready | content hash + canonical work ID | literature map, readers, cards and BibTeX audit | 已核实 |
| `RUN-PRODUCT-20260904` | AMD official documentation, AMD/Xilinx GitHub and exact-title scholarly web search | 2026-09-04 | `Vivado AI Assistant`, `Vivado AI Assistant MCP`, `VivadoMCP paper` | Exact-title/source verification; no stable database-wide total claimed | Product, software artifact and paper identities kept separate | AMD course spec and public VivadoMCP found; no peer-reviewed Vivado AI Assistant method/evaluation paper found in this bounded search | 已核实、范围受限 |

Execution evidence:

- `D:\Obsidian Vault\博士开题\硬件代码生成\SR2FPGA-TCAD\01_literature\gap-search-log.md`;
- `...\当前检索与证据状态.md`;
- `...\literature-map.md`;
- `...\comparison-change-log.md`;
- `...\baseline-eligibility.md`.

## 3. Not executed or not reconstructable

| Source/claim | Current status | Permitted wording |
|---|---|---|
| Full Scopus search | 待执行 | “Scopus query prepared”; not “Scopus searched” |
| Full Web of Science search | 待执行 | “WoS query prepared” |
| Full IEEE Xplore command search | 待执行 | “IEEE query prepared”; exact-title checks in the 2026-07 refinement remain separately recorded |
| Full ACM DL search | 待执行 | “ACM query prepared”; exact-title checks remain separately recorded |
| Full CNKI search | 待执行 | “CNKI query prepared” |
| Systematic search through 2026-08-27 | 记录不足 | Do not claim completion; the review drafted on that date exceeds the reconstructable execution cutoff |
| Search saturation | 未关闭 | The historical search log explicitly keeps saturation open |

## 4. Reporting template for future runs

Every future execution row must record:

```text
run_id:
platform/interface:
executed_at:
complete_query:
date/language/document filters:
returned_count:
screened_count:
deduplicated_count:
included_count:
exclusion reasons:
export file/hash:
operator notes:
```

Unknown counts remain `not_available`; they are never estimated.
