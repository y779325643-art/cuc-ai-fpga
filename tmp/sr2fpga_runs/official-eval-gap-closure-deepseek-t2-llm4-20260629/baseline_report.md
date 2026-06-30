# SR2FPGA Baseline Report: official-eval-gap-closure-deepseek-t2-llm4-20260629

Pass-rate knee: T2 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | rtl_compile_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| source | deepseek-his-v12 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| failure_origin | natural_llm | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| requirement_style | natural_component | 1 | L0:1 | 0.0% | 0 | 0.0% |
| contract_skeleton_mode | behavior_files | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | L0:1 | 0.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 1 | L0:1 | 0.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| behavior_files | 1 | L0:1 | 0.0% | 0 | 0.0% |
