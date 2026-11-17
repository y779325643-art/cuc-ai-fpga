# Superseded specifications

**Nothing here is a current instruction.** These documents are retained because
the active plan cites them as provenance, because they record what was true when
decisions were made, and because historical evidence is bound to their
identities. Do not resume work from them.

Current authority is the
[Paper-1 research plan `paper1-v2.2`](../2026-09-15-sr2fpga-paper1-research-plan-v2.2.zh.md)
and its subordinate
[code-architecture spec `v2.1`](../2026-09-15-sr2fpga-paper1-code-architecture-development-spec-v2.1.zh.md).
Migration state is in the
[migration record](../../migrations/research-plan-alignment.md).

## Research plans

| File | Version | Why it is here |
| --- | --- | --- |
| `2026-08-14-sr2fpga-paper1-research-program-design.md` | `paper1-v1.8` | The former canonical English specification. Superseded 2026-09-14 by v2.1, then by v2.2. Cited by v2.1 as `[S0]` |
| `2026-08-14-sr2fpga-paper1-research-program-design.zh.md` | labelled `paper1-freeze-v1.7` | Chinese companion to the above. Its version label records its own state at the time and is deliberately **not** corrected |
| `2026-09-14-sr2fpga-paper1-research-plan-v2.0.zh.md` | `paper1-v2.0-draft` | The editing base for v2.1. Cited by v2.1 as `[D0]` |
| `2026-09-14-sr2fpga-paper1-research-plan-v2.1.zh.md` | `paper1-v2.1` | Adopted 2026-09-14, superseded 2026-09-15 by v2.2. Cited by v2.2 as `[R1]`. Its section 16.4 WP0 catalog inventory was independently verified and remains a valid input |

## Code architecture specifications

| File | Version | Why it is here |
| --- | --- | --- |
| `2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md` | `sr2fpga-paper1-code-dev-v1.12` | Written against v1.7/v1.8 method families, the G0-G9 gate sequence, and the superseded budget formula. Fully replaced by spec v2.1. Cited by spec v2.1 as `[H]` |
| `2026-09-14-sr2fpga-paper1-code-architecture-development-spec-v2.0.zh.md` | `...-v2.0-draft` | Targeted PC 2.0 and the four-family population; never adopted. The direct architectural base of spec v2.1, which cites it as `[A]` |

## Project Contract formats

| File | Status | Why it is here |
| --- | --- | --- |
| `PC-2.0-clean-slate-design.zh.md` | `pc-2.0-design-candidate` | Never adopted or registered. The drafting base for PC 2.1, which cites it as `[B0]`. Its schemas are kept at [`contracts/pc/2.0/`](../../../contracts/pc/2.0/), also unregistered |
| `2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md` | System-HIS v1.2 semantics | No longer the active PC serialization — `sr2fpga-pc-2.1` replaced it. **Still the reference for reading existing artifacts**, and `system_his` remains registered in `contracts/manifest.json` for exactly that reason |

## Superseded PC study design

| File | Why it is here |
| --- | --- |
| `2026-09-11-pc-layered-study-design-v1.md` | The A/B/A-R/B-R layered comparison designed over System-HIS v1.2, under the v1.8 protocol |
| `2026-09-11-pc-field-responsibility-v1.md` | Field-responsibility and assembly rules for the System-HIS v1.2 PC decision interface |

Both describe the pre-PC-2.1 approach, in which the model wrote decisions into a
System-HIS document. Under PC 2.1 the model emits a `design` projection directly
and the trusted controller injects `bindings`. Their contracts — `pc_decisions`,
`pc_assembly_record`, `pc_assembly_execution` — **remain registered**, because
existing artifacts reference them; they are not part of the new runtime path.

## Rules for this directory

- Version labels inside these files record their own historical state. Do not
  rewrite them, and do not global-replace `v1.7`, `v1.8`, `v2.1`, "four
  families", or old format names — those strings also appear in valid historical
  records and in the byte identities the active plan cites.
- Cited SHA-256 values in the active plan and spec refer to these bytes. Editing
  a file here breaks that chain.
- Adding a scope banner at the top of a file is acceptable; changing its
  substance is not.
- **Relative links inside these files do not all resolve.** They were written
  one directory higher and were deliberately not rewritten, because the active
  plan and spec cite these files by SHA-256 and editing them would break that
  chain. Resolve such a link by hand against the repository root.
