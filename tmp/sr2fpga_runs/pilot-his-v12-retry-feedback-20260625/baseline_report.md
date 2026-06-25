# SR2FPGA Baseline Report: pilot-his-v12-retry-feedback-20260625

Pass-rate knee: T2 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| failure_family | generation_failure | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| failure_family | rtl_compile_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| source | deepseek-his-v12 | 2 | GEN_FAIL:1, L0:1 | 0.0% | 1 | 50.0% |
| failure_origin | natural_llm | 2 | GEN_FAIL:1, L0:1 | 0.0% | 1 | 50.0% |
| difficulty_tier | T2 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T4 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| requirement_style | simple_prompt | 2 | GEN_FAIL:1, L0:1 | 0.0% | 1 | 50.0% |
| topology_id | t2_stream_accumulator | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| measurement_point | b_tool_in_loop_repair | 2 | GEN_FAIL:1, L0:1 | 0.0% | 1 | 50.0% |
