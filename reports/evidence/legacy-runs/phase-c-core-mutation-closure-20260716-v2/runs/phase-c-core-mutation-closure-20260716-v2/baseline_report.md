# SR2FPGA Baseline Report: phase-c-core-mutation-closure-20260716-v2

Pass-rate knee: not observed above threshold 80.0%.

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| source | deterministic | 4 | L3:4 | 100.0% | 0 | 0.0% |
| failure_origin | deterministic | 4 | L3:4 | 100.0% | 0 | 0.0% |
| difficulty_tier | T0 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 4 | L3:4 | 100.0% | 0 | 0.0% |
| contract_skeleton_mode | deterministic_template | 4 | L3:4 | 100.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t5_vector_mac_pipeline | 1 | L3:1 | 100.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 4 | L3:4 | 100.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 4 | L3:4 | 100.0% | 0 | 0.0% |

## Testbench Oracle Strength

| samples | reference passed | mutation cases | killed | mutation score | Line A ready | Line A not ready |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 15 | 15 | 100.0% | 4 | 0 |

| surviving_mutation | samples |
|---|---:|

## L0-L4 Survival

| level | pass | fail | not_run |
|---|---:|---:|---:|
| l0 | 4 | 0 | 0 |
| l1 | 4 | 0 | 0 |
| l2 | 4 | 0 | 0 |
| l3 | 4 | 0 | 0 |
| l4_open | 0 | 0 | 4 |

## Generated-HIS Credit

| credit_bucket | count |
|---|---:|
| credited | 4 |

| generated_his_pass_level | count |
|---|---:|
| L3 | 4 |

## H0-H3 Summary

| stage | pass | fail | not_applicable |
|---|---:|---:|---:|
| h0 | 4 | 0 | 0 |
| h1 | 4 | 0 | 0 |
| h2 | 4 | 0 | 0 |
| h3 | 3 | 0 | 1 |

## L4-open

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 4 |

| skip_reason | count |
|---|---:|
| disabled_by_config | 4 |

## L4-commercial

| pass | fail | not_run |
|---:|---:|---:|
| 0 | 0 | 4 |

| skip_reason | count |
|---|---:|
| disabled_by_config | 4 |

## Derived Training Views

| view | available | official eval unit | standalone pass credit | rows | file-level passed |
|---|---|---|---|---:|---:|
| req2file | yes | no | no | 33 | 0 |
