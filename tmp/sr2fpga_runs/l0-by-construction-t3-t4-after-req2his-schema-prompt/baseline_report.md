# SR2FPGA Baseline Report: l0-by-construction-t3-t4-after-req2his-schema-prompt

Pass-rate knee: T4 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | generation_failure | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| source | deepseek-his-v12 | 2 | GEN_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| failure_origin | natural_llm | 2 | GEN_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| difficulty_tier | T3 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T4 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| requirement_style | natural_component | 2 | GEN_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| contract_skeleton_mode | behavior_files | 2 | GEN_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| topology_id | t3_stream_fork | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| measurement_point | a_first_attempt_no_tools | 2 | GEN_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| behavior_files | 2 | GEN_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
