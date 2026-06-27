# SR2FPGA Baseline Report: deepseek-v4-pro-his-v12-repair-t1-t4-fidelity-fresh

Pass-rate knee: T2 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 1 | L3:1 | 100.0% | 0 | 0.0% |
| failure_family | generation_failure | 2 | GEN_FAIL:2 | 0.0% | 2 | 100.0% |
| failure_family | repair_failure | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| source | deepseek-his-v12 | 4 | GEN_FAIL:2, L0_FAIL:1, L3:1 | 25.0% | 3 | 75.0% |
| failure_origin | natural_llm | 4 | GEN_FAIL:2, L0_FAIL:1, L3:1 | 25.0% | 3 | 75.0% |
| difficulty_tier | T1 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T3 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T4 | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| requirement_style | simple_prompt | 4 | GEN_FAIL:2, L0_FAIL:1, L3:1 | 25.0% | 3 | 75.0% |
| topology_id | t1_event_counter | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t3_stream_fork | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t4_dual_stream_join | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| measurement_point | b_tool_in_loop_repair | 4 | GEN_FAIL:2, L0_FAIL:1, L3:1 | 25.0% | 3 | 75.0% |
