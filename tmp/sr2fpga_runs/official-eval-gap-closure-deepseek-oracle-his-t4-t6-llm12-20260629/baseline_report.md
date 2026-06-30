# SR2FPGA Baseline Report: official-eval-gap-closure-deepseek-oracle-his-t4-t6-llm12-20260629

Pass-rate knee: T4 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | generation_failure | 2 | GEN_FAIL:2 | 0.0% | 2 | 100.0% |
| failure_family | rtl_compile_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| source | deepseek-oracle-his-v12 | 3 | GEN_FAIL:2, L0:1 | 0.0% | 2 | 66.7% |
| failure_origin | natural_llm | 3 | GEN_FAIL:2, L0:1 | 0.0% | 2 | 66.7% |
| difficulty_tier | T4 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T5 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T6 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| requirement_style | natural_component | 3 | GEN_FAIL:2, L0:1 | 0.0% | 2 | 66.7% |
| contract_skeleton_mode | behavior_files | 3 | GEN_FAIL:2, L0:1 | 0.0% | 2 | 66.7% |
| topology_id | t4_dual_stream_join | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t5_vector_mac_pipeline | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t6_td_update_core | 1 | L0:1 | 0.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 3 | GEN_FAIL:2, L0:1 | 0.0% | 2 | 66.7% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| behavior_files | 3 | GEN_FAIL:2, L0:1 | 0.0% | 2 | 66.7% |
