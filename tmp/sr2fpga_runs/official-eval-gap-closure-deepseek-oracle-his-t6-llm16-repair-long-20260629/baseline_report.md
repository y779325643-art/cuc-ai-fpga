# SR2FPGA Baseline Report: official-eval-gap-closure-deepseek-oracle-his-t6-llm16-repair-long-20260629

Pass-rate knee: T6 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | rtl_compile_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| source | deepseek-oracle-his-v12 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| failure_origin | natural_llm | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T6 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| requirement_style | natural_component | 1 | L0:1 | 0.0% | 0 | 0.0% |
| contract_skeleton_mode | behavior_files | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t6_td_update_core | 1 | L0:1 | 0.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 1 | L0:1 | 0.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| behavior_files | 1 | L0:1 | 0.0% | 0 | 0.0% |
