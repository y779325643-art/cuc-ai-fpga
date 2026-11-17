# 配置文件与安装入口索引

只列当前未忽略的公开配置/制作依赖文件，不读取 configs/local、环境凭证或机器私有路径。JSON Schema 与格式另见[84项契约表](../07-contract-registry.md)。

`configs/current` 表示维护中的旧 runner 示例，并不是 PC2.1 正式实验配置。当前执行器由注册的 pc21-runtime-config-v1 和显式准备的开发配置驱动，不能拿旧 YAML 直接替换。

| 文件 | 角色 |
| --- | --- |
| [agent/configs/archive/sr2fpga_l0_by_construction_ablation.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_ablation.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/archive/sr2fpga_l0_by_construction_ablation_after_fixes.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_ablation_after_fixes.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_behavior_retry.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_behavior_retry.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_req2his_schema_prompt.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_req2his_schema_prompt.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_state_hardening.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_state_hardening.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_top_wiring.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_top_wiring.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_width_parameters.example.yaml](../../../../agent/configs/archive/sr2fpga_l0_by_construction_t3_t4_after_width_parameters.example.yaml) | 历史运行设计/回归参数，非当前默认入口 |
| [agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml](../../../../agent/configs/current/sr2fpga_deterministic_curriculum_smoke.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_his_v12_smoke.example.yaml](../../../../agent/configs/current/sr2fpga_his_v12_smoke.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_l0_by_construction_ablation_after_hardening.example.yaml](../../../../agent/configs/current/sr2fpga_l0_by_construction_ablation_after_hardening.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_l0_by_construction_t3_t4_after_identifier_testbench.example.yaml](../../../../agent/configs/current/sr2fpga_l0_by_construction_t3_t4_after_identifier_testbench.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml](../../../../agent/configs/current/sr2fpga_line_a_l4_dual_tool_reference.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_line_a_l4_representative.example.yaml](../../../../agent/configs/current/sr2fpga_line_a_l4_representative.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_line_a_oracle_evidence.example.yaml](../../../../agent/configs/current/sr2fpga_line_a_oracle_evidence.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_official_eval_gap_closure.example.yaml](../../../../agent/configs/current/sr2fpga_official_eval_gap_closure.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_phase_b_core_closure.example.yaml](../../../../agent/configs/current/sr2fpga_phase_b_core_closure.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_phase_c_core_mutation_closure.example.yaml](../../../../agent/configs/current/sr2fpga_phase_c_core_mutation_closure.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_phase_c_independent_oracle.example.yaml](../../../../agent/configs/current/sr2fpga_phase_c_independent_oracle.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_phase_d_control.example.yaml](../../../../agent/configs/current/sr2fpga_phase_d_control.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/current/sr2fpga_phase_d_multiteacher_pilot.example.yaml](../../../../agent/configs/current/sr2fpga_phase_d_multiteacher_pilot.example.yaml) | 维护中的 legacy runner 示例；检查预算、模型和工具副作用后才能执行 |
| [agent/configs/legacy/sr2fpga_agent.example.yaml](../../../../agent/configs/legacy/sr2fpga_agent.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/configs/legacy/sr2fpga_baseline_a.example.yaml](../../../../agent/configs/legacy/sr2fpga_baseline_a.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/configs/legacy/sr2fpga_baseline_b.example.yaml](../../../../agent/configs/legacy/sr2fpga_baseline_b.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/configs/legacy/sr2fpga_baseline_b_smoke.example.yaml](../../../../agent/configs/legacy/sr2fpga_baseline_b_smoke.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/configs/legacy/sr2fpga_baseline_b_t3_t4_smoke.example.yaml](../../../../agent/configs/legacy/sr2fpga_baseline_b_t3_t4_smoke.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/configs/legacy/sr2fpga_baseline_b_tightened.example.yaml](../../../../agent/configs/legacy/sr2fpga_baseline_b_tightened.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/configs/legacy/sr2fpga_multi_teacher.example.yaml](../../../../agent/configs/legacy/sr2fpga_multi_teacher.example.yaml) | 兼容用旧配置，非PC2.1配置 |
| [agent/pyproject.toml](../../../../agent/pyproject.toml) | 包依赖、可选重依赖、console script 与工具规则 |
| outputs/presentations/project-overview-redesign/package.json（快照 `outputs/presentations/project-overview-redesign/package.json`） | 展示材料制作时的JavaScript依赖描述，不属于Agent运行环境 |
| outputs/presentations/team-sync-redesign/package.json（快照 `outputs/presentations/team-sync-redesign/package.json`） | 展示材料制作时的JavaScript依赖描述，不属于Agent运行环境 |
| outputs/presentations/team-sync/package.json（快照 `outputs/presentations/team-sync/package.json`） | 展示材料制作时的JavaScript依赖描述，不属于Agent运行环境 |
| [pytest.ini](../../../../pytest.ini) | 设置源码搜索路径；未限定testpaths，见默认发现风险 |
| [training/configs/train_lora.example.yaml](../../../../training/configs/train_lora.example.yaml) | 手工训练/数据smoke示例；配置存在不代表已运行 |
| [training/configs/train_qwen_req2file_short.example.yaml](../../../../training/configs/train_qwen_req2file_short.example.yaml) | 手工训练/数据smoke示例；配置存在不代表已运行 |
| [training/configs/train_qwen_smoke.example.yaml](../../../../training/configs/train_qwen_smoke.example.yaml) | 手工训练/数据smoke示例；配置存在不代表已运行 |
| [training/pyproject.toml](../../../../training/pyproject.toml) | 包依赖、可选重依赖、console script 与工具规则 |

## 安装时注册的命令

下表直接读当前 pyproject.toml 的 project.scripts，命令注册不等于在当前环境已经安装。`python -m sr2fpga_agent.pc/execution/analysis` 是另一种包入口，不会自动变成下表的legacy runner。

| 所属包 | 命令 | 实际入口 |
| --- | --- | --- |
| agent | `sr2fpga-agent` | `sr2fpga_agent.cli:main` |
| agent | `sr2fpga-runner` | `sr2fpga_agent.runner:main` |
| agent | `sr2fpga-baseline-report` | `sr2fpga_agent.baseline_report:main` |
| agent | `sr2fpga-req2file-eval` | `sr2fpga_agent.req2file_eval:main` |
| agent | `sr2fpga-task-evidence` | `sr2fpga_agent.task_evidence:main` |
| agent | `sr2fpga-ambiguity-audit` | `sr2fpga_agent.ambiguity_audit_runner:main` |
| training | `sr2fpga-prepare-dataset` | `sr2fpga_training.prepare_dataset:main` |
| training | `sr2fpga-training-dry-run` | `sr2fpga_training.training_dry_run:main` |
| training | `sr2fpga-train-lora` | `sr2fpga_training.train_lora:main` |
| training | `sr2fpga-merge-lora` | `sr2fpga_training.merge_lora:main` |

配置/包描述文件合计：36。没有发现当前工作区 `.github` 下的CI配置；不能据此推断服务器外部CI不存在。
