# Paper-1 v1.6 Decoding-Control Review

Status: active pre-outcome protocol-amendment record. This is not an experiment
result, G3 acceptance artifact, or G4b authorization.

## Reason for amendment

The v1.5 design keyed paired blocks by provider decoding seed and required a
reproducible frozen decoding mechanism for paired confirmatory execution. A
bounded development diagnostic found three byte-identical DeepSeek outputs and
one stable reported fingerprint under a fixed request, but the reviewed
provider documentation did not document deterministic seed control. The
observation cannot identify whether the requested seed caused the match. The
OpenAI probe stopped at authentication and supplies no capability evidence.

Requiring a `deterministic_documented` real provider at G3 would confuse a
development-conformance gate with a later campaign-design decision. Allowing an
undocumented seed to stand in for common randomness would instead make the
official estimator indefensible.

## v1.6 decisions

1. The repeated-measure block is keyed by
   `(semantic_instance_id, replicate_id)`, not provider seed.
2. `requested_decoding_seed` remains first-class request provenance.
   `documented_seed_control` may support identical-request replay within the
   provider's reviewed boundary, but cross-method common-randomness claims need
   a separate documented coupling mechanism.
3. A separate local `execution_schedule_seed` freezes balanced method order and
   never enters a provider request.
4. G4b selects exactly one `decoding_control_mode`:
   `documented_seed_control` or `stochastic_blocked`.
5. `stochastic_blocked` estimates expected method effects over the frozen
   provider/configuration distribution and forbids deterministic, seed-effect,
   same-realization, and bitwise-replay claims.
6. G3 verifies the capability classifier and strict guard using artifact-derived
   positive and negative fixtures; a real provider need not be eligible at G3.
7. Positive capability conclusions must be recomputed from frozen protocol,
   documentation-review, and per-call observations rather than trusted summary
   booleans.

## Evidence and claim boundary

- Supported diagnostic statement: one DeepSeek prompt/configuration produced
  three matching non-empty output hashes and fingerprints; seed capability is
  still `unverified`.
- Supported missingness statement: the OpenAI probe was unavailable because of
  authentication.
- Unsupported statements: provider determinism, seed causality, bitwise replay,
  method superiority, G3 acceptance, G4b readiness, or any official outcome.

## Implementation consequences

The current Runner still uses `decoding_seed` as its repeated-measure identity.
It therefore does not yet implement v1.6. G3 remains open until first-class
`replicate_id`, independent schedule authority, dereferenceable independent
documentation-review authority, per-call capability evidence and task/profile
seed binding, shared checkpoints/cost views, the remaining scenario matrix, and
a positive artifact-derived acceptance reducer are complete. The development
capability reader now recomputes its summaries and eligibility from complete
protocol and ordered per-call observations, so that narrower fail-closed slice
is implemented but does not close the end-to-end chain.
