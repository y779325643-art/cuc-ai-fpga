# SR2FPGA Phase D H2 Hardening Design

## Goal

Classify the 24 frozen Phase D pilot failures and make a narrow H2 compatibility
improvement without weakening the lowerability gate or rewriting pilot evidence.

## Evidence Baseline

The frozen pilot contains 24 scoreable episodes:

- 12 generation failures before H-stage validation;
- 12 generated System-HIS candidates that pass H0/H1 and fail H2;
- no live L0-L4 verdict and no eligible repair attempt.

The H2 failures expose three recurring compatibility classes:

1. structured `verification.scenarios` objects are stringified instead of
   reading their canonical `name` or `kind` field;
2. generated `semantic_kind` labels use descriptive synonyms that are not in
   the canonical H2 vocabulary;
3. generated data-flow protocols use descriptive aliases that are not in the
   canonical H2 vocabulary.

## Design

Use strict compatibility hardening:

1. Parse scenario strings and scenario objects explicitly. An object is
   lowerable only when `kind`, or otherwise `name`, resolves to a supported
   canonical scenario. Missing or unknown values still fail H2.
2. Canonicalize only an explicit, reviewed set of lossless semantic-kind and
   protocol aliases. Unknown labels still fail H2.
3. Add the canonical H2 vocabularies and scenario representation rule to both
   initial REQ2HIS and retry prompts. This aligns future model output with the
   existing gate instead of broadening the gate to every observed phrase.
4. Replay the frozen generated System-HIS artifacts read-only and report H2
   diagnostics before and after the change. Original `labels.json`,
   `trajectory.json`, and run summaries remain immutable.

## Non-Goals

- Do not add every pilot label or free-form scenario to a whitelist.
- Do not infer a scenario profile from arbitrary English text.
- Do not reinterpret generation failures as H2 failures.
- Do not rerun model APIs or overwrite the frozen pilot.
- Do not claim L0-L4 progress from an H2-only replay.

## Acceptance Criteria

1. A structured scenario object with a canonical `name` or `kind` passes H2.
2. A structured scenario object with an unknown or missing identifier fails H2
   with a concise diagnostic that does not stringify the whole object.
3. Reviewed canonical aliases pass; unrelated semantic kinds and protocols
   continue to fail.
4. REQ2HIS prompts expose the exact canonical vocabularies and require scenario
   strings or objects with a canonical `kind`.
5. A read-only replay produces per-sample before/after diagnostics and aggregate
   counts for all 24 frozen episodes.
6. Targeted tests and the full `LLM/tests` suite pass.

