# G3 Provider Seed-Capability Probe

Status: executed development diagnostic with one documented protocol amendment;
not a Paper-1 campaign and not an official or G3 acceptance artifact.

## Question and decision boundary

The probe asks whether a frozen provider/model profile produces byte-identical
responses under a repeated fixed-seed request and a stable reported backend
fingerprint. The independent variable is the provider/model profile. Prompt,
seed, temperature, output ceiling, repetition count, adapter code and analysis
are fixed. The dependent observations are request success, output SHA-256,
system fingerprint and provider-reported token usage.

Observed repeatability is not proof of guaranteed determinism. A profile is a
paired-confirmatory candidate only when deterministic seed control is also
documented by a frozen, hash-bound provider mechanism. Best-effort or
undocumented profiles remain ineligible even if all three outputs match.

## Experiment matrix

| Run ID | Factor | Value | Fixed configuration | Expected outcome |
| --- | --- | --- | --- | --- |
| `seedcap-deepseek-v4-flash` | provider/profile | DeepSeek `deepseek-v4-flash` | seed 17; fixed JSON prompt; temperature 0.1; max output 128; 3 repetitions; OpenAI-compatible adapter | repeatability may be observed, but classification remains `unverified` while seed is undocumented |
| `seedcap-openai-gpt4omini-snapshot` | provider/profile | OpenAI `gpt-4o-mini-2024-07-18` | seed 17; same prompt and temperature; max output 32; 3 repetitions; OpenAI-compatible adapter | matching observations may yield `best_effort_observed`; best-effort documentation is not deterministic guarantee |

The original preregistration used max output 32 for both profiles. The first
DeepSeek diagnostic consumed the full output allowance but returned an empty
final-text field. Empty response hashes are not valid repeatability evidence.
Before the final analytical run, the probe was changed to classify an empty
response as `response_invalid` and the DeepSeek ceiling was amended to 128.
This changes the protocol hash and capability profile ID. OpenAI retained the
original ceiling because it stopped at authentication before inference.

Final planned analytical calls: three per reachable profile, sequentially. A
profile aborts after its first logical-call error. Instrumentation-development
reruns are reported below and are not pooled into the analytical comparison.

## Resource estimate

- GPU hours: 0; this is an external API diagnostic.
- API calls: at most 6, with one transport attempt per call and an abort after
  the first logical-call error for a profile.
- Revised token planning ceiling: approximately 128 input plus 128 output
  tokens per DeepSeek call and 64 input plus 32 output tokens per OpenAI call.
  Actual provider-reported tokens must be retained in capability artifacts.
- At the prices checked on 2026-08-26, the revised final analytical ceiling is
  below USD 0.0003 total. Pricing is diagnostic planning metadata and must be
  refreshed before a later run.
- Storage: two small JSON artifacts plus content-addressed refs; no response
  text, credential, hidden evaluator material or candidate project is stored.

## Execution commands

The CLI reads a separately archived provider-document snapshot and computes its
SHA-256. A URL, live-page observation, or caller-entered digest alone is not a
content commitment. The local path is not persisted. This CLI path records a
`self_reviewed_development` review provenance; it cannot create a positive
paired-confirmatory profile. The repository does not yet implement a
dereferenceable independent-review artifact/loader; only a synthetic fixture
exercises that future positive branch.

```powershell
python -m sr2fpga_agent.provider_seed_probe `
  --artifact-root artifacts/provider-seed-probes/deepseek-v4-flash-reducer-v1 `
  --env-file .env `
  --model deepseek-v4-flash `
  --base-url https://api.deepseek.com `
  --api-key-env DEEPSEEK_API_KEY `
  --seed 17 `
  --repetitions 3 `
  --max-tokens 128 `
  --documentation-status seed_undocumented `
  --documentation-snapshot artifacts/provider-seed-probes/documentation/deepseek-chat-completions-2026-08-26.html `
  --documentation-source-url https://api-docs.deepseek.com/api/create-chat-completion/

