# SR2FPGA Baseline Report: deepseek-baseline-b-tightened

Pass-rate knee: T3 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 4 | L0:2, L3:2 | 50.0% | 1 | 25.0% |
| failure_family | rtl_compile_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| source | deepseek | 4 | L0:2, L3:2 | 50.0% | 1 | 25.0% |
| failure_origin | natural_llm | 4 | L0:2, L3:2 | 50.0% | 1 | 25.0% |
| difficulty_tier | T1 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T4 | 1 | L0:1 | 0.0% | 1 | 100.0% |
| requirement_style | natural_component | 4 | L0:2, L3:2 | 50.0% | 1 | 25.0% |
| topology_id | t1_event_counter | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t3_stream_fork | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | L0:1 | 0.0% | 1 | 100.0% |
| measurement_point | b_tool_in_loop_repair | 4 | L0:2, L3:2 | 50.0% | 1 | 25.0% |
