# SR2FPGA Baseline Report: l0-by-construction-t3-t4-after-state-hardening

Pass-rate knee: T3 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | rtl_compile_failure | 2 | L0:2 | 0.0% | 0 | 0.0% |
| source | deepseek-his-v12 | 2 | L0:2 | 0.0% | 0 | 0.0% |
| failure_origin | natural_llm | 2 | L0:2 | 0.0% | 0 | 0.0% |
| difficulty_tier | T3 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T4 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| requirement_style | natural_component | 2 | L0:2 | 0.0% | 0 | 0.0% |
| contract_skeleton_mode | behavior_files | 2 | L0:2 | 0.0% | 0 | 0.0% |
| topology_id | t3_stream_fork | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | L0:1 | 0.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 2 | L0:2 | 0.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| behavior_files | 2 | L0:2 | 0.0% | 0 | 0.0% |
