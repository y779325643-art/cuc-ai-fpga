# SR2FPGA Baseline Report: phase-b-core-closure-20260713-v4

Pass-rate knee: T3 (L3 pass rate 66.7% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| source | deterministic | 9 | L3:7, ORACLE_NOT_READY:2 | 77.8% | 0 | 0.0% |
| failure_origin | deterministic | 9 | L3:7, ORACLE_NOT_READY:2 | 77.8% | 0 | 0.0% |
| difficulty_tier | T1 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 6 | L3:4, ORACLE_NOT_READY:2 | 66.7% | 0 | 0.0% |
| requirement_style | simple_prompt | 9 | L3:7, ORACLE_NOT_READY:2 | 77.8% | 0 | 0.0% |
| contract_skeleton_mode | deterministic_template | 9 | L3:7, ORACLE_NOT_READY:2 | 77.8% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 9 | L3:7, ORACLE_NOT_READY:2 | 77.8% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 9 | L3:7, ORACLE_NOT_READY:2 | 77.8% | 0 | 0.0% |

## Testbench Oracle Strength

| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |
|---:|---:|---:|---:|---:|---:|---:|
| 9 | 9 | 41 | 37 | 90.0% | 7 | 2 |

| surviving_mutation | samples |
|---|---:|
| hardcoded_first_coordinate | 1 |
| history_updates_while_stalled | 1 |
| ignore_in_last | 1 |
| top_in_ready_stuck_high | 1 |

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
| L3 | 7 |
| ORACLE_NOT_READY | 2 |

## H0-H3 Summary

| stage | pass | fail | not_applicable |
|---|---:|---:|---:|
| h0 | 9 | 0 | 0 |
| h1 | 9 | 0 | 0 |
| h2 | 9 | 0 | 0 |
| h3 | 0 | 0 | 9 |

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
| req2file | yes | no | no | 77 | 0 |
