# SR2FPGA Baseline Report: t0-t4-deterministic-smoke

Pass-rate knee: not observed above threshold 80.0%.

| group | value | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---|---:|---|---:|---:|---:|
| source | deterministic | 24 | L3:24 | 100.0% | 0 | 0.0% |
| failure_origin | deterministic | 24 | L3:24 | 100.0% | 0 | 0.0% |
| difficulty_tier | T0 | 12 | L3:12 | 100.0% | 0 | 0.0% |
| difficulty_tier | T1 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| difficulty_tier | T2 | 2 | L3:2 | 100.0% | 0 | 0.0% |
| difficulty_tier | T3 | 4 | L3:4 | 100.0% | 0 | 0.0% |
| difficulty_tier | T4 | 4 | L3:4 | 100.0% | 0 | 0.0% |
| requirement_style | simple_prompt | 24 | L3:24 | 100.0% | 0 | 0.0% |
| contract_skeleton_mode | deterministic_template | 24 | L3:24 | 100.0% | 0 | 0.0% |
| topology_id | t10_rl_accelerator_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t11_batch_rl_accelerator_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t12_replay_arbiter_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t1_event_counter | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t2_stream_accumulator | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t3_stream_fork | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t4_dual_stream_join | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t5_vector_mac_pipeline | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t6_td_update_core | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t7_policy_value_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t8_replay_sample_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| topology_id | t9_host_protocol_shell | 1 | L3:1 | 100.0% | 0 | 0.0% |
| measurement_point | a_first_attempt_no_tools | 24 | L3:24 | 100.0% | 0 | 0.0% |

## Contract Skeleton Ablation

| mode | total | pass_levels | L3 pass rate | L0 contract failures | cross-file error rate |
|---|---:|---|---:|---:|---:|
| deterministic_template | 24 | L3:24 | 100.0% | 0 | 0.0% |
