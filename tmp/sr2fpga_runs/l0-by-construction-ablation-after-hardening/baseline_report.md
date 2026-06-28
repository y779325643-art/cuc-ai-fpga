# SR2FPGA Baseline Report: l0-by-construction-ablation-after-hardening

Pass-rate knee: T1 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 4 | L0_FAIL:4 | 0.0% | 4 | 100.0% |
| failure_family | generation_failure | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| failure_family | rtl_compile_failure | 3 | L0:3 | 0.0% | 0 | 0.0% |
| source | deepseek | 4 | L0_FAIL:4 | 0.0% | 4 | 100.0% |
| source | deepseek-his-v12 | 4 | GEN_FAIL:1, L0:3 | 0.0% | 1 | 25.0% |
| failure_origin | natural_llm | 8 | GEN_FAIL:1, L0:3, L0_FAIL:4 | 0.0% | 5 | 62.5% |
| difficulty_tier | T1 | 2 | L0:1, L0_FAIL:1 | 0.0% | 1 | 50.0% |
| difficulty_tier | T2 | 2 | L0:1, L0_FAIL:1 | 0.0% | 1 | 50.0% |
| difficulty_tier | T3 | 2 | GEN_FAIL:1, L0_FAIL:1 | 0.0% | 2 | 100.0% |
| difficulty_tier | T4 | 2 | L0:1, L0_FAIL:1 | 0.0% | 1 | 50.0% |
| requirement_style | natural_component | 8 | GEN_FAIL:1, L0:3, L0_FAIL:4 | 0.0% | 5 | 62.5% |
| contract_skeleton_mode | behavior_files | 4 | GEN_FAIL:1, L0:3 | 0.0% | 1 | 25.0% |
| contract_skeleton_mode | legacy_full_project | 4 | L0_FAIL:4 | 0.0% | 4 | 100.0% |
| topology_id | t1_event_counter | 2 | L0:1, L0_FAIL:1 | 0.0% | 1 | 50.0% |
| topology_id | t2_stream_accumulator | 2 | L0:1, L0_FAIL:1 | 0.0% | 1 | 50.0% |
| topology_id | t3_stream_fork | 2 | GEN_FAIL:1, L0_FAIL:1 | 0.0% | 2 | 100.0% |
| topology_id | t4_dual_stream_join | 2 | L0:1, L0_FAIL:1 | 0.0% | 1 | 50.0% |
| measurement_point | a_first_attempt_no_tools | 8 | GEN_FAIL:1, L0:3, L0_FAIL:4 | 0.0% | 5 | 62.5% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| legacy_full_project | 4 | L0_FAIL:4 | 0.0% | 4 | 100.0% |
| behavior_files | 4 | GEN_FAIL:1, L0:3 | 0.0% | 1 | 25.0% |

L0 contract failure delta (behavior_files - legacy_full_project): -3
L3 pass-rate delta (behavior_files - legacy_full_project): +0.0 pp
