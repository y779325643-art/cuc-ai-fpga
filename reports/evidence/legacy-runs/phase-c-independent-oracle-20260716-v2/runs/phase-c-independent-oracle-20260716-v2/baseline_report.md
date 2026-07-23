# SR2FPGA Baseline Report: phase-c-independent-oracle-20260716-v2

Pass-rate knee: not observed above threshold 80.0%.

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| source | deterministic | 9 | L3:9 | 100.0% | 0 | 0.0% |
| failure_origin | deterministic | 9 | L3:9 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 8 | L3:8 | 100.0% | 0 | 0.0% |
| difficulty_tier | T4 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 9 | L3:9 | 100.0% | 0 | 0.0% |
| contract_skeleton_mode | deterministic_template | 9 | L3:9 | 100.0% | 0 | 0.0% |
| topology_id | t10_rl_accelerator_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t6_td_update_core | 1 | L3:1 | 100.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 9 | L3:9 | 100.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 9 | L3:9 | 100.0% | 0 | 0.0% |

## Testbench Oracle Strength

| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |
|---:|---:|---:|---:|---:|---:|---:|
| 9 | 9 | 45 | 45 | 100.0% | 9 | 0 |

| surviving_mutation | samples |
|---|---:|

## L0-L4 Survival

| level | pass | fail | not_run |
|---|---:|---:|---:|
| l0 | 9 | 0 | 0 |
| l1 | 9 | 0 | 0 |
| l2 | 9 | 0 | 0 |
| l3 | 9 | 0 | 0 |
| l4_open | 0 | 0 | 9 |

## Generated-HIS Credit

| credit_bucket | count |
|---|---:|
| credited | 9 |

| generated_his_pass_level | count |
|---|---:|
| L3 | 9 |

## H0-H3 Summary

| stage | pass | fail | not_applicable |
|---|---:|---:|---:|
| h0 | 9 | 0 | 0 |
| h1 | 9 | 0 | 0 |
| h2 | 9 | 0 | 0 |
| h3 | 2 | 0 | 7 |

## L4-open

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 9 |

| skip_reason | count |
|---|---:|
| disabled_by_config | 9 |

## L4-commercial

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 9 |

| skip_reason | count |
|---|---:|
| disabled_by_config | 9 |

## Derived Training Views

| view | available | official eval unit | standalone pass credit | rows | file-level passed |
|---|---|---|---|---:|---:|
| req2file | yes | no | no | 83 | 0 |
