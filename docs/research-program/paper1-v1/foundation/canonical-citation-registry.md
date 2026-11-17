# Paper-1 Canonical Citation Registry

Status: active citation registry. Its canonical-version labels below are
**historical**: it was written for `paper1-v1.8` and candidate `paper1-v1.9`.
The current research authority is
[`paper1-v2.2`](../../../specs/2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md),
adopted 2026-09-15. Citation routing still applies; any claim-permission
statement inherited from v1.8 must be re-read against v2.2. See the
[migration record](../../../migrations/research-plan-alignment.md).

Updated: 2026-09-10; scope notice added 2026-09-15

Authority: citation routing only; this registry does not override the current
research plan, current code, contracts, or artifact-backed outcomes.

## Contract

Each work has exactly one canonical citation key. A claim is `claim-ready` only
when the following chain exists and the evidence card permits that claim:

`citation key -> reader -> evidence card -> source map -> PDF SHA-256 -> source anchor`

Statuses:

- `已核实`: complete local claim chain exists;
- `原文已核实`: a primary PDF, content hash and page-level bounded claims exist,
  but the full reader/card/source-map chain is not yet complete;
- `官方原文页已核实`: the current primary arXiv abstract/full-HTML page and
  section-bounded claims were checked, but no local PDF hash is registered;
- `待核实`: identity is recorded, but claim-level local evidence is incomplete;
- `AI推断`: no entry below may use this status as bibliographic fact.

The canonical BibTeX file is
[`canonical-references.bib`](canonical-references.bib). Historical TCAD/TRETS
BibTeX files remain provenance inputs and are not edited.

Reading coverage and the limits of the historical Obsidian notes are recorded
in [`reading-coverage-audit-v1.7.md`](reading-coverage-audit-v1.7.md).

## Alias normalization

| Historical key | Canonical key | Status | Reason |
|---|---|---|---|
| `rtlrepo` | `rtl-repo` | 已核实 | Same title and arXiv ID as the TCAD claim-ready work |
| `spec2rtl` | `spec2rtl-agent` | 已核实 | Same title, authors, and arXiv ID |
| `phoenix` | `phoenix-bench` | 已核实 | Same title and arXiv ID; TCAD key is linked to the reader/card |

No current derived manuscript may introduce these historical aliases as new
keys.

## Claim-ready works

All paths below are relative to `SR2FPGA-TCAD/01_literature` in the local research vault.
The evidence-ID column names the stable prefix/range in the evidence card; the
card controls the exact permitted wording.

