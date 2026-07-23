# SR2FPGA Baseline Report: line-a-oracle-evidence-20260713-v2

Pass-rate knee: not observed above threshold 80.0%.

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| source | deterministic | 6 | L3:6 | 100.0% | 0 | 0.0% |
| failure_origin | deterministic | 6 | L3:6 | 100.0% | 0 | 0.0% |
| difficulty_tier | T0 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| difficulty_tier | T1 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 6 | L3:6 | 100.0% | 0 | 0.0% |
| contract_skeleton_mode | deterministic_template | 6 | L3:6 | 100.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 6 | L3:6 | 100.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 6 | L3:6 | 100.0% | 0 | 0.0% |

## Testbench Oracle Strength

| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 6 | 22 | 22 | 100.0% | 6 | 0 |

| surviving_mutation | samples |
|---|---:|

## L0-L4 Survival

| level | pass | fail | not_run |
|---|---:|---:|---:|
| l0 | 6 | 0 | 0 |
| l1 | 6 | 0 | 0 |
| l2 | 6 | 0 | 0 |
| l3 | 6 | 0 | 0 |
| l4_open | 0 | 0 | 6 |

## Generated-HIS Credit

| credit_bucket | count |
|---|---:|
| credited | 6 |

| generated_his_pass_level | count |
|---|---:|
| L3 | 6 |

## H0-H3 Summary

| stage | pass | fail | not_applicable |
|---|---:|---:|---:|
| h0 | 6 | 0 | 0 |
| h1 | 6 | 0 | 0 |
| h2 | 6 | 0 | 0 |
| h3 | 0 | 0 | 6 |

## L4-open

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 6 |

| skip_reason | count |
|---|---:|
| disabled_by_config | 6 |

## L4-commercial

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 6 |

| skip_reason | count |
|---|---:|
| disabled_by_config | 6 |

## Derived Training Views

| view | available | official eval unit | standalone pass credit | rows | file-level passed |
|---|---|---|---|---:|---:|
| req2file | yes | no | no | 47 | 0 |
