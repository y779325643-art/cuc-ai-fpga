# SR2FPGA Baseline Report: deepseek-baseline-b-t3-t4-smoke

Pass-rate knee: T3 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 2 | L0:1, L1:1 | 0.0% | 1 | 50.0% |
| failure_family | rtl_compile_failure | 1 | L1:1 | 0.0% | 0 | 0.0% |
| failure_family | rtl_sim_failure | 1 | L1:1 | 0.0% | 0 | 0.0% |
| source | deepseek | 2 | L0:1, L1:1 | 0.0% | 1 | 50.0% |
| failure_origin | natural_llm | 2 | L0:1, L1:1 | 0.0% | 1 | 50.0% |
| difficulty_tier | T3 | 1 | L0:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T4 | 1 | L1:1 | 0.0% | 0 | 0.0% |
| requirement_style | natural_component | 2 | L0:1, L1:1 | 0.0% | 1 | 50.0% |
| topology_id | t3_stream_fork | 1 | L0:1 | 0.0% | 1 | 100.0% |
| topology_id | t4_dual_stream_join | 1 | L1:1 | 0.0% | 0 | 0.0% |
| measurement_point | b_tool_in_loop_repair | 2 | L0:1, L1:1 | 0.0% | 1 | 50.0% |