| Canonical key | Reader/card/source map | PDF SHA-256 | Evidence IDs | Primary Paper-1 role | Status |
|---|---|---|---|---|---|
| `agon` | `readers/agon/`; `evidence-cards/agon.md` | `ECD245D8795A26AC4967E2A7DEABED6E7B52AF894993C23EAAA6D5251FB86C7C` | `E-AGON-01`–`11` | executable semantic IR / processor framework boundary | 已核实 |
| `alpha-rtl` | `readers/alpha-rtl/`; `evidence-cards/alpha-rtl.md` | `1551BAF2001AB257E262D6CB850E1D9A48941DD610615A53CDC32FFBD311E71E` | `E-AR-01`–`07` | test-time parameter update boundary; outside Paper-1 treatment | 已核实 |
| `archxbench` | `readers/archxbench/`; `evidence-cards/archxbench.md` | `B1A3BF488F6B6AC09C9E3D16EB0A24DF9AE8D52D30882F4A9FDB38F1C353D69D` | `E-ARCHX-01`–`07` | complex multi-module external benchmark | 已核实 |
| `autochip` | `readers/autochip/`; `evidence-cards/autochip.md` | `2A1C69FEDB453165359B6B3C59FA8A61618B943415E076F98365A39D4BB88FD2` | `E-AUTO-01`–`07` | public compiler/simulation feedback repair | 已核实 |
| `chatcpu` | `readers/chatcpu/`; `evidence-cards/chatcpu.md` | `8B41341618238741FEEB46D9B792FD12061D771126771BDEBE3C1369D994E5F2` | `E-CCPU-01`–`07` | structured CPU specification / shared reference boundary | 已核实 |
| `chip-chat` | `readers/chip-chat/`; `evidence-cards/chip-chat.md` | `07BF2365EEFAF48A9D88DD3CB74177A666C0752724144DD7AE417810B3F74899` | `E-CC-01`–`11` | human-in-the-loop physical completion case | 已核实 |
| `chipcraftbrain` | `readers/chipcraftbrain/`; `evidence-cards/chipcraftbrain.md` | `D045A6BA00E9EA127BAEE2310EFBB6158FDFF50AF9F845065D5E77B81333FEF7` | `E-CCB-01`–`12` | multi-agent/RL/FPGA capability boundary | 已核实 |
| `chipmate` | `readers/chipmate/`; `evidence-cards/chipmate.md` | `F53962DEDD91207A87339781B32CFAB8FD8D11076EAC8D9682982A07DF639F55` | `E-CM-01`–`09` | multi-agent training boundary; outside Paper-1 treatment | 已核实 |
| `chipseek-r1` | `readers/chipseek-r1/`; `evidence-cards/chipseek-r1.md` | `13BB6CD441482898A873C122D258B347C96A50BD4FA7256866CD847C3D0CFADD` | `E-CHIP-01`–`10` | EDA-reward RL boundary; outside Paper-1 treatment | 已核实 |
| `cktevo` | `readers/cktevo/`; `evidence-cards/cktevo.md` | `B0FDF85B3E395B9FE442EABB39DFDD6EF7152EBC0748A8E0EB84922D8217B2BF` | `E-CKT-01`–`10` | existing-repository RTL evolution/PPA | 已核实 |
| `cppl` | `readers/cppl/`; `evidence-cards/cppl.md` | `8D50A3EA04860226C8A0EEC61438F79541B61B7ABD54F9B4FC8703199F9F6D3E` | `E-CPPL-01`–`07` | circuit IR / compiler-mediated generation | 已核实 |
| `dr-rtl` | `readers/dr-rtl/`; `evidence-cards/dr-rtl.md` | `3214D59D631565931717C852184C98BD0C4678274E71E5707482E8EBBBA774AE` | `E-DR-01`–`07` | external skill memory on existing RTL; outside Paper-1 treatment | 已核实 |
| `firrtl` | `readers/firrtl/`; `evidence-cards/firrtl.md` | `5CAF5D28C16AB214D4E7D5BB9E4484D97402D2AAA597195DCD63415222C573B0` | `E-FIRRTL-01`–`07` | compiler-IR ancestry | 已核实 |
| `formalrtl` | `readers/formalrtl/`; `evidence-cards/formalrtl.md` | `B8D09D36988314E9DFBBFF0808EE595E4ACD9A9C5870B86828FD5381DA10D361` | `E-FORMAL-01`–`10` | executable reference/formal feedback comparator | 已核实 |
| `gpt4aigchip` | `readers/gpt4aigchip/`; `evidence-cards/gpt4aigchip.md` | `ECFCCB74C3A17C2DCB216800276A29396057F25BD49607E9B15EDCC7DF903F81` | `E-G4AC-01`–`12` | template/HLS accelerator capability comparator | 已核实 |
| `hivegen` | `readers/hivegen/`; `evidence-cards/hivegen.md` | `C086F30727D0970E2B59BA52DA1D64B01A59A06CDC9D2C1D94B7C50BB8BB9E44` | `E-HVG-01`–`11` | hierarchical multi-module generation | 已核实 |
| `horizon` | `readers/horizon/`; `evidence-cards/horizon.md` | `DE420EF263A123EEC89B2C2079C181A46602520DDDD31CA98AE5BED012772C55` | `E-HZN-01`–`11` | repository evolution / visible-evaluator closest work | 已核实 |
| `phoenix-bench` | `readers/phoenix-bench/`; `evidence-cards/phoenix-bench.md` | `C5854AB9952C4ACFD860D5B4D0FAA46F8CE58617AB122D8079D2C54098439E65` | `E-PHX-01`–`09` | real-world repository repair benchmark | 已核实 |
| `representation-bottleneck` | `readers/representation-bottleneck/`; `evidence-cards/representation-bottleneck.md` | `3436252ECE43F62FB7632D5B0017087A72EEC52FA1CFE9E79509192ABB9B2CD3` | `E-RB-01`–`11` | representation-choice comparator | 已核实 |
| `resbench` | `readers/resbench/`; `evidence-cards/resbench.md` | `CEDC9F499039E0AAA8498AAF7FC9385EC023944A98459DD4D1DD5A0C98E8EC09` | `E-RES-01`–`08` | FPGA resource-aware evaluation | 已核实 |
| `rtl-repo` | `readers/rtl-repo/`; `evidence-cards/rtl-repo.md` | `730FB5F6FB6E321BF87F64F340B92A93CE91348C6F2B054670E59DF72DDC7ECE` | `E-RTLREPO-01`–`06` | repository-context completion boundary | 已核实 |
| `rtlfixer` | `readers/rtlfixer/`; `evidence-cards/rtlfixer.md` | `5CF927D1F80AF388A352F9DCD6B0A005B53CCDF23AFD6F7FB14D9D35DE61F5AB` | `E-RTLFIX-01`–`06` | compiler-guided syntax repair | 已核实 |
| `rtllm` | `readers/rtllm/`; `evidence-cards/rtllm.md` | `FE62987F4FA18D44F109EB6D599B9167055C9178406288CA9772A4DFC55E5A37` | `E-RTLLM-01`–`07` | module benchmark / design quality | 已核实 |
| `spec2rtl-agent` | `readers/spec2rtl-agent/`; `evidence-cards/spec2rtl-agent.md` | `6BE9536DE4DBEAD9F0DFA93CADAB0ADDC5627305EE0BC2997434B59EF1BC2506` | `E-S2R-01`–`08` | long specification / staged representation / HLS | 已核实 |
| `verilogcoder` | `readers/verilogcoder/`; `evidence-cards/verilogcoder.md` | `152D94E8B9742C467203FB499C1795EC4AC3945F97B9244ACEC70F1DF72CE7F8` | `E-VC-01`–`09` | planning and waveform-based public repair | 已核实 |
| `verilogeval` | `readers/verilogeval/`; `evidence-cards/verilogeval.md` | `3F09E1176C0ED2CC6F90EE4398DB4665DF12A14060988707ED11225783D06320` | `E-VE-01`–`08` | module-generation benchmark | 已核实 |
| `verireason` | `readers/verireason/`; `evidence-cards/verireason.md` | `7872B790770720A840469CA6DB23DD8BB629CDD90A37FBC8282D50DA89930011` | `E-VERI-01`–`08` | testbench-reward RL boundary; outside Paper-1 treatment | 已核实 |

