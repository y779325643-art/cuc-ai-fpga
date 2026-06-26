# SR2FPGA Baseline Report: qwen-t234-coder2

Pass-rate knee: T2 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 2 | L0_FAIL:2 | 0.0% | 2 | 100.0% |
| failure_family | rtl_compile_failure | 1 | L0:1 | 0.0% | 0 | 0.0% |
| source | qwen | 3 | L0:1, L0_FAIL:2 | 0.0% | 2 | 66.7% |
| failure_origin | natural_llm | 3 | L0:1, L0_FAIL:2 | 0.0% | 2 | 66.7% |
| difficulty_tier | T2 | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T3 | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T4 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 3 | L0:1, L0_FAIL:2 | 0.0% | 2 | 66.7% |
| topology_id | t2_stream_accumulator | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t3_stream_fork | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t4_dual_stream_join | 1 | L0:1 | 0.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 3 | L0:1, L0_FAIL:2 | 0.0% | 2 | 66.7% |

## Latent Testbench Issues

| issue_type | count |
|---|---:|
| testbench_stimulus_reaccept_risk | 2 |
