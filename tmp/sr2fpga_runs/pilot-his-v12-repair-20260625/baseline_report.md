# SR2FPGA Baseline Report: pilot-his-v12-repair-20260625

Pass-rate knee: T2 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 1 | L3:1 | 100.0% | 0 | 0.0% |
| failure_family | generation_failure | 2 | GEN_FAIL:2 | 0.0% | 2 | 100.0% |
| source | deepseek-his-v12 | 3 | GEN_FAIL:2, L3:1 | 33.3% | 2 | 66.7% |
| failure_origin | natural_llm | 3 | GEN_FAIL:2, L3:1 | 33.3% | 2 | 66.7% |
| difficulty_tier | T1 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T4 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| requirement_style | simple_prompt | 3 | GEN_FAIL:2, L3:1 | 33.3% | 2 | 66.7% |
| topology_id | t1_event_counter | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t4_dual_stream_join | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| measurement_point | b_tool_in_loop_repair | 3 | GEN_FAIL:2, L3:1 | 33.3% | 2 | 66.7% |
