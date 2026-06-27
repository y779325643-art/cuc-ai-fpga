# SR2FPGA Baseline Report: deepseek-v4-pro-his-v12-repair-t2-t3-prompt-fidelity

Pass-rate knee: T3 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | rtl_compile_failure | 2 | L1:1, L3:1 | 50.0% | 0 | 0.0% |
| failure_family | rtl_sim_failure | 1 | L1:1 | 0.0% | 0 | 0.0% |
| source | deepseek-his-v12 | 2 | L1:1, L3:1 | 50.0% | 0 | 0.0% |
| failure_origin | natural_llm | 2 | L1:1, L3:1 | 50.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 1 | L1:1 | 0.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 2 | L1:1, L3:1 | 50.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t3_stream_fork | 1 | L1:1 | 0.0% | 0 | 0.0% |
| measurement_point | b_tool_in_loop_repair | 2 | L1:1, L3:1 | 50.0% | 0 | 0.0% |