## Source-verified works

These three works were checked directly against local primary PDFs in
[`supplemental-source-verified-evidence.md`](supplemental-source-verified-evidence.md).
They may support only the bounded claims listed there.

| Canonical key | PDF SHA-256 | Evidence IDs | Status |
|---|---|---|---|
| `hint` | `452473E873BC5A77D5DCEC64F0F7452F0E2017510D1C281CA13349642BEFEFDF` | `E-HINT-S01`–`05` | 原文已核实 |
| `rtlcoder` | `FD623A2FABC372C434030A8A1C45293990552BA4561EC18EA4D55EE` | `E-RTLC-S01`–`04` | 原文已核实 |
| `cvdp` | `D85E66E7FA3AE80E40C810C45877FF3E2DBED515D47F2C0326779E9EE973E58D` | `E-CVDP-S01`–`05` | 原文已核实 |

## Official-primary-page verified works

These works were checked against current arXiv primary pages in
[`external-primary-source-evidence.md`](external-primary-source-evidence.md).

| Canonical key | Version | Evidence IDs | Status |
|---|---|---|---|
| `realbench` | arXiv:2507.16200v1 | `E-REAL-W01`–`05` | 官方原文页已核实 |
| `hwebench` | arXiv:2604.14709v3 | `E-HWE-W01`–`05` | 官方原文页已核实 |
| `closerbench` | arXiv:2607.16632v1 | `E-CLOSER-W01`–`04` | 官方原文页已核实 |
| `chipverilog` | arXiv:2607.13079v3 | `E-CHIPV-W01`–`04` | 官方原文页已核实 |

## v1.9 mathematical-foundation identities

The following sources were added for the candidate DSC/EA theory stack. Their
bibliographic identities were checked against publisher, DOI, DBLP, or official
arXiv metadata on 2026-09-10. They are not yet `claim-ready` because local
readers, evidence cards, source maps, and PDF hashes have not been completed.

