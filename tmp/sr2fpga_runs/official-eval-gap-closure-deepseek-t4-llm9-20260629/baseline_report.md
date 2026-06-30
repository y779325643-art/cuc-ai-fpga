# SR2FPGA Baseline Report: official-eval-gap-closure-deepseek-t4-llm9-20260629

Pass-rate knee: T4 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | generation_failure | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| source | deepseek-his-v12 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| failure_origin | natural_llm | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T4 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| requirement_style | natural_component | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| contract_skeleton_mode | behavior_files | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t4_dual_stream_join | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| measurement_point | a_first_attempt_no_tools | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| behavior_files | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
