# SR2FPGA Baseline Report: line-a-l4-dual-tool-20260713-v2

Pass-rate knee: not observed above threshold 80.0%.

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| source | deterministic | 2 | L4:2 | 100.0% | 0 | 0.0% |
| failure_origin | deterministic | 2 | L4:2 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 2 | L4:2 | 100.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 2 | L4:2 | 100.0% | 0 | 0.0% |
| contract_skeleton_mode | deterministic_template | 2 | L4:2 | 100.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 2 | L4:2 | 100.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 2 | L4:2 | 100.0% | 0 | 0.0% |

## Testbench Oracle Strength

| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 2 | 9 | 9 | 100.0% | 2 | 0 |

| surviving_mutation | samples |
|---|---:|

## L0-L4 Survival

| level | pass | fail | not_run |
|---|---:|---:|---:|
| l0 | 2 | 0 | 0 |
| l1 | 2 | 0 | 0 |
| l2 | 2 | 0 | 0 |
| l3 | 2 | 0 | 0 |
| l4_open | 2 | 0 | 0 |

## Generated-HIS Credit

| credit_bucket | count |
|---|---:|
| credited | 2 |

| generated_his_pass_level | count |
|---|---:|
| L4 | 2 |

## H0-H3 Summary

| stage | pass | fail | not_applicable |
|---|---:|---:|---:|
| h0 | 2 | 0 | 0 |
| h1 | 2 | 0 | 0 |
| h2 | 2 | 0 | 0 |
| h3 | 0 | 0 | 2 |

## L4-open

| pass | fail | not_run |
|---:|---:|---:|
| 2 | 0 | 0 |

| skip_reason | count |
|---|---:|

## L4-commercial

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 2 |

| skip_reason | count |
|---|---:|
| missing_tool | 2 |

## Derived Training Views

| view | available | official eval unit | standalone pass credit | rows | file-level passed |
|---|---|---|---|---:|---:|
| req2file | yes | no | no | 17 | 0 |
