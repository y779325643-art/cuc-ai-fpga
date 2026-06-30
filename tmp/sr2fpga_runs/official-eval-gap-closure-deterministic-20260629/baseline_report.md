# SR2FPGA Baseline Report: official-eval-gap-closure-deterministic-20260629

Pass-rate knee: T3 (L3 pass rate 0.0% < 80.0%).

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| failure_family | artifact_contract_failure | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| failure_family | rtl_compile_failure | 5 | L0:5 | 0.0% | 0 | 0.0% |
| failure_family | rtl_sim_failure | 1 | L1:1 | 0.0% | 0 | 0.0% |
| source | deterministic | 14 | L0:5, L0_FAIL:1, L1:1, L3:7 | 50.0% | 1 | 7.1% |
| failure_origin | compositional_assembly | 14 | L0:5, L0_FAIL:1, L1:1, L3:7 | 50.0% | 1 | 7.1% |
| difficulty_tier | T1 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 1 | L1:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T4 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T5 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T6 | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| difficulty_tier | T7 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T8 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T9 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | T10 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T11 | 1 | L0:1 | 0.0% | 0 | 0.0% |
| difficulty_tier | T12 | 1 | L3:1 | 100.0% | 0 | 0.0% |
| difficulty_tier | S1 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| requirement_style | contract | 2 | L3:2 | 100.0% | 0 | 0.0% |
| requirement_style | natural_component | 12 | L0:5, L0_FAIL:1, L1:1, L3:5 | 41.7% | 1 | 8.3% |
| contract_skeleton_mode | deterministic_template | 14 | L0:5, L0_FAIL:1, L1:1, L3:7 | 50.0% | 1 | 7.1% |
| topology_id | t10_rl_accelerator_shell | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t11_batch_rl_accelerator_shell | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t12_replay_arbiter_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t1_event_counter | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t3_stream_fork | 1 | L1:1 | 0.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t5_vector_mac_pipeline | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t6_td_update_core | 1 | L0_FAIL:1 | 0.0% | 1 | 100.0% |
| topology_id | t7_policy_value_shell | 1 | L0:1 | 0.0% | 0 | 0.0% |
| topology_id | t8_replay_sample_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t9_host_protocol_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 14 | L0:5, L0_FAIL:1, L1:1, L3:7 | 50.0% | 1 | 7.1% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 14 | L0:5, L0_FAIL:1, L1:1, L3:7 | 50.0% | 1 | 7.1% |