python -m sr2fpga_agent.provider_seed_probe `
  --artifact-root artifacts/provider-seed-probes/openai-gpt4omini-reducer-v1 `
  --env-file .env `
  --model gpt-4o-mini-2024-07-18 `
  --base-url https://api.openai.com/v1 `
  --api-key-env OPENAI_API_KEY `
  --seed 17 `
  --repetitions 3 `
  --max-tokens 32 `
  --documentation-status best_effort_documented `
  --documentation-snapshot artifacts/provider-seed-probes/documentation/openai-python-chat-completion-params-2026-08-26.py `
  --documentation-source-url https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py
```

## Analysis and abort rules

1. Compare only output hashes and fingerprints; do not inspect response content
   to redefine the protocol.
2. `complete` requires all three logical calls. A call error aborts remaining
   calls and produces `partial` or `infrastructure_error`, never a model/design
   failure.
3. Any output mismatch is `nonrepeatable_observed`. Missing or differing
   fingerprints are fail-closed for candidate eligibility but are classified
   separately as `backend_identity_unverified`, not as output nonrepeatability.
4. Matching DeepSeek observations remain `unverified`; matching OpenAI
   observations remain `best_effort_observed` under the currently reviewed
   documentation semantics.
5. Only a future `deterministic_documented` profile with an independently
   reviewed snapshot, complete matching probe and exact source identity may
   become a `reproducible_frozen_candidate`. This still grants no official, G3
   or G4b authority.

The persisted raw protocol and ordered per-call observations are authoritative.
The loader recomputes all counts, status, hash/fingerprint conclusions, token
totals, classification, limitations, profile ID and eligibility; tampering with
an aggregate field fails closed rather than changing the decision.

## Execution record — 2026-08-26

Documentation was frozen locally before the calls:

- DeepSeek Chat Completions HTML snapshot SHA-256
  `7a391a15fbef0903a6968e49ccfe8cb879a86f8f80cf8e88f0d2385e271c06aa`;
  the reviewed page documents `system_fingerprint` but does not document a
  `seed` request parameter or deterministic-seed guarantee.
- OpenAI official Python SDK Chat Completions parameter snapshot SHA-256
  `55541366b971c97495b4d283dde86bcf2193c1d870e507826d904cb1d0141010`;
  its `seed` field states best-effort repeatability and explicitly says
  determinism is not guaranteed.

Final analytical outcomes:

| Profile | Calls | Observation | Classification | Authority |
| --- | ---: | --- | --- | --- |
| DeepSeek `deepseek-v4-flash`, max output 128 | 3/3 complete | one non-empty output SHA-256 across all calls; one reported fingerprint across all calls; 342 input and 156 output tokens | `unverified` because seed support is undocumented and the documentation review is development-self-reviewed | `paired_confirmatory_eligible=false`; all official/G3/G4b flags false |
| OpenAI `gpt-4o-mini-2024-07-18` | 0/3 complete; first call stopped | sanitized failure category `authentication`; no provider token usage | `unavailable` | `paired_confirmatory_eligible=false`; all official/G3/G4b flags false |

The final DeepSeek artifact is
`provider-seed-capabilities/seedcap-fb9e7922ac91f46d7cf972ec2f97582c`
with content SHA-256
`436fb7fb1139246a30921b2305131ca55ced4d99db38f1e756b932f1eec4e850`.
The final OpenAI diagnostic artifact is
`provider-seed-capabilities/seedcap-ceeef74699c354f2ed962a0ab3845c41`
with content SHA-256
`683fa419991e51ce3a88eff56333dc1f3899af31a1f597ac739d5d0bc6af3781`.
Both live under ignored local `artifacts/provider-seed-probes/` stores and are
development diagnostics, not committed evidence-ledger entries.

During instrumentation development and schema replacement, two 32-token
DeepSeek sets, one superseded aggregate-only 128-token set, and two superseded
OpenAI authentication attempts were made. The 32-token sets produced empty
final text; the aggregate-only artifacts cannot satisfy the final raw-evidence
schema. Across all four DeepSeek sets, the provider reported 1,368 input and 533
output tokens. No OpenAI usage was reported across the three authentication
attempts. These reruns explain why actual calls exceeded the original six-call
planning estimate; they are excluded from the final analytical artifact and do
not increase its sample size.