| Canonical key | Verified identity | Candidate role | Status |
| --- | --- | --- | --- |
| `benveniste-contracts-2007` | arXiv:0706.1456 | generic assumption--guarantee contract basis | 待核实 |
| `cimatti-tonetta-contract-refinement-2015` | DOI 10.1016/j.scico.2014.06.011 | contract refinement and proof-obligation boundary | 待核实 |
| `deb-nsga2-2002` | DOI 10.1109/4235.996017 | constrained nondominated sorting, elitism, and diversity | 待核实 |
| `auger-hypervolume-2012` | DOI 10.1016/j.tcs.2011.03.012 | hypervolume and reference-point interpretation | 待核实 |
| `jha-seshia-ogis-2017` | DOI 10.1007/s00236-017-0294-5 | OGIS/CEGIS basis for bounded public repair | 待核实 |
| `lee-messerschmitt-sdf-1987` | DOI 10.1109/PROC.1987.13876 | synchronous-dataflow balance constraints | 待核实 |
| `nabi-vanderbauwhede-roofline-2019` | DOI 10.1016/j.jpdc.2017.05.014 | FPGA Roofline-guided DSE | 待核实 |
| `mouret-clune-map-elites-2015` | arXiv:1504.04909 | optional quality-diversity extension, not minimum method | 待核实 |
| `yu-nas-search-evaluation-2020` | arXiv:1902.08142v3 | isolate search-policy effects from search-space effects and retain random search | 待核实 |
| `yang-nas-evaluation-2020` | arXiv:1912.12522v3; ICLR 2020 | search-space/protocol confounding and relative-to-random evaluation | 待核实 |

## v1.9 full-text related-work audit identities

The following works were audited through their complete accessible official
arXiv HTML and publication metadata on 2026-09-10. Section-bounded feature
claims and baseline roles are recorded in
[`../audit/v1.9-related-work-feature-audit-2026-09-10.md`](../audit/v1.9-related-work-feature-audit-2026-09-10.md).
They remain below local `claim-ready` status until a PDF hash, reader, evidence
card, and source map are registered.

| Canonical key | Verified identity/status | Audit role | Status |
| --- | --- | --- | --- |
| `evoverilog-2025` | arXiv:2508.13156v1 | LLM idea-tree, population EA, nondominated Verilog generation | 官方原文页已核实 |
| `revolution-2026` | arXiv:2510.21407v1; accepted ASP-DAC 2026 | closest released LLM evolutionary RTL baseline | 官方原文页已核实 |
| `evolve-2026` | arXiv:2601.18067v1 | IGR/MCTS and IC-RTL search reference | 官方原文页已核实 |
| `poet-2026` | arXiv:2603.19333v1 | differential-testing and power-oriented Pareto optimization | 官方原文页已核实 |
| `cradle-2025` | arXiv:2508.08709v1; accepted ISOCC 2025; DOI 10.1109/ISOCC66390.2025.11329873 | conversational FPGA RTL DSE comparator | 官方原文页已核实 |
| `fpgagent-2026` | arXiv:2608.23630v1 | evolutionary HLS-to-board cross-paradigm reference | 官方原文页已核实 |
| `finhardbench-2026` | arXiv:2608.00909v1; COLM 2026 conference paper | post-P&R FPGA benchmark and random/SA/BO DSE comparison | 官方原文页已核实 |
| `ares-2026` | arXiv:2607.27879v1 | normalized-cost and adaptive-effort RTL optimization | 官方原文页已核实 |
| `autodse-2022` | ACM TODAES 27(4), Article 32; DOI 10.1145/3494534 | published HLS DSE anchor | 官方原文页已核实 |

## Identity-ready works

No canonical bibliography entry remains identity-only after the current
primary-page verification. Discovery-only names remain outside this set.

Works named only in logs, including `OpenLLM-RTL`, `ChipBench`, `CIRCT`, and
`Spec-Driven Hardware Evolution`, remain discovery-only until a canonical key
and identity record are added.

## Source-path migration note

Fifteen legacy source maps still record `文献/papers/...`, while the matching
files now live under `文献/PDF 原文/...`. The SHA-256 values above were resolved
against the current vault and matched. This registry supplies a stable content
identity, but the historical source maps remain unchanged as requested.

## Use rule

1. Use only canonical keys in current derived writing.
2. Use claim-ready works only within the wording permitted by their evidence
   cards and source anchors.
3. Use official-primary-page claims only with the registered version and
   section-bounded evidence; do not copy numerical claims from session citations.
4. Never use a literature claim to imply an SR2FPGA outcome.
