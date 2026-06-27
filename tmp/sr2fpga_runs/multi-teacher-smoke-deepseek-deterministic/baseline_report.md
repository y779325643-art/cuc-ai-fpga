# SR2FPGA Baseline Report: multi-teacher-smoke-deepseek-deterministic

Pass-rate knee: T1 (L3 pass rate 50.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| source | deepseek-his-v12 | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| source | deterministic | 1 | L3:1 | 100.0% | 0 | 0.0% |
| failure_origin | deterministic_template | 1 | L3:1 | 100.0% | 0 | 0.0% |
| failure_origin | natural_llm | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T1 | 2 | L0_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| requirement_style | simple_prompt | 2 | L0_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| topology_id | t1_event_counter | 2 | L0_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
| measurement_point | a_first_attempt_no_tools | 2 | L0_FAIL:1, L3:1 | 50.0% | 1 | 50.0% |
