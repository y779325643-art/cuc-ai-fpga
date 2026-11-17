# Task catalog

The registered catalog remains at
[`sr2fpga-task-catalog-v0.2.json`](sr2fpga-task-catalog-v0.2.json).
Its data revision is **0.4.0**; the retained v0.2 envelope/path identifies the
existing exchange surface. Revision 0.4.0 intentionally changes current research
selection; it must not be substituted into an old run's fingerprint.

`current_research` binds `paper1-v2.3` / `sr2fpga-pc-2.1` and
`llm_inference_subsystems_v1`. `recommended_sets.paper1_core` contains QKV
projection, KV-cache decode attention and gated FFN. Fixed development task,
oracle, reference and harness implementations exist; family status is `partial`,
qualification `not_ready`, with no legacy generator aliases,
mutation suite or numeric qualification threshold. `system_his_profile` and
`skeleton_level` are `not_applicable` for these identities; the legacy fields do
not define a PC2.1 task. Oracle kinds and L3/L4 entries are target responsibilities,
not implemented capabilities. Task cards, design clusters, splits and profiles
must be qualified and frozen before formal execution. The development entry is
`python -m sr2fpga_agent.tasks.llm`; its controls are not legacy Runner aliases.

The preceding three AI families are retained in
`legacy_quantized_ai_core_v2_2`. Original evidence rows are preserved; new LLM
ledger rows are empty/not-run placeholders, not a promotion of local reference tests.

Previous core and physical/held-out selections use explicit `legacy_` keys.
Old `paper1_core` family roles become `development_regression`. Retained global
Line A/B, G4a and threshold policies are enumerated as historical metadata;
they do not define new task qualification. New core family recipes are disabled.
The historical recipe deny policy remains conservative for legacy development.

`task_catalog.current_research_family_specs()` rejects absent or incompatible
current population metadata without falling back to old sets. The evidence
ledger adds only three `not_implemented` / `not_run` rows; all original result
rows remain unchanged. Reported old L3/L4 or mutation counts do not transfer.
