# SR2FPGA Baseline Report: qwen-t234

Pass-rate knee: T2 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | generation_failure | 3 | GEN_FAIL:3 | 0.0% | 3 | 100.0% |
| source | qwen | 3 | GEN_FAIL:3 | 0.0% | 3 | 100.0% |
| failure_origin | natural_llm | 3 | GEN_FAIL:3 | 0.0% | 3 | 100.0% |
| difficulty_tier | T2 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T3 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T4 | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| requirement_style | simple_prompt | 3 | GEN_FAIL:3 | 0.0% | 3 | 100.0% |
| topology_id | t2_stream_accumulator | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t3_stream_fork | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t4_dual_stream_join | 1 | GEN_FAIL:1 | 0.0% | 1 | 100.0% |
| measurement_point | a_first_attempt_no_tools | 3 | GEN_FAIL:3 | 0.0% | 3 | 100.0% |
