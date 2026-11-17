# agent-legacy-shared：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/__init__.py) · 25 行 · SHA-256 `a7fd5a6ac621aa9c94b568bff09471f2b47da7baa65210e3db9d46f54c270fe3`

> SR2FPGA lightweight data generation agent.

导入模块：`sr2fpga_agent.agent`、`sr2fpga_agent.generation`、`sr2fpga_agent.models`、`sr2fpga_agent.project_generator`、`sr2fpga_agent.providers`、`sr2fpga_agent.repair`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/agent.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/agent.py) · 3740 行 · SHA-256 `af571d72de3b811dfdae612816e5c97f7cc64aeaf936d707986029f8229c7ac3`

> High-level SR2FPGA data generation orchestration.

导入模块：`__future__`、`dataclasses`、`difflib`、`hashlib`、`json`、`os`、`pathlib`、`shlex`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.evaluator_dispatch`、`sr2fpga_agent.failure_injector`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.generation.req2his`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.log_parser`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.openxc7_report`、`sr2fpga_agent.oracle_runner`、`sr2fpga_agent.oracles`、`sr2fpga_agent.oracles.types`、`sr2fpga_agent.paired_measurement`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.project_contract`、`sr2fpga_agent.project_generator`、`sr2fpga_agent.public_evaluator`、`sr2fpga_agent.public_l2_harness`、`sr2fpga_agent.recorder`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.rtl_identifier_checker`、`sr2fpga_agent.semantic_trace`、`sr2fpga_agent.system_his_checker`、`sr2fpga_agent.system_his_fidelity`、`sr2fpga_agent.terminal_selection`、`sr2fpga_agent.testbench_checker`、`sr2fpga_agent.tool_runner`、`sr2fpga_agent.vivado_report`、`subprocess`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_RequirementBoundaryMetadataError` — `_RequirementBoundaryMetadataError` | class / [123](../../../../agent/src/sr2fpga_agent/agent.py#L123) | 无直接调用 |
| `DataGenerationAgent` — `DataGenerationAgent` | class / [127](../../../../agent/src/sr2fpga_agent/agent.py#L127) | 无直接调用 |
| `DataGenerationAgent.__init__` — `__init__(self, dataset_root, command_runner, project_generator, repairer, system_his_repairer, repair_provider_name, max_attempts, enable_openxc7_l4, openxc7_tool, openxc7_command, openxc7_part, openxc7_board_profile, openxc7_timeout_seconds, enable_vivado_l4, vivado_tool, vivado_command, vivado_part, vivado_timeout_seconds, enable_independent_oracle, development_hidden_evaluation_authority, development_hidden_private_commitment, development_attempt_public_evaluation_authority, development_terminal_public_evaluation_authority, development_public_candidate_store, development_public_evaluator_store, development_public_workspace_root, development_trusted_public_l2_harness, attempt_cost_ledger_factory, attempt_cost_router, tool_versions, tool_environment_ref, l4_tool_environment, l4_tool_environment_ref)` | function / [130](../../../../agent/src/sr2fpga_agent/agent.py#L130) | `AccountingCommandRunner`、`CommandRunner`、`DatasetRecorder`、`DevelopmentAttemptPublicEvaluationAuthority`、`DevelopmentPublicToolEvaluator`、`DevelopmentTerminalPublicEvaluationAuthority`、`ProjectGenerator`、`ValueError`、`_embedded_system_his_repairer`、`all`、`any`、`bytes`、`dict` |
| `DataGenerationAgent.run_one` — `run_one(self, sample_id, requirement, request, platform, metadata)` | function / [310](../../../../agent/src/sr2fpga_agent/agent.py#L310) | `dict`、`self._development_hidden_conformance_outcome_ref.to_dict`、`self._development_hidden_execution_state_ref.to_dict`、`self._development_selected_public_outcome_ref.to_dict`、`self._development_terminal_public_outcome_ref.to_dict`、`self._development_terminal_selection_ref.to_dict`、`self._finish_cost_attempt`、`self._reconcile_attempt_trajectory`、`self._run_one_impl`、`self.last_canonical_trajectory.artifact_ref.to_dict`、`summary.artifact_ref.to_dict` |
| `DataGenerationAgent._run_one_impl` — `_run_one_impl(self, sample_id, requirement, request, platform, metadata)` | function / [380](../../../../agent/src/sr2fpga_agent/agent.py#L380) | `<dynamic>.get`、`<dynamic>.replace`、`AttemptRecord`、`GeneratedProject`、`SystemHisValidationError`、`TerminalSelectionCandidate`、`ValueError`、`_authoritative_agent_diagnosis`、`_authoritative_public_tool_results`、`_automatic_pass_credit_reason`、`_diagnose_first_failure`、`_expected_bram`、`_generation_failure_tool_result`、`_h_stage_tool_result`、`_h_stages_applicable`、`_l0_tool_result`、`_l4_open_record`、`_labels`、`_measured_qor`、`_normalize_missing_tool`、`_not_applicable_h_stage_report`、`_not_run_h_stage_report`、`_openxc7_pnr_command`、`_oracle_bundle_failure_tool_result`、`_oracle_error_profile`、`_oracle_not_run_profile`、`_oracle_profile`、`_raw_tool_pass_level`、`_repair_eligibility`、`_repair_failure_diagnosis`、`_repair_failure_tool_result`、`_req_his_fidelity`、`_requirement_boundary_stop`、`_run_l4_commercial_reference`、`_sha256`、`_stage_entries`、`_supports_staged_his_generation`、`_system_his_candidate_project`、`_system_his_failure_diagnosis`、`_system_his_patch`、`_system_his_repair_provider`、`_tool_infrastructure_reason`、`_tool_non_repairable_reason`、`_trajectory`、`_validate_generated_project_h_stages`、`_write_project`、`all`、`all_stage_entries.extend`、`attempt_measurements.append`、`bool`、`build_episode_measurement`、`build_oracle_bundle_for_request`、`build_patch_metadata`、`check_his_project_consistency`、`check_project_package_l0`、`development_selection_candidates.append`、`diagnosis.get`、`dict`、`final_oracle_profile.get`、`final_tool_results.get`、`finalize_patch_metadata`、`first_failed_h_stage`、`float`、`isinstance`、`json.dumps`、`l4_commercial.get`、`labels.get`、`max`、`metadata.get`、`patch.to_dict`、`patches.append`、`previous_patch.repair_regression.get`、`project.files.get`、`range`、`replace`、`self._active_cost_ledger.record_cost`、`self._development_public_authority_enabled`、`self._evaluate_development_attempt_publicly`、`self._finish_cost_attempt`、`self._oracle_strength`、`self._record_generation_failure`、`self._reserve_outer_repair_attempt`、`self._run_development_hidden_evaluation`、`self._run_development_terminal_public_evaluation`、`self._run_pipeline`、`self._seal_terminal_candidate`、`self._select_and_seal_development_terminal`、`self._start_cost_attempt`、`self.command_runner.run`、`self.project_generator.generate`、`self.project_generator.generate_from_system_his`、`self.project_generator.generate_system_his`、`self.recorder.start_sample`、`self.recorder.update_patch_metadata`、`self.recorder.write_attempt`、`self.recorder.write_final`、`self.repairer.repair`、`self.system_his_repairer.repair`、`str`、`time.monotonic`、`tool_results.items`、`validate_sample_id`、`validate_system_his_payload_h_stages` |
| `DataGenerationAgent._start_cost_attempt` — `_start_cost_attempt(self, attempt_id)` | function / [1061](../../../../agent/src/sr2fpga_agent/agent.py#L1061) | `ValueError`、`factory`、`router.activate`、`time.monotonic` |
| `DataGenerationAgent._reconcile_attempt_trajectory` — `_reconcile_attempt_trajectory(self)` | function / [1077](../../../../agent/src/sr2fpga_agent/agent.py#L1077) | `reconcile_attempt_trajectory` |
| `DataGenerationAgent._development_public_authority_enabled` — `_development_public_authority_enabled(self, metadata)` | function / [1099](../../../../agent/src/sr2fpga_agent/agent.py#L1099) | `<dynamic>.get`、`<dynamic>.strip`、`<dynamic>.upper`、`str` |
| `DataGenerationAgent._evaluate_development_attempt_publicly` — `_evaluate_development_attempt_publicly(self, sample_id, request, metadata, project, attempt_id)` | function / [1111](../../../../agent/src/sr2fpga_agent/agent.py#L1111) | `ValueError`、`_public_envelope_failure_reason`、`authority.candidate_store.root.resolve`、`authority.evaluate_once`、`method_policy_sha256`、`read_verified_development_authoritative_attempt_public_outcome`、`self._build_project_envelope_ref`、`self._development_projection_sha256`、`store.append_event`、`store.root.resolve`、`store.seal_public_evaluation_candidate`、`store.seal_unverified_public_evaluation_candidate` |
| `DataGenerationAgent._build_project_envelope_ref` — `_build_project_envelope_ref(self, store, sample_id, method_condition, candidate_id, attempt_id, project)` | function / [1184](../../../../agent/src/sr2fpga_agent/agent.py#L1184) | `_sha256`、`_trusted_event_id`、`build_composite_project_envelope`、`build_project_envelope`、`method_policy_sha256`、`store.append_event`、`store.put_validated_json` |
| `DataGenerationAgent._select_and_seal_development_terminal` — `_select_and_seal_development_terminal(self, sample_id, request, metadata, candidates, outcomes, his_validations)` | function / [1248](../../../../agent/src/sr2fpga_agent/agent.py#L1248) | `<dynamic>.get`、`TerminalSelectionError`、`_artifact_ref_from_payload`、`_authoritative_public_tool_results`、`candidate_payload.get`、`int`、`isinstance`、`json.loads`、`read_verified_development_authoritative_attempt_public_outcome`、`select_development_terminal_candidate`、`selected_attempt.removeprefix`、`store.append_event`、`store.read_public_evaluation_candidate`、`store.read_verified`、`store.seal_candidate`、`str` |
| `DataGenerationAgent._run_development_terminal_public_evaluation` — `_run_development_terminal_public_evaluation(self, request, metadata)` | function / [1326](../../../../agent/src/sr2fpga_agent/agent.py#L1326) | `ValueError`、`authority.candidate_store.root.resolve`、`authority.evaluate_once`、`method_policy_sha256`、`read_verified_development_authoritative_attempt_public_outcome`、`self._development_projection_sha256`、`store.root.resolve` |
| `DataGenerationAgent._seal_terminal_candidate` — `_seal_terminal_candidate(self, sample_id, request, metadata, project, final_attempt_id, tool_results, his_validation)` | function / [1368](../../../../agent/src/sr2fpga_agent/agent.py#L1368) | `_raw_tool_pass_level`、`_sha256`、`_trusted_event_id`、`build_composite_project_envelope`、`build_project_envelope`、`method_policy_sha256`、`self._development_projection_sha256`、`store.append_event`、`store.put_validated_json`、`store.seal_candidate`、`str` |
| `DataGenerationAgent._finish_cost_attempt` — `_finish_cost_attempt(self, emergency)` | function / [1487](../../../../agent/src/sr2fpga_agent/agent.py#L1487) | `ledger.close`、`ledger.record_cost`、`max`、`reconcile_cost_events`、`router.deactivate`、`self.last_cost_summaries.append`、`set`、`sorted`、`time.monotonic` |
| `DataGenerationAgent._reserve_outer_repair_attempt` — `_reserve_outer_repair_attempt(self)` | function / [1519](../../../../agent/src/sr2fpga_agent/agent.py#L1519) | `ledger.reserve`、`max` |
| `DataGenerationAgent._oracle_strength` — `_oracle_strength(self, project, sample_dir, platform, task_type, reference_results, oracle_bundle)` | function / [1533](../../../../agent/src/sr2fpga_agent/agent.py#L1533) | `ToolResult`、`_write_oracle_mutation_evidence`、`_write_project`、`build_oracle_strength`、`mutation_results.get`、`mutations.items`、`oracle_mutation_projects`、`reference_results.get`、`self._run_pipeline` |
| `DataGenerationAgent._run_development_hidden_evaluation` — `_run_development_hidden_evaluation(self, sample_id, request, metadata, project, tool_results, his_validation)` | function / [1580](../../../../agent/src/sr2fpga_agent/agent.py#L1580) | `<dynamic>.get`、`<dynamic>.strip`、`<dynamic>.upper`、`authority.candidate_store.root.resolve`、`authority.evaluate_once`、`authority.publish_sanitized_outcome`、`authority.store_private_commitment`、`cost_store.read_verified`、`cost_store.reference`、`cost_store.root.resolve`、`development_hidden_case_seed`、`first_failed_h_stage`、`hidden_state.get`、`json.loads`、`method_policy_sha256`、`outcome.outcome_id.removeprefix`、`outcome.to_dict`、`self._development_projection_sha256`、`self._record_hidden_evaluator_cost`、`str`、`time.monotonic`、`tool_results.get` |
| `DataGenerationAgent._record_hidden_evaluator_cost` — `_record_hidden_evaluator_cost(self, started, status, infrastructure_retries)` | function / [1669](../../../../agent/src/sr2fpga_agent/agent.py#L1669) | `ledger.record_cost`、`max`、`time.monotonic` |
| `DataGenerationAgent._development_projection_sha256` — `_development_projection_sha256(self, metadata, request, method_condition)` | function / [1686](../../../../agent/src/sr2fpga_agent/agent.py#L1686) | `<dynamic>.get`、`_sha256`、`context.get`、`isinstance`、`len`、`pack.get` |
| `DataGenerationAgent._record_generation_failure` — `_record_generation_failure(self, sample_id, sample_dir, request, exc, metadata)` | function / [1714](../../../../agent/src/sr2fpga_agent/agent.py#L1714) | `<dynamic>.get`、`AttemptRecord`、`GeneratedProject`、`ToolResult`、`_generation_boundary_failure`、`_generation_failure_affected_files`、`_generation_failure_labels`、`_generation_infrastructure_reason`、`_h_stages_applicable`、`_l4_commercial_record`、`_l4_open_record`、`_measured_qor`、`_not_applicable_h_stage_report`、`_stage_entries`、`_trajectory`、`build_episode_measurement`、`diagnosis.update`、`h_stage_labels`、`isinstance`、`labels.update`、`list`、`self.recorder.write_attempt`、`self.recorder.write_final`、`str` |
| `DataGenerationAgent._run_pipeline` — `_run_pipeline(self, project, project_dir, platform, oracle_bundle, oracle_evidence_out, oracle_evidence_path)` | function / [1863](../../../../agent/src/sr2fpga_agent/agent.py#L1863) | `_normalize_missing_tool`、`_not_run_tool_result`、`_openxc7_pnr_command`、`_oracle_boundary_failure_evidence`、`_oracle_boundary_failure_tool_result`、`_synth_input_tool_result`、`_testbench_needs_oracle`、`_unsupported_synth_language_tool_result`、`_validate_simulation_output`、`build_yosys_script`、`check_rtl_identifiers`、`check_testbench_static_issues`、`len`、`list`、`manifest.artifact_paths_by_role.get`、`oracle_evidence_out.append`、`replace`、`resolve_project_manifest`、`rtl_identifier_tool_result`、`run_oracle_scenarios`、`self.command_runner.run`、`testbench_observation_tool_result`、`write_oracle_run_evidence` |
| `_write_project` — `_write_project(project_dir, project)` | function / [2047](../../../../agent/src/sr2fpga_agent/agent.py#L2047) | `project.files.items`、`project_file_target`、`target.parent.mkdir`、`target.write_text` |
| `_l0_tool_result` — `_l0_tool_result(result, checker)` | function / [2054](../../../../agent/src/sr2fpga_agent/agent.py#L2054) | `<dynamic>.join`、`ToolResult` |
| `_h_stage_tool_result` — `_h_stage_tool_result(report)` | function / [2070](../../../../agent/src/sr2fpga_agent/agent.py#L2070) | `<dynamic>.get`、`<dynamic>.join`、`ToolResult`、`first_failed_h_stage`、`report.get`、`str` |
| `_oracle_bundle_failure_tool_result` — `_oracle_bundle_failure_tool_result(exc)` | function / [2084](../../../../agent/src/sr2fpga_agent/agent.py#L2084) | `ToolResult`、`str` |
| `_oracle_not_run_profile` — `_oracle_not_run_profile(family_id, skip_reason)` | function / [2096](../../../../agent/src/sr2fpga_agent/agent.py#L2096) | 无直接调用 |
| `_oracle_error_profile` — `_oracle_error_profile(family_id, exc, failure_type)` | function / [2108](../../../../agent/src/sr2fpga_agent/agent.py#L2108) | `str` |
| `_oracle_profile` — `_oracle_profile(family_id, bundle, evidence)` | function / [2127](../../../../agent/src/sr2fpga_agent/agent.py#L2127) | `_oracle_error_profile`、`_oracle_evidence_is_infrastructure`、`_oracle_not_run_profile`、`evidence.class_status`、`evidence.scenario_counts`、`profile.update`、`sanitize_oracle_profile` |
| `_oracle_boundary_failure_evidence` — `_oracle_boundary_failure_evidence(bundle, exc, failure_type, scenario_results)` | function / [2175](../../../../agent/src/sr2fpga_agent/agent.py#L2175) | `OracleRunEvidence`、`str` |
| `_oracle_boundary_failure_tool_result` — `_oracle_boundary_failure_tool_result(exc, failure_type)` | function / [2193](../../../../agent/src/sr2fpga_agent/agent.py#L2193) | `ToolResult` |
| `_oracle_evidence_is_infrastructure` — `_oracle_evidence_is_infrastructure(evidence)` | function / [2205](../../../../agent/src/sr2fpga_agent/agent.py#L2205) | 无直接调用 |
| `_repair_failure_tool_result` — `_repair_failure_tool_result(exc)` | function / [2212](../../../../agent/src/sr2fpga_agent/agent.py#L2212) | `ToolResult`、`str` |
| `_generation_failure_tool_result` — `_generation_failure_tool_result(exc)` | function / [2224](../../../../agent/src/sr2fpga_agent/agent.py#L2224) | `ToolResult`、`str` |
| `_synth_input_tool_result` — `_synth_input_tool_result(exc)` | function / [2236](../../../../agent/src/sr2fpga_agent/agent.py#L2236) | `ToolResult`、`str` |
| `_unsupported_synth_language_tool_result` — `_unsupported_synth_language_tool_result(exc)` | function / [2248](../../../../agent/src/sr2fpga_agent/agent.py#L2248) | `ToolResult`、`str` |
| `_normalize_missing_tool` — `_normalize_missing_tool(result)` | function / [2261](../../../../agent/src/sr2fpga_agent/agent.py#L2261) | `replace` |
| `_tool_infrastructure_reason` — `_tool_infrastructure_reason(tool_results)` | function / [2272](../../../../agent/src/sr2fpga_agent/agent.py#L2272) | `result.stage.startswith`、`tool_results.values` |
| `_tool_non_repairable_reason` — `_tool_non_repairable_reason(tool_results)` | function / [2283](../../../../agent/src/sr2fpga_agent/agent.py#L2283) | `_tool_infrastructure_reason`、`tool_results.values` |
| `_repair_failure_diagnosis` — `_repair_failure_diagnosis(exc, upstream_diagnosis)` | function / [2290](../../../../agent/src/sr2fpga_agent/agent.py#L2290) | `_generation_failure_affected_files`、`_repair_failure_type`、`str` |
| `_repair_failure_type` — `_repair_failure_type(exc)` | function / [2300](../../../../agent/src/sr2fpga_agent/agent.py#L2300) | `<dynamic>.lower`、`str` |
| `_automatic_pass_credit_reason` — `_automatic_pass_credit_reason(patches)` | function / [2307](../../../../agent/src/sr2fpga_agent/agent.py#L2307) | `any` |
| `_public_envelope_failure_reason` — `_public_envelope_failure_reason(exc)` | function / [2315](../../../../agent/src/sr2fpga_agent/agent.py#L2315) | `str` |
| `_artifact_ref_from_payload` — `_artifact_ref_from_payload(payload)` | function / [2324](../../../../agent/src/sr2fpga_agent/agent.py#L2324) | `ArtifactRef`、`payload.get` |
| `_authoritative_public_tool_results` — `_authoritative_public_tool_results(outcome)` | function / [2333](../../../../agent/src/sr2fpga_agent/agent.py#L2333) | `ToolResult`、`stage_names.items` |
| `_authoritative_agent_diagnosis` — `_authoritative_agent_diagnosis(diagnosis)` | function / [2361](../../../../agent/src/sr2fpga_agent/agent.py#L2361) | 无直接调用 |
| `_generation_failure_affected_files` — `_generation_failure_affected_files(exc)` | function / [2373](../../../../agent/src/sr2fpga_agent/agent.py#L2373) | `<dynamic>.lower`、`str` |
| `_diagnose_first_failure` — `_diagnose_first_failure(tool_results, l0_result, system_his_applicable)` | function / [2380](../../../../agent/src/sr2fpga_agent/agent.py#L2380) | `_is_l4_non_model_not_run_result`、`_structured_diagnosis`、`classify_failure`、`log_text.strip`、`result.stage.startswith`、`tool_results.values` |
| `_system_his_failure_diagnosis` — `_system_his_failure_diagnosis(report)` | function / [2437](../../../../agent/src/sr2fpga_agent/agent.py#L2437) | `<dynamic>.join`、`failed_stage.upper`、`first_failed_h_stage`、`isinstance`、`list`、`report.get`、`stage_report.get`、`str` |
| `_write_oracle_mutation_evidence` — `_write_oracle_mutation_evidence(sample_dir, project_dir, tool_results)` | function / [2458](../../../../agent/src/sr2fpga_agent/agent.py#L2458) | `<dynamic>.as_posix`、`<dynamic>.write_text`、`_diagnose_first_failure`、`asdict`、`diagnosis.get`、`eval_dir.mkdir`、`isinstance`、`json.dumps`、`project_dir.relative_to`、`structured.get`、`tool_results.get`、`tool_results.items` |
| `_structured_diagnosis` — `_structured_diagnosis(result, log_text, failure_type)` | function / [2499](../../../../agent/src/sr2fpga_agent/agent.py#L2499) | `any`、`classify_failure`、`diagnose_semantic_trace`、`parse_semantic_trace`、`parse_test_fail_mismatches`、`parse_tool_warnings`、`parse_yosys_stats`、`trace.values` |
| `_validate_simulation_output` — `_validate_simulation_output(result)` | function / [2518](../../../../agent/src/sr2fpga_agent/agent.py#L2518) | `replace` |
| `_testbench_needs_oracle` — `_testbench_needs_oracle(testbench)` | function / [2535](../../../../agent/src/sr2fpga_agent/agent.py#L2535) | 无直接调用 |
| `_not_run_tool_result` — `_not_run_tool_result(stage, skip_reason)` | function / [2539](../../../../agent/src/sr2fpga_agent/agent.py#L2539) | `ToolResult` |
| `_measured_qor` — `_measured_qor(tool_results, l4_open, l4_commercial)` | function / [2552](../../../../agent/src/sr2fpga_agent/agent.py#L2552) | `_empty_measured_qor`、`_l4_commercial_record`、`dict`、`l4_open.get`、`measured_qor.update`、`parse_yosys_stats`、`tool_results.get` |
| `_generation_failure_labels` — `_generation_failure_labels(l4_open, l4_commercial)` | function / [2590](../../../../agent/src/sr2fpga_agent/agent.py#L2590) | `_l4_commercial_record` |
| `_labels` — `_labels(tool_results, l4_open, final_attempt_id, failure_count, his_validation, oracle_strength, enforce_oracle_readiness, expected_bram, l4_commercial, oracle_profile)` | function / [2634](../../../../agent/src/sr2fpga_agent/agent.py#L2634) | `_h_stages_not_applicable`、`_l2_sim_outcome`、`_l4_agreement_class`、`_l4_commercial_record`、`_oracle_not_run_profile`、`_raw_tool_pass_level`、`_tool_infrastructure_reason`、`_tool_log`、`_tool_mismatches`、`_tool_stage_outcome`、`_tool_warnings`、`dict`、`first_failed_h_stage`、`h_stage_labels`、`l4_open.get`、`labels.setdefault`、`labels.update`、`oracle_profile.get`、`oracle_strength.get`、`parse_yosys_stats`、`str`、`tool_results.get` |
| `_tool_stage_outcome` — `_tool_stage_outcome(result)` | function / [2773](../../../../agent/src/sr2fpga_agent/agent.py#L2773) | `<dynamic>.get` |
| `_l2_sim_outcome` — `_l2_sim_outcome(tool_results)` | function / [2782](../../../../agent/src/sr2fpga_agent/agent.py#L2782) | `tool_results.get` |
| `_raw_tool_pass_level` — `_raw_tool_pass_level(tool_results, his_validation)` | function / [2800](../../../../agent/src/sr2fpga_agent/agent.py#L2800) | `failed_h_stage.upper`、`first_failed_h_stage`、`tool_results.get` |
| `_repair_eligibility` — `_repair_eligibility(diagnosis, h_stage_failed, oracle_infrastructure_failure, has_repairer, attempt_id, max_attempts)` | function / [2832](../../../../agent/src/sr2fpga_agent/agent.py#L2832) | 无直接调用 |
| `_generation_infrastructure_reason` — `_generation_infrastructure_reason(exc)` | function / [2854](../../../../agent/src/sr2fpga_agent/agent.py#L2854) | `<dynamic>.lower`、`any`、`str` |
| `_requirement_boundary_stop` — `_requirement_boundary_stop(metadata)` | function / [2871](../../../../agent/src/sr2fpga_agent/agent.py#L2871) | `<dynamic>.join`、`CriticalAmbiguity`、`RequirementCapabilityGapError`、`RequirementClarificationRequired`、`RequirementEnvelope`、`_RequirementBoundaryMetadataError`、`_boundary_string_tuple`、`boundary.get`、`isinstance`、`len`、`metadata.get`、`pack.get`、`public_context.get`、`tuple`、`validate_episode_pack`、`zip` |
| `_boundary_string_tuple` — `_boundary_string_tuple(boundary, key)` | function / [2942](../../../../agent/src/sr2fpga_agent/agent.py#L2942) | `_RequirementBoundaryMetadataError`、`any`、`boundary.get`、`isinstance`、`tuple` |
| `_generation_boundary_failure` — `_generation_boundary_failure(exc)` | function / [2953](../../../../agent/src/sr2fpga_agent/agent.py#L2953) | `isinstance`、`list` |
| `_l4_agreement_class` — `_l4_agreement_class(l4_open, l4_commercial)` | function / [2977](../../../../agent/src/sr2fpga_agent/agent.py#L2977) | `l4_commercial.get`、`l4_open.get` |
| `_tool_log` — `_tool_log(result)` | function / [2987](../../../../agent/src/sr2fpga_agent/agent.py#L2987) | 无直接调用 |
| `_tool_warnings` — `_tool_warnings(result)` | function / [2991](../../../../agent/src/sr2fpga_agent/agent.py#L2991) | `_tool_log`、`parse_tool_warnings` |
| `_tool_mismatches` — `_tool_mismatches(result)` | function / [2995](../../../../agent/src/sr2fpga_agent/agent.py#L2995) | `_tool_log`、`parse_test_fail_mismatches` |
| `_expected_bram` — `_expected_bram(project)` | function / [2999](../../../../agent/src/sr2fpga_agent/agent.py#L2999) | `<dynamic>.get`、`expected.get`、`isinstance`、`json.loads`、`payload.get`、`project.files.get` |
| `_empty_measured_qor` — `_empty_measured_qor()` | function / [3020](../../../../agent/src/sr2fpga_agent/agent.py#L3020) | 无直接调用 |
| `_sha256` — `_sha256(value)` | function / [3024](../../../../agent/src/sr2fpga_agent/agent.py#L3024) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`payload.encode` |
| `_trusted_event_id` — `_trusted_event_id(store, reference)` | function / [3034](../../../../agent/src/sr2fpga_agent/agent.py#L3034) | `ValueError`、`event.get`、`isinstance`、`json.loads`、`store.has_event_id`、`store.read_verified` |
| `_openxc7_wrapper_report_paths` — `_openxc7_wrapper_report_paths(project_dir, attempt_id)` | function / [3042](../../../../agent/src/sr2fpga_agent/agent.py#L3042) | `<dynamic>.is_file` |
| `_l4_open_record` — `_l4_open_record(tool_results, enabled, attempt_id, tool, board_profile, project_dir, core_tool_environment_ref, l4_tool_environment, l4_tool_environment_ref)` | function / [3051](../../../../agent/src/sr2fpga_agent/agent.py#L3051) | `_finalize_l4_qor_record`、`_is_l4_toolchain_environment_failure`、`_openxc7_wrapper_report_paths`、`_tool_result_stage_status`、`classify_failure`、`parse_openxc7_report`、`record.update`、`tool_results.get` |
| `_l4_commercial_record` — `_l4_commercial_record(tool_results, enabled, tool, core_tool_environment_ref, l4_tool_environment, l4_tool_environment_ref)` | function / [3157](../../../../agent/src/sr2fpga_agent/agent.py#L3157) | `_finalize_l4_qor_record`、`tool_results.get` |
| `_run_l4_commercial_reference` — `_run_l4_commercial_reference(tool_results, enabled, project_dir, attempt_id, tool, vivado_command, part, target_period_ns, timeout_seconds, core_tool_environment_ref, l4_tool_environment, l4_tool_environment_ref)` | function / [3205](../../../../agent/src/sr2fpga_agent/agent.py#L3205) | `_finalize_l4_qor_record`、`_l4_commercial_record`、`isinstance`、`os.environ.get`、`report.get`、`run_vivado_reference` |
| `_tool_result_stage_status` — `_tool_result_stage_status(result)` | function / [3302](../../../../agent/src/sr2fpga_agent/agent.py#L3302) | 无直接调用 |
| `_finalize_l4_qor_record` — `_finalize_l4_qor_record(record, lane, source_stage, source_stage_status, project_dir, attempt_id, core_tool_environment_ref, l4_tool_environment, l4_tool_environment_ref, fallback_relative_paths)` | function / [3312](../../../../agent/src/sr2fpga_agent/agent.py#L3312) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_captured_l4_tool_version`、`_l4_raw_evidence_refs`、`dict`、`incomplete_reasons.append`、`isinstance`、`record.get`、`relative_paths.update`、`sorted` |
| `_captured_l4_tool_version` — `_captured_l4_tool_version(l4_tool_environment, lane)` | function / [3384](../../../../agent/src/sr2fpga_agent/agent.py#L3384) | `isinstance`、`l4_tool_environment.get`、`lane_record.get`、`lanes.get`、`tool.get` |
| `_l4_raw_evidence_refs` — `_l4_raw_evidence_refs(project_dir, relative_paths)` | function / [3405](../../../../agent/src/sr2fpga_agent/agent.py#L3405) | `<dynamic>.hexdigest`、`<dynamic>.resolve`、`Path`、`attempts_dir.parent.resolve`、`hashlib.sha256`、`len`、`path.is_file`、`path.is_relative_to`、`path.read_bytes`、`refs.append`、`relative_path.split`、`sorted` |
| `_is_l4_non_model_not_run_result` — `_is_l4_non_model_not_run_result(result)` | function / [3430](../../../../agent/src/sr2fpga_agent/agent.py#L3430) | `_is_l4_toolchain_environment_failure` |
| `_is_l4_toolchain_environment_failure` — `_is_l4_toolchain_environment_failure(result)` | function / [3434](../../../../agent/src/sr2fpga_agent/agent.py#L3434) | `<dynamic>.lower`、`any` |
| `_openxc7_pnr_command` — `_openxc7_pnr_command(project_dir, platform, command_prefix, part)` | function / [3445](../../../../agent/src/sr2fpga_agent/agent.py#L3445) | `_clock_period_ns`、`_default_openxc7_command_prefix`、`_openxc7_part`、`_openxc7_project_dir_arg`、`_split_command_prefix`、`os.environ.get` |
| `_split_command_prefix` — `_split_command_prefix(command_prefix)` | function / [3463](../../../../agent/src/sr2fpga_agent/agent.py#L3463) | `shlex.split` |
| `_default_openxc7_command_prefix` — `_default_openxc7_command_prefix()` | function / [3467](../../../../agent/src/sr2fpga_agent/agent.py#L3467) | `RepositoryPaths.discover`、`_windows_path_to_wsl`、`str`、`wrapper.is_file` |
| `openxc7_tool_probe_command` — `openxc7_tool_probe_command()` | function / [3476](../../../../agent/src/sr2fpga_agent/agent.py#L3476) | `_default_openxc7_command_prefix`、`os.environ.get` |
| `_windows_path_to_wsl` — `_windows_path_to_wsl(path)` | function / [3484](../../../../agent/src/sr2fpga_agent/agent.py#L3484) | `<dynamic>.as_posix`、`<dynamic>.lower`、`len`、`path.resolve` |
| `_openxc7_part` — `_openxc7_part(platform)` | function / [3491](../../../../agent/src/sr2fpga_agent/agent.py#L3491) | 无直接调用 |
| `_openxc7_project_dir_arg` — `_openxc7_project_dir_arg(project_dir)` | function / [3495](../../../../agent/src/sr2fpga_agent/agent.py#L3495) | `project_dir.resolve`、`str`、`text.replace` |
| `_his_source_used_for_generation` — `_his_source_used_for_generation(project_generator)` | function / [3500](../../../../agent/src/sr2fpga_agent/agent.py#L3500) | `getattr`、`str` |
| `_validate_generated_project_h_stages` — `_validate_generated_project_h_stages(request, project, metadata, project_generator, platform)` | function / [3505](../../../../agent/src/sr2fpga_agent/agent.py#L3505) | `<dynamic>.get`、`_his_source_used_for_generation`、`context_from_validated_episode_pack`、`isinstance`、`parse_system_his_payload`、`project.files.get`、`validate_frozen_system_his_payload_h_stages`、`validate_system_his_h_stages` |
| `_h_stages_applicable` — `_h_stages_applicable(metadata, project_generator)` | function / [3542](../../../../agent/src/sr2fpga_agent/agent.py#L3542) | `<dynamic>.lower`、`<dynamic>.replace`、`<dynamic>.split`、`<dynamic>.strip`、`<dynamic>.upper`、`metadata.get`、`method_condition.replace`、`str`、`type` |
| `_supports_staged_his_generation` — `_supports_staged_his_generation(project_generator)` | function / [3558](../../../../agent/src/sr2fpga_agent/agent.py#L3558) | `callable`、`getattr` |
| `_embedded_system_his_repairer` — `_embedded_system_his_repairer(project_generator)` | function / [3564](../../../../agent/src/sr2fpga_agent/agent.py#L3564) | `callable`、`getattr` |
| `_system_his_candidate_project` — `_system_his_candidate_project(request, candidate_output)` | function / [3570](../../../../agent/src/sr2fpga_agent/agent.py#L3570) | `GeneratedProject`、`candidate_output.endswith` |
| `_system_his_patch` — `_system_his_patch(before_project, after_project, before_report, after_report, diagnosis, attempt_id, provider_name)` | function / [3581](../../../../agent/src/sr2fpga_agent/agent.py#L3581) | `<dynamic>.join`、`PatchMetadata`、`_h_status_map`、`after_content.splitlines`、`after_project.files.get`、`after_status.get`、`before_content.splitlines`、`before_project.files.get`、`before_status.items`、`diagnosis.get`、`difflib.unified_diff`、`first_failed_h_stage`、`list`、`sorted`、`str` |
| `_h_status_map` — `_h_status_map(report)` | function / [3639](../../../../agent/src/sr2fpga_agent/agent.py#L3639) | `<dynamic>.get`、`report.get`、`str` |
| `_system_his_repair_provider` — `_system_his_repair_provider(metadata)` | function / [3646](../../../../agent/src/sr2fpga_agent/agent.py#L3646) | `metadata.get`、`str` |
| `_not_run_h_stage_report` — `_not_run_h_stage_report(reason)` | function / [3652](../../../../agent/src/sr2fpga_agent/agent.py#L3652) | `dict` |
| `_not_applicable_h_stage_report` — `_not_applicable_h_stage_report()` | function / [3665](../../../../agent/src/sr2fpga_agent/agent.py#L3665) | `dict` |
| `_h_stages_not_applicable` — `_h_stages_not_applicable(report)` | function / [3678](../../../../agent/src/sr2fpga_agent/agent.py#L3678) | `<dynamic>.get`、`all`、`isinstance`、`report.get` |
| `_clock_period_ns` — `_clock_period_ns(clock_hz)` | function / [3688](../../../../agent/src/sr2fpga_agent/agent.py#L3688) | 无直接调用 |
| `_stage_entries` — `_stage_entries(attempt_id, tool_results, diagnosis, has_patch)` | function / [3694](../../../../agent/src/sr2fpga_agent/agent.py#L3694) | `entries.append`、`tool_results.values` |
| `_trajectory` — `_trajectory(sample_id, attempts)` | function / [3719](../../../../agent/src/sr2fpga_agent/agent.py#L3719) | 无直接调用 |
| `_req_his_fidelity` — `_req_his_fidelity(request, project, platform)` | function / [3726](../../../../agent/src/sr2fpga_agent/agent.py#L3726) | `check_system_his_req_fidelity`、`isinstance`、`json.loads`、`project.files.get` |

## `agent/src/sr2fpga_agent/ambiguity_audit_runner.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py) · 357 行 · SHA-256 `5f91274ba1d9c442f88214c395434e782c436de0c7796331fc0989768d841c78`

> Independent evaluator-side runner for sealed Paper-1 ambiguity cases.

导入模块：`__future__`、`argparse`、`dataclasses`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.ambiguity_events`、`sr2fpga_agent.ambiguity_outcome`、`sr2fpga_agent.ambiguity_witness`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.requirement_audit`、`sr2fpga_agent.requirement_boundary`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_ambiguity_case_manifest` — `build_ambiguity_case_manifest(audit_run_id, cases)` | function / [35](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L35) | `_sha256`、`validate_ambiguity_case_manifest` |
| `load_ambiguity_case_manifest` — `load_ambiguity_case_manifest(path)` | function / [52](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L52) | `Path`、`ValueError`、`isinstance`、`json.loads`、`manifest_path.is_file`、`manifest_path.read_text`、`validate_ambiguity_case_manifest` |
| `run_ambiguity_audit_manifest` — `run_ambiguity_audit_manifest(manifest)` | function / [66](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L66) | `run_ambiguity_audit_with_events` |
| `run_ambiguity_audit_with_events` — `run_ambiguity_audit_with_events(manifest)` | function / [73](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L73) | `AmbiguityAuditEventInterceptor`、`ClarificationAnswerBranch`、`PlatformProfile`、`ProjectRequest`、`RequirementAuditGold`、`ValueError`、`build_requirement_audit_artifact`、`build_requirement_audit_case`、`case_ids.add`、`cases.append`、`events.build_artifact`、`events.phase_a_completed`、`events.phase_a_started`、`private.get`、`set`、`tuple`、`validate_ambiguity_case_manifest` |
| `ClarificationReplayAuthority` — `ClarificationReplayAuthority` | class / [136](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L136) | 无直接调用 |
| `ClarificationReplayAuthority.__init__` — `__init__(self, evaluator_store)` | function / [139](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L139) | 无直接调用 |
| `ClarificationReplayAuthority.run` — `run(self, manifest, phase_a_artifact)` | function / [142](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L142) | `<dynamic>.get`、`ValueError`、`_sha256`、`phase_cases.get`、`replays.append`、`self._run_one`、`self._verify_phase_a_eligibility`、`validate_ambiguity_case_manifest`、`validate_clarification_replay_artifact`、`validate_requirement_audit_artifact` |
| `ClarificationReplayAuthority._verify_phase_a_eligibility` — `_verify_phase_a_eligibility(self, sealed_case, phase_case)` | function / [180](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L180) | `PlatformProfile`、`ValueError`、`_sha256`、`asdict` |
| `ClarificationReplayAuthority._run_one` — `_run_one(self, manifest, sealed_case, phase_case, branch)` | function / [203](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L203) | `PlatformProfile`、`ProjectRequest`、`ValueError`、`_sha256`、`evaluate_requirement_boundary`、`self._store.consume_once`、`set`、`sorted`、`time.monotonic` |
| `main` — `main(argv)` | function / [270](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L270) | `<dynamic>.run`、`AmbiguityAuditObservation`、`ArtifactStore`、`ClarificationReplayAuthority`、`_write_replay_artifact`、`argparse.ArgumentParser`、`build_ambiguity_outcome`、`load_ambiguity_case_manifest`、`load_ambiguity_witness_artifact`、`parser.add_argument`、`parser.error`、`parser.parse_args`、`run_ambiguity_audit_with_events`、`validate_witness_manifest_binding`、`write_ambiguity_audit_events`、`write_ambiguity_outcome`、`write_requirement_audit_artifact` |
| `validate_ambiguity_case_manifest` — `validate_ambiguity_case_manifest(manifest)` | function / [322](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L322) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_sha256`、`contract.validate`、`manifest.items` |
| `validate_clarification_replay_artifact` — `validate_clarification_replay_artifact(artifact)` | function / [332](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L332) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_sha256`、`artifact.items`、`contract.validate` |
| `_write_replay_artifact` — `_write_replay_artifact(path, artifact)` | function / [342](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L342) | `json.dumps`、`path.parent.mkdir`、`path.write_text`、`validate_clarification_replay_artifact` |
| `_sha256` — `_sha256(value)` | function / [351](../../../../agent/src/sr2fpga_agent/ambiguity_audit_runner.py#L351) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `agent/src/sr2fpga_agent/ambiguity_events.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/ambiguity_events.py) · 137 行 · SHA-256 `666bd0811abc957d8385970ae129f14001aaac6590c7ac81f2189b1f85299f36`

> Evaluator-owned event channel and downstream interceptor for OASA.

导入模块：`__future__`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.contract_registry`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `DownstreamEventIntercepted` — `DownstreamEventIntercepted` | class / [16](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L16) | 无直接调用 |
| `AmbiguityAuditEventInterceptor` — `AmbiguityAuditEventInterceptor` | class / [20](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L20) | 无直接调用 |
| `AmbiguityAuditEventInterceptor.__init__` — `__init__(self, audit_run_id, manifest_sha256)` | function / [21](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L21) | 无直接调用 |
| `AmbiguityAuditEventInterceptor.phase_a_started` — `phase_a_started(self, ambiguity_case_id)` | function / [26](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L26) | `self._append` |
| `AmbiguityAuditEventInterceptor.phase_a_completed` — `phase_a_completed(self, ambiguity_case_id, execution_status, counters, infrastructure_status, predicted_disposition, not_run_reason_id)` | function / [29](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L29) | `dict`、`self._append` |
| `AmbiguityAuditEventInterceptor.attempt_downstream` — `attempt_downstream(self, ambiguity_case_id, downstream_kind, callback)` | function / [50](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L50) | `DownstreamEventIntercepted`、`self._append` |
| `AmbiguityAuditEventInterceptor.record_escaped_downstream` — `record_escaped_downstream(self, ambiguity_case_id, downstream_kind)` | function / [69](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L69) | `self._append` |
| `AmbiguityAuditEventInterceptor.build_artifact` — `build_artifact(self, phase_a_audit_sha256)` | function / [83](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L83) | `_sha256`、`list`、`validate_ambiguity_audit_events` |
| `AmbiguityAuditEventInterceptor._append` — `_append(self, ambiguity_case_id, event_type, **fields)` | function / [96](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L96) | `len`、`self._events.append` |
| `validate_ambiguity_audit_events` — `validate_ambiguity_audit_events(artifact)` | function / [112](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L112) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_sha256`、`artifact.items`、`contract.validate`、`len`、`list`、`range` |
| `write_ambiguity_audit_events` — `write_ambiguity_audit_events(path, artifact)` | function / [126](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L126) | `json.dumps`、`path.parent.mkdir`、`path.write_text`、`validate_ambiguity_audit_events` |
| `_sha256` — `_sha256(value)` | function / [135](../../../../agent/src/sr2fpga_agent/ambiguity_events.py#L135) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

## `agent/src/sr2fpga_agent/ambiguity_outcome.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py) · 533 行 · SHA-256 `b8bddfa1b854ee12ab51cb0b6ffe9c6245adbda4cd4e43709b0e1fc884f3d20b`

> Cluster-aware reducers for Paper-1 requirement ambiguity audit artifacts.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.ambiguity_audit_runner`、`sr2fpga_agent.ambiguity_events`、`sr2fpga_agent.ambiguity_witness`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.requirement_audit`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `AmbiguityAuditObservation` — `AmbiguityAuditObservation` | class / [43](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L43) | 无直接调用 |
| `build_ambiguity_outcome` — `build_ambiguity_outcome(manifest, witness_artifact, observations)` | function / [50](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L50) | `<dynamic>.get`、`<dynamic>.join`、`ValueError`、`_accumulate_precision_recall`、`_add_counters`、`_audit_cost`、`_case_map`、`_disposition_counts`、`_empty_counters`、`_empty_infrastructure_status_counts`、`_initial_clusters`、`_precision_recall`、`_rate`、`_sha256`、`_validated_event_map`、`_validated_replay_map`、`all`、`assert_private_canary_not_exposed`、`bool`、`case_manifest.items`、`int`、`len`、`max`、`next`、`observation_cluster_states.items`、`observation_ids.add`、`observation_records.append`、`questioned_fact_ids.intersection`、`replay_map.get`、`set`、`sorted`、`sum`、`used_replays.add`、`validate_ambiguity_case_manifest`、`validate_ambiguity_outcome`、`validate_requirement_audit_artifact`、`validate_witness_manifest_binding` |
| `validate_ambiguity_outcome` — `validate_ambiguity_outcome(artifact)` | function / [355](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L355) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_sha256`、`artifact.items`、`contract.validate` |
| `write_ambiguity_outcome` — `write_ambiguity_outcome(path, artifact)` | function / [365](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L365) | `json.dumps`、`path.parent.mkdir`、`path.write_text`、`validate_ambiguity_outcome` |
| `_validated_replay_map` — `_validated_replay_map(manifest, observation, phase_a)` | function / [374](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L374) | `ValueError`、`_case_map`、`validate_clarification_replay_artifact` |
| `_validated_event_map` — `_validated_event_map(manifest, observation, phase_a, phase_cases)` | function / [392](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L392) | `<dynamic>.append`、`ValueError`、`grouped.items`、`len`、`validate_ambiguity_audit_events` |
| `_case_map` — `_case_map(items, label)` | function / [438](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L438) | `ValueError` |
| `_initial_clusters` — `_initial_clusters(cases)` | function / [448](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L448) | `<dynamic>.append`、`cases.items`、`grouped.items`、`grouped.setdefault`、`sorted` |
| `_disposition_counts` — `_disposition_counts()` | function / [472](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L472) | 无直接调用 |
| `_empty_counters` — `_empty_counters()` | function / [476](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L476) | 无直接调用 |
| `_empty_infrastructure_status_counts` — `_empty_infrastructure_status_counts()` | function / [480](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L480) | 无直接调用 |
| `_add_counters` — `_add_counters(totals, counters)` | function / [484](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L484) | 无直接调用 |
| `_audit_cost` — `_audit_cost(counters, infrastructure_status_counts)` | function / [492](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L492) | `dict` |
| `_rate` — `_rate(numerator, denominator)` | function / [502](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L502) | 无直接调用 |
| `_accumulate_precision_recall` — `_accumulate_precision_recall(counts, predicted, gold)` | function / [510](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L510) | `len`、`predicted.intersection` |
| `_precision_recall` — `_precision_recall(counts)` | function / [520](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L520) | 无直接调用 |
| `_sha256` — `_sha256(value)` | function / [531](../../../../agent/src/sr2fpga_agent/ambiguity_outcome.py#L531) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/ambiguity_witness.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py) · 150 行 · SHA-256 `aee833069a831fc018cc0d009539e81f4038c39cdea3accd8130cc4721c746df`

> Evaluator-only witness, adjudication, and visibility checks for OASA.

导入模块：`__future__`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.ambiguity_audit_runner`、`sr2fpga_agent.contract_registry`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_ambiguity_witness_artifact` — `build_ambiguity_witness_artifact(manifest, private_canary, cases)` | function / [17](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L17) | `_sha256`、`validate_ambiguity_case_manifest`、`validate_ambiguity_witness_artifact`、`validate_witness_manifest_binding` |
| `load_ambiguity_witness_artifact` — `load_ambiguity_witness_artifact(path)` | function / [38](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L38) | `Path`、`ValueError`、`artifact_path.is_file`、`artifact_path.read_text`、`isinstance`、`json.loads`、`validate_ambiguity_witness_artifact` |
| `validate_ambiguity_witness_artifact` — `validate_ambiguity_witness_artifact(artifact)` | function / [52](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L52) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_case_map`、`_sha256`、`artifact.items`、`cases.items`、`contract.validate`、`len`、`set` |
| `validate_witness_manifest_binding` — `validate_witness_manifest_binding(manifest, witness_artifact)` | function / [72](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L72) | `ValueError`、`_case_map`、`assert_private_canary_not_exposed`、`manifest_cases.items`、`set`、`validate_ambiguity_case_manifest`、`validate_ambiguity_witness_artifact` |
| `assert_private_canary_not_exposed` — `assert_private_canary_not_exposed(manifest, witness_artifact, *runtime_artifacts)` | function / [114](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L114) | `ValueError`、`json.dumps` |
| `write_ambiguity_witness_artifact` — `write_ambiguity_witness_artifact(path, artifact)` | function / [129](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L129) | `json.dumps`、`path.parent.mkdir`、`path.write_text`、`validate_ambiguity_witness_artifact` |
| `_case_map` — `_case_map(items, label)` | function / [138](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L138) | `ValueError` |
| `_sha256` — `_sha256(value)` | function / [148](../../../../agent/src/sr2fpga_agent/ambiguity_witness.py#L148) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

## `agent/src/sr2fpga_agent/artifact_store.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/artifact_store.py) · 717 行 · SHA-256 `536a687856c7d3e1f997e9c946c327ccb600ba5f9c8001f8a31510b9101ceb14`

> Small local write-once authority for CD3 artifacts and events.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.project_contract`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ArtifactConflictError` — `ArtifactConflictError` | class / [22](../../../../agent/src/sr2fpga_agent/artifact_store.py#L22) | 无直接调用 |
| `ArtifactIntegrityError` — `ArtifactIntegrityError` | class / [26](../../../../agent/src/sr2fpga_agent/artifact_store.py#L26) | 无直接调用 |
| `OneShotViolation` — `OneShotViolation` | class / [30](../../../../agent/src/sr2fpga_agent/artifact_store.py#L30) | 无直接调用 |
| `BudgetReservationError` — `BudgetReservationError` | class / [34](../../../../agent/src/sr2fpga_agent/artifact_store.py#L34) | 无直接调用 |
| `ArtifactRef` — `ArtifactRef` | class / [39](../../../../agent/src/sr2fpga_agent/artifact_store.py#L39) | 无直接调用 |
| `ArtifactRef.to_dict` — `to_dict(self)` | function / [45](../../../../agent/src/sr2fpga_agent/artifact_store.py#L45) | `asdict` |
| `ArtifactStore` — `ArtifactStore` | class / [49](../../../../agent/src/sr2fpga_agent/artifact_store.py#L49) | 无直接调用 |
| `ArtifactStore.__init__` — `__init__(self, root)` | function / [52](../../../../agent/src/sr2fpga_agent/artifact_store.py#L52) | `Path`、`self.root.mkdir` |
| `ArtifactStore.put_blob` — `put_blob(self, key, content, media_type)` | function / [56](../../../../agent/src/sr2fpga_agent/artifact_store.py#L56) | `<dynamic>.hexdigest`、`ArtifactConflictError`、`ArtifactIntegrityError`、`ArtifactRef`、`TypeError`、`_canonical_json`、`_safe_key`、`_write_exclusive`、`blob_path.exists`、`blob_path.parent.mkdir`、`blob_path.read_bytes`、`hashlib.sha256`、`isinstance`、`json.loads`、`len`、`ref_path.exists`、`ref_path.parent.mkdir`、`ref_path.read_text`、`reference.to_dict`、`self._ref_path` |
| `ArtifactStore.put_validated_json` — `put_validated_json(self, key, payload, contract_key, registry)` | function / [88](../../../../agent/src/sr2fpga_agent/artifact_store.py#L88) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_canonical_json`、`contract.validate`、`self.put_blob` |
| `ArtifactStore.read_verified` — `read_verified(self, key_or_ref)` | function / [106](../../../../agent/src/sr2fpga_agent/artifact_store.py#L106) | `<dynamic>.hexdigest`、`ArtifactIntegrityError`、`_SHA256_RE.fullmatch`、`_safe_key`、`blob_path.is_file`、`blob_path.read_bytes`、`hashlib.sha256`、`isinstance`、`len`、`self._read_ref` |
| `ArtifactStore.reference` — `reference(self, key)` | function / [124](../../../../agent/src/sr2fpga_agent/artifact_store.py#L124) | `<dynamic>.is_file`、`_safe_key`、`self._read_ref`、`self._ref_path` |
| `ArtifactStore.append_event` — `append_event(self, episode_id, event_type, payload)` | function / [132](../../../../agent/src/sr2fpga_agent/artifact_store.py#L132) | `<dynamic>.hexdigest`、`_canonical_json`、`_safe_segment`、`dict`、`event_dir.exists`、`event_dir.glob`、`hashlib.sha256`、`len`、`self.put_blob`、`tuple` |
| `ArtifactStore.event_refs` — `event_refs(self, episode_id)` | function / [158](../../../../agent/src/sr2fpga_agent/artifact_store.py#L158) | `<dynamic>.as_posix`、`ArtifactIntegrityError`、`_safe_segment`、`event_dir.glob`、`event_dir.is_dir`、`ref_path.relative_to`、`references.append`、`relative.removesuffix`、`self._read_ref`、`sorted`、`tuple` |
| `ArtifactStore.has_event_id` — `has_event_id(self, event_id)` | function / [175](../../../../agent/src/sr2fpga_agent/artifact_store.py#L175) | `<dynamic>.hexdigest`、`ArtifactRef`、`_EVENT_ID_RE.fullmatch`、`_canonical_json`、`event.get`、`event.items`、`event_root.is_dir`、`event_root.rglob`、`hashlib.sha256`、`isinstance`、`json.loads`、`ref_path.read_text`、`reference.key.endswith`、`self.read_verified` |
| `ArtifactStore.seal_candidate` — `seal_candidate(self, candidate_id, project, project_envelope_ref, requirement_projection_sha256, creation_event_ref, public_evidence_refs)` | function / [206](../../../../agent/src/sr2fpga_agent/artifact_store.py#L206) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_require_sha256`、`_safe_segment`、`content.encode`、`creation_event.get`、`envelope.get`、`envelope_contract.validate`、`isinstance`、`json.loads`、`project.files.items`、`project_file_refs.append`、`self.has_event_id`、`self.put_blob`、`self.put_validated_json`、`self.read_verified`、`sorted`、`verify_project_envelope` |
| `ArtifactStore.seal_public_evaluation_candidate` — `seal_public_evaluation_candidate(self, candidate_id, attempt_id, project, project_envelope_ref, requirement_projection_sha256, creation_event_ref)` | function / [278](../../../../agent/src/sr2fpga_agent/artifact_store.py#L278) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_artifact_ref_payload`、`_require_sha256`、`_safe_segment`、`content.encode`、`creation_event.get`、`envelope.get`、`event_payload.get`、`expected_identity.items`、`isinstance`、`json.loads`、`project.files.items`、`project_file_refs.append`、`self.has_event_id`、`self.put_blob`、`self.put_validated_json`、`self.read_verified`、`sorted`、`verify_project_envelope` |
| `ArtifactStore.seal_unverified_public_evaluation_candidate` — `seal_unverified_public_evaluation_candidate(self, candidate_id, episode_id, attempt_id, method_condition_id, project, project_envelope_reason, requirement_projection_sha256, creation_event_ref)` | function / [373](../../../../agent/src/sr2fpga_agent/artifact_store.py#L373) | `TypeError`、`ValueError`、`_artifact_ref_payload`、`_require_sha256`、`_safe_segment`、`content.encode`、`creation_event.get`、`event_payload.get`、`expected_identity.items`、`isinstance`、`json.loads`、`project.files.items`、`project_file_refs.append`、`self.has_event_id`、`self.put_blob`、`self.put_validated_json`、`self.read_verified`、`sorted`、`validate_project_relative_path` |
| `ArtifactStore.read_public_evaluation_candidate` — `read_public_evaluation_candidate(self, seal_ref)` | function / [461](../../../../agent/src/sr2fpga_agent/artifact_store.py#L461) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ArtifactIntegrityError`、`ArtifactRef`、`ContractRegistry`、`GeneratedProject`、`content.decode`、`hashlib.sha256`、`isinstance`、`json.loads`、`reference_fields.append`、`seal.get`、`self.has_event_id`、`self.read_verified`、`validate_project_relative_path` |
| `ArtifactStore.read_sealed_project` — `read_sealed_project(self, seal_ref)` | function / [532](../../../../agent/src/sr2fpga_agent/artifact_store.py#L532) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ArtifactIntegrityError`、`ContractRegistry`、`GeneratedProject`、`content.decode`、`hashlib.sha256`、`isinstance`、`json.loads`、`record.get`、`seal.get`、`self.read_verified`、`validate_project_relative_path` |
| `ArtifactStore.consume_once` — `consume_once(self, operation_id, subject_sha256)` | function / [574](../../../../agent/src/sr2fpga_agent/artifact_store.py#L574) | `<dynamic>.exists`、`OneShotViolation`、`_canonical_json`、`_require_sha256`、`_safe_segment`、`self._ref_path`、`self.put_blob` |
| `ArtifactStore._read_ref` — `_read_ref(self, key)` | function / [592](../../../../agent/src/sr2fpga_agent/artifact_store.py#L592) | `ArtifactRef`、`KeyError`、`json.loads`、`path.is_file`、`path.read_text`、`self._ref_path` |
| `ArtifactStore._ref_path` — `_ref_path(self, key)` | function / [604](../../../../agent/src/sr2fpga_agent/artifact_store.py#L604) | `<dynamic>.resolve`、`Path`、`PurePosixPath`、`ValueError`、`_safe_key`、`list`、`target.is_relative_to` |
| `EpisodeBudgetLedger` — `EpisodeBudgetLedger` | class / [614](../../../../agent/src/sr2fpga_agent/artifact_store.py#L614) | 无直接调用 |
| `EpisodeBudgetLedger.__init__` — `__init__(self, store, episode_id, limits)` | function / [617](../../../../agent/src/sr2fpga_agent/artifact_store.py#L617) | `ValueError`、`_safe_segment`、`any`、`dict`、`self.limits.values` |
| `EpisodeBudgetLedger.reserve` — `reserve(self, axis, amount)` | function / [630](../../../../agent/src/sr2fpga_agent/artifact_store.py#L630) | `BudgetReservationError`、`KeyError`、`ValueError`、`self.store.append_event` |
| `EpisodeBudgetLedger.summary` — `summary(self)` | function / [653](../../../../agent/src/sr2fpga_agent/artifact_store.py#L653) | `self.limits.items` |
| `_safe_key` — `_safe_key(value)` | function / [664](../../../../agent/src/sr2fpga_agent/artifact_store.py#L664) | `PurePosixPath`、`ValueError`、`_safe_segment`、`any`、`isinstance`、`path.as_posix`、`path.is_absolute` |
| `_safe_segment` — `_safe_segment(value)` | function / [675](../../../../agent/src/sr2fpga_agent/artifact_store.py#L675) | `<dynamic>.casefold`、`ValueError`、`isinstance`、`range`、`re.fullmatch`、`value.endswith`、`value.split` |
| `_require_sha256` — `_require_sha256(value, label)` | function / [687](../../../../agent/src/sr2fpga_agent/artifact_store.py#L687) | `ValueError`、`_SHA256_RE.fullmatch`、`isinstance` |
| `artifact_ref_from_payload` — `artifact_ref_from_payload(payload)` | function / [692](../../../../agent/src/sr2fpga_agent/artifact_store.py#L692) | `ArtifactRef` |
| `_artifact_ref_payload` — `_artifact_ref_payload(reference)` | function / [703](../../../../agent/src/sr2fpga_agent/artifact_store.py#L703) | 无直接调用 |
| `_write_exclusive` — `_write_exclusive(path, content)` | function / [712](../../../../agent/src/sr2fpga_agent/artifact_store.py#L712) | `ArtifactConflictError`、`handle.write`、`path.open` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`re.compile`

## `agent/src/sr2fpga_agent/baseline_report.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/baseline_report.py) · 559 行 · SHA-256 `6dbde4e71d1efd3f01cae21f2d858370314cdf26d1fe684411d359a02022712c`

> Baseline report helpers for SR2FPGA runner summaries.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `baseline_rows` — `baseline_rows(summary)` | function / [24](../../../../agent/src/sr2fpga_agent/baseline_report.py#L24) | `_pass_levels`、`calibration.get`、`cell.get`、`float`、`int`、`isinstance`、`rows.append`、`sorted`、`str`、`summary.get` |
| `detect_pass_rate_knee` — `detect_pass_rate_knee(rows, threshold)` | function / [54](../../../../agent/src/sr2fpga_agent/baseline_report.py#L54) | `_sort_key`、`dict`、`float`、`item.get`、`row.get`、`sorted` |
| `render_markdown` — `render_markdown(run_id, rows, knee_threshold, summary)` | function / [63](../../../../agent/src/sr2fpga_agent/baseline_report.py#L63) | `<dynamic>.format`、`<dynamic>.join`、`_append_contract_skeleton_ablation_section`、`_append_derived_training_views_section`、`_append_generated_his_credit_section`、`_append_h_stage_section`、`_append_l0_l4_survival_section`、`_append_l4_commercial_section`、`_append_l4_open_section`、`_append_latent_testbench_issue_section`、`_append_oracle_strength_section`、`_append_phase_d_paired_section`、`_append_repair_metrics_section`、`_format_pass_levels`、`_format_rate`、`_knee_summary`、`detect_pass_rate_knee`、`lines.append` |
| `main` — `main(argv)` | function / [105](../../../../agent/src/sr2fpga_agent/baseline_report.py#L105) | `argparse.ArgumentParser`、`args.output.parent.mkdir`、`args.output.write_text`、`args.summary.read_text`、`baseline_rows`、`json.loads`、`parser.add_argument`、`parser.parse_args`、`print`、`render_markdown`、`str`、`summary.get` |
| `_sort_key` — `_sort_key(value)` | function / [132](../../../../agent/src/sr2fpga_agent/baseline_report.py#L132) | `<dynamic>.isdigit`、`int`、`str`、`text.startswith` |
| `_pass_levels` — `_pass_levels(value)` | function / [139](../../../../agent/src/sr2fpga_agent/baseline_report.py#L139) | `int`、`isinstance`、`str`、`value.items` |
| `_format_pass_levels` — `_format_pass_levels(pass_levels)` | function / [145](../../../../agent/src/sr2fpga_agent/baseline_report.py#L145) | `<dynamic>.join`、`sorted` |
| `_format_rate` — `_format_rate(rate)` | function / [151](../../../../agent/src/sr2fpga_agent/baseline_report.py#L151) | 无直接调用 |
| `_knee_summary` — `_knee_summary(knee, threshold)` | function / [155](../../../../agent/src/sr2fpga_agent/baseline_report.py#L155) | `<dynamic>.format`、`_format_rate`、`float`、`knee.get` |
| `_append_contract_skeleton_ablation_section` — `_append_contract_skeleton_ablation_section(lines, summary)` | function / [167](../../../../agent/src/sr2fpga_agent/baseline_report.py#L167) | `<dynamic>.format`、`_format_pass_levels`、`_format_percentage_points`、`_format_rate`、`_pass_levels`、`behavior.get`、`cell.get`、`cells.get`、`float`、`int`、`isinstance`、`legacy.get`、`lines.append`、`lines.extend`、`matrix.get`、`sorted`、`str`、`summary.get` |
| `_contract_skeleton_sort_key` — `_contract_skeleton_sort_key(value)` | function / [211](../../../../agent/src/sr2fpga_agent/baseline_report.py#L211) | `order.get`、`str` |
| `_format_percentage_points` — `_format_percentage_points(delta)` | function / [221](../../../../agent/src/sr2fpga_agent/baseline_report.py#L221) | 无直接调用 |
| `_append_phase_d_paired_section` — `_append_phase_d_paired_section(lines, summary)` | function / [225](../../../../agent/src/sr2fpga_agent/baseline_report.py#L225) | `<dynamic>.format`、`_append_phase_d_group_table`、`comparison.get`、`final.get`、`initial.get`、`int`、`isinstance`、`level.lower`、`lines.append`、`lines.extend`、`paired.get`、`sorted`、`summary.get` |
| `_append_phase_d_group_table` — `_append_phase_d_group_table(lines, title, raw_groups)` | function / [288](../../../../agent/src/sr2fpga_agent/baseline_report.py#L288) | `<dynamic>.format`、`<dynamic>.join`、`cell.get`、`final.get`、`initial.get`、`int`、`isinstance`、`lines.append`、`lines.extend`、`sorted` |
| `_append_latent_testbench_issue_section` — `_append_latent_testbench_issue_section(lines, summary)` | function / [321](../../../../agent/src/sr2fpga_agent/baseline_report.py#L321) | `int`、`isinstance`、`lines.append`、`lines.extend`、`sorted`、`summary.get` |
| `_append_oracle_strength_section` — `_append_oracle_strength_section(lines, summary)` | function / [338](../../../../agent/src/sr2fpga_agent/baseline_report.py#L338) | `<dynamic>.format`、`float`、`int`、`isinstance`、`lines.append`、`lines.extend`、`sorted`、`strength.get`、`summary.get` |
| `_append_repair_metrics_section` — `_append_repair_metrics_section(lines, summary)` | function / [380](../../../../agent/src/sr2fpga_agent/baseline_report.py#L380) | `<dynamic>.format`、`_format_rate`、`float`、`int`、`isinstance`、`lines.extend`、`metrics.get`、`summary.get` |
| `_append_l4_open_section` — `_append_l4_open_section(lines, summary)` | function / [404](../../../../agent/src/sr2fpga_agent/baseline_report.py#L404) | `counts.get`、`int`、`isinstance`、`lines.append`、`lines.extend`、`sorted`、`summary.get` |
| `_append_l4_commercial_section` — `_append_l4_commercial_section(lines, summary)` | function / [427](../../../../agent/src/sr2fpga_agent/baseline_report.py#L427) | `counts.get`、`int`、`isinstance`、`lines.append`、`lines.extend`、`sorted`、`summary.get` |
| `_append_h_stage_section` — `_append_h_stage_section(lines, summary)` | function / [450](../../../../agent/src/sr2fpga_agent/baseline_report.py#L450) | `<dynamic>.format`、`counts.get`、`h_stage.get`、`int`、`isinstance`、`lines.append`、`lines.extend`、`summary.get` |
| `_append_l0_l4_survival_section` — `_append_l0_l4_survival_section(lines, summary)` | function / [476](../../../../agent/src/sr2fpga_agent/baseline_report.py#L476) | `counts.get`、`int`、`isinstance`、`levels.get`、`lines.append`、`lines.extend`、`summary.get` |
| `_append_generated_his_credit_section` — `_append_generated_his_credit_section(lines, summary)` | function / [497](../../../../agent/src/sr2fpga_agent/baseline_report.py#L497) | `credit.items`、`int`、`isinstance`、`lines.append`、`lines.extend`、`pass_levels.items`、`sorted`、`summary.get` |
| `_append_derived_training_views_section` — `_append_derived_training_views_section(lines, summary)` | function / [525](../../../../agent/src/sr2fpga_agent/baseline_report.py#L525) | `<dynamic>.format`、`_yes_no`、`int`、`isinstance`、`lines.append`、`lines.extend`、`sorted`、`str`、`summary.get`、`view.get` |
| `_yes_no` — `_yes_no(value)` | function / [554](../../../../agent/src/sr2fpga_agent/baseline_report.py#L554) | 无直接调用 |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `agent/src/sr2fpga_agent/block_cost_accounting.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py) · 615 行 · SHA-256 `1efceeef3d77b1f8d160f3074640db568f19a53447fd012ad1bc3fc629cfb4ab`

> Method-neutral, development-only accounting for paired-block preparation.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.models`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `BlockPreparationCostLedgerError` — `BlockPreparationCostLedgerError` | class / [46](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L46) | 无直接调用 |
| `ModelCostLedger` — `ModelCostLedger` | class / [51](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L51) | 无直接调用 |
| `ModelCostLedger.reserve` — `reserve(self, axis, amount, stage, visibility_class, limit, used_after, started_at)` | function / [52](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L52) | 无直接调用 |
| `ModelCostLedger.record_budget_exhausted` — `record_budget_exhausted(self, axis, amount, stage, visibility_class, limit, used_after, started_at)` | function / [64](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L64) | 无直接调用 |
| `ModelCostLedger.record_cost` — `record_cost(self, stage, visibility_class, cost_delta, status, duration_seconds, input_artifact_hashes, output_artifact_hashes, unavailable_axes, started_at)` | function / [76](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L76) | 无直接调用 |
| `ReplayedBlockPreparation` — `ReplayedBlockPreparation` | class / [92](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L92) | 无直接调用 |
| `BlockPreparationCostLedger` — `BlockPreparationCostLedger` | class / [101](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L101) | 无直接调用 |
| `BlockPreparationCostLedger.__init__` — `__init__(self, store, paired_block_ref, failure_origin)` | function / [104](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L104) | `store.read_verified`、`validate_accounting_failure_origin` |
| `BlockPreparationCostLedger.event_refs` — `event_refs(self)` | function / [122](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L122) | `tuple` |
| `BlockPreparationCostLedger.observed_axes` — `observed_axes(self)` | function / [126](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L126) | `frozenset`、`set` |
| `BlockPreparationCostLedger.activate_checkpoint` — `activate_checkpoint(self, checkpoint_id)` | function / [129](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L129) | `BlockPreparationCostLedgerError`、`self._require_checkpoint` |
| `BlockPreparationCostLedger.reserve` — `reserve(self, axis, amount, stage, visibility_class, limit, used_after, started_at)` | function / [135](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L135) | `_require_axis_value`、`self._append_cost_event` |
| `BlockPreparationCostLedger.record_budget_exhausted` — `record_budget_exhausted(self, axis, amount, stage, visibility_class, limit, used_after, started_at)` | function / [164](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L164) | `_require_axis_value`、`self._append_cost_event` |
| `BlockPreparationCostLedger.record_cost` — `record_cost(self, stage, visibility_class, cost_delta, status, duration_seconds, input_artifact_hashes, output_artifact_hashes, unavailable_axes, started_at)` | function / [193](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L193) | `BlockPreparationCostLedgerError`、`dict`、`self._append_cost_event` |
| `BlockPreparationCostLedger.record_checkpoint` — `record_checkpoint(self, checkpoint_id, event_kind, status, input_refs, output_refs, reason)` | function / [227](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L227) | `BlockPreparationCostLedgerError`、`_verified_references`、`expected.get`、`isinstance`、`self._append`、`self._require_checkpoint` |
| `BlockPreparationCostLedger.close` — `close(self, zero_axes, unavailable_axes)` | function / [272](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L272) | `<dynamic>.join`、`BlockPreparationCostLedgerError`、`declared_unavailable.items`、`dict`、`isinstance`、`self._append`、`self._values.get`、`set`、`sorted` |
| `BlockPreparationCostLedger._append_cost_event` — `_append_cost_event(self, stage, visibility_class, event_kind, status, cost_delta, unavailable_axes, budget_reservation, duration_seconds, started_at, input_artifact_hashes, output_artifact_hashes)` | function / [328](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L328) | `BlockPreparationCostLedgerError`、`_accumulate_delta`、`_sorted_hashes`、`_validate_delta`、`self._append`、`self._require_active_checkpoint` |
| `BlockPreparationCostLedger._append` — `_append(self, checkpoint_id, stage, visibility_class, event_kind, status, duration_seconds, input_refs, output_refs, input_artifact_hashes, output_artifact_hashes, budget_reservation, cost_delta, unavailable_axes, reason, started_at)` | function / [373](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L373) | `<dynamic>.hexdigest`、`BlockPreparationCostLedgerError`、`_CHECKPOINT_PARENTS.get`、`_canonical_json`、`_event_id_from_ref`、`dict`、`hashlib.sha256`、`len`、`list`、`reference.to_dict`、`self._refs.append`、`self.paired_block_ref.to_dict`、`self.store.put_validated_json`、`time.time` |
| `BlockPreparationCostLedger._require_checkpoint` — `_require_checkpoint(self, checkpoint_id)` | function / [443](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L443) | `BlockPreparationCostLedgerError` |
| `BlockPreparationCostLedger._require_active_checkpoint` — `_require_active_checkpoint(self)` | function / [447](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L447) | `BlockPreparationCostLedgerError` |
| `replay_development_block_preparation` — `replay_development_block_preparation(store, event_refs, registry)` | function / [453](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L453) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`BlockPreparationCostLedgerError`、`ContractRegistry`、`ReplayedBlockPreparation`、`_accumulate_delta`、`_artifact_ref`、`_axis_results`、`_canonical_json`、`_validate_delta`、`_verify_event_references`、`contract.validate`、`declared_unavailable.get`、`enumerate`、`event.items`、`events.append`、`hashlib.sha256`、`json.loads`、`len`、`paired_block_ref.to_dict`、`store.read_verified`、`tuple`、`unavailable.items` |
| `_axis_results` — `_axis_results(values, unavailable, declared)` | function / [558](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L558) | `BlockPreparationCostLedgerError`、`values.get` |
| `_verified_references` — `_verified_references(store, refs)` | function / [578](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L578) | `store.read_verified`、`tuple` |
| `_verify_event_references` — `_verify_event_references(store, event)` | function / [585](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L585) | `BlockPreparationCostLedgerError`、`_artifact_ref`、`any`、`isinstance`、`len`、`store.read_verified` |
| `_sorted_hashes` — `_sorted_hashes(values)` | function / [604](../../../../agent/src/sr2fpga_agent/block_cost_accounting.py#L604) | `BlockPreparationCostLedgerError`、`int`、`isinstance`、`len`、`set`、`sorted`、`tuple` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/block_preparation.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/block_preparation.py) · 902 行 · SHA-256 `99c89b7ad663b828bb3de8a50e59be1da5776882f3e070e2064a5af42e35b9da`

> Verified development-only shared-checkpoint manifests.

导入模块：`__future__`、`dataclasses`、`enum`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.block_cost_accounting`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.generation.context_direct`、`sr2fpga_agent.generation.context_his`、`sr2fpga_agent.method_adapters`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.paired_block`、`sr2fpga_agent.project_contract`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `CheckpointId` — `CheckpointId` | class / [46](../../../../agent/src/sr2fpga_agent/block_preparation.py#L46) | 无直接调用 |
| `SharedCheckpointResumeError` — `SharedCheckpointResumeError` | class / [52](../../../../agent/src/sr2fpga_agent/block_preparation.py#L52) | 无直接调用 |
| `CheckpointNode` — `CheckpointNode` | class / [74](../../../../agent/src/sr2fpga_agent/block_preparation.py#L74) | 无直接调用 |
| `PreparedBlockArtifacts` — `PreparedBlockArtifacts` | class / [89](../../../../agent/src/sr2fpga_agent/block_preparation.py#L89) | 无直接调用 |
| `BlockPreparationFacades` — `BlockPreparationFacades` | class / [100](../../../../agent/src/sr2fpga_agent/block_preparation.py#L100) | 无直接调用 |
| `prepare_development_paired_block` — `prepare_development_paired_block(store, paired_block_ref, pairing, context, platform, facades, model_budget, preparation_policy_sha256)` | function / [106](../../../../agent/src/sr2fpga_agent/block_preparation.py#L106) | `MethodArtifactGateway`、`PairedArtifactCoordinator`、`PreparedBlockArtifacts`、`RuntimeError`、`ValueError`、`_preparation_failure_reason`、`_prepared_checkpoint_node`、`_require_sha256`、`_require_store_reference`、`all`、`artifacts.put_project`、`artifacts.read_planning`、`coordinator.materialize_project_checkpoint`、`coordinator.materialize_system_his_checkpoint`、`expected_pairing.items`、`facades.direct.emit_project`、`facades.his_validation.validate_his`、`facades.system_his.emit_his`、`facades.system_his.emit_skeleton_project`、`h_report.get`、`isinstance`、`ledger.activate_checkpoint`、`ledger.close`、`ledger.record_checkpoint`、`load_development_paired_block`、`pairing.digest`、`platform_profile_sha256`、`read_development_shared_checkpoint_manifest`、`replay_development_block_preparation`、`set`、`states.values`、`tuple`、`write_development_shared_checkpoint_manifest` |
| `_prepared_checkpoint_node` — `_prepared_checkpoint_node(store, checkpoint_id, state, replay)` | function / [311](../../../../agent/src/sr2fpga_agent/block_preparation.py#L311) | `CheckpointNode`、`_event_set_sha256`、`tuple`、`zip` |
| `_preparation_failure_reason` — `_preparation_failure_reason(exc)` | function / [346](../../../../agent/src/sr2fpga_agent/block_preparation.py#L346) | `type` |
| `write_development_shared_checkpoint_manifest` — `write_development_shared_checkpoint_manifest(store, paired_block_ref, preparation_policy_sha256, nodes, block_event_refs)` | function / [352](../../../../agent/src/sr2fpga_agent/block_preparation.py#L352) | `ValueError`、`_event_set_sha256`、`_node_payload`、`_require_sha256`、`_require_store_reference`、`_validate_nodes`、`all`、`load_development_paired_block`、`paired_block_ref.to_dict`、`reference.to_dict`、`replay_development_block_preparation`、`store.put_validated_json`、`tuple` |
| `read_development_shared_checkpoint_manifest` — `read_development_shared_checkpoint_manifest(store, reference)` | function / [397](../../../../agent/src/sr2fpga_agent/block_preparation.py#L397) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_artifact_ref`、`_event_set_sha256`、`_node_from_payload`、`_require_sha256`、`_require_store_reference`、`_validate_nodes`、`all`、`isinstance`、`json.loads`、`load_development_paired_block`、`replay_development_block_preparation`、`store.read_verified`、`tuple` |
| `verify_development_shared_checkpoint_manifest_against_policy` — `verify_development_shared_checkpoint_manifest_against_policy(store, reference, expected_preparation_policy)` | function / [431](../../../../agent/src/sr2fpga_agent/block_preparation.py#L431) | `ValueError`、`planned.get`、`read_development_shared_checkpoint_manifest`、`validate_development_block_preparation_policy`、`zip` |
| `validate_development_block_preparation_policy` — `validate_development_block_preparation_policy(store, expected_preparation_policy)` | function / [478](../../../../agent/src/sr2fpga_agent/block_preparation.py#L478) | `<dynamic>.hexdigest`、`ValueError`、`_artifact_ref`、`_canonical_json`、`_require_sha256`、`_require_store_reference`、`all`、`any`、`artifact_key.endswith`、`dict`、`exclusive_ceilings.values`、`hashlib.sha256`、`isinstance`、`iter`、`len`、`load_development_paired_block`、`next`、`policy.items`、`prefix.split`、`prefixes.add`、`set`、`trusted_key.endswith`、`tuple`、`type`、`zip` |
| `blocked_methods_from_verified_manifest` — `blocked_methods_from_verified_manifest(store, reference)` | function / [628](../../../../agent/src/sr2fpga_agent/block_preparation.py#L628) | `<dynamic>.append`、`candidates.items`、`candidates.setdefault`、`read_development_shared_checkpoint_manifest`、`str` |
| `read_complete_development_shared_checkpoint_resume` — `read_complete_development_shared_checkpoint_resume(store, reference, expected_preparation_policy)` | function / [648](../../../../agent/src/sr2fpga_agent/block_preparation.py#L648) | `SharedCheckpointResumeError`、`ValueError`、`_artifact_ref`、`_require_sha256`、`isinstance`、`paired_block_ref.to_dict`、`store.reference`、`validate_development_block_preparation_policy`、`verify_development_shared_checkpoint_manifest_against_policy` |
| `_validate_nodes` — `_validate_nodes(store, nodes, events, event_refs)` | function / [690](../../../../agent/src/sr2fpga_agent/block_preparation.py#L690) | `ValueError`、`_event_set_sha256`、`_validate_node_artifacts`、`len`、`set`、`tuple`、`zip` |
| `_validate_node_artifacts` — `_validate_node_artifacts(store, node, events)` | function / [744](../../../../agent/src/sr2fpga_agent/block_preparation.py#L744) | `<dynamic>.hexdigest`、`ValueError`、`_artifact_ref`、`_require_checkpoint_artifact_key`、`_require_store_reference`、`_verify_project_digest`、`any`、`hashlib.sha256`、`isinstance`、`json.loads`、`len`、`store.read_verified`、`tuple` |
| `_verify_project_digest` — `_verify_project_digest(content, expected, label)` | function / [820](../../../../agent/src/sr2fpga_agent/block_preparation.py#L820) | `GeneratedProject`、`ValueError`、`dict`、`json.loads`、`project_package_sha256`、`str` |
| `_require_checkpoint_artifact_key` — `_require_checkpoint_artifact_key(node)` | function / [831](../../../../agent/src/sr2fpga_agent/block_preparation.py#L831) | `ValueError`、`node.artifact_ref.key.endswith` |
| `_node_payload` — `_node_payload(node)` | function / [839](../../../../agent/src/sr2fpga_agent/block_preparation.py#L839) | `list`、`node.artifact_ref.to_dict`、`node.trusted_skeleton_ref.to_dict`、`reference.to_dict` |
| `_node_from_payload` — `_node_from_payload(payload)` | function / [857](../../../../agent/src/sr2fpga_agent/block_preparation.py#L857) | `CheckpointId`、`CheckpointNode`、`_artifact_ref`、`tuple` |
| `_event_set_sha256` — `_event_set_sha256(store, references)` | function / [877](../../../../agent/src/sr2fpga_agent/block_preparation.py#L877) | `<dynamic>.hexdigest`、`ValueError`、`_canonical_json`、`event.get`、`hashlib.sha256`、`ids.append`、`isinstance`、`json.loads`、`store.read_verified` |
| `_require_store_reference` — `_require_store_reference(store, reference, label)` | function / [888](../../../../agent/src/sr2fpga_agent/block_preparation.py#L888) | `ValueError`、`store.read_verified`、`store.reference` |
| `_require_sha256` — `_require_sha256(value, label)` | function / [894](../../../../agent/src/sr2fpga_agent/block_preparation.py#L894) | `ValueError`、`int`、`isinstance`、`len` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/budget_allocation.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/budget_allocation.py) · 218 行 · SHA-256 `cf2e34970c6e36f66e17af9333e8be9c26ce597eb08401b04f572dfbb666a4ed`

> Registered B4 model-call allocations from 'paper1-v2.1' section 6.4.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.method_contract`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `BudgetAllocationError` — `BudgetAllocationError` | class / [46](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L46) | 无直接调用 |
| `BudgetAllocation` — `BudgetAllocation` | class / [51](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L51) | 无直接调用 |
| `BudgetAllocation.__post_init__` — `__post_init__(self)` | function / [72](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L72) | `ValueError`、`_initial_stages`、`len`、`method_contract` |
| `BudgetAllocation.standalone_max_model_calls` — `standalone_max_model_calls(self)` | function / [99](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L99) | 无直接调用 |
| `BudgetAllocation.unresolved_axes` — `unresolved_axes(self)` | function / [105](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L105) | `getattr`、`tuple` |
| `BudgetAllocation.is_freeze_ready` — `is_freeze_ready(self)` | function / [111](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L111) | 无直接调用 |
| `BudgetAllocation.to_dict` — `to_dict(self)` | function / [116](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L116) | `getattr`、`list` |
| `_initial_stages` — `_initial_stages(contract)` | function / [133](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L133) | `tuple` |
| `budget_allocation` — `budget_allocation(condition)` | function / [169](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L169) | `BudgetAllocationError`、`MethodConditionId`、`isinstance` |
| `assert_b4_conformant` — `assert_b4_conformant(condition, standalone_ceiling)` | function / [188](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L188) | `ValueError`、`budget_allocation` |
| `budget_policy_sha256` — `budget_policy_sha256()` | function / [205](../../../../agent/src/sr2fpga_agent/budget_allocation.py#L205) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`<dynamic>.to_dict`、`hashlib.sha256`、`json.dumps` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`BudgetAllocation`、`dataclass`

## `agent/src/sr2fpga_agent/checkpoint_stop_outcome.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/checkpoint_stop_outcome.py) · 94 行 · SHA-256 `3949d9e26d71ec3c5c583823d612e1e096f2859d649fbcf24ad99b364f0453a5`

> Registered, replayable no-candidate outcomes for failed shared preparation.

导入模块：`__future__`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.block_preparation`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.paired_block`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `reconcile_checkpoint_stop_outcome` — `reconcile_checkpoint_stop_outcome(store, episode_pack_ref, checkpoint_manifest_ref)` | function / [18](../../../../agent/src/sr2fpga_agent/checkpoint_stop_outcome.py#L18) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.split`、`ArtifactRef`、`ValueError`、`any`、`audit.get`、`blocked_methods_from_verified_manifest`、`checkpoint_manifest_ref.to_dict`、`episode_pack_ref.to_dict`、`hashlib.sha256`、`json.dumps`、`json.loads`、`load_development_paired_block`、`next`、`read_development_shared_checkpoint_manifest`、`store.put_validated_json`、`store.read_verified`、`str`、`validate_episode_pack` |
| `read_verified_checkpoint_stop_outcome` — `read_verified_checkpoint_stop_outcome(store, reference)` | function / [83](../../../../agent/src/sr2fpga_agent/checkpoint_stop_outcome.py#L83) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ArtifactRef`、`ContractRegistry`、`ValueError`、`json.loads`、`reconcile_checkpoint_stop_outcome`、`store.read_verified` |

## `agent/src/sr2fpga_agent/cli.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/cli.py) · 553 行 · SHA-256 `354d55e561a400727a4c23361b9a569fb47bcffbb056b840f9d125514ed6cf1e`

> Command-line entry point for the SR2FPGA data generation agent.

导入模块：`__future__`、`argparse`、`json`、`os`、`pathlib`、`sr2fpga_agent.agent`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.family_recipe`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.generation`、`sr2fpga_agent.method_adapters`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.providers`、`sr2fpga_agent.repair`、`sr2fpga_agent.requirement_boundary`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `main` — `main(argv)` | function / [41](../../../../agent/src/sr2fpga_agent/cli.py#L41) | `<dynamic>.join`、`<dynamic>.run_one`、`<dynamic>.to_dict`、`ArtifactStore`、`DataGenerationAgent`、`FrozenContextDirectProjectGenerator`、`ModelCallBudget`、`PlatformProfile`、`ProjectRequest`、`SystemExit`、`_bind_cli_frozen_his_generator`、`_cli_method_condition`、`_default_model_call_ceiling`、`_write_model_budget_summary`、`argparse.ArgumentParser`、`boundary.to_dict`、`build_development_episode_pack`、`build_project_generator`、`build_repairer`、`context_from_validated_episode_pack`、`enumerate`、`evaluate_requirement_boundary`、`freeze_ready_requirement_context`、`isinstance`、`model_budget.summary`、`parser.add_argument`、`parser.parse_args`、`print`、`result.get`、`select_family_recipe` |
| `_cli_method_condition` — `_cli_method_condition(provider, repair_enabled, output_repair_enabled)` | function / [255](../../../../agent/src/sr2fpga_agent/cli.py#L255) | 无直接调用 |
| `_bind_cli_frozen_his_generator` — `_bind_cli_frozen_his_generator(generator, method_condition, context, platform, artifact_store, episode_id, output_repair_enabled)` | function / [268](../../../../agent/src/sr2fpga_agent/cli.py#L268) | `FrozenContextHisGeneratorBridge`、`FrozenContextSystemHisCorrectionFacade`、`FrozenContextSystemHisFacade`、`FrozenContextSystemHisValidationFacade`、`GenerationServices`、`MethodArtifactGateway`、`SystemExit`、`client_for_stage`、`isinstance` |
| `_default_model_call_ceiling` — `_default_model_call_ceiling(method_condition, max_attempts, output_repair_enabled)` | function / [320](../../../../agent/src/sr2fpga_agent/cli.py#L320) | `SystemExit`、`max` |
| `_write_model_budget_summary` — `_write_model_budget_summary(dataset_root, sample_id, summary)` | function / [337](../../../../agent/src/sr2fpga_agent/cli.py#L337) | `json.dumps`、`json.loads`、`metadata_path.exists`、`metadata_path.read_text`、`metadata_path.write_text` |
| `build_project_generator` — `build_project_generator(provider, model, base_url, api_key_env, event_sink, model_budget, decoding_seed, wire_api, reasoning_effort, disable_response_storage, timeout_seconds, transport_attempts)` | function / [349](../../../../agent/src/sr2fpga_agent/cli.py#L349) | `DirectProjectGenerator`、`OpenAICompatibleClient`、`OpenAICompatibleConfig`、`SystemExit`、`TwoStageProjectGenerator`、`model_budget.client`、`os.environ.get` |
| `build_project_generator_for_connection` — `build_project_generator_for_connection(connection, event_sink, model_budget, decoding_seed)` | function / [412](../../../../agent/src/sr2fpga_agent/cli.py#L412) | `AnthropicCompatibleClient`、`AnthropicCompatibleConfig`、`DirectProjectGenerator`、`OpenAICompatibleClient`、`OpenAICompatibleConfig`、`OracleHisProjectGenerator`、`SystemExit`、`TwoStageProjectGenerator`、`getattr`、`model_budget.client`、`os.environ.get` |
| `build_repairer` — `build_repairer(provider, model, base_url, api_key_env, model_budget, decoding_seed, timeout_seconds, transport_attempts)` | function / [470](../../../../agent/src/sr2fpga_agent/cli.py#L470) | `OpenAICompatibleClient`、`OpenAICompatibleConfig`、`ProjectRepairer`、`SystemExit`、`model_budget.client`、`os.environ.get` |
| `build_repairer_for_connection` — `build_repairer_for_connection(connection, model_budget, decoding_seed)` | function / [502](../../../../agent/src/sr2fpga_agent/cli.py#L502) | `AnthropicCompatibleClient`、`AnthropicCompatibleConfig`、`OpenAICompatibleClient`、`OpenAICompatibleConfig`、`ProjectRepairer`、`SystemExit`、`getattr`、`model_budget.client`、`os.environ.get` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `agent/src/sr2fpga_agent/contract_registry.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/contract_registry.py) · 175 行 · SHA-256 `df527ea959b89761872f0c38894d1cb8b5e5227682d180e957668bd2294016e7`

> Manifest-aware access to registered JSON contracts.

导入模块：`__future__`、`dataclasses`、`json`、`jsonschema`、`pathlib`、`referencing`、`sr2fpga_agent.repository_paths`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RegisteredContract` — `RegisteredContract` | class / [31](../../../../agent/src/sr2fpga_agent/contract_registry.py#L31) | 无直接调用 |
| `RegisteredContract.validate` — `validate(self, payload)` | function / [38](../../../../agent/src/sr2fpga_agent/contract_registry.py#L38) | `_cached_validator`、`_json_path`、`sorted`、`str`、`tuple`、`validator.iter_errors` |
| `ContractRegistry` — `ContractRegistry` | class / [53](../../../../agent/src/sr2fpga_agent/contract_registry.py#L53) | 无直接调用 |
| `ContractRegistry.__init__` — `__init__(self, paths)` | function / [54](../../../../agent/src/sr2fpga_agent/contract_registry.py#L54) | `RepositoryPaths.discover`、`_cached_manifest` |
| `ContractRegistry.load_schema` — `load_schema(self, key)` | function / [59](../../../../agent/src/sr2fpga_agent/contract_registry.py#L59) | `<dynamic>.get`、`KeyError`、`Path`、`PurePosixPath`、`RegisteredContract`、`ValueError`、`_SCHEMA_DEPENDENCIES.get`、`_cached_schema`、`_resolved`、`contracts.get`、`document.get`、`entry.get`、`isinstance`、`relative.is_absolute`、`self._manifest.get`、`self.load_schema`、`tuple` |
| `_resolved` — `_resolved(path)` | function / [109](../../../../agent/src/sr2fpga_agent/contract_registry.py#L109) | `_RESOLVED_CACHE.get`、`path.resolve`、`str` |
| `_cached_manifest` — `_cached_manifest(path)` | function / [120](../../../../agent/src/sr2fpga_agent/contract_registry.py#L120) | `_MANIFEST_CACHE.get`、`_load_object`、`file_identity` |
| `_cached_schema` — `_cached_schema(path)` | function / [131](../../../../agent/src/sr2fpga_agent/contract_registry.py#L131) | `Draft202012Validator.check_schema`、`_SCHEMA_CACHE.get`、`_load_object`、`file_identity` |
| `_cached_validator` — `_cached_validator(path, document, dependencies)` | function / [143](../../../../agent/src/sr2fpga_agent/contract_registry.py#L143) | `<dynamic>.with_resources`、`Draft202012Validator`、`Registry`、`Resource.from_contents`、`_VALIDATOR_CACHE.get`、`file_identity` |
| `_load_object` — `_load_object(path)` | function / [164](../../../../agent/src/sr2fpga_agent/contract_registry.py#L164) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_json_path` — `_json_path(parts)` | function / [171](../../../../agent/src/sr2fpga_agent/contract_registry.py#L171) | `isinstance` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/contract_skeleton.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/contract_skeleton.py) · 563 行 · SHA-256 `8f7ad969c389be621370247cb0946431ee6d542a3c6b6a2917529a322e314707`

> Contract-preserving skeleton generation from System-HIS v1.2.

导入模块：`__future__`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.project_generator`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_contract_skeleton_project` — `build_contract_skeleton_project(request, platform, system_his)` | function / [18](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L18) | `<dynamic>.get`、`GeneratedProject`、`ValueError`、`_component_module`、`_json`、`_list`、`_manifest`、`_mapping`、`_placeholder_module`、`_predicted_qor`、`_string_list`、`_testbench`、`_timing_sdc`、`_top_module`、`_top_source`、`artifacts.get`、`component.get`、`str`、`system_his.get`、`top.get` |
| `merge_behavior_files` — `merge_behavior_files(skeleton, behavior_files)` | function / [59](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L59) | `<dynamic>.join`、`GeneratedProject`、`ValueError`、`_fill_behavior_hole`、`_validate_behavior_body`、`behavior_files.items`、`dict`、`files.items`、`set`、`sorted` |
| `_validate_behavior_body` — `_validate_behavior_body(path, behavior)` | function / [81](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L81) | `ValueError`、`re.search` |
| `_fill_behavior_hole` — `_fill_behavior_hole(content, behavior)` | function / [86](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L86) | `<dynamic>.join`、`<dynamic>.splitlines`、`<dynamic>.strip`、`_declared_localparams`、`_drop_duplicate_skeleton_localparams`、`_drop_duplicate_unused_clock_reset_lines`、`content.replace`、`line.strip` |
| `_declared_localparams` — `_declared_localparams(verilog)` | function / [98](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L98) | `match.group`、`re.finditer` |
| `_drop_duplicate_skeleton_localparams` — `_drop_duplicate_skeleton_localparams(content, declared)` | function / [105](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L105) | `<dynamic>.join`、`content.endswith`、`content.splitlines`、`lines.append`、`match.group`、`re.fullmatch` |
| `_drop_duplicate_unused_clock_reset_lines` — `_drop_duplicate_unused_clock_reset_lines(content, behavior)` | function / [117](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L117) | `<dynamic>.join`、`behavior.endswith`、`behavior.splitlines`、`re.fullmatch` |
| `_manifest` — `_manifest(request, platform, system_his, top_module, sources)` | function / [128](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L128) | `<dynamic>.get`、`_first_string`、`_mapping`、`system_his.get` |
| `_top_module` — `_top_module(system_his, top_module, components_by_source)` | function / [158](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L158) | `<dynamic>.join`、`<dynamic>.strip`、`_data_flow_assignment_lines`、`_instance_lines`、`_instance_wire`、`_is_top_passthrough`、`_list`、`_mapping`、`_merged_parameters`、`_parameter_block`、`_port_block`、`_range`、`component.get`、`components_by_name.get`、`components_by_name.values`、`components_by_source.values`、`declared_wires.add`、`instance_map.get`、`lines.append`、`lines.extend`、`parameter.get`、`port_map.get`、`set`、`str`、`system_his.get`、`top.get` |
| `_component_module` — `_component_module(component, system_his)` | function / [204](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L204) | `<dynamic>.join`、`<dynamic>.strip`、`_fsm_states_for_component`、`_list`、`_parameter_block`、`_port_block`、`_unused_clock_reset_line`、`component.get`、`lines.append`、`str` |
| `_placeholder_module` — `_placeholder_module(source, component_names, system_his)` | function / [225](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L225) | `<dynamic>.removesuffix`、`_component_module`、`source.rsplit` |
| `_instance_lines` — `_instance_lines(instance, component, top_parameter_names)` | function / [231](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L231) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.strip`、`_instance_wire`、`_is_top_passthrough`、`_list`、`_mapping`、`_parameter_override_block`、`component.get`、`connections.append`、`instance.get`、`lines.append`、`set`、`str` |
| `_data_flow_assignment_lines` — `_data_flow_assignment_lines(system_his)` | function / [249](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L249) | `<dynamic>.get`、`<dynamic>.join`、`_append_assignment`、`_companion_signal`、`_endpoint_signal`、`_list`、`_mapping`、`_parse_endpoint`、`_ports_by_endpoint_owner`、`lines.append`、`set`、`sorted`、`system_his.get`、`unused_signals.add`、`zip` |
| `_append_assignment` — `_append_assignment(lines, seen, assigned_sinks, source, sink)` | function / [292](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L292) | `assigned_sinks.get`、`len`、`lines.append`、`seen.add` |
| `_ports_by_endpoint_owner` — `_ports_by_endpoint_owner(system_his)` | function / [314](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L314) | `<dynamic>.get`、`<dynamic>.strip`、`_list`、`_mapping`、`component.get`、`components_by_name.get`、`instance_map.get`、`str`、`system_his.get` |
| `_parse_endpoint` — `_parse_endpoint(endpoint)` | function / [339](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L339) | `<dynamic>.strip`、`isinstance`、`str`、`text.split` |
| `_endpoint_signal` — `_endpoint_signal(owner, port)` | function / [349](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L349) | `_instance_wire` |
| `_companion_signal` — `_companion_signal(owner, port, suffix, ports_by_owner)` | function / [355](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L355) | `_endpoint_signal`、`candidates.append`、`port.endswith`、`port.removesuffix`、`ports_by_owner.get`、`set` |
| `_unused_clock_reset_line` — `_unused_clock_reset_line(ports)` | function / [368](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L368) | `<dynamic>.join`、`<dynamic>.strip`、`_mapping`、`names.append`、`port_map.get`、`str` |
| `_testbench` — `_testbench(request, platform, system_his, top_module)` | function / [381](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L381) | `_deterministic_functional_testbench`、`_fail_safe_testbench` |
| `_deterministic_functional_testbench` — `_deterministic_functional_testbench(request, platform, top_module)` | function / [393](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L393) | `<dynamic>.files.get`、`<dynamic>.generate`、`ProjectGenerator` |
| `_fail_safe_testbench` — `_fail_safe_testbench(task_type)` | function / [408](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L408) | `<dynamic>.replace`、`task_type.replace` |
| `_merged_parameters` — `_merged_parameters(top_parameters, components)` | function / [421](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L421) | `<dynamic>.get`、`<dynamic>.strip`、`_list`、`_mapping`、`merged.append`、`parameter.get`、`parameter_map.get`、`seen.add`、`str` |
| `_timing_sdc` — `_timing_sdc(system_his)` | function / [434](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L434) | `_mapping`、`float`、`str`、`system_his.get`、`timing.get` |
| `_predicted_qor` — `_predicted_qor(system_his)` | function / [445](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L445) | `_mapping`、`resources.get`、`system_his.get` |
| `_port_block` — `_port_block(ports)` | function / [450](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L450) | `<dynamic>.join`、`<dynamic>.strip`、`_mapping`、`_range`、`declarations.append`、`port_map.get`、`str` |
| `_parameter_block` — `_parameter_block(parameters)` | function / [461](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L461) | `<dynamic>.join`、`<dynamic>.strip`、`_mapping`、`declarations.append`、`parameter_map.get`、`str` |
| `_parameter_override_block` — `_parameter_override_block(values, top_parameter_names)` | function / [472](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L472) | `<dynamic>.join`、`set`、`values.items` |
| `_range` — `_range(width)` | function / [481](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L481) | `<dynamic>.strip`、`isinstance`、`str`、`text.startswith`、`width.get` |
| `_fsm_states_for_component` — `_fsm_states_for_component(component_name, system_his)` | function / [503](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L503) | `<dynamic>.get`、`<dynamic>.strip`、`_fsm_owner`、`_list`、`_mapping`、`fsm_map.get`、`instances_by_name.get`、`seen.add`、`set`、`states.append`、`str`、`system_his.get` |
| `_fsm_owner` — `_fsm_owner(fsm)` | function / [523](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L523) | `<dynamic>.strip`、`fsm.get`、`name.split`、`str` |
| `_is_top_passthrough` — `_is_top_passthrough(port_name, instance)` | function / [533](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L533) | `instance.get`、`str` |
| `_instance_wire` — `_instance_wire(instance_name, port_name)` | function / [537](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L537) | 无直接调用 |
| `_top_source` — `_top_source(sources)` | function / [541](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L541) | 无直接调用 |
| `_json` — `_json(payload)` | function / [545](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L545) | `json.dumps` |
| `_mapping` — `_mapping(value)` | function / [549](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L549) | `isinstance` |
| `_list` — `_list(value)` | function / [553](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L553) | `isinstance` |
| `_string_list` — `_string_list(value)` | function / [557](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L557) | `_list`、`isinstance`、`item.strip` |
| `_first_string` — `_first_string(value, default)` | function / [561](../../../../agent/src/sr2fpga_agent/contract_skeleton.py#L561) | `_string_list` |

## `agent/src/sr2fpga_agent/cost_accounting.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/cost_accounting.py) · 869 行 · SHA-256 `a29545dff90c1c12e74c1d0c1905e1a6c15061ecc5276e2bc24c14d2847f09c0`

> Write-once attempt-cost events and deterministic cost reconciliation.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.evaluator_dispatch`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.public_evaluator`、`sr2fpga_agent.terminal_selection`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `CostAccountingError` — `CostAccountingError` | class / [56](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L56) | 无直接调用 |
| `ReconciledCostSummary` — `ReconciledCostSummary` | class / [61](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L61) | 无直接调用 |
| `ReconciledTrajectory` — `ReconciledTrajectory` | class / [67](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L67) | 无直接调用 |
| `AttemptCostLedger` — `AttemptCostLedger` | class / [72](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L72) | 无直接调用 |
| `AttemptCostLedger.__init__` — `__init__(self, store, episode_id, attempt_id, method_condition, failure_origin, candidate_id, input_artifact_hashes)` | function / [75](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L75) | `set`、`sorted`、`tuple`、`validate_accounting_failure_origin` |
| `AttemptCostLedger.event_refs` — `event_refs(self)` | function / [99](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L99) | `tuple` |
| `AttemptCostLedger.observed_axes` — `observed_axes(self)` | function / [103](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L103) | `frozenset`、`set` |
| `AttemptCostLedger.reserve` — `reserve(self, axis, amount, stage, visibility_class, limit, used_after, started_at)` | function / [106](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L106) | `_require_axis_value`、`self._append` |
| `AttemptCostLedger.record_budget_exhausted` — `record_budget_exhausted(self, axis, amount, stage, visibility_class, limit, used_after, started_at)` | function / [135](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L135) | `_require_axis_value`、`self._append` |
| `AttemptCostLedger.record_cost` — `record_cost(self, stage, visibility_class, cost_delta, status, duration_seconds, input_artifact_hashes, output_artifact_hashes, unavailable_axes, started_at)` | function / [164](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L164) | `CostAccountingError`、`dict`、`self._append`、`tuple` |
| `AttemptCostLedger.close` — `close(self, zero_axes, unavailable_axes, started_at)` | function / [193](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L193) | `<dynamic>.join`、`CostAccountingError`、`declared_unavailable.items`、`dict`、`isinstance`、`self._append`、`self._values.get`、`set`、`sorted` |
| `AttemptCostLedger._append` — `_append(self, stage, visibility_class, event_type, status, started_at, duration_seconds, budget_reservation, cost_delta, unavailable_axes, input_artifact_hashes, output_artifact_hashes)` | function / [242](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L242) | `<dynamic>.hexdigest`、`CostAccountingError`、`_accumulate_delta`、`_canonical_json`、`_event_id_from_ref`、`_validate_delta`、`dict`、`hashlib.sha256`、`len`、`self._refs.append`、`self.store.put_validated_json`、`set`、`sorted`、`time.time` |
| `AttemptCostLedgerRouter` — `AttemptCostLedgerRouter` | class / [302](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L302) | 无直接调用 |
| `AttemptCostLedgerRouter.__init__` — `__init__(self)` | function / [305](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L305) | 无直接调用 |
| `AttemptCostLedgerRouter.activate` — `activate(self, ledger)` | function / [308](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L308) | `CostAccountingError` |
| `AttemptCostLedgerRouter.current` — `current(self)` | function / [313](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L313) | 无直接调用 |
| `AttemptCostLedgerRouter.deactivate` — `deactivate(self, ledger)` | function / [316](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L316) | `CostAccountingError` |
| `AccountingCommandRunner` — `AccountingCommandRunner` | class / [322](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L322) | 无直接调用 |
| `AccountingCommandRunner.__init__` — `__init__(self, delegate, router)` | function / [325](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L325) | 无直接调用 |
| `AccountingCommandRunner.run` — `run(self, command, cwd, stage, timeout_seconds)` | function / [329](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L329) | `getattr`、`self._delegate.run`、`self._record`、`time.monotonic` |
| `AccountingCommandRunner._record` — `_record(self, stage, duration, status)` | function / [352](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L352) | `float`、`ledger.record_cost`、`max`、`self._router.current` |
| `validate_accounting_failure_origin` — `validate_accounting_failure_origin(value)` | function / [368](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L368) | `CostAccountingError` |
| `reconcile_cost_events` — `reconcile_cost_events(store, event_refs, summary_key, registry)` | function / [375](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L375) | `<dynamic>.hexdigest`、`<dynamic>.join`、`ContractRegistry`、`CostAccountingError`、`ReconciledCostSummary`、`_accumulate_delta`、`_canonical_json`、`_validate_delta`、`contract_registry.load_schema`、`declared_unavailable.get`、`enumerate`、`event.items`、`event_contract.validate`、`events.append`、`hashlib.sha256`、`json.loads`、`len`、`store.put_validated_json`、`store.read_verified`、`sum`、`tuple`、`unavailable.items`、`values.get` |
| `reconcile_attempt_trajectory` — `reconcile_attempt_trajectory(store, cost_summary_refs, terminal_candidate_ref, terminal_candidate_missing_reason, development_hidden_outcome_ref, development_hidden_conformance_outcome_ref, development_terminal_selection_ref, development_selected_public_outcome_ref, development_terminal_public_outcome_ref, registry)` | function / [492](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L492) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.validate`、`ContractRegistry`、`CostAccountingError`、`ReconciledTrajectory`、`_canonical_json`、`attempts.append`、`contract_registry.load_schema`、`development_hidden_conformance_outcome_ref.to_dict`、`development_selected_public_outcome_ref.to_dict`、`development_terminal_public_outcome_ref.to_dict`、`development_terminal_selection_ref.to_dict`、`dict`、`event_refs.append`、`failure_origins.update`、`hashlib.sha256`、`iter`、`json.loads`、`len`、`method_policy_sha256`、`missing.append`、`next`、`range`、`read_verified_development_authoritative_attempt_public_outcome`、`read_verified_development_hidden_conformance_outcome`、`read_verified_development_public_outcome`、`read_verified_development_terminal_selection`、`reconcile_cost_events`、`reference.to_dict`、`seen_attempt_ids.add`、`selected_public.get`、`set`、`sorted`、`store.put_validated_json`、`store.read_verified`、`store.reference`、`summaries.append`、`summaries.sort`、`summary_contract.validate`、`summary_ref.to_dict`、`terminal_candidate_ref.to_dict`、`terminal_public.get`、`trajectory_contract.validate`、`tuple` |
| `_event_id_from_ref` — `_event_id_from_ref(store, reference, error, label)` | function / [797](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L797) | `error`、`isinstance`、`json.loads`、`payload.get`、`store.read_verified` |
| `_validate_delta` — `_validate_delta(cost_delta, unavailable_axes, error)` | function / [811](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L811) | `<dynamic>.join`、`_require_axis_value`、`cost_delta.items`、`error`、`isinstance`、`set`、`sorted`、`unavailable_axes.get` |
| `_require_axis_value` — `_require_axis_value(axis, value, allow_zero, error)` | function / [834](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L834) | `error`、`isinstance` |
| `_accumulate_delta` — `_accumulate_delta(values, unavailable, cost_delta, unavailable_axes, error)` | function / [851](../../../../agent/src/sr2fpga_agent/cost_accounting.py#L851) | `cost_delta.items`、`error`、`unavailable.get`、`values.get` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`

## `agent/src/sr2fpga_agent/episode_executor.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/episode_executor.py) · 470 行 · SHA-256 `3c5dc024ecc5d03353ad4a04e109862e5cfb7a94ac28848fb3f9b55081e9ce53`

> Explicit pre-candidate execution state machine for Paper-1 methods.

导入模块：`__future__`、`dataclasses`、`enum`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.method_adapters`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PreCandidateState` — `PreCandidateState` | class / [25](../../../../agent/src/sr2fpga_agent/episode_executor.py#L25) | 无直接调用 |
| `PreCandidateOutcome` — `PreCandidateOutcome` | class / [37](../../../../agent/src/sr2fpga_agent/episode_executor.py#L37) | 无直接调用 |
| `EpisodeExecutor` — `EpisodeExecutor` | class / [48](../../../../agent/src/sr2fpga_agent/episode_executor.py#L48) | `SharedArtifactRefs` |
| `EpisodeExecutor.__init__` — `__init__(self, max_his_corrections, max_project_output_repairs, max_shared_pre_candidate_repairs)` | function / [55](../../../../agent/src/sr2fpga_agent/episode_executor.py#L55) | `RepairController`、`ValueError` |
| `EpisodeExecutor.emit_candidate` — `emit_candidate(self, adapter, context, services, shared_artifacts)` | function / [76](../../../../agent/src/sr2fpga_agent/episode_executor.py#L76) | `MethodStageFailure`、`PreCandidateOutcome`、`_failed_h_details`、`adapter.emit_initial`、`dict`、`h_report.get`、`isinstance`、`self._failed`、`self._lower`、`self._repair.correct_his`、`self._transition`、`services.artifacts.read_planning`、`services.his_validation.validate_his`、`str`、`tuple`、`type` |
| `EpisodeExecutor._lower` — `_lower(self, adapter, context, services, shared_artifacts, planning, states, h_report, corrections, output_repairs)` | function / [221](../../../../agent/src/sr2fpga_agent/episode_executor.py#L221) | `MethodStageFailure`、`PreCandidateOutcome`、`adapter.repair_project_output`、`callable`、`getattr`、`isinstance`、`lower`、`self._failed`、`self._project_output_repair_unavailable_reason`、`self._transition`、`str`、`tuple`、`type` |
| `EpisodeExecutor._project_output_repair_unavailable_reason` — `_project_output_repair_unavailable_reason(self, adapter, corrections, output_repairs)` | function / [348](../../../../agent/src/sr2fpga_agent/episode_executor.py#L348) | `isinstance` |
| `EpisodeExecutor._failed` — `_failed(self, states, services, adapter, failure, planning, h_report, corrections, output_repairs)` | function / [366](../../../../agent/src/sr2fpga_agent/episode_executor.py#L366) | `PreCandidateOutcome`、`failure.parent_output_ref.to_dict`、`failure.produced_output_ref.to_dict`、`isinstance`、`self._transition`、`tuple` |
| `EpisodeExecutor._transition` — `_transition(states, services, adapter, state, **payload)` | function / [413](../../../../agent/src/sr2fpga_agent/episode_executor.py#L413) | `RuntimeError`、`services.artifacts.append_event`、`set`、`states.append` |
| `_failed_h_details` — `_failed_h_details(report)` | function / [464](../../../../agent/src/sr2fpga_agent/episode_executor.py#L464) | `isinstance`、`report.get`、`stage_report.get`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/episode_outcome.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/episode_outcome.py) · 828 行 · SHA-256 `df23678b8529591937e853c0284157f1ea2b216ebca40d085338882fb990906e`

> Fail-closed development projections and event-derived episode reducers.

导入模块：`__future__`、`collections`、`dataclasses`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.evaluator_dispatch`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.paired_measurement`、`sr2fpga_agent.public_evaluator`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `EpisodeOutcomeError` — `EpisodeOutcomeError` | class / [33](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L33) | 无直接调用 |
| `EpisodeOutcomeRecord` — `EpisodeOutcomeRecord` | class / [38](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L38) | 无直接调用 |
| `project_development_public_evaluation` — `project_development_public_evaluation(store, sample_dir, episode_id, method_condition, analysis_population, terminal_public_outcome_ref, registry)` | function / [43](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L43) | `<dynamic>.hexdigest`、`ContractRegistry`、`EpisodeOutcomeError`、`Path`、`_canonical_json`、`_classify_missingness`、`_project_repair`、`_project_stages`、`_read_object_file`、`dict`、`hashlib.sha256`、`isinstance`、`read_verified_development_public_outcome`、`store.put_validated_json`、`terminal_public_outcome_ref.to_dict`、`trajectory.get` |
| `read_verified_development_episode_outcome` — `read_verified_development_episode_outcome(store, outcome_ref, registry)` | function / [129](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L129) | `ArtifactRef`、`ContractRegistry`、`EpisodeOutcomeError`、`_read_registered`、`reconcile_development_episode_outcome` |
| `reconcile_development_episode_outcome` — `reconcile_development_episode_outcome(store, public_evaluation_ref, trajectory_ref, registry)` | function / [158](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L158) | `<dynamic>.get`、`<dynamic>.hexdigest`、`ArtifactRef`、`ContractRegistry`、`EpisodeOutcomeError`、`_canonical_json`、`_development_vpp_l3`、`_optional_artifact_ref`、`_read_registered`、`_verify_terminal_hidden_event_sequence`、`hashlib.sha256`、`hidden_conformance_ref.to_dict`、`isinstance`、`method_policy_sha256`、`public_evaluation_ref.to_dict`、`read_verified_development_hidden_conformance_outcome`、`read_verified_development_public_outcome`、`reconcile_attempt_trajectory`、`reference.to_dict`、`store.put_validated_json`、`trajectory.get`、`trajectory_ref.to_dict` |
| `reconcile_excluded_full_pack_outcomes` — `reconcile_excluded_full_pack_outcomes(store, smoke_id, source_runner_reconciliation_ref, outcomes, registry)` | function / [377](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L377) | `ContractRegistry`、`Counter`、`EpisodeOutcomeError`、`_read_registered`、`dict`、`isinstance`、`len`、`list`、`method_records.append`、`outcome.get`、`record.outcome_ref.to_dict`、`set`、`source_by_method.get`、`source_runner_reconciliation_ref.to_dict`、`store.put_validated_json`、`tuple` |
| `_development_vpp_l3` — `_development_vpp_l3(stage_outcomes, hidden_conformance)` | function / [516](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L516) | `failed.append`、`unavailable.append` |
| `_verify_terminal_hidden_event_sequence` — `_verify_terminal_hidden_event_sequence(store, trajectory)` | function / [550](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L550) | `<dynamic>.get`、`ArtifactRef`、`EpisodeOutcomeError`、`enumerate`、`hidden_events.append`、`isinstance`、`json.loads`、`len`、`store.read_verified` |
| `_project_repair` — `_project_repair(trajectory, measurement)` | function / [600](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L600) | `EpisodeOutcomeError`、`_nonnegative_int`、`accounting.get`、`bool`、`build_episode_measurement`、`by_scope_raw.get`、`dict`、`int`、`isinstance`、`issues.append`、`issues.extend`、`item.get`、`measurement.get`、`raw.get`、`rebuilt.get`、`set`、`sorted`、`str`、`sum`、`trajectory.get` |
| `_project_stages` — `_project_stages(labels, method)` | function / [670](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L670) | `EpisodeOutcomeError`、`_stage`、`_stage_from_check`、`_stage_from_text`、`any`、`checks.get`、`isinstance`、`labels.get`、`str` |
| `_classify_missingness` — `_classify_missingness(labels, measurement, stages)` | function / [711](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L711) | `any`、`labels.get`、`measurement.get`、`stages.values`、`str` |
| `_stage_from_text` — `_stage_from_text(value, missing_reason)` | function / [737](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L737) | `<dynamic>.get`、`_stage`、`str` |
| `_stage_from_check` — `_stage_from_check(value, upstream_failed, missing_reason)` | function / [746](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L746) | `_stage` |
| `_stage` — `_stage(status, reason)` | function / [759](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L759) | 无直接调用 |
| `_read_object_file` — `_read_object_file(path, label)` | function / [765](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L765) | `EpisodeOutcomeError`、`isinstance`、`json.loads`、`path.read_bytes` |
| `_read_registered` — `_read_registered(store, reference, registry, contract_key, label)` | function / [778](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L778) | `<dynamic>.join`、`<dynamic>.validate`、`EpisodeOutcomeError`、`_verify_content_id`、`json.loads`、`registry.load_schema`、`store.read_verified` |
| `_verify_content_id` — `_verify_content_id(payload, contract_key, label)` | function / [796](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L796) | `<dynamic>.get`、`<dynamic>.hexdigest`、`EpisodeOutcomeError`、`_canonical_json`、`hashlib.sha256`、`payload.get`、`payload.items` |
| `_nonnegative_int` — `_nonnegative_int(value, label)` | function / [812](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L812) | `EpisodeOutcomeError`、`isinstance` |
| `_optional_artifact_ref` — `_optional_artifact_ref(payload)` | function / [818](../../../../agent/src/sr2fpga_agent/episode_outcome.py#L818) | `ArtifactRef`、`EpisodeOutcomeError`、`isinstance` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`

## `agent/src/sr2fpga_agent/evaluator_dispatch.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py) · 381 行 · SHA-256 `56a36179bf92223a05b2820e1efd15400de842f2a7f670bb7e1fcfe434a58ba0`

> Development-only sealed-candidate boundary for evaluator-owned execution.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`re`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.hidden_execution_state`、`sr2fpga_agent.models`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `HiddenEvaluatorInput` — `HiddenEvaluatorInput` | class / [20](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L20) | 无直接调用 |
| `OpaqueHiddenOutcomeRef` — `OpaqueHiddenOutcomeRef` | class / [34](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L34) | 无直接调用 |
| `OpaqueHiddenOutcomeRef.to_dict` — `to_dict(self)` | function / [40](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L40) | `asdict` |
| `DevelopmentHiddenEvaluationAuthority` — `DevelopmentHiddenEvaluationAuthority` | class / [44](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L44) | 无直接调用 |
| `DevelopmentHiddenEvaluationAuthority.__init__` — `__init__(self, candidate_store, evaluator_store, evaluator)` | function / [52](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L52) | `ValueError`、`candidate_store.root.resolve`、`evaluator_store.root.resolve` |
| `DevelopmentHiddenEvaluationAuthority.evaluate_once` — `evaluate_once(self, terminal_candidate_ref, private_commitment_ref, public_contract_sha256, public_profile_sha256, tool_environment_policy_sha256, decoding_seed, max_infrastructure_retries)` | function / [64](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L64) | `<dynamic>.hexdigest`、`<dynamic>.to_dict`、`ArtifactIntegrityError`、`HiddenEvaluatorInput`、`OpaqueHiddenOutcomeRef`、`ValueError`、`_canonical_json`、`_require_sha256`、`dict`、`execution_ref.to_dict`、`execution_refs.append`、`hashlib.sha256`、`isinstance`、`json.loads`、`range`、`raw_outcome.get`、`ref.to_dict`、`self._candidate_store.read_sealed_project`、`self._candidate_store.read_verified`、`self._evaluator`、`self._evaluator_store.append_event`、`self._evaluator_store.consume_once`、`self._evaluator_store.put_blob`、`self._evaluator_store.read_verified`、`semantic_commit_ref.to_dict`、`str`、`terminal.get`、`type` |
| `DevelopmentHiddenEvaluationAuthority.candidate_store` — `candidate_store(self)` | function / [197](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L197) | 无直接调用 |
| `DevelopmentHiddenEvaluationAuthority.evaluator_store` — `evaluator_store(self)` | function / [201](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L201) | 无直接调用 |
| `DevelopmentHiddenEvaluationAuthority.store_private_commitment` — `store_private_commitment(self, key, private_commitment)` | function / [204](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L204) | `TypeError`、`ValueError`、`bytes`、`isinstance`、`self._evaluator_store.put_blob` |
| `DevelopmentHiddenEvaluationAuthority.publish_sanitized_outcome` — `publish_sanitized_outcome(self, opaque_ref, registry)` | function / [219](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L219) | `<dynamic>.hexdigest`、`TypeError`、`ValueError`、`_OPAQUE_HIDDEN_OUTCOME_RE.fullmatch`、`_canonical_json`、`_read_json_object`、`_require_sha256`、`hashlib.sha256`、`isinstance`、`ledger.get`、`match.group`、`opaque_ref.to_dict`、`private_record.get`、`raw_outcome.get`、`reconcile_hidden_execution_state`、`self._candidate_store.put_validated_json` |
| `development_hidden_case_seed` — `development_hidden_case_seed(metadata, sample_id)` | function / [322](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L322) | `<dynamic>.digest`、`_canonical_json`、`hashlib.sha256`、`int.from_bytes`、`isinstance`、`metadata.get` |
| `_require_sha256` — `_require_sha256(label, value)` | function / [335](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L335) | `ValueError`、`int`、`isinstance`、`len`、`value.lower` |
| `read_verified_development_hidden_conformance_outcome` — `read_verified_development_hidden_conformance_outcome(store, reference, registry)` | function / [346](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L346) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_canonical_json`、`_read_json_object`、`hashlib.sha256`、`payload.pop` |
| `_read_json_object` — `_read_json_object(store, key_or_ref, label)` | function / [368](../../../../agent/src/sr2fpga_agent/evaluator_dispatch.py#L368) | `ValueError`、`isinstance`、`json.loads`、`store.read_verified` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`re.compile`

## `agent/src/sr2fpga_agent/failure_injector.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/failure_injector.py) · 818 行 · SHA-256 `c7358a5ef1d4319fc47d274b5136a325000968c6c9c503da9ab38557256f679d`

> Synthetic failure injectors for SR2FPGA repair trajectory generation.

导入模块：`__future__`、`dataclasses`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.task_catalog`、`sr2fpga_agent.task_families`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `FailureInjectingProjectGenerator` — `FailureInjectingProjectGenerator` | class / [15](../../../../agent/src/sr2fpga_agent/failure_injector.py#L15) | 无直接调用 |
| `FailureInjectingProjectGenerator.his_source_used_for_generation` — `his_source_used_for_generation(self)` | function / [22](../../../../agent/src/sr2fpga_agent/failure_injector.py#L22) | `getattr` |
| `FailureInjectingProjectGenerator.generate` — `generate(self, request, platform)` | function / [25](../../../../agent/src/sr2fpga_agent/failure_injector.py#L25) | `apply_failure_injectors`、`self.base_generator.generate` |
| `apply_failure_injectors` — `apply_failure_injectors(project, injectors)` | function / [30](../../../../agent/src/sr2fpga_agent/failure_injector.py#L30) | `GeneratedProject`、`ValueError`、`_constraint_missing_clock`、`_missing_manifest_source`、`_multimodule_connection_mismatch`、`_rename_reset_port`、`_testbench_expected_value_mismatch`、`_undefined_signal_reference`、`_width_mismatch`、`_wrong_top_module`、`dict` |
| `oracle_mutation_projects` — `oracle_mutation_projects(project, task_type)` | function / [54](../../../../agent/src/sr2fpga_agent/failure_injector.py#L54) | `GeneratedProject`、`_oracle_dut_mutation`、`_task_family_spec_for_project` |
| `_task_family_spec_for_project` — `_task_family_spec_for_project(project, task_type)` | function / [68](../../../../agent/src/sr2fpga_agent/failure_injector.py#L68) | `<dynamic>.get`、`_task_family_spec`、`isinstance`、`json.loads`、`project.files.get` |
| `_task_family_spec` — `_task_family_spec(task_type)` | function / [87](../../../../agent/src/sr2fpga_agent/failure_injector.py#L87) | `family_id_for_task_type`、`task_family_spec_for_family_id` |
| `_oracle_dut_mutation` — `_oracle_dut_mutation(files, family_id, mutation_name)` | function / [97](../../../../agent/src/sr2fpga_agent/failure_injector.py#L97) | `any`、`dict`、`files.get`、`re.subn`、`replacements.get`、`source.replace` |
| `_rename_reset_port` — `_rename_reset_port(files)` | function / [698](../../../../agent/src/sr2fpga_agent/failure_injector.py#L698) | `ValueError`、`dict`、`top_rtl.replace`、`updated.get` |
| `_undefined_signal_reference` — `_undefined_signal_reference(files)` | function / [708](../../../../agent/src/sr2fpga_agent/failure_injector.py#L708) | `ValueError`、`_replace_once`、`dict`、`updated.get` |
| `_missing_manifest_source` — `_missing_manifest_source(files)` | function / [723](../../../../agent/src/sr2fpga_agent/failure_injector.py#L723) | `_load_manifest`、`dict`、`json.dumps`、`list`、`sources.append` |
| `_wrong_top_module` — `_wrong_top_module(files)` | function / [735](../../../../agent/src/sr2fpga_agent/failure_injector.py#L735) | `_load_manifest`、`dict`、`json.dumps` |
| `_width_mismatch` — `_width_mismatch(files)` | function / [743](../../../../agent/src/sr2fpga_agent/failure_injector.py#L743) | `ValueError`、`dict`、`int`、`match.group`、`re.search`、`top_rtl.replace`、`updated.get` |
| `_testbench_expected_value_mismatch` — `_testbench_expected_value_mismatch(files)` | function / [758](../../../../agent/src/sr2fpga_agent/failure_injector.py#L758) | `ValueError`、`_replace_once`、`dict`、`updated.get` |
| `_constraint_missing_clock` — `_constraint_missing_clock(files)` | function / [773](../../../../agent/src/sr2fpga_agent/failure_injector.py#L773) | `ValueError`、`dict` |
| `_multimodule_connection_mismatch` — `_multimodule_connection_mismatch(files)` | function / [782](../../../../agent/src/sr2fpga_agent/failure_injector.py#L782) | `ValueError`、`dict`、`top_rtl.replace`、`updated.get` |
| `_replace_once` — `_replace_once(text, old, new, error_message)` | function / [803](../../../../agent/src/sr2fpga_agent/failure_injector.py#L803) | `ValueError`、`text.replace` |
| `_load_manifest` — `_load_manifest(files)` | function / [809](../../../../agent/src/sr2fpga_agent/failure_injector.py#L809) | `ValueError`、`isinstance`、`json.loads`、`manifest.get` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/family_recipe.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/family_recipe.py) · 435 行 · SHA-256 `8f26e9b3a3cac454878c7952580fa67834bee1a6056a46ee7b7959ad55954b9e`

> Exact, auditable selection of optional task-family prompt recipes.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.prompts`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.task_catalog`、`sr2fpga_agent.task_families`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `FamilyRecipeSpec` — `FamilyRecipeSpec` | class / [31](../../../../agent/src/sr2fpga_agent/family_recipe.py#L31) | 无直接调用 |
| `FamilyRecipeDecision` — `FamilyRecipeDecision` | class / [43](../../../../agent/src/sr2fpga_agent/family_recipe.py#L43) | 无直接调用 |
| `FamilyRecipeDecision.to_dict` — `to_dict(self)` | function / [59](../../../../agent/src/sr2fpga_agent/family_recipe.py#L59) | `asdict` |
| `_spec` — `_spec(task_type, *identifiers, phrases)` | function / [66](../../../../agent/src/sr2fpga_agent/family_recipe.py#L66) | `FamilyRecipeSpec`、`dict.fromkeys`、`family_id_for_task_type`、`tuple` |
| `family_recipe_specs` — `family_recipe_specs()` | function / [159](../../../../agent/src/sr2fpga_agent/family_recipe.py#L159) | `ValueError`、`family_id_for_task_type`、`load_exact_task_family_aliases`、`load_task_family_specs`、`resolve_exact_task_family` |
| `select_family_recipe` — `select_family_recipe(request, envelope, deny_policy)` | function / [188](../../../../agent/src/sr2fpga_agent/family_recipe.py#L188) | `<dynamic>.join`、`_add_family_match`、`_all_exact_family_aliases`、`_contains_phrase`、`_decision`、`_joined_aliases`、`_normalize`、`_recipe_identifier_owners`、`any`、`family_recipe_specs`、`identifier_owners.get`、`iter`、`len`、`load_exact_task_family_aliases`、`load_family_recipe_deny_policy`、`matched_recipe_phrases.append`、`next`、`recipe_matches.get`、`recipe_matches.values`、`request.task_type.strip`、`resolve_exact_task_family`、`sorted`、`tuple` |
| `_decision` — `_decision(policy, recipe, status, reason, family_id, matched_alias)` | function / [327](../../../../agent/src/sr2fpga_agent/family_recipe.py#L327) | `FamilyRecipeDecision`、`_recipe_sha256` |
| `recipe_task_type` — `recipe_task_type(decision)` | function / [352](../../../../agent/src/sr2fpga_agent/family_recipe.py#L352) | `ValueError`、`family_recipe_specs` |
| `_recipe_identifier_owners` — `_recipe_identifier_owners(recipes)` | function / [363](../../../../agent/src/sr2fpga_agent/family_recipe.py#L363) | `ValueError`、`_normalize`、`owners.get` |
| `_all_exact_family_aliases` — `_all_exact_family_aliases(catalog_aliases)` | function / [377](../../../../agent/src/sr2fpga_agent/family_recipe.py#L377) | `_normalize`、`aliases.update`、`len`、`set`、`sorted`、`tuple` |
| `_add_family_match` — `_add_family_match(matches, family_id, alias)` | function / [383](../../../../agent/src/sr2fpga_agent/family_recipe.py#L383) | `<dynamic>.append`、`matches.setdefault` |
| `_joined_aliases` — `_joined_aliases(matches)` | function / [395](../../../../agent/src/sr2fpga_agent/family_recipe.py#L395) | `<dynamic>.join`、`matches.values`、`sorted` |
| `_contains_phrase` — `_contains_phrase(normalized_text, normalized_phrase)` | function / [399](../../../../agent/src/sr2fpga_agent/family_recipe.py#L399) | `any` |
| `_normalize` — `_normalize(value)` | function / [407](../../../../agent/src/sr2fpga_agent/family_recipe.py#L407) | `<dynamic>.casefold`、`<dynamic>.strip`、`re.sub`、`value.strip` |
| `_recipe_sha256` — `_recipe_sha256(recipe)` | function / [411](../../../../agent/src/sr2fpga_agent/family_recipe.py#L411) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`_system_his_v12_retry_guidance`、`_system_his_v12_task_guidance`、`hashlib.sha256`、`json.dumps`、`list` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`_spec`、`dataclass`

## `agent/src/sr2fpga_agent/frozen_context.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/frozen_context.py) · 373 行 · SHA-256 `df974aee98ba80236cd86847c619fd0525e0d394d6bac6b448347b99e9c83145`

> Immutable ready requirement context and visibility-safe episode pack.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`re`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.requirement_boundary`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RequirementFactRecord` — `RequirementFactRecord` | class / [27](../../../../agent/src/sr2fpga_agent/frozen_context.py#L27) | 无直接调用 |
| `RequirementFactRecord.to_dict` — `to_dict(self)` | function / [33](../../../../agent/src/sr2fpga_agent/frozen_context.py#L33) | `_json_value`、`list` |
| `FrozenRequirementContext` — `FrozenRequirementContext` | class / [43](../../../../agent/src/sr2fpga_agent/frozen_context.py#L43) | 无直接调用 |
| `FrozenRequirementContext.to_dict` — `to_dict(self)` | function / [55](../../../../agent/src/sr2fpga_agent/frozen_context.py#L55) | `record.to_dict` |
| `FrozenEpisodePack` — `FrozenEpisodePack` | class / [71](../../../../agent/src/sr2fpga_agent/frozen_context.py#L71) | 无直接调用 |
| `FrozenEpisodePack.to_dict` — `to_dict(self)` | function / [82](../../../../agent/src/sr2fpga_agent/frozen_context.py#L82) | `dict`、`list`、`self.context.to_dict` |
| `FrozenEpisodePack.generation_visible` — `generation_visible(self)` | function / [100](../../../../agent/src/sr2fpga_agent/frozen_context.py#L100) | `self.context.to_dict` |
| `freeze_ready_requirement_context` — `freeze_ready_requirement_context(decision, platform)` | function / [106](../../../../agent/src/sr2fpga_agent/frozen_context.py#L106) | `FrozenRequirementContext`、`RequirementFactRecord`、`ValueError`、`_freeze`、`_sha256`、`asdict`、`capability_profile_id`、`platform_profile_id`、`record.to_dict`、`records.append`、`tuple` |
| `platform_profile_sha256` — `platform_profile_sha256(platform)` | function / [163](../../../../agent/src/sr2fpga_agent/frozen_context.py#L163) | `_sha256`、`asdict` |
| `platform_profile_id` — `platform_profile_id(platform)` | function / [167](../../../../agent/src/sr2fpga_agent/frozen_context.py#L167) | `_identifier` |
| `capability_profile_id` — `capability_profile_id(registry_version)` | function / [171](../../../../agent/src/sr2fpga_agent/frozen_context.py#L171) | `_identifier` |
| `frozen_requirement_trace_template` — `frozen_requirement_trace_template(context)` | function / [175](../../../../agent/src/sr2fpga_agent/frozen_context.py#L175) | `_json_value` |
| `frozen_public_project_request` — `frozen_public_project_request(context)` | function / [199](../../../../agent/src/sr2fpga_agent/frozen_context.py#L199) | `ProjectRequest`、`ValueError`、`frozen_project_name`、`isinstance`、`next` |
| `frozen_project_name` — `frozen_project_name(context)` | function / [222](../../../../agent/src/sr2fpga_agent/frozen_context.py#L222) | `context.requirement_id.replace` |
| `build_development_episode_pack` — `build_development_episode_pack(context, episode_id, analysis_population, method_condition, evaluator_metadata, private_ref_ids, paired_block_ref)` | function / [227](../../../../agent/src/sr2fpga_agent/frozen_context.py#L227) | `<dynamic>.join`、`FrozenEpisodePack`、`MethodConditionId`、`ValueError`、`_sha256`、`context.to_dict`、`dict`、`isinstance`、`list`、`pack.to_dict`、`validate_episode_pack` |
| `validate_episode_pack` — `validate_episode_pack(payload)` | function / [288](../../../../agent/src/sr2fpga_agent/frozen_context.py#L288) | `<dynamic>.load_schema`、`ContractRegistry`、`_sha256`、`contract.validate`、`errors.append`、`isinstance`、`list`、`payload.get`、`payload.items`、`public.get`、`public.items`、`tuple` |
| `context_from_validated_episode_pack` — `context_from_validated_episode_pack(payload)` | function / [308](../../../../agent/src/sr2fpga_agent/frozen_context.py#L308) | `<dynamic>.join`、`FrozenRequirementContext`、`RequirementFactRecord`、`ValueError`、`_freeze`、`str`、`tuple`、`validate_episode_pack` |
| `_identifier` — `_identifier(prefix, value)` | function / [338](../../../../agent/src/sr2fpga_agent/frozen_context.py#L338) | `<dynamic>.strip`、`_sha256`、`re.sub`、`value.strip` |
| `_sha256` — `_sha256(value)` | function / [343](../../../../agent/src/sr2fpga_agent/frozen_context.py#L343) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`_json_value`、`hashlib.sha256`、`json.dumps` |
| `_freeze` — `_freeze(value)` | function / [353](../../../../agent/src/sr2fpga_agent/frozen_context.py#L353) | `_freeze`、`isinstance`、`sorted`、`str`、`tuple`、`value.items` |
| `_json_value` — `_json_value(value)` | function / [361](../../../../agent/src/sr2fpga_agent/frozen_context.py#L361) | `_json_value`、`all`、`isinstance`、`len`、`str`、`value.items` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/full_pack_smoke.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py) · 1017 行 · SHA-256 `1e54b4b79ae8db33f632f218eadaa83363165ce2e322b1e6773606c50be19381`

> Reconcile a development-only excluded M0-M5 full-pack smoke.

导入模块：`__future__`、`dataclasses`、`json`、`pathlib`、`re`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.episode_outcome`、`sr2fpga_agent.measurement_freeze`、`sr2fpga_agent.method_adapters`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.paired_block`、`sr2fpga_agent.paired_cost_views`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `FullPackMethodRecord` — `FullPackMethodRecord` | class / [45](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L45) | 无直接调用 |
| `FullPackScenarioRecord` — `FullPackScenarioRecord` | class / [61](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L61) | 无直接调用 |
| `FullPackRunnerArtifactRecord` — `FullPackRunnerArtifactRecord` | class / [72](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L72) | 无直接调用 |
| `FullPackReconciliationError` — `FullPackReconciliationError` | class / [78](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L78) | 无直接调用 |
| `reconcile_excluded_full_pack` — `reconcile_excluded_full_pack(store, smoke_id, methods, scenarios)` | function / [82](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L82) | `_validate_methods`、`_validate_scenarios`、`asdict`、`dict`、`list`、`sorted`、`store.put_validated_json`、`tuple` |
| `reconcile_full_pack_runner_artifacts` — `reconcile_full_pack_runner_artifacts(store, smoke_id, source_smoke_report_ref, runner_artifacts)` | function / [137](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L137) | `<dynamic>.values`、`ArtifactRef`、`ContractRegistry`、`FullPackReconciliationError`、`_read_and_validate`、`_read_registered_json`、`any`、`int`、`iter`、`len`、`list`、`load_development_paired_block`、`method_records.append`、`next`、`paired_block_ref.to_dict`、`record.trajectory_ref.to_dict`、`reference.to_dict`、`registry.load_schema`、`seen_episodes.add`、`set`、`source_smoke_report_ref.to_dict`、`store.put_validated_json`、`tuple` |
| `assemble_excluded_run_full_pack` — `assemble_excluded_run_full_pack(store, events_path, smoke_id, scenarios)` | function / [331](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L331) | `<dynamic>.splitlines`、`ArtifactRef`、`ContractRegistry`、`FullPackMethodRecord`、`FullPackReconciliationError`、`FullPackRunnerArtifactRecord`、`MethodArtifactGateway`、`ProjectCandidateEmission`、`_artifact_ref_from_event`、`_read_registered_json`、`_validated_completion_paired_block`、`artifact_gateway.read_project`、`audit_only.get`、`completed.append`、`event.get`、`events_path.read_text`、`isinstance`、`json.loads`、`len`、`line.strip`、`method_artifacts.get`、`method_records.append`、`paired_block_ref.to_dict`、`projections.add`、`reconcile_excluded_full_pack`、`reconcile_full_pack_runner_artifacts`、`set`、`store.read_verified`、`str` |
| `assemble_excluded_run_full_pack_with_outcomes` — `assemble_excluded_run_full_pack_with_outcomes(store, events_path, smoke_id, scenarios)` | function / [492](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L492) | `ArtifactRef`、`EpisodeOutcomeRecord`、`FullPackReconciliationError`、`_artifact_ref_from_event`、`_excluded_completion_events`、`assemble_excluded_run_full_pack`、`event.get`、`outcome_records.append`、`reconcile_development_episode_outcome`、`reconcile_excluded_full_pack_outcomes` |
| `assemble_excluded_run_full_pack_with_cost_views` — `assemble_excluded_run_full_pack_with_cost_views(store, events_path, smoke_id, scenarios, reducer_policy_sha256)` | function / [549](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L549) | `ArtifactRef`、`FullPackReconciliationError`、`MethodCostSource`、`_artifact_ref_from_event`、`_excluded_completion_events`、`_frozen_preparation_policy`、`assemble_excluded_run_full_pack`、`audit.get`、`event.get`、`isinstance`、`methods.append`、`paired_block_ref.to_dict`、`reconcile_development_paired_block_costs`、`runner.get`、`tuple` |
| `_frozen_preparation_policy` — `_frozen_preparation_policy(store, events_path, paired_block_ref)` | function / [656](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L656) | `<dynamic>.read_text`、`FullPackReconciliationError`、`TypeError`、`ValueError`、`dict`、`freeze_fingerprint`、`isinstance`、`json.loads`、`load_development_paired_block`、`measurement_freeze.get`、`paired_block_ref.to_dict`、`policy.get` |
| `_validated_completion_paired_block` — `_validated_completion_paired_block(store, completed, events_path)` | function / [694](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L694) | `ArtifactRef`、`FullPackReconciliationError`、`all`、`any`、`by_sample_id.get`、`event.get`、`freeze_fingerprint`、`freeze_path.read_text`、`identity_fields.items`、`isinstance`、`json.loads`、`len`、`list`、`load_development_paired_block`、`measurement_freeze.get`、`range`、`record.get`、`reference.to_dict`、`set`、`str` |
| `_excluded_completion_events` — `_excluded_completion_events(events_path)` | function / [807](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L807) | `<dynamic>.splitlines`、`FullPackReconciliationError`、`completed.append`、`event.get`、`events_path.read_text`、`isinstance`、`json.loads`、`len`、`line.strip`、`set`、`str` |
| `_artifact_ref_from_event` — `_artifact_ref_from_event(event, field, method)` | function / [836](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L836) | `ArtifactRef`、`FullPackReconciliationError`、`event.get`、`isinstance` |
| `_read_registered_json` — `_read_registered_json(store, reference, registry, contract_key, label)` | function / [852](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L852) | `_read_and_validate`、`registry.load_schema` |
| `_read_and_validate` — `_read_and_validate(store, reference, contract, label)` | function / [868](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L868) | `<dynamic>.join`、`FullPackReconciliationError`、`contract.validate`、`json.loads`、`store.read_verified` |
| `_validate_methods` — `_validate_methods(records)` | function / [887](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L887) | `FullPackReconciliationError`、`_require_sha256`、`any`、`len`、`set` |
| `_validate_scenarios` — `_validate_scenarios(records, projection)` | function / [942](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L942) | `<dynamic>.join`、`FullPackReconciliationError`、`_require_scenario`、`bool`、`isinstance`、`item.facts.get`、`sorted` |
| `_require_scenario` — `_require_scenario(records, kind, predicate)` | function / [1010](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L1010) | `FullPackReconciliationError`、`any`、`predicate` |
| `_require_sha256` — `_require_sha256(label, value)` | function / [1015](../../../../agent/src/sr2fpga_agent/full_pack_smoke.py#L1015) | `FullPackReconciliationError`、`_SHA256_RE.fullmatch`、`isinstance` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`re.compile`、`tuple`

## `agent/src/sr2fpga_agent/g3_acceptance.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/g3_acceptance.py) · 407 行 · SHA-256 `920a5df62b70196c78f6e618ef86a73ca263e6e1116f3bccab70a79c22c24463`

> Artifact-rebuilt G3 development acceptance, separate from official outcomes.

导入模块：`__future__`、`argparse`、`hashlib`、`json`、`pathlib`、`pytest`、`sr2fpga_agent.ambiguity_outcome`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.checkpoint_stop_outcome`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.episode_outcome`、`sr2fpga_agent.evaluator_dispatch`、`sr2fpga_agent.g3_test_evidence`、`sr2fpga_agent.hidden_execution_state`、`sr2fpga_agent.his_correction_outcome`、`sr2fpga_agent.measurement_freeze`、`sr2fpga_agent.model_gateway_provenance`、`sr2fpga_agent.paired_cost_views`、`sr2fpga_agent.pc_assembly`、`sr2fpga_agent.pre_candidate_outcome`、`sr2fpga_agent.provider_seed_capability`、`sr2fpga_agent.public_evaluator`、`sr2fpga_agent.repository_paths`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_test` — `_test(module, name)` | function / [27](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L27) | 无直接调用 |
| `reconcile_g3_acceptance` — `reconcile_g3_acceptance(root, test_evidence_ref)` | function / [111](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L111) | `<dynamic>.append`、`<dynamic>.put_validated_json`、`ArtifactStore`、`REQUIRED_SCENARIOS.items`、`ValueError`、`_artifact_gaps`、`_digest`、`all`、`any`、`len`、`matrix.append`、`node.startswith`、`read_test_evidence`、`reasons.append`、`reasons.extend`、`set`、`sorted`、`test_evidence_ref.to_dict` |
| `read_verified_g3_acceptance` — `read_verified_g3_acceptance(root, reference)` | function / [162](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L162) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.read_verified`、`<dynamic>.validate`、`ArtifactRef`、`ArtifactStore`、`ContractRegistry`、`ValueError`、`json.loads`、`reconcile_g3_acceptance` |
| `_artifact_gaps` — `_artifact_gaps(root, scenario, records)` | function / [173](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L173) | `<dynamic>.append`、`AmbiguityAuditObservation`、`ArtifactRef`、`ArtifactStore`、`ValueError`、`_closed_gold_block`、`_replay_hidden_companion`、`all`、`any`、`build_ambiguity_outcome`、`failure_origins.get`、`freeze_fingerprint`、`initial.get`、`json.loads`、`len`、`range`、`read_development_paired_block_cost_reconciliation`、`read_verified_checkpoint_stop_outcome`、`read_verified_development_episode_outcome`、`read_verified_development_hidden_conformance_outcome`、`read_verified_development_his_correction_outcome`、`read_verified_development_pre_candidate_stop_outcome`、`read_verified_development_public_outcome`、`read_verified_model_gateway_provenance`、`read_verified_pc_assembly`、`read_verified_provider_seed_capability`、`retry_costs.get`、`scenario.startswith`、`seen.add`、`set`、`store.read_verified`、`sum`、`verified.get`、`verified.setdefault` |
| `_replay_hidden_companion` — `_replay_hidden_companion(root, candidate_store, ref)` | function / [342](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L342) | `<dynamic>.glob`、`<dynamic>.removeprefix`、`ArtifactRef`、`ArtifactStore`、`ValueError`、`candidate_store.read_verified`、`json.loads`、`private.reference`、`read_verified_hidden_execution_state`、`sorted` |
| `_closed_gold_block` — `_closed_gold_block(costs, outcomes)` | function / [359](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L359) | `all`、`any` |
| `_digest` — `_digest(payload)` | function / [368](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L368) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps` |
| `main` — `main(argv)` | function / [372](../../../../agent/src/sr2fpga_agent/g3_acceptance.py#L372) | `<dynamic>.reference`、`ArtifactStore`、`G3TestEvidenceRecorder`、`REQUIRED_SCENARIOS.values`、`argparse.ArgumentParser`、`args.output_root.resolve`、`discover_repository_root`、`hasattr`、`int`、`json.dumps`、`parser.add_argument`、`parser.error`、`parser.parse_args`、`print`、`pytest.main`、`read_verified_g3_acceptance`、`reconcile_g3_acceptance`、`ref.to_dict`、`root.exists`、`root.is_dir`、`sorted`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`_test`、`main`

## `agent/src/sr2fpga_agent/g3_test_evidence.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py) · 180 行 · SHA-256 `81a6ca51cc0092745826b62ad49db90bde192b8ddbc219db2ab5ebbe125e9572`

> Trusted local pytest recorder for excluded development engineering evidence.

导入模块：`__future__`、`hashlib`、`importlib.metadata`、`json`、`os`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.repository_paths`、`sys`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `source_fingerprint` — `source_fingerprint(root)` | function / [28](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L28) | `<dynamic>.as_posix`、`<dynamic>.hexdigest`、`Path`、`files.extend`、`hashlib.sha256`、`name.startswith`、`os.walk`、`path.read_bytes`、`path.relative_to`、`sorted` |
| `G3TestEvidenceRecorder` — `G3TestEvidenceRecorder` | class / [46](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L46) | 无直接调用 |
| `G3TestEvidenceRecorder.__init__` — `__init__(self, output_root)` | function / [49](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L49) | `<dynamic>.hexdigest`、`<dynamic>.read_bytes`、`ArtifactStore`、`ValueError`、`discover_repository_root`、`hashlib.sha256`、`output_root.resolve`、`self.sources_before.items`、`self.store.put_blob`、`set`、`source_fingerprint` |
| `G3TestEvidenceRecorder.pytest_sessionstart` — `pytest_sessionstart(self, session)` | function / [68](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L68) | 无直接调用 |
| `G3TestEvidenceRecorder.pytest_sessionstart.put_blob` — `put_blob(store, key, content, media_type)` | function / [71](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L71) | `recorder._snapshot`、`recorder.original_put_blob` |
| `G3TestEvidenceRecorder.pytest_sessionstart.put_validated_json` — `put_validated_json(store, key, payload, contract_key, registry)` | function / [76](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L76) | `recorder._recorded_artifacts.add`、`recorder._source`、`recorder.artifacts.append`、`recorder.original_put_validated_json`、`ref.to_dict` |
| `G3TestEvidenceRecorder.pytest_collection_finish` — `pytest_collection_finish(self, session)` | function / [93](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L93) | `getattr`、`isinstance` |
| `G3TestEvidenceRecorder.pytest_runtest_setup` — `pytest_runtest_setup(self, item)` | function / [102](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L102) | 无直接调用 |
| `G3TestEvidenceRecorder.pytest_runtest_logreport` — `pytest_runtest_logreport(self, report)` | function / [105](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L105) | `bool`、`getattr`、`self.reports.append` |
| `G3TestEvidenceRecorder.pytest_sessionfinish` — `pytest_sessionfinish(self, session, exitstatus)` | function / [112](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L112) | `_runtime_versions`、`int`、`self.store.put_validated_json`、`source_fingerprint` |
| `G3TestEvidenceRecorder._source` — `_source(self, store)` | function / [133](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L133) | `ArtifactStore`、`len`、`path.is_relative_to`、`store.root.resolve` |
| `G3TestEvidenceRecorder._snapshot` — `_snapshot(self, store, ref, content)` | function / [142](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L142) | `freeze_path.is_file`、`freeze_path.read_bytes`、`self._source`、`self.original_put_blob`、`snapshot.reference` |
| `read_test_evidence` — `read_test_evidence(root, reference)` | function / [157](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L157) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`<dynamic>.values`、`ArtifactStore`、`ContractRegistry`、`ValueError`、`_runtime_versions`、`discover_repository_root`、`hashlib.sha256`、`json.loads`、`set`、`source_fingerprint`、`store.read_verified` |
| `_runtime_versions` — `_runtime_versions()` | function / [178](../../../../agent/src/sr2fpga_agent/g3_test_evidence.py#L178) | `<dynamic>.join`、`map`、`version` |

## `agent/src/sr2fpga_agent/hidden_execution_state.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/hidden_execution_state.py) · 137 行 · SHA-256 `18a976940aa25f73c666bee8a3d6cef4dc31b6cb94c98dae212bf070615a5ff3`

> Two-axis hidden execution closure rebuilt from evaluator-private events.

导入模块：`__future__`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.evaluator_dispatch`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `reconcile_hidden_execution_state` — `reconcile_hidden_execution_state(candidate_store, evaluator_store, legacy_outcome_ref)` | function / [15](../../../../agent/src/sr2fpga_agent/hidden_execution_state.py#L15) | `<dynamic>.get`、`<dynamic>.hexdigest`、`<dynamic>.removeprefix`、`<dynamic>.to_dict`、`ArtifactRef`、`ValueError`、`_canonical_json`、`_read_event`、`candidate_store.put_validated_json`、`candidate_store.root.resolve`、`enumerate`、`evaluator_store.event_refs`、`evaluator_store.read_verified`、`evaluator_store.reference`、`evaluator_store.root.resolve`、`events.append`、`hashlib.sha256`、`int`、`isinstance`、`json.loads`、`legacy_outcome_ref.to_dict`、`len`、`read_verified_development_hidden_conformance_outcome`、`ref.to_dict`、`tuple` |
| `read_verified_hidden_execution_state` — `read_verified_hidden_execution_state(candidate_store, evaluator_store, reference)` | function / [117](../../../../agent/src/sr2fpga_agent/hidden_execution_state.py#L117) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ArtifactRef`、`ContractRegistry`、`ValueError`、`candidate_store.read_verified`、`json.loads`、`reconcile_hidden_execution_state` |
| `_read_event` — `_read_event(store, ref, stream_id, sequence, event_type)` | function / [129](../../../../agent/src/sr2fpga_agent/hidden_execution_state.py#L129) | `<dynamic>.hexdigest`、`ValueError`、`_canonical_json`、`event.get`、`event.items`、`hashlib.sha256`、`json.loads`、`store.read_verified` |

## `agent/src/sr2fpga_agent/his_correction_outcome.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py) · 411 行 · SHA-256 `08c49a0d41c300aafe5f539ccd8fb6a3efbe0b97325222932220c1101dda8429`

> Artifact-derived acceptance for excluded M5 System-HIS correction.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.episode_outcome`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.project_contract`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.system_his_capabilities`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `HisCorrectionOutcomeError` — `HisCorrectionOutcomeError` | class / [48](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L48) | 无直接调用 |
| `read_verified_development_his_correction_outcome` — `read_verified_development_his_correction_outcome(store, outcome_ref, registry)` | function / [52](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L52) | `<dynamic>.get`、`<dynamic>.hexdigest`、`ArtifactRef`、`ContractRegistry`、`HisCorrectionOutcomeError`、`PlatformProfile`、`_canonical_json`、`_read_json`、`_read_registered`、`hashlib.sha256`、`payload.items`、`raw.get`、`reconcile_development_his_correction_outcome` |
| `reconcile_development_his_correction_outcome` — `reconcile_development_his_correction_outcome(store, episode_pack_ref, initial_his_ref, corrected_his_ref, method_event_refs, candidate_artifact_ref, trajectory_ref, development_episode_outcome_ref, platform, registry)` | function / [99](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L99) | `<dynamic>.hexdigest`、`<dynamic>.join`、`ArtifactRef`、`ContractRegistry`、`GeneratedProject`、`HisCorrectionOutcomeError`、`_canonical_json`、`_expected_initial_statuses`、`_read_json`、`_read_registered`、`_reconcile_cost`、`_verify_method_events`、`asdict`、`candidate_artifact_ref.to_dict`、`capability_profile_id`、`capability_profile_sha256`、`context_from_validated_episode_pack`、`corrected_his_ref.to_dict`、`corrected_report.get`、`corrected_statuses.values`、`development_episode_outcome_ref.to_dict`、`dict`、`episode_pack_ref.to_dict`、`first_failed_h_stage`、`hashlib.sha256`、`initial_his_ref.to_dict`、`initial_report.get`、`item.to_dict`、`json.loads`、`list`、`load_system_his_backend_capabilities`、`method_policy_sha256`、`platform_profile_id`、`platform_profile_sha256`、`project_package_sha256`、`read_verified_development_episode_outcome`、`set`、`store.put_validated_json`、`store.read_sealed_project`、`str`、`terminal_project.files.get`、`terminal_ref.to_dict`、`trajectory_ref.to_dict`、`tuple`、`validate_episode_pack`、`validate_frozen_system_his_payload_h_stages` |
| `_verify_method_events` — `_verify_method_events(store, refs, episode_id, initial_sha256, corrected_sha256, failed_stage)` | function / [297](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L297) | `<dynamic>.get`、`<dynamic>.hexdigest`、`HisCorrectionOutcomeError`、`_canonical_json`、`_read_json`、`enumerate`、`event.get`、`event.items`、`hashlib.sha256`、`len`、`ref.key.endswith`、`set`、`store.event_refs`、`store.has_event_id`、`str`、`tuple`、`zip` |
| `_reconcile_cost` — `_reconcile_cost(store, refs, attempts, registry)` | function / [337](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L337) | `<dynamic>.get`、`<dynamic>.items`、`ArtifactRef`、`HisCorrectionOutcomeError`、`_read_json`、`_read_registered`、`len`、`reconcile_cost_events`、`set`、`sorted`、`stages.get`、`stages.values`、`sum`、`tuple`、`unavailable.update`、`zip` |
| `_expected_initial_statuses` — `_expected_initial_statuses(failed_stage)` | function / [389](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L389) | `_H_STAGES.index`、`enumerate` |
| `_read_registered` — `_read_registered(store, ref, registry, key, label)` | function / [394](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L394) | `<dynamic>.join`、`<dynamic>.validate`、`HisCorrectionOutcomeError`、`_read_json`、`registry.load_schema` |
| `_read_json` — `_read_json(store, ref, label)` | function / [402](../../../../agent/src/sr2fpga_agent/his_correction_outcome.py#L402) | `HisCorrectionOutcomeError`、`isinstance`、`json.loads`、`store.read_verified` |

## `agent/src/sr2fpga_agent/his_validation.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/his_validation.py) · 361 行 · SHA-256 `52d666fbc52808bbb30d39ad10ba07577f1484ec939d2403b1d759a78e07c433`

> H0-H3 System-HIS validation stages.

导入模块：`__future__`、`json`、`sr2fpga_agent.contract_skeleton`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.system_his_capabilities`、`sr2fpga_agent.system_his_fidelity`、`sr2fpga_agent.system_his_schema`、`sr2fpga_agent.system_his_v12_checker`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SystemHisValidationError` — `SystemHisValidationError` | class / [38](../../../../agent/src/sr2fpga_agent/his_validation.py#L38) | 无直接调用 |
| `SystemHisValidationError.__init__` — `__init__(self, candidate_output, report, candidate_artifact_sha256)` | function / [41](../../../../agent/src/sr2fpga_agent/his_validation.py#L41) | `<dynamic>.__init__`、`<dynamic>.join`、`first_failed_h_stage`、`isinstance`、`list`、`report.get`、`self.failed_h_stage.upper`、`stage_report.get`、`super` |
| `validate_system_his_h_stages` — `validate_system_his_h_stages(request, project, his_source_used_for_generation, platform)` | function / [58](../../../../agent/src/sr2fpga_agent/his_validation.py#L58) | `_initial_report`、`_load_his_payload`、`validate_system_his_payload_h_stages` |
| `validate_system_his_payload_h_stages` — `validate_system_his_payload_h_stages(request, payload, his_source_used_for_generation, platform)` | function / [77](../../../../agent/src/sr2fpga_agent/his_validation.py#L77) | `_dry_lowerability_errors`、`_h0_payload_errors`、`_h3_scores`、`_h3_status`、`_initial_report`、`_lowerability_errors`、`_stage`、`check_system_his_req_fidelity`、`check_system_his_v12`、`check_system_his_well_formedness`、`h2_errors.extend`、`list`、`w_rules.items` |
| `validate_frozen_system_his_payload_h_stages` — `validate_frozen_system_his_payload_h_stages(context, payload, platform, his_source_used_for_generation)` | function / [121](../../../../agent/src/sr2fpga_agent/his_validation.py#L121) | `ValueError`、`_dry_lowerability_errors`、`_frozen_identity_errors`、`_h0_payload_errors`、`_h3_scores`、`_h3_status`、`_initial_report`、`_lowerability_errors`、`_stage`、`check_frozen_context_system_his_fidelity`、`check_system_his_v12`、`check_system_his_well_formedness`、`frozen_public_project_request`、`h2_errors.extend`、`list`、`platform_profile_sha256`、`w_rules.items` |
| `validate_system_his_candidate` — `validate_system_his_candidate(request, candidate_output, his_source_used_for_generation, platform)` | function / [172](../../../../agent/src/sr2fpga_agent/his_validation.py#L172) | `SystemHisValidationError`、`_initial_report`、`parse_system_his_payload`、`str`、`validate_system_his_payload_h_stages` |
| `first_failed_h_stage` — `first_failed_h_stage(report)` | function / [196](../../../../agent/src/sr2fpga_agent/his_validation.py#L196) | `data.get`、`isinstance`、`report.get` |
| `h_stage_labels` — `h_stage_labels(report)` | function / [204](../../../../agent/src/sr2fpga_agent/his_validation.py#L204) | `data.get`、`isinstance`、`report.get` |
| `_load_his_payload` — `_load_his_payload(project)` | function / [215](../../../../agent/src/sr2fpga_agent/his_validation.py#L215) | `_h0_payload_errors`、`isinstance`、`json.loads`、`project.files.get` |
| `_h0_payload_errors` — `_h0_payload_errors(payload)` | function / [228](../../../../agent/src/sr2fpga_agent/his_validation.py#L228) | `validate_registered_system_his_schema` |
| `_lowerability_errors` — `_lowerability_errors(payload)` | function / [232](../../../../agent/src/sr2fpga_agent/his_validation.py#L232) | `<dynamic>.strip`、`COMPONENT_SEMANTIC_KIND_ALIASES.get`、`DATA_FLOW_PROTOCOL_ALIASES.get`、`_list`、`_scenario_identifier`、`artifacts.get`、`component.get`、`enumerate`、`errors.append`、`flow.get`、`isinstance`、`payload.get`、`str`、`verification.get` |
| `_dry_lowerability_errors` — `_dry_lowerability_errors(request, platform, payload)` | function / [281](../../../../agent/src/sr2fpga_agent/his_validation.py#L281) | `build_contract_skeleton_project` |
| `_frozen_identity_errors` — `_frozen_identity_errors(context, payload)` | function / [293](../../../../agent/src/sr2fpga_agent/his_validation.py#L293) | `frozen_project_name`、`isinstance`、`payload.get`、`project.get`、`values.extend` |
| `_scenario_identifier` — `_scenario_identifier(scenario)` | function / [314](../../../../agent/src/sr2fpga_agent/his_validation.py#L314) | `<dynamic>.strip`、`isinstance`、`scenario.get`、`scenario.strip`、`str` |
| `_h3_status` — `_h3_status(result)` | function / [325](../../../../agent/src/sr2fpga_agent/his_validation.py#L325) | `isinstance`、`metric.get`、`result.metrics.values` |
| `_h3_scores` — `_h3_scores(metrics)` | function / [332](../../../../agent/src/sr2fpga_agent/his_validation.py#L332) | `isinstance`、`metric.get`、`metrics.items` |
| `_initial_report` — `_initial_report(his_source_used_for_generation, h0_errors)` | function / [345](../../../../agent/src/sr2fpga_agent/his_validation.py#L345) | `_stage` |
| `_stage` — `_stage(status, diagnostics)` | function / [356](../../../../agent/src/sr2fpga_agent/his_validation.py#L356) | 无直接调用 |
| `_list` — `_list(value)` | function / [360](../../../../agent/src/sr2fpga_agent/his_validation.py#L360) | `isinstance` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`load_system_his_backend_capabilities`

## `agent/src/sr2fpga_agent/l4_tool_environment.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py) · 286 行 · SHA-256 `c156bc5cbfd4edb8aea5a938578e37bcd64c0b3959870effd85411567b1f2484`

> Explicitly authorized exact-version probes for development L4 tools.

导入模块：`__future__`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.tool_environment`、`subprocess`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `collect_development_l4_tool_environment` — `collect_development_l4_tool_environment(open_enabled, commercial_enabled, probe_authorized, open_probe_command, vivado_command, timeout_seconds, resolver, command_executor)` | function / [20](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L20) | `TypeError`、`_collect_commercial_lane`、`_collect_open_lane`、`all`、`isinstance`、`lanes.values`、`validate_development_l4_tool_environment` |
| `validate_development_l4_tool_environment` — `validate_development_l4_tool_environment(snapshot)` | function / [73](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L73) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`all`、`lanes.items`、`lanes.values`、`list` |
| `l4_tool_version_projection` — `l4_tool_version_projection(snapshot)` | function / [119](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L119) | `<dynamic>.items`、`validate_development_l4_tool_environment` |
| `_collect_open_lane` — `_collect_open_lane(enabled, authorized, command, timeout_seconds, command_executor)` | function / [135](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L135) | `_failed_lane`、`_initial_lane`、`_last_probe_payload`、`_normalize_tool_record`、`command_executor`、`executable_env`、`isinstance`、`list`、`payload.get` |
| `_collect_commercial_lane` — `_collect_commercial_lane(enabled, authorized, command, timeout_seconds, resolver, command_executor)` | function / [180](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L180) | `<dynamic>.hexdigest`、`Path`、`_combined_output`、`_failed_lane`、`_initial_lane`、`command_executor`、`executable_env`、`hashlib.sha256`、`len`、`line.strip`、`next`、`output.encode`、`output.splitlines`、`resolved.read_bytes`、`resolver`、`sanitize_version_line`、`str` |
| `_initial_lane` — `_initial_lane(enabled, authorized)` | function / [228](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L228) | 无直接调用 |
| `_failed_lane` — `_failed_lane(failure_type)` | function / [241](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L241) | 无直接调用 |
| `_last_probe_payload` — `_last_probe_payload(stdout)` | function / [245](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L245) | `isinstance`、`json.loads`、`reversed`、`stdout.splitlines` |
| `_normalize_tool_record` — `_normalize_tool_record(value)` | function / [258](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L258) | `TypeError`、`ValueError`、`any`、`int`、`isinstance`、`len`、`sanitize_version_line`、`str` |
| `_combined_output` — `_combined_output(stdout, stderr)` | function / [281](../../../../agent/src/sr2fpga_agent/l4_tool_environment.py#L281) | `<dynamic>.join`、`isinstance`、`value.strip` |

## `agent/src/sr2fpga_agent/local_tools.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/local_tools.py) · 140 行 · SHA-256 `478231d90f9fa25b969d4a63f122ad722fc0d96d9b2480f65e36416e514f97c3`

> Local executable discovery helpers for cross-platform developer machines.

导入模块：`__future__`、`os`、`pathlib`、`shutil`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `resolve_executable` — `resolve_executable(name, path_env, fallback_dirs)` | function / [14](../../../../agent/src/sr2fpga_agent/local_tools.py#L14) | `Path`、`_existing_fallback_dirs`、`os.environ.get`、`os.pathsep.join`、`shutil.which`、`str` |
| `executable_env` — `executable_env(base_env, fallback_dirs)` | function / [34](../../../../agent/src/sr2fpga_agent/local_tools.py#L34) | `_existing_fallback_dirs`、`_path_entries_for_fallbacks`、`_set_oss_cad_suite_env`、`dict`、`env.get`、`os.pathsep.join`、`str` |
| `discover_tool_statuses` — `discover_tool_statuses(tools, path_env, fallback_dirs)` | function / [51](../../../../agent/src/sr2fpga_agent/local_tools.py#L51) | `resolve_executable` |
| `_existing_fallback_dirs` — `_existing_fallback_dirs(fallback_dirs)` | function / [65](../../../../agent/src/sr2fpga_agent/local_tools.py#L65) | `_default_fallback_bin_dirs`、`path.exists`、`tuple` |
| `_default_fallback_bin_dirs` — `_default_fallback_bin_dirs()` | function / [70](../../../../agent/src/sr2fpga_agent/local_tools.py#L70) | `<dynamic>.expanduser`、`<dynamic>.strip`、`Path`、`_dedupe_paths`、`configured.split`、`entry.strip`、`os.environ.get`、`paths.append`、`paths.extend`、`root.name.lower`、`tuple` |
| `_path_entries_for_fallbacks` — `_path_entries_for_fallbacks(fallback_dirs)` | function / [93](../../../../agent/src/sr2fpga_agent/local_tools.py#L93) | `_dedupe_paths`、`_oss_cad_suite_root`、`entries.append`、`lib_dir.exists` |
| `_set_oss_cad_suite_env` — `_set_oss_cad_suite_env(env, fallback_dirs)` | function / [105](../../../../agent/src/sr2fpga_agent/local_tools.py#L105) | `_oss_cad_suite_root`、`cert_file.exists`、`env.setdefault`、`root_text.endswith`、`str`、`verilator_root.exists` |
| `_oss_cad_suite_root` — `_oss_cad_suite_root(path)` | function / [123](../../../../agent/src/sr2fpga_agent/local_tools.py#L123) | `Path`、`normalized.name.lower`、`root.name.lower` |
| `_dedupe_paths` — `_dedupe_paths(paths)` | function / [131](../../../../agent/src/sr2fpga_agent/local_tools.py#L131) | `<dynamic>.lower`、`seen.add`、`set`、`str`、`unique.append` |

## `agent/src/sr2fpga_agent/log_parser.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/log_parser.py) · 188 行 · SHA-256 `807ad95ea6c6430215ec9143240e5a39967a10d9cba2a1cc6a22fa31b48822f5`

> Log parsing and failure classification for lightweight RTL tools.

导入模块：`__future__`、`collections`、`json`、`re`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `parse_test_fail_mismatches` — `parse_test_fail_mismatches(log_text)` | function / [20](../../../../agent/src/sr2fpga_agent/log_parser.py#L20) | `<dynamic>.strip`、`actual.group`、`cycle.group`、`expected.group`、`int`、`isinstance`、`json.loads`、`legacy.append`、`log_text.splitlines`、`raw_line.removeprefix`、`raw_line.startswith`、`re.search`、`signal.group`、`structured.append` |
| `parse_tool_warnings` — `parse_tool_warnings(log_text)` | function / [62](../../../../agent/src/sr2fpga_agent/log_parser.py#L62) | `_VERILATOR_WARNING_TAXONOMY.get`、`log_text.splitlines`、`raw_line.lower`、`re.findall`、`re.match`、`warning_class.upper`、`warnings.append` |
| `classify_failure` — `classify_failure(log_text)` | function / [87](../../../../agent/src/sr2fpga_agent/log_parser.py#L87) | `any`、`log_text.lower` |
| `parse_yosys_stats` — `parse_yosys_stats(log_text)` | function / [140](../../../../agent/src/sr2fpga_agent/log_parser.py#L140) | `cell_breakdown.items`、`cell_match.group`、`cell_name.upper`、`current_cell_match.group`、`current_total_match.group`、`defaultdict`、`int`、`line.endswith`、`line.startswith`、`log_text.splitlines`、`raw_line.strip`、`re.match`、`total_match.group` |

## `agent/src/sr2fpga_agent/measurement_freeze.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/measurement_freeze.py) · 91 行 · SHA-256 `236e1fb1fbf742a503c2846682fa675a81dbc8dc5ac478110faec1d9e4b722ab`

> Immutable measurement protocol records for frozen SR2FPGA runs.

导入模块：`__future__`、`hashlib`、`json`、`pathlib`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_measurement_freeze` — `build_measurement_freeze(run_id, config_fingerprint, sample_records, source_records, max_attempts, timeouts, tool_versions, l4_family_ids, tool_environment_ref, l4_tool_environment_ref)` | function / [20](../../../../agent/src/sr2fpga_agent/measurement_freeze.py#L20) | `_reject_secret_like_fields`、`dict`、`len`、`sorted` |
| `freeze_fingerprint` — `freeze_fingerprint(manifest)` | function / [53](../../../../agent/src/sr2fpga_agent/measurement_freeze.py#L53) | `<dynamic>.hexdigest`、`canonical.encode`、`hashlib.sha256`、`json.dumps`、`manifest.items` |
| `write_or_validate_freeze` — `write_or_validate_freeze(path, manifest, resume)` | function / [59](../../../../agent/src/sr2fpga_agent/measurement_freeze.py#L59) | `RuntimeError`、`freeze_fingerprint`、`json.dumps`、`json.loads`、`path.exists`、`path.parent.mkdir`、`path.read_text`、`path.write_text` |
| `_reject_secret_like_fields` — `_reject_secret_like_fields(value, path)` | function / [82](../../../../agent/src/sr2fpga_agent/measurement_freeze.py#L82) | `<dynamic>.lower`、`ValueError`、`_reject_secret_like_fields`、`any`、`enumerate`、`isinstance`、`str`、`value.items` |

## `agent/src/sr2fpga_agent/method_adapters.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/method_adapters.py) · 680 行 · SHA-256 `74b94c8fe665993a8abf5961c8c7974db43deedbf47182f798f9769da6c17be2`

> Provider-neutral Paper-1 method adapters and paired initial artifacts.

导入模块：`__future__`、`dataclasses`、`enum`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.block_preparation`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.project_contract`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PlanningArtifactKind` — `PlanningArtifactKind` | class / [23](../../../../agent/src/sr2fpga_agent/method_adapters.py#L23) | 无直接调用 |
| `PlanningArtifactEmission` — `PlanningArtifactEmission` | class / [29](../../../../agent/src/sr2fpga_agent/method_adapters.py#L29) | 无直接调用 |
| `ProjectCandidateEmission` — `ProjectCandidateEmission` | class / [35](../../../../agent/src/sr2fpga_agent/method_adapters.py#L35) | 无直接调用 |
| `SkeletonProjectOutput` — `SkeletonProjectOutput` | class / [41](../../../../agent/src/sr2fpga_agent/method_adapters.py#L41) | 无直接调用 |
| `MethodStageFailure` — `MethodStageFailure` | class / [47](../../../../agent/src/sr2fpga_agent/method_adapters.py#L47) | 无直接调用 |
| `RepairableProjectOutputFailure` — `RepairableProjectOutputFailure` | class / [54](../../../../agent/src/sr2fpga_agent/method_adapters.py#L54) | 无直接调用 |
| `ProjectOutputNoProgressFailure` — `ProjectOutputNoProgressFailure` | class / [61](../../../../agent/src/sr2fpga_agent/method_adapters.py#L61) | 无直接调用 |
| `SharedArtifactRefs` — `SharedArtifactRefs` | class / [78](../../../../agent/src/sr2fpga_agent/method_adapters.py#L78) | 无直接调用 |
| `PairingKey` — `PairingKey` | class / [84](../../../../agent/src/sr2fpga_agent/method_adapters.py#L84) | 无直接调用 |
| `PairingKey.digest` — `digest(self)` | function / [92](../../../../agent/src/sr2fpga_agent/method_adapters.py#L92) | `_sha256_json` |
| `DirectGenerationFacade` — `DirectGenerationFacade` | class / [105](../../../../agent/src/sr2fpga_agent/method_adapters.py#L105) | 无直接调用 |
| `DirectGenerationFacade.emit_project` — `emit_project(self, context)` | function / [106](../../../../agent/src/sr2fpga_agent/method_adapters.py#L106) | 无直接调用 |
| `UntypedPlanFacade` — `UntypedPlanFacade` | class / [109](../../../../agent/src/sr2fpga_agent/method_adapters.py#L109) | 无直接调用 |
| `UntypedPlanFacade.emit_plan` — `emit_plan(self, context)` | function / [110](../../../../agent/src/sr2fpga_agent/method_adapters.py#L110) | 无直接调用 |
| `UntypedPlanFacade.emit_project` — `emit_project(self, context, plan)` | function / [112](../../../../agent/src/sr2fpga_agent/method_adapters.py#L112) | 无直接调用 |
| `SystemHisFacade` — `SystemHisFacade` | class / [119](../../../../agent/src/sr2fpga_agent/method_adapters.py#L119) | 无直接调用 |
| `SystemHisFacade.emit_his` — `emit_his(self, context)` | function / [120](../../../../agent/src/sr2fpga_agent/method_adapters.py#L120) | 无直接调用 |
| `SystemHisFacade.emit_free_project` — `emit_free_project(self, context, system_his)` | function / [122](../../../../agent/src/sr2fpga_agent/method_adapters.py#L122) | 无直接调用 |
| `SystemHisFacade.emit_skeleton_project` — `emit_skeleton_project(self, context, system_his)` | function / [128](../../../../agent/src/sr2fpga_agent/method_adapters.py#L128) | 无直接调用 |
| `SystemHisValidationFacade` — `SystemHisValidationFacade` | class / [135](../../../../agent/src/sr2fpga_agent/method_adapters.py#L135) | 无直接调用 |
| `SystemHisValidationFacade.validate_his` — `validate_his(self, context, system_his)` | function / [136](../../../../agent/src/sr2fpga_agent/method_adapters.py#L136) | 无直接调用 |
| `SystemHisProjectOutputRepairFacade` — `SystemHisProjectOutputRepairFacade` | class / [143](../../../../agent/src/sr2fpga_agent/method_adapters.py#L143) | 无直接调用 |
| `SystemHisProjectOutputRepairFacade.emit_skeleton_project_output` — `emit_skeleton_project_output(self, context, system_his)` | function / [144](../../../../agent/src/sr2fpga_agent/method_adapters.py#L144) | 无直接调用 |
| `SystemHisProjectOutputRepairFacade.lower_skeleton_project_output` — `lower_skeleton_project_output(self, context, system_his, output)` | function / [150](../../../../agent/src/sr2fpga_agent/method_adapters.py#L150) | 无直接调用 |
| `SystemHisProjectOutputRepairFacade.repair_skeleton_project_output` — `repair_skeleton_project_output(self, context, system_his, previous_output, error)` | function / [157](../../../../agent/src/sr2fpga_agent/method_adapters.py#L157) | 无直接调用 |
| `RepairFacade` — `RepairFacade` | class / [166](../../../../agent/src/sr2fpga_agent/method_adapters.py#L166) | 无直接调用 |
| `RepairFacade.correct_his` — `correct_his(self, context, system_his, diagnosis)` | function / [167](../../../../agent/src/sr2fpga_agent/method_adapters.py#L167) | 无直接调用 |
| `RepairFacade.repair_project` — `repair_project(self, context, project, diagnosis)` | function / [174](../../../../agent/src/sr2fpga_agent/method_adapters.py#L174) | 无直接调用 |
| `MethodArtifactGateway` — `MethodArtifactGateway` | class / [182](../../../../agent/src/sr2fpga_agent/method_adapters.py#L182) | 无直接调用 |
| `MethodArtifactGateway.__init__` — `__init__(self, store)` | function / [185](../../../../agent/src/sr2fpga_agent/method_adapters.py#L185) | 无直接调用 |
| `MethodArtifactGateway.put_planning` — `put_planning(self, key, kind, payload)` | function / [189](../../../../agent/src/sr2fpga_agent/method_adapters.py#L189) | `PlanningArtifactEmission`、`ValueError`、`_canonical_json`、`payload.get`、`self.__store.put_blob`、`self.__store.put_validated_json` |
| `MethodArtifactGateway.read_planning` — `read_planning(self, emission)` | function / [203](../../../../agent/src/sr2fpga_agent/method_adapters.py#L203) | `ValueError`、`isinstance`、`json.loads`、`self.__store.read_verified` |
| `MethodArtifactGateway.put_project` — `put_project(self, key, project)` | function / [209](../../../../agent/src/sr2fpga_agent/method_adapters.py#L209) | `ProjectCandidateEmission`、`_canonical_json`、`project_package_sha256`、`self.__store.put_blob` |
| `MethodArtifactGateway.read_project` — `read_project(self, emission)` | function / [214](../../../../agent/src/sr2fpga_agent/method_adapters.py#L214) | `GeneratedProject`、`ValueError`、`dict`、`json.loads`、`project_package_sha256`、`self.__store.read_verified`、`str` |
| `MethodArtifactGateway.put_model_output` — `put_model_output(self, key, content)` | function / [221](../../../../agent/src/sr2fpga_agent/method_adapters.py#L221) | `content.encode`、`self.__store.put_blob` |
| `MethodArtifactGateway.read_model_output` — `read_model_output(self, reference)` | function / [228](../../../../agent/src/sr2fpga_agent/method_adapters.py#L228) | `<dynamic>.decode`、`self.__store.read_verified` |
| `MethodArtifactGateway.append_event` — `append_event(self, episode_id, event_type, payload)` | function / [231](../../../../agent/src/sr2fpga_agent/method_adapters.py#L231) | `<dynamic>.append`、`self.__event_refs.setdefault`、`self.__store.append_event` |
| `MethodArtifactGateway.event_refs` — `event_refs(self, episode_id)` | function / [236](../../../../agent/src/sr2fpga_agent/method_adapters.py#L236) | `self.__event_refs.get`、`tuple` |
| `GenerationServices` — `GenerationServices` | class / [241](../../../../agent/src/sr2fpga_agent/method_adapters.py#L241) | 无直接调用 |
| `MethodAdapter` — `MethodAdapter` | class / [252](../../../../agent/src/sr2fpga_agent/method_adapters.py#L252) | 无直接调用 |
| `MethodAdapter.emit_initial` — `emit_initial(self, context, services, shared_artifacts)` | function / [255](../../../../agent/src/sr2fpga_agent/method_adapters.py#L255) | 无直接调用 |
| `_AdapterBase` — `_AdapterBase` | class / [263](../../../../agent/src/sr2fpga_agent/method_adapters.py#L263) | 无直接调用 |
| `_AdapterBase._key` — `_key(self, context, suffix)` | function / [266](../../../../agent/src/sr2fpga_agent/method_adapters.py#L266) | 无直接调用 |
| `DirectMethodAdapter` — `DirectMethodAdapter` | class / [270](../../../../agent/src/sr2fpga_agent/method_adapters.py#L270) | 无直接调用 |
| `DirectMethodAdapter.__init__` — `__init__(self, condition)` | function / [271](../../../../agent/src/sr2fpga_agent/method_adapters.py#L271) | `ValueError`、`method_contract` |
| `DirectMethodAdapter.emit_initial` — `emit_initial(self, context, services, shared_artifacts)` | function / [276](../../../../agent/src/sr2fpga_agent/method_adapters.py#L276) | `_exception_failure`、`_failure`、`self._key`、`services.artifacts.append_event`、`services.artifacts.put_project`、`services.artifacts.read_project`、`services.direct.emit_project` |
| `DirectRepairMethodAdapter` — `DirectRepairMethodAdapter` | class / [298](../../../../agent/src/sr2fpga_agent/method_adapters.py#L298) | 无直接调用 |
| `DirectRepairMethodAdapter.__init__` — `__init__(self)` | function / [299](../../../../agent/src/sr2fpga_agent/method_adapters.py#L299) | `<dynamic>.__init__`、`super` |
| `DirectRepairMethodAdapter.repair_project` — `repair_project(self, context, candidate, diagnosis, services)` | function / [302](../../../../agent/src/sr2fpga_agent/method_adapters.py#L302) | `RuntimeError`、`_sha256_json`、`self._key`、`services.artifacts.put_project`、`services.artifacts.read_project`、`services.repair.repair_project` |
| `StructuredDirectMethodAdapter` — `StructuredDirectMethodAdapter` | class / [314](../../../../agent/src/sr2fpga_agent/method_adapters.py#L314) | `method_contract` |
| `StructuredDirectMethodAdapter.emit_initial` — `emit_initial(self, context, services, shared_artifacts)` | function / [317](../../../../agent/src/sr2fpga_agent/method_adapters.py#L317) | `_exception_failure`、`_failure`、`self._key`、`services.artifacts.put_planning`、`services.untyped.emit_plan` |
| `StructuredDirectMethodAdapter.emit_project_from_validated_planning` — `emit_project_from_validated_planning(self, context, planning, services, shared_artifacts)` | function / [328](../../../../agent/src/sr2fpga_agent/method_adapters.py#L328) | `_exception_failure`、`_failure`、`self._key`、`services.artifacts.put_project`、`services.artifacts.read_planning`、`services.untyped.emit_project` |
| `HisMethodAdapter` — `HisMethodAdapter` | class / [339](../../../../agent/src/sr2fpga_agent/method_adapters.py#L339) | 无直接调用 |
| `HisMethodAdapter.__init__` — `__init__(self, condition)` | function / [340](../../../../agent/src/sr2fpga_agent/method_adapters.py#L340) | `ValueError`、`method_contract` |
| `HisMethodAdapter.emit_initial` — `emit_initial(self, context, services, shared_artifacts)` | function / [345](../../../../agent/src/sr2fpga_agent/method_adapters.py#L345) | `_exception_failure`、`_failure`、`self._key`、`services.artifacts.append_event`、`services.artifacts.put_planning`、`services.artifacts.read_planning`、`services.system_his.emit_his` |
| `HisMethodAdapter.emit_project_from_validated_planning` — `emit_project_from_validated_planning(self, context, planning, services, shared_artifacts)` | function / [368](../../../../agent/src/sr2fpga_agent/method_adapters.py#L368) | `_exception_failure`、`_failure`、`self._emit_repairable_skeleton_project`、`self._key`、`services.artifacts.append_event`、`services.artifacts.put_project`、`services.artifacts.read_planning`、`services.artifacts.read_project`、`services.system_his.emit_free_project`、`services.system_his.emit_skeleton_project` |
| `HisMethodAdapter._emit_repairable_skeleton_project` — `_emit_repairable_skeleton_project(self, context, planning, services, attempt, previous_failure)` | function / [403](../../../../agent/src/sr2fpga_agent/method_adapters.py#L403) | `ProjectOutputNoProgressFailure`、`RepairableProjectOutputFailure`、`SkeletonProjectOutput`、`_exception_failure`、`_failure`、`facade.emit_skeleton_project_output`、`facade.lower_skeleton_project_output`、`facade.repair_skeleton_project_output`、`self._key`、`services.artifacts.put_model_output`、`services.artifacts.put_project`、`services.artifacts.read_model_output`、`services.artifacts.read_planning`、`str`、`type` |
| `HisRepairMethodAdapter` — `HisRepairMethodAdapter` | class / [486](../../../../agent/src/sr2fpga_agent/method_adapters.py#L486) | 无直接调用 |
| `HisRepairMethodAdapter.__init__` — `__init__(self)` | function / [487](../../../../agent/src/sr2fpga_agent/method_adapters.py#L487) | `<dynamic>.__init__`、`super` |
| `HisRepairMethodAdapter.correct_his` — `correct_his(self, context, planning, diagnosis, services)` | function / [490](../../../../agent/src/sr2fpga_agent/method_adapters.py#L490) | `RuntimeError`、`_sha256_json`、`self._key`、`services.artifacts.put_planning`、`services.artifacts.read_planning`、`services.repair.correct_his` |
| `HisRepairMethodAdapter.repair_project_output` — `repair_project_output(self, context, planning, failure, services, attempt)` | function / [503](../../../../agent/src/sr2fpga_agent/method_adapters.py#L503) | `self._emit_repairable_skeleton_project` |
| `HisRepairMethodAdapter.repair_project` — `repair_project(self, context, candidate, diagnosis, services)` | function / [520](../../../../agent/src/sr2fpga_agent/method_adapters.py#L520) | `RuntimeError`、`_sha256_json`、`self._key`、`services.artifacts.put_project`、`services.artifacts.read_project`、`services.repair.repair_project` |
| `HisCorrectionCapable` — `HisCorrectionCapable` | class / [533](../../../../agent/src/sr2fpga_agent/method_adapters.py#L533) | 无直接调用 |
| `HisCorrectionCapable.correct_his` — `correct_his(self, context, planning, diagnosis, services)` | function / [534](../../../../agent/src/sr2fpga_agent/method_adapters.py#L534) | 无直接调用 |
| `ProjectRepairCapable` — `ProjectRepairCapable` | class / [538](../../../../agent/src/sr2fpga_agent/method_adapters.py#L538) | 无直接调用 |
| `ProjectRepairCapable.repair_project` — `repair_project(self, context, candidate, diagnosis, services)` | function / [539](../../../../agent/src/sr2fpga_agent/method_adapters.py#L539) | 无直接调用 |
| `ProjectOutputRepairCapable` — `ProjectOutputRepairCapable` | class / [543](../../../../agent/src/sr2fpga_agent/method_adapters.py#L543) | 无直接调用 |
| `ProjectOutputRepairCapable.repair_project_output` — `repair_project_output(self, context, planning, failure, services, attempt)` | function / [544](../../../../agent/src/sr2fpga_agent/method_adapters.py#L544) | 无直接调用 |
| `RepairController` — `RepairController` | class / [555](../../../../agent/src/sr2fpga_agent/method_adapters.py#L555) | 无直接调用 |
| `RepairController.correct_his` — `correct_his(self, adapter, context, planning, diagnosis, services)` | function / [556](../../../../agent/src/sr2fpga_agent/method_adapters.py#L556) | `PermissionError`、`adapter.correct_his`、`isinstance` |
| `RepairController.repair_project` — `repair_project(self, adapter, context, candidate, diagnosis, services)` | function / [561](../../../../agent/src/sr2fpga_agent/method_adapters.py#L561) | `PermissionError`、`adapter.repair_project`、`isinstance` |
| `MethodAdapterRegistry` — `MethodAdapterRegistry` | class / [567](../../../../agent/src/sr2fpga_agent/method_adapters.py#L567) | 无直接调用 |
| `MethodAdapterRegistry.create` — `create(self, condition)` | function / [568](../../../../agent/src/sr2fpga_agent/method_adapters.py#L568) | `DirectMethodAdapter`、`DirectRepairMethodAdapter`、`HisMethodAdapter`、`HisRepairMethodAdapter`、`MethodConditionId`、`StructuredDirectMethodAdapter`、`isinstance` |
| `PairedArtifactCoordinator` — `PairedArtifactCoordinator` | class / [581](../../../../agent/src/sr2fpga_agent/method_adapters.py#L581) | 无直接调用 |
| `PairedArtifactCoordinator.__init__` — `__init__(self, store)` | function / [584](../../../../agent/src/sr2fpga_agent/method_adapters.py#L584) | `MethodArtifactGateway` |
| `PairedArtifactCoordinator.materialize_initial_project` — `materialize_initial_project(self, pairing, factory)` | function / [588](../../../../agent/src/sr2fpga_agent/method_adapters.py#L588) | `GeneratedProject`、`ProjectCandidateEmission`、`dict`、`json.loads`、`pairing.digest`、`project_package_sha256`、`self._store.read_verified`、`self._store.reference`、`self.materialize_project_checkpoint`、`str` |
| `PairedArtifactCoordinator.materialize_project_checkpoint` — `materialize_project_checkpoint(self, pairing, checkpoint_id, factory)` | function / [603](../../../../agent/src/sr2fpga_agent/method_adapters.py#L603) | `GeneratedProject`、`ProjectCandidateEmission`、`ValueError`、`_paired_event_stream_id`、`dict`、`factory`、`json.loads`、`pairing.digest`、`project_package_sha256`、`self._artifacts.put_project`、`self._store.append_event`、`self._store.read_verified`、`self._store.reference`、`str` |
| `PairedArtifactCoordinator.materialize_system_his` — `materialize_system_his(self, pairing, factory)` | function / [634](../../../../agent/src/sr2fpga_agent/method_adapters.py#L634) | `self.materialize_system_his_checkpoint` |
| `PairedArtifactCoordinator.materialize_system_his_checkpoint` — `materialize_system_his_checkpoint(self, pairing, factory)` | function / [641](../../../../agent/src/sr2fpga_agent/method_adapters.py#L641) | `PlanningArtifactEmission`、`_paired_event_stream_id`、`factory`、`pairing.digest`、`self._artifacts.put_planning`、`self._store.append_event`、`self._store.reference` |
| `_paired_event_stream_id` — `_paired_event_stream_id(paired_block_id)` | function / [666](../../../../agent/src/sr2fpga_agent/method_adapters.py#L666) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`hashlib.sha256` |
| `_failure` — `_failure(stage, message)` | function / [673](../../../../agent/src/sr2fpga_agent/method_adapters.py#L673) | `MethodStageFailure` |
| `_exception_failure` — `_exception_failure(stage, exc)` | function / [677](../../../../agent/src/sr2fpga_agent/method_adapters.py#L677) | `MethodStageFailure`、`str`、`type` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/method_contract.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/method_contract.py) · 233 行 · SHA-256 `d3e4998b34902403408f6e773750ca900b1a0d25509d508946e76d7117911b15`

> Closed Paper-1 method vocabulary for M0-M5.

导入模块：`__future__`、`dataclasses`、`enum`、`hashlib`、`json`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `MethodConditionId` — `MethodConditionId` | class / [20](../../../../agent/src/sr2fpga_agent/method_contract.py#L20) | 无直接调用 |
| `PlanningRepresentation` — `PlanningRepresentation` | class / [29](../../../../agent/src/sr2fpga_agent/method_contract.py#L29) | 无直接调用 |
| `ProjectGenerationKind` — `ProjectGenerationKind` | class / [35](../../../../agent/src/sr2fpga_agent/method_contract.py#L35) | 无直接调用 |
| `ModelStageId` — `ModelStageId` | class / [42](../../../../agent/src/sr2fpga_agent/method_contract.py#L42) | 无直接调用 |
| `HStageApplicability` — `HStageApplicability` | class / [52](../../../../agent/src/sr2fpga_agent/method_contract.py#L52) | 无直接调用 |
| `MethodContract` — `MethodContract` | class / [58](../../../../agent/src/sr2fpga_agent/method_contract.py#L58) | 无直接调用 |
| `MethodContract.__post_init__` — `__post_init__(self)` | function / [72](../../../../agent/src/sr2fpga_agent/method_contract.py#L72) | `ValueError` |
| `method_contract` — `method_contract(condition)` | function / [201](../../../../agent/src/sr2fpga_agent/method_contract.py#L201) | `KeyError`、`MethodConditionId`、`isinstance` |
| `method_policy_sha256` — `method_policy_sha256(condition)` | function / [209](../../../../agent/src/sr2fpga_agent/method_contract.py#L209) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`list`、`method_contract` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`MethodContract`、`dataclass`

## `agent/src/sr2fpga_agent/model_budget.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/model_budget.py) · 419 行 · SHA-256 `261134aa45617587693e4228d7e32fc8aaa42c15b9c13556e73195a0bab6356b`

> Per-episode model-call budget and first-class call events.

导入模块：`__future__`、`dataclasses`、`sr2fpga_agent.block_cost_accounting`、`sr2fpga_agent.providers`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ModelCallBudgetExceeded` — `ModelCallBudgetExceeded` | class / [13](../../../../agent/src/sr2fpga_agent/model_budget.py#L13) | 无直接调用 |
| `ModelCallBudget` — `ModelCallBudget` | class / [18](../../../../agent/src/sr2fpga_agent/model_budget.py#L18) | `field` |
| `ModelCallBudget.__post_init__` — `__post_init__(self)` | function / [31](../../../../agent/src/sr2fpga_agent/model_budget.py#L31) | `ValueError` |
| `ModelCallBudget.client` — `client(self, client, stage)` | function / [53](../../../../agent/src/sr2fpga_agent/model_budget.py#L53) | `BudgetedModelClient` |
| `ModelCallBudget.reserve` — `reserve(self, stage, operation, input_chars)` | function / [56](../../../../agent/src/sr2fpga_agent/model_budget.py#L56) | `ModelCallBudgetExceeded`、`ledger.record_budget_exhausted`、`ledger.reserve`、`self._cost_ledger`、`self._emit`、`time.monotonic` |
| `ModelCallBudget.finish` — `finish(self, call_id, stage, operation, started, output_chars, error, provider_transport_attempts, provider_token_usage, provider_response_provenance, provider_response_details)` | function / [98](../../../../agent/src/sr2fpga_agent/model_budget.py#L98) | `_normalized_response_provenance`、`_normalized_token_usage`、`all`、`dict`、`isinstance`、`ledger.record_cost`、`self._cost_ledger`、`self._emit`、`self.call_records.append`、`time.monotonic`、`token_usage.items`、`type` |
| `ModelCallBudget.reserve_parser_schema_retry` — `reserve_parser_schema_retry(self, stage, operation)` | function / [168](../../../../agent/src/sr2fpga_agent/model_budget.py#L168) | `ModelCallBudgetExceeded`、`ledger.record_budget_exhausted`、`ledger.reserve`、`self._cost_ledger`、`self._emit` |
| `ModelCallBudget.summary` — `summary(self)` | function / [206](../../../../agent/src/sr2fpga_agent/model_budget.py#L206) | `all`、`isinstance`、`list`、`record.get`、`sum`、`token_totals.values` |
| `ModelCallBudget._emit` — `_emit(self, payload)` | function / [240](../../../../agent/src/sr2fpga_agent/model_budget.py#L240) | `self.event_sink` |
| `ModelCallBudget._cost_ledger` — `_cost_ledger(self)` | function / [244](../../../../agent/src/sr2fpga_agent/model_budget.py#L244) | `self.attempt_cost_ledger_provider` |
| `BudgetedModelClient` — `BudgetedModelClient` | class / [250](../../../../agent/src/sr2fpga_agent/model_budget.py#L250) | 无直接调用 |
| `BudgetedModelClient.__init__` — `__init__(self, client, budget, stage)` | function / [253](../../../../agent/src/sr2fpga_agent/model_budget.py#L253) | 无直接调用 |
| `BudgetedModelClient.config` — `config(self)` | function / [259](../../../../agent/src/sr2fpga_agent/model_budget.py#L259) | `getattr` |
| `BudgetedModelClient.for_stage` — `for_stage(self, stage)` | function / [262](../../../../agent/src/sr2fpga_agent/model_budget.py#L262) | `BudgetedModelClient` |
| `BudgetedModelClient.with_output_format` — `with_output_format(self, response_format)` | function / [265](../../../../agent/src/sr2fpga_agent/model_budget.py#L265) | `BudgetedModelClient`、`callable`、`factory`、`getattr` |
| `BudgetedModelClient.chat` — `chat(self, messages)` | function / [270](../../../../agent/src/sr2fpga_agent/model_budget.py#L270) | `self._call` |
| `BudgetedModelClient.stream_chat` — `stream_chat(self, messages)` | function / [273](../../../../agent/src/sr2fpga_agent/model_budget.py#L273) | `self._call` |
| `BudgetedModelClient.record_parser_schema_retry` — `record_parser_schema_retry(self, operation)` | function / [276](../../../../agent/src/sr2fpga_agent/model_budget.py#L276) | `self._budget.reserve_parser_schema_retry` |
| `BudgetedModelClient._call` — `_call(self, operation, messages)` | function / [279](../../../../agent/src/sr2fpga_agent/model_budget.py#L279) | `<dynamic>`、`getattr`、`item.get`、`len`、`self._budget.finish`、`self._budget.reserve`、`self._consume_response_details`、`self._consume_response_provenance`、`self._consume_token_usage`、`self._consume_transport_attempt_count`、`str`、`sum` |
| `BudgetedModelClient._consume_transport_attempt_count` — `_consume_transport_attempt_count(self)` | function / [310](../../../../agent/src/sr2fpga_agent/model_budget.py#L310) | `callable`、`consumer`、`getattr`、`isinstance` |
| `BudgetedModelClient._consume_token_usage` — `_consume_token_usage(self)` | function / [319](../../../../agent/src/sr2fpga_agent/model_budget.py#L319) | `callable`、`consumer`、`getattr` |
| `BudgetedModelClient._consume_response_provenance` — `_consume_response_provenance(self)` | function / [323](../../../../agent/src/sr2fpga_agent/model_budget.py#L323) | `callable`、`consumer`、`getattr` |
| `BudgetedModelClient._consume_response_details` — `_consume_response_details(self)` | function / [327](../../../../agent/src/sr2fpga_agent/model_budget.py#L327) | `callable`、`consumer`、`getattr` |
| `client_for_stage` — `client_for_stage(client, stage)` | function / [332](../../../../agent/src/sr2fpga_agent/model_budget.py#L332) | `callable`、`factory`、`getattr` |
| `record_parser_schema_retry` — `record_parser_schema_retry(client, operation)` | function / [337](../../../../agent/src/sr2fpga_agent/model_budget.py#L337) | `callable`、`getattr`、`recorder` |
| `_normalized_token_usage` — `_normalized_token_usage(usage)` | function / [343](../../../../agent/src/sr2fpga_agent/model_budget.py#L343) | `isinstance`、`usage.get` |
| `_normalized_response_provenance` — `_normalized_response_provenance(provenance)` | function / [357](../../../../agent/src/sr2fpga_agent/model_budget.py#L357) | `fingerprint.strip`、`int`、`isinstance`、`len`、`provenance.get`、`provider_model.strip` |

## `agent/src/sr2fpga_agent/model_gateway_provenance.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/model_gateway_provenance.py) · 112 行 · SHA-256 `376ab236a24eae7e70cc052d6223942063181bd6244c5bad22ece0c040c512fb`

> Development-only model-gateway provenance artifacts.

导入模块：`__future__`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.provider_seed_capability`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `write_model_gateway_provenance` — `write_model_gateway_provenance(store, episode_id, analysis_population, method_condition, event, seed_control_evidence_ref)` | function / [14](../../../../agent/src/sr2fpga_agent/model_gateway_provenance.py#L14) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`_validate_seed_binding`、`event.get`、`hashlib.sha256`、`isinstance`、`json.dumps`、`provider.get`、`seed_control_evidence_ref.to_dict`、`store.put_validated_json` |
| `read_verified_model_gateway_provenance` — `read_verified_model_gateway_provenance(store, reference)` | function / [74](../../../../agent/src/sr2fpga_agent/model_gateway_provenance.py#L74) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_validate_seed_binding`、`hashlib.sha256`、`json.dumps`、`json.loads`、`store.read_verified` |
| `_validate_seed_binding` — `_validate_seed_binding(store, payload)` | function / [94](../../../../agent/src/sr2fpga_agent/model_gateway_provenance.py#L94) | `ArtifactRef`、`ValueError`、`read_verified_provider_seed_capability` |

## `agent/src/sr2fpga_agent/models.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/models.py) · 137 行 · SHA-256 `a87d300dfb2c2aea574bdd7133d66026cf0b8b53bcc1e5c468bece3198709a62`

> Shared data models and canonical JSON identity rules for the SR2FPGA agent.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PlatformProfile` — `PlatformProfile` | class / [21](../../../../agent/src/sr2fpga_agent/models.py#L21) | 无直接调用 |
| `ProjectRequest` — `ProjectRequest` | class / [35](../../../../agent/src/sr2fpga_agent/models.py#L35) | 无直接调用 |
| `GeneratedProject` — `GeneratedProject` | class / [45](../../../../agent/src/sr2fpga_agent/models.py#L45) | `field` |
| `ToolResult` — `ToolResult` | class / [53](../../../../agent/src/sr2fpga_agent/models.py#L53) | 无直接调用 |
| `RepairResult` — `RepairResult` | class / [67](../../../../agent/src/sr2fpga_agent/models.py#L67) | 无直接调用 |
| `PatchMetadata` — `PatchMetadata` | class / [76](../../../../agent/src/sr2fpga_agent/models.py#L76) | `field` |
| `PatchMetadata.to_dict` — `to_dict(self)` | function / [94](../../../../agent/src/sr2fpga_agent/models.py#L94) | 无直接调用 |
| `compact_json_text` — `compact_json_text(value)` | function / [116](../../../../agent/src/sr2fpga_agent/models.py#L116) | `json.dumps` |
| `compact_json_bytes` — `compact_json_bytes(value)` | function / [122](../../../../agent/src/sr2fpga_agent/models.py#L122) | `<dynamic>.encode`、`compact_json_text` |
| `canonical_json_bytes` — `canonical_json_bytes(value)` | function / [128](../../../../agent/src/sr2fpga_agent/models.py#L128) | `<dynamic>.encode`、`compact_json_text` |
| `sha256_json` — `sha256_json(value)` | function / [134](../../../../agent/src/sr2fpga_agent/models.py#L134) | `<dynamic>.hexdigest`、`compact_json_bytes`、`hashlib.sha256` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/openxc7_report.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/openxc7_report.py) · 188 行 · SHA-256 `4fb7af63d2da5cb694ef96c7159338db8372fc24cf4ea4337077811923a1318d`

> OpenXC7/nextpnr-xilinx report parsing helpers.

导入模块：`__future__`、`json`、`re`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `parse_openxc7_report` — `parse_openxc7_report(report_text)` | function / [10](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L10) | `_parse_json_report`、`_parse_log_report`、`metrics.update` |
| `_parse_log_report` — `_parse_log_report(report_text)` | function / [26](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L26) | `_resource_bucket`、`float`、`int`、`match.group`、`metrics.update`、`min`、`re.findall`、`re.search`、`report_text.splitlines`、`wns_match.group` |
| `_parse_json_report` — `_parse_json_report(report_text)` | function / [64](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L64) | `_extract_json_payload`、`_find_numeric_by_key`、`_json_log_strings`、`_parse_log_report`、`_resource_bucket`、`_used_count`、`_walk_json_items`、`metrics.update` |
| `_extract_json_payload` — `_extract_json_payload(report_text)` | function / [93](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L93) | `decoder.raw_decode`、`isinstance`、`json.JSONDecoder`、`json.loads`、`list`、`match.start`、`re.finditer`、`reversed` |
| `_resource_bucket` — `_resource_bucket(resource_name)` | function / [109](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L109) | `name.endswith`、`name.startswith`、`resource_name.upper` |
| `_walk_json_items` — `_walk_json_items(value)` | function / [122](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L122) | `_walk_json_items`、`isinstance`、`str`、`value.items` |
| `_used_count` — `_used_count(value)` | function / [132](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L132) | `int`、`isinstance`、`value.get` |
| `_find_numeric_by_key` — `_find_numeric_by_key(value, key_fragments)` | function / [146](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L146) | `<dynamic>.lower`、`_as_float`、`_find_numeric_by_key`、`any`、`isinstance`、`str`、`value.items` |
| `_json_log_strings` — `_json_log_strings(value)` | function / [165](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L165) | `<dynamic>.lower`、`_json_log_strings`、`isinstance`、`logs.append`、`logs.extend`、`str`、`value.items` |
| `_as_float` — `_as_float(value)` | function / [179](../../../../agent/src/sr2fpga_agent/openxc7_report.py#L179) | `float`、`isinstance`、`match.group`、`re.search` |

## `agent/src/sr2fpga_agent/oracle_runner.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracle_runner.py) · 275 行 · SHA-256 `ea46e9d846375f0e50faf827efd267db447bd9a0ccffcdc6a3b34ff801a2ac4b`

> Execute evaluator-local oracle scenarios in isolated simulator processes.

导入模块：`__future__`、`json`、`os`、`pathlib`、`re`、`shutil`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.log_parser`、`sr2fpga_agent.models`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.oracles.types`、`sr2fpga_agent.tool_runner`、`tempfile`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `run_oracle_scenarios` — `run_oracle_scenarios(command_runner, project_dir, bundle)` | function / [26](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L26) | `OracleRunEvidence`、`OracleRunEvidence.from_results`、`Path`、`_oracle_failure_type`、`_run_scenario`、`aggregate_oracle_tool_result`、`enumerate`、`load_oracle_bundle`、`runtime_root.mkdir`、`shutil.rmtree`、`str`、`tempfile.gettempdir`、`tuple`、`uuid.uuid4` |
| `_run_scenario` — `_run_scenario(command_runner, project_dir, bundle, scenario, runtime_root, scenario_index)` | function / [86](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L86) | `OracleScenarioResult.from_tool_result`、`_simulator_path`、`command_runner.run`、`parse_test_fail_mismatches`、`shutil.copyfile`、`tuple`、`validate_oracle_simulation_output` |
| `_simulator_path` — `_simulator_path(path)` | function / [124](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L124) | `<dynamic>.as_posix`、`path.resolve` |
| `validate_oracle_simulation_output` — `validate_oracle_simulation_output(result)` | function / [128](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L128) | `_failed_result`、`_has_oracle_vector_read_failure`、`any`、`line.strip`、`log_text.lower`、`log_text.splitlines`、`re.match` |
| `_has_oracle_vector_read_failure` — `_has_oracle_vector_read_failure(lines)` | function / [169](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L169) | `any`、`line.lower` |
| `_failed_result` — `_failed_result(result, stderr_suffix)` | function / [187](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L187) | `<dynamic>.lstrip`、`ToolResult`、`list`、`stderr.rstrip` |
| `aggregate_oracle_tool_result` — `aggregate_oracle_tool_result(evidence)` | function / [202](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L202) | `<dynamic>.join`、`<dynamic>.rstrip`、`ToolResult`、`result.stderr.rstrip`、`result.stdout.rstrip`、`sum` |
| `write_oracle_run_evidence` — `write_oracle_run_evidence(path, evidence)` | function / [226](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L226) | `<dynamic>.encode`、`<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`Path`、`ValueError`、`contract.validate`、`evidence.to_dict`、`handle.fileno`、`handle.flush`、`handle.write`、`json.dumps`、`os.fsync`、`os.replace`、`path.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary_path.unlink` |
| `_oracle_failure_type` — `_oracle_failure_type(exc)` | function / [269](../../../../agent/src/sr2fpga_agent/oracle_runner.py#L269) | `<dynamic>.lower`、`str` |

## `agent/src/sr2fpga_agent/paired_block.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/paired_block.py) · 159 行 · SHA-256 `9910093713753b00893053ab66554986dd1e348e3b2e944a1ddd799e224a6c69`

> Development-only paired-block identity and balanced execution order.

导入模块：`__future__`、`collections.abc`、`hashlib`、`json`、`random`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_balanced_method_orders` — `build_balanced_method_orders(execution_schedule_seed)` | function / [20](../../../../agent/src/sr2fpga_agent/paired_block.py#L20) | `ValueError`、`isinstance`、`len`、`list`、`random.Random`、`randomizer.shuffle`、`range`、`tuple` |
| `write_development_paired_block` — `write_development_paired_block(store, paired_block_id, semantic_instance_id, replicate_id, public_projection_sha256, model_provenance_sha256, decoding_control_mode, requested_decoding_seed, execution_schedule_seed, method_order)` | function / [43](../../../../agent/src/sr2fpga_agent/paired_block.py#L43) | `RuntimeError`、`build_development_paired_block`、`development_paired_block_reference`、`store.put_validated_json` |
| `build_development_paired_block` — `build_development_paired_block(paired_block_id, semantic_instance_id, replicate_id, public_projection_sha256, model_provenance_sha256, decoding_control_mode, requested_decoding_seed, execution_schedule_seed, method_order)` | function / [80](../../../../agent/src/sr2fpga_agent/paired_block.py#L80) | `_validate_paired_block`、`list` |
| `development_paired_block_reference` — `development_paired_block_reference(payload)` | function / [116](../../../../agent/src/sr2fpga_agent/paired_block.py#L116) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`ArtifactRef`、`_canonical_json`、`_validate_paired_block`、`hashlib.sha256`、`len` |
| `load_development_paired_block` — `load_development_paired_block(store, key_or_ref)` | function / [132](../../../../agent/src/sr2fpga_agent/paired_block.py#L132) | `ValueError`、`_validate_paired_block`、`isinstance`、`json.loads`、`store.read_verified` |
| `_validate_paired_block` — `_validate_paired_block(payload)` | function / [148](../../../../agent/src/sr2fpga_agent/paired_block.py#L148) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`build_balanced_method_orders`、`tuple` |

## `agent/src/sr2fpga_agent/paired_cost_views.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/paired_cost_views.py) · 1000 行 · SHA-256 `124337dd58904434bb83c1a0b06db2192450af74496ecc9c738e2bfc2f8e5855`

> Verified development-only actual, standalone, and incremental cost views.

导入模块：`__future__`、`dataclasses`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.block_cost_accounting`、`sr2fpga_agent.block_preparation`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.models`、`sr2fpga_agent.paired_block`、`sr2fpga_agent.project_contract`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PairedCostReconciliationError` — `PairedCostReconciliationError` | class / [52](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L52) | 无直接调用 |
| `MethodCostSource` — `MethodCostSource` | class / [57](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L57) | 无直接调用 |
| `_VerifiedMethodCost` — `_VerifiedMethodCost` | class / [65](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L65) | 无直接调用 |
| `reconcile_development_paired_block_costs` — `reconcile_development_paired_block_costs(store, paired_block_ref, checkpoint_manifest_ref, block_event_refs, methods, source_full_pack_runner_ref, reducer_policy_sha256, expected_preparation_policy)` | function / [74](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L74) | `PairedCostReconciliationError`、`_aggregate_axes`、`_blocked_method`、`_contrast_record`、`_incomplete_reasons`、`_load_verified_method_cost`、`_method_record`、`_normalize_method_sources`、`_read_manifest`、`_read_paired_block`、`_require_disjoint_source_partition`、`_require_sha256`、`_sha256_json`、`_validate_full_pack_lineage`、`_validate_method_availability`、`all`、`blocked_methods.get`、`blocked_methods_from_verified_manifest`、`checkpoint_manifest_ref.to_dict`、`episode_ids.add`、`list`、`paired_block_ref.to_dict`、`reference.to_dict`、`replay_development_block_preparation`、`set`、`source_full_pack_runner_ref.to_dict`、`store.put_validated_json`、`tuple`、`verified_methods.values` |
| `read_development_paired_block_cost_reconciliation` — `read_development_paired_block_cost_reconciliation(store, reference, expected_preparation_policy)` | function / [282](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L282) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`MethodCostSource`、`PairedCostReconciliationError`、`_artifact_ref`、`_optional_ref`、`isinstance`、`json.loads`、`reconcile_development_paired_block_costs`、`store.read_verified`、`tuple` |
| `_read_paired_block` — `_read_paired_block(store, reference)` | function / [344](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L344) | `PairedCostReconciliationError`、`_require_exact_reference`、`load_development_paired_block` |
| `_read_manifest` — `_read_manifest(store, reference, expected_preparation_policy)` | function / [352](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L352) | `PairedCostReconciliationError`、`_require_exact_reference`、`verify_development_shared_checkpoint_manifest_against_policy` |
| `_normalize_method_sources` — `_normalize_method_sources(methods)` | function / [371](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L371) | `PairedCostReconciliationError`、`any`、`isinstance`、`len`、`set`、`tuple` |
| `_validate_method_availability` — `_validate_method_availability(source, nodes, expected_blocked_checkpoint)` | function / [387](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L387) | `PairedCostReconciliationError` |
| `_blocked_method` — `_blocked_method(source)` | function / [436](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L436) | `_VerifiedMethodCost`、`_zero_axes` |
| `_load_verified_method_cost` — `_load_verified_method_cost(store, source, required_input_hashes)` | function / [447](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L447) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`PairedCostReconciliationError`、`_VerifiedMethodCost`、`_aggregate_axes`、`_artifact_ref`、`_optional_ref`、`_require_exact_reference`、`_sha256_json`、`any`、`event_ids.extend`、`event_refs.extend`、`json.loads`、`len`、`reconcile_cost_events`、`required_input_hashes.issubset`、`seen_attempts.add`、`set`、`sorted`、`store.read_verified`、`summaries.append`、`summary_axes.append`、`trajectory.items`、`tuple` |
| `_require_disjoint_source_partition` — `_require_disjoint_source_partition(replay, methods)` | function / [635](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L635) | `PairedCostReconciliationError`、`len`、`seen_ids.update`、`seen_refs.update`、`set` |
| `_validate_full_pack_lineage` — `_validate_full_pack_lineage(store, reference, paired_block_ref, paired_block, methods, checkpoint_nodes)` | function / [652](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L652) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`GeneratedProject`、`PairedCostReconciliationError`、`ValueError`、`_artifact_ref`、`_require_exact_reference`、`dict`、`item.to_dict`、`json.loads`、`paired_block_ref.to_dict`、`payload.get`、`project_package_sha256`、`set`、`smoke.get`、`store.read_verified`、`store.reference`、`str`、`verified.source.trajectory_ref.to_dict` |
| `_method_record` — `_method_record(method, verified, replay, nodes)` | function / [800](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L800) | `_aggregate_axes`、`_sha256_json`、`item.to_dict`、`list`、`verified.source.trajectory_ref.to_dict` |
| `_contrast_record` — `_contrast_record(contrast_id, component_axes, methods, nodes)` | function / [835](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L835) | `_aggregate_axes`、`_signed_delta_axes`、`next`、`signed.values` |
| `_aggregate_axes` — `_aggregate_axes(components)` | function / [892](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L892) | `<dynamic>.join`、`sum`、`tuple` |
| `_signed_delta_axes` — `_signed_delta_axes(treatment, baseline, forced_reason)` | function / [918](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L918) | 无直接调用 |
| `_zero_axes` — `_zero_axes()` | function / [947](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L947) | 无直接调用 |
| `_incomplete_reasons` — `_incomplete_reasons(manifest, methods)` | function / [954](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L954) | `methods.items`、`methods.values`、`reasons.update`、`sorted` |
| `_optional_ref` — `_optional_ref(payload)` | function / [978](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L978) | `_artifact_ref` |
| `_require_exact_reference` — `_require_exact_reference(store, reference, label)` | function / [982](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L982) | `PairedCostReconciliationError`、`store.read_verified`、`store.reference` |
| `_require_sha256` — `_require_sha256(value, label)` | function / [992](../../../../agent/src/sr2fpga_agent/paired_cost_views.py#L992) | `PairedCostReconciliationError`、`int`、`isinstance`、`len` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/paired_measurement.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/paired_measurement.py) · 451 行 · SHA-256 `8699b974ecc4a4a8a0415d75041e3f7b43084af4eaf26ed77a06a1cc57e465b0`

> Attempt-level and paired-run measurements for Paper-1 episodes.

导入模块：`__future__`、`json`、`pathlib`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_episode_measurement` — `build_episode_measurement(attempts, patches, l4_open)` | function / [34](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L34) | `<dynamic>.get`、`ValueError`、`_infrastructure_reason`、`_l4_measurement`、`_level_rank`、`_measurement_point`、`_repair_accounting`、`bool`、`dict`、`int`、`isinstance`、`item.get`、`patch.get`、`sorted`、`str` |
| `collect_paired_results` — `collect_paired_results(dataset_root, sample_ids)` | function / [84](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L84) | `<dynamic>.append`、`<dynamic>.get`、`ValueError`、`_aggregate_groups`、`_count_values`、`_initial_vs_final`、`_read_episode_result`、`int`、`iter`、`len`、`next`、`pairs.append`、`pairs_by_id.setdefault`、`sorted`、`str`、`sum` |
| `_measurement_point` — `_measurement_point(attempt, measurement_point)` | function / [133](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L133) | `attempt.get`、`bool`、`int`、`str` |
| `_infrastructure_reason` — `_infrastructure_reason(attempts)` | function / [147](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L147) | `attempt.get`、`str` |
| `_l4_measurement` — `_l4_measurement(value)` | function / [157](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L157) | `isinstance`、`raw.get`、`str` |
| `_read_episode_result` — `_read_episode_result(sample_dir, sample_id)` | function / [165](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L165) | `<dynamic>.join`、`ValueError`、`_read_json`、`isinstance`、`metadata.get`、`required.items`、`str`、`trajectory.get` |
| `_read_json` — `_read_json(path)` | function / [188](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L188) | `ValueError`、`isinstance`、`json.loads`、`path.exists`、`path.read_text` |
| `_aggregate_groups` — `_aggregate_groups(episodes, key)` | function / [197](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L197) | `<dynamic>.append`、`_aggregate_episodes`、`groups.items`、`groups.setdefault`、`sorted`、`str` |
| `_aggregate_episodes` — `_aggregate_episodes(episodes)` | function / [204](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L204) | `<dynamic>.get`、`_aggregate_repair`、`_count_values`、`_repair_success_count`、`_survival`、`len`、`str`、`sum` |
| `_survival` — `_survival(episodes, point)` | function / [222](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L222) | `<dynamic>.get`、`_level_rank`、`int`、`len`、`str`、`sum` |
| `_initial_vs_final` — `_initial_vs_final(episodes)` | function / [235](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L235) | `<dynamic>.get`、`_aggregate_repair`、`_repair_success_count`、`_survival`、`len`、`sum` |
| `_repair_accounting` — `_repair_accounting(attempts, patches)` | function / [256](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L256) | `<dynamic>.append`、`_valid_patch_record`、`all`、`any`、`attempt.get`、`bool`、`enumerate`、`int`、`isinstance`、`issues.append`、`len`、`matched_patch_indexes.add`、`patch.get`、`patches_by_diagnosis.get`、`patches_by_diagnosis.setdefault`、`set`、`sorted`、`status_counts.get`、`str` |
| `_valid_patch_record` — `_valid_patch_record(patch)` | function / [375](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L375) | `all`、`bool`、`isinstance`、`patch.get` |
| `_aggregate_repair` — `_aggregate_repair(episodes)` | function / [387](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L387) | `<dynamic>.get`、`_count_values`、`accounting.get`、`episode_scopes.get`、`int`、`isinstance`、`measurement.get`、`status_counts.items`、`status_values.append`、`str`、`values.get` |
| `_repair_success_count` — `_repair_success_count(episodes)` | function / [431](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L431) | `<dynamic>.get`、`int`、`isinstance`、`sum` |
| `_count_values` — `_count_values(values)` | function / [443](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L443) | `counts.get` |
| `_level_rank` — `_level_rank(level)` | function / [450](../../../../agent/src/sr2fpga_agent/paired_measurement.py#L450) | `_LEVEL_RANK.get`、`str` |

## `agent/src/sr2fpga_agent/parsers.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/parsers.py) · 743 行 · SHA-256 `da81d21cb8bf374a38013ef8f14b18fb3e6ad9885e56b4a71f80e9344a176f6e`

> Response parsers and project validation helpers.

导入模块：`__future__`、`dataclasses`、`difflib`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.project_contract`、`sr2fpga_agent.rtl_introspect`、`sr2fpga_agent.system_his_checker`、`sr2fpga_agent.system_his_v12_checker`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ResolvedTopPort` — `ResolvedTopPort` | class / [29](../../../../agent/src/sr2fpga_agent/parsers.py#L29) | 无直接调用 |
| `ResolvedProjectManifest` — `ResolvedProjectManifest` | class / [38](../../../../agent/src/sr2fpga_agent/parsers.py#L38) | 无直接调用 |
| `resolve_project_manifest` — `resolve_project_manifest(files)` | function / [52](../../../../agent/src/sr2fpga_agent/parsers.py#L52) | `ValueError`、`_resolve_legacy_manifest`、`_resolve_project_package_v1`、`isinstance`、`json.loads`、`manifest.get`、`validate_project_relative_path` |
| `check_project_package_l0` — `check_project_package_l0(project)` | function / [76](../../../../agent/src/sr2fpga_agent/parsers.py#L76) | `<dynamic>.join`、`L0CheckResult`、`_validate_canonical_top_interface`、`declared_modules`、`errors.append`、`list`、`manifest.source_languages.get`、`resolve_project_manifest`、`set`、`sorted`、`str` |
| `parse_project_files` — `parse_project_files(content, expected_task_type, manifest_policy)` | function / [218](../../../../agent/src/sr2fpga_agent/parsers.py#L218) | `<dynamic>.join`、`ValueError`、`_enforce_manifest_policy`、`_ensure_trailing_newline`、`_files_from_list`、`_strip_markdown_fence`、`_validate_expected_rtl_structure`、`files.items`、`isinstance`、`json.loads`、`payload.get`、`raw_files.items`、`resolve_project_manifest`、`set`、`sorted`、`str`、`validate_project_relative_path` |
| `parse_behavior_files` — `parse_behavior_files(content)` | function / [252](../../../../agent/src/sr2fpga_agent/parsers.py#L252) | `ValueError`、`_strip_markdown_fence`、`isinstance`、`json.loads`、`payload.get`、`raw_behavior.items`、`str` |
| `parse_system_his_payload` — `parse_system_his_payload(content)` | function / [268](../../../../agent/src/sr2fpga_agent/parsers.py#L268) | `ValueError`、`_strip_markdown_fence`、`isinstance`、`json.loads`、`payload.get` |
| `parse_system_his_v12` — `parse_system_his_v12(content)` | function / [285](../../../../agent/src/sr2fpga_agent/parsers.py#L285) | `<dynamic>.join`、`ValueError`、`check_system_his_v12`、`parse_system_his_payload` |
| `_validate_system_his_contract_unchanged` — `_validate_system_his_contract_unchanged(expected, actual)` | function / [296](../../../../agent/src/sr2fpga_agent/parsers.py#L296) | `ValueError`、`_canonical_json`、`actual.get`、`expected.get` |
| `diff_projects` — `diff_projects(old, new)` | function / [303](../../../../agent/src/sr2fpga_agent/parsers.py#L303) | `<dynamic>.join`、`chunks.extend`、`difflib.unified_diff`、`new.files.get`、`new_content.splitlines`、`old.files.get`、`old_content.splitlines`、`set`、`sorted` |
| `_minimize_repaired_project` — `_minimize_repaired_project(original, repaired, diagnosis)` | function / [322](../../../../agent/src/sr2fpga_agent/parsers.py#L322) | `GeneratedProject`、`_diagnosis_mentions_path`、`_manifest_is_valid_for_project`、`dict`、`original.files.get`、`repaired.files.get` |
| `_manifest_is_valid_for_project` — `_manifest_is_valid_for_project(files)` | function / [337](../../../../agent/src/sr2fpga_agent/parsers.py#L337) | `_validate_manifest` |
| `_validate_repair_preserves_l0_when_not_repairing_l0` — `_validate_repair_preserves_l0_when_not_repairing_l0(repaired_project, diagnosis)` | function / [345](../../../../agent/src/sr2fpga_agent/parsers.py#L345) | `<dynamic>.join`、`ValueError`、`check_project_l0`、`diagnosis.get`、`str` |
| `_diagnosis_mentions_path` — `_diagnosis_mentions_path(diagnosis, path)` | function / [357](../../../../agent/src/sr2fpga_agent/parsers.py#L357) | `<dynamic>.lower`、`diagnosis.get`、`isinstance`、`json.dumps`、`path.lower`、`str` |
| `_ensure_trailing_newline` — `_ensure_trailing_newline(content)` | function / [364](../../../../agent/src/sr2fpga_agent/parsers.py#L364) | `content.endswith` |
| `_manifest_policy_for_project` — `_manifest_policy_for_project(files)` | function / [368](../../../../agent/src/sr2fpga_agent/parsers.py#L368) | `files.get`、`isinstance`、`json.loads` |
| `_enforce_manifest_policy` — `_enforce_manifest_policy(manifest, policy)` | function / [380](../../../../agent/src/sr2fpga_agent/parsers.py#L380) | `ValueError` |
| `_validate_canonical_top_interface` — `_validate_canonical_top_interface(files, manifest, errors)` | function / [394](../../../../agent/src/sr2fpga_agent/parsers.py#L394) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.strip`、`declared_module_ports`、`errors.append`、`expected_names.count`、`files.get`、`manifest.source_languages.get`、`module_port_body`、`re.search`、`re.sub`、`set`、`sorted`、`widths_equivalent` |
| `_validate_manifest` — `_validate_manifest(files)` | function / [473](../../../../agent/src/sr2fpga_agent/parsers.py#L473) | `resolve_project_manifest` |
| `_resolve_project_package_v1` — `_resolve_project_package_v1(manifest, files)` | function / [477](../../../../agent/src/sr2fpga_agent/parsers.py#L477) | `<dynamic>.append`、`<dynamic>.join`、`ResolvedProjectManifest`、`ResolvedTopPort`、`ValueError`、`_manifest_path`、`_reject_duplicate_paths`、`_require_complete_rtl_source_set`、`_require_referenced_files`、`artifact_paths.append`、`artifact_paths_by_role.items`、`artifact_paths_by_role.setdefault`、`enumerate`、`project_name.strip`、`record.get`、`set`、`sorted`、`sources.append`、`top_module.strip`、`tuple`、`validate_project_package_manifest` |
| `_resolve_legacy_manifest` — `_resolve_legacy_manifest(manifest, files)` | function / [554](../../../../agent/src/sr2fpga_agent/parsers.py#L554) | `<dynamic>.join`、`<dynamic>.strip`、`ResolvedProjectManifest`、`ValueError`、`_legacy_artifact_paths`、`_manifest_path`、`_reject_duplicate_paths`、`_require_complete_rtl_source_set`、`_require_referenced_files`、`all`、`artifact_paths_by_role.items`、`artifact_paths_by_role.values`、`declared_modules`、`isinstance`、`len`、`manifest.get`、`missing_fields.append`、`str`、`top_module.strip`、`tuple` |
| `_legacy_artifact_paths` — `_legacy_artifact_paths(manifest, files)` | function / [602](../../../../agent/src/sr2fpga_agent/parsers.py#L602) | `<dynamic>.append`、`ValueError`、`_legacy_named_paths`、`_manifest_path`、`artifacts.setdefault`、`constraints.values`、`isinstance`、`manifest.get`、`path.rsplit`、`reports.items`、`simulation.get` |
| `_legacy_named_paths` — `_legacy_named_paths(value, field)` | function / [636](../../../../agent/src/sr2fpga_agent/parsers.py#L636) | `ValueError`、`_manifest_path`、`isinstance`、`value.items` |
| `_manifest_path` — `_manifest_path(value, field)` | function / [652](../../../../agent/src/sr2fpga_agent/parsers.py#L652) | `ValueError`、`isinstance`、`validate_project_relative_path` |
| `_reject_duplicate_paths` — `_reject_duplicate_paths(paths, field)` | function / [658](../../../../agent/src/sr2fpga_agent/parsers.py#L658) | `<dynamic>.join`、`ValueError`、`paths.count`、`sorted` |
| `_require_referenced_files` — `_require_referenced_files(files, paths, role)` | function / [664](../../../../agent/src/sr2fpga_agent/parsers.py#L664) | `<dynamic>.join`、`ValueError`、`sorted` |
| `_require_complete_rtl_source_set` — `_require_complete_rtl_source_set(files, sources, artifact_paths_by_role)` | function / [676](../../../../agent/src/sr2fpga_agent/parsers.py#L676) | `<dynamic>.endswith`、`<dynamic>.join`、`ValueError`、`artifact_paths_by_role.get`、`path.lower`、`sorted` |
| `_validate_expected_rtl_structure` — `_validate_expected_rtl_structure(files, expected_task_type)` | function / [699](../../../../agent/src/sr2fpga_agent/parsers.py#L699) | 无直接调用 |
| `_project_task_type` — `_project_task_type(files)` | function / [707](../../../../agent/src/sr2fpga_agent/parsers.py#L707) | `files.get`、`isinstance`、`json.loads`、`system_his.get` |
| `_project_system_his_schema` — `_project_system_his_schema(files)` | function / [716](../../../../agent/src/sr2fpga_agent/parsers.py#L716) | `files.get`、`isinstance`、`json.loads`、`system_his.get` |
| `_files_from_list` — `_files_from_list(raw_files)` | function / [725](../../../../agent/src/sr2fpga_agent/parsers.py#L725) | `ValueError`、`isinstance`、`str` |
| `_strip_markdown_fence` — `_strip_markdown_fence(content)` | function / [734](../../../../agent/src/sr2fpga_agent/parsers.py#L734) | `<dynamic>.join`、`<dynamic>.startswith`、`<dynamic>.strip`、`content.strip`、`stripped.splitlines`、`stripped.startswith` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/path_safety.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/path_safety.py) · 328 行 · SHA-256 `aa3e3450303d77b6b1d5bb5573b57d8d3ad0152835f6d00d68140703e580d69a`

> Path and tool-script input validation for generated project artifacts.

导入模块：`__future__`、`collections.abc`、`pathlib`、`re`、`sr2fpga_agent.contract_skeleton`、`sr2fpga_agent.models`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `UnsupportedSynthesisLanguageError` — `UnsupportedSynthesisLanguageError` | class / [32](../../../../agent/src/sr2fpga_agent/path_safety.py#L32) | 无直接调用 |
| `validate_sample_id` — `validate_sample_id(sample_id)` | function / [36](../../../../agent/src/sr2fpga_agent/path_safety.py#L36) | `ValueError`、`_SAFE_SAMPLE_ID.fullmatch` |
| `validate_project_relative_path` — `validate_project_relative_path(path)` | function / [44](../../../../agent/src/sr2fpga_agent/path_safety.py#L44) | `PurePosixPath`、`ValueError`、`_SAFE_PATH_PART.fullmatch`、`relative.as_posix`、`relative.is_absolute` |
| `project_file_target` — `project_file_target(project_dir, relative_path)` | function / [58](../../../../agent/src/sr2fpga_agent/path_safety.py#L58) | `<dynamic>.resolve`、`ValueError`、`project_dir.resolve`、`target.relative_to`、`validate_project_relative_path` |
| `build_yosys_script` — `build_yosys_script(sources, top_module, source_languages)` | function / [71](../../../../agent/src/sr2fpga_agent/path_safety.py#L71) | `<dynamic>.append`、`<dynamic>.join`、`ValueError`、`_SAFE_VERILOG_IDENTIFIER.fullmatch`、`_yosys_source_language`、`dict`、`languages.get`、`set`、`sorted`、`source_groups.append`、`validate_project_relative_path` |
| `_yosys_source_language` — `_yosys_source_language(source, declared_language)` | function / [108](../../../../agent/src/sr2fpga_agent/path_safety.py#L108) | `<dynamic>.lower`、`<dynamic>.suffix.lower`、`PurePosixPath`、`UnsupportedSynthesisLanguageError`、`ValueError`、`declared_language.strip`、`isinstance` |
| `build_patch_metadata` — `build_patch_metadata(old, new, diagnosis, patch_id)` | function / [137](../../../../agent/src/sr2fpga_agent/path_safety.py#L137) | `PatchMetadata`、`_is_model_editable`、`_is_trusted_artifact`、`_rtl_edit_surface_respected`、`_status_map`、`all`、`bool`、`diagnosis.get`、`new.files.get`、`old.files.get`、`set`、`sorted`、`str` |
| `finalize_patch_metadata` — `finalize_patch_metadata(metadata, tool_result_after)` | function / [185](../../../../agent/src/sr2fpga_agent/path_safety.py#L185) | `PatchMetadata`、`all`、`bool`、`dict`、`metadata.repair_regression.get`、`metadata.to_dict`、`metadata.tool_result_before.items`、`sorted`、`stage.lower`、`str`、`tool_result_after.get` |
| `_status_map` — `_status_map(value)` | function / [216](../../../../agent/src/sr2fpga_agent/path_safety.py#L216) | `isinstance`、`str`、`value.items` |
| `_is_model_editable` — `_is_model_editable(path)` | function / [222](../../../../agent/src/sr2fpga_agent/path_safety.py#L222) | `path.startswith` |
| `_rtl_edit_surface_respected` — `_rtl_edit_surface_respected(old, new, files_touched, allow_legacy_interface_change)` | function / [226](../../../../agent/src/sr2fpga_agent/path_safety.py#L226) | `_behavior_regions_respected`、`_rtl_interface_signature`、`any`、`old.files.items`、`path.startswith` |
| `_behavior_regions_respected` — `_behavior_regions_respected(old, new)` | function / [259](../../../../agent/src/sr2fpga_agent/path_safety.py#L259) | `_masked_behavior_regions`、`all`、`len`、`re.search` |
| `_masked_behavior_regions` — `_masked_behavior_regions(content)` | function / [269](../../../../agent/src/sr2fpga_agent/path_safety.py#L269) | `content.count`、`len`、`list`、`match.group`、`pattern.finditer`、`pattern.sub`、`re.compile`、`re.escape` |
| `_rtl_interface_signature` — `_rtl_interface_signature(content)` | function / [287](../../../../agent/src/sr2fpga_agent/path_safety.py#L287) | `match.end`、`match.start`、`re.findall`、`re.finditer`、`re.sub`、`signatures.append`、`tuple`、`without_comments.find` |
| `_is_trusted_artifact` — `_is_trusted_artifact(path)` | function / [299](../../../../agent/src/sr2fpga_agent/path_safety.py#L299) | `<dynamic>.lower`、`<dynamic>.lstrip`、`PurePosixPath`、`any`、`filename_stem.endswith`、`filename_stem.startswith`、`normalized.startswith`、`normalized.strip`、`path.replace` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`re.compile`

## `agent/src/sr2fpga_agent/pc_assembly.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc_assembly.py) · 456 行 · SHA-256 `86bf597ae75579006f01dbb361be147ba152ab9f7bc5cd8346ba3dfaf562e807`

> Opt-in PC decision interface; never an implicit migration or repair pass.

导入模块：`__future__`、`argparse`、`copy`、`dataclasses`、`hashlib`、`importlib.metadata`、`json`、`jsonschema`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.contract_skeleton`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.providers`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.system_his_capabilities`、`sys`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PCAssemblyError` — `PCAssemblyError` | class / [42](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L42) | 无直接调用 |
| `PCAssemblyError.__init__` — `__init__(self, stage, path, message)` | function / [43](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L43) | `<dynamic>.__init__`、`super` |
| `_json_bytes` — `_json_bytes(value)` | function / [48](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L48) | `<dynamic>.encode`、`json.dumps` |
| `_hash` — `_hash(content)` | function / [53](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L53) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `_runtime_stamp` — `_runtime_stamp()` | function / [57](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L57) | `<dynamic>.as_posix`、`<dynamic>.rglob`、`_hash`、`_json_bytes`、`discover_repository_root`、`path.read_bytes`、`path.relative_to`、`sorted`、`version` |
| `_validate_context` — `_validate_context(context, platform)` | function / [66](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L66) | `<dynamic>.encode`、`<dynamic>.items`、`<dynamic>.validate`、`ContractRegistry`、`Draft202012Validator`、`ValueError`、`_hash`、`capability_profile_id`、`capability_profile_sha256`、`context.to_dict`、`json.dumps`、`len`、`load_system_his_backend_capabilities`、`platform_profile_id`、`platform_profile_sha256`、`public.items`、`registry.load_schema`、`set` |
| `_context_from_public` — `_context_from_public(public)` | function / [97](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L97) | `FrozenRequirementContext`、`RequirementFactRecord`、`_freeze`、`tuple` |
| `_unique` — `_unique(items, label)` | function / [105](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L105) | `PCAssemblyError` |
| `_resolve_binding` — `_resolve_binding(pc, binding, label)` | function / [115](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L115) | `<dynamic>.join`、`<dynamic>.replace`、`<dynamic>.split`、`PCAssemblyError`、`enumerate`、`isinstance`、`item.get`、`len`、`pointer.append`、`str`、`token.replace` |
| `_model_field_sources` — `_model_field_sources(value, prefix)` | function / [141](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L141) | `<dynamic>.replace`、`_model_field_sources`、`enumerate`、`isinstance`、`result.update`、`str`、`value.items` |
| `_assemble` — `_assemble(context, body)` | function / [151](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L151) | `<dynamic>.append`、`<dynamic>.get`、`PCAssemblyError`、`ValueError`、`_model_field_sources`、`_resolve_binding`、`_unique`、`copy.deepcopy`、`enumerate`、`field_sources.update`、`frozen_project_name`、`frozen_requirement_trace_template`、`instances.values`、`list`、`names.add`、`set`、`sorted`、`sources.append`、`str`、`validate_project_relative_path` |
| `_no_duplicate_keys` — `_no_duplicate_keys(pairs)` | function / [231](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L231) | `ValueError` |
| `PCAssemblyResult` — `PCAssemblyResult` | class / [241](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L241) | `field` |
| `assemble_pc` — `assemble_pc(context, platform, raw_response)` | function / [251](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L251) | `<dynamic>.encode`、`<dynamic>.get`、`<dynamic>.load_schema`、`<dynamic>.throw`、`<dynamic>.validate`、`ContractRegistry`、`PCAssemblyResult`、`ValueError`、`_assemble`、`_validate_context`、`first_failed_h_stage`、`isinstance`、`json.dumps`、`json.loads`、`next`、`raw_response.decode`、`report.get`、`str`、`tuple`、`validate_frozen_system_his_payload_h_stages` |
| `decision_messages` — `decision_messages(context, platform)` | function / [281](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L281) | `<dynamic>.load_schema`、`ContractRegistry`、`_validate_context`、`context.to_dict`、`frozen_requirement_trace_template`、`json.dumps`、`set`、`sorted` |
| `_persist` — `_persist(store, prefix, context, platform, raw, calls, provider_failure, execution_ref)` | function / [304](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L304) | `<dynamic>.path.read_bytes`、`<dynamic>.validate`、`ContractRegistry`、`PCAssemblyResult`、`ValueError`、`_hash`、`_json_bytes`、`_runtime_stamp`、`asdict`、`assemble_pc`、`context.to_dict`、`context_ref.to_dict`、`execution_ref.to_dict`、`json.loads`、`list`、`pc_ref.to_dict`、`platform_ref.to_dict`、`raw_ref.to_dict`、`registry.load_schema`、`report_ref.to_dict`、`store.put_blob`、`store.put_validated_json`、`store.read_verified` |
| `_claim` — `_claim(store, attempt_id)` | function / [351](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L351) | `<dynamic>.mkdir`、`claims.mkdir`、`validate_sample_id` |
| `record_pc_assembly` — `record_pc_assembly(store, attempt_id, context, platform, raw_response)` | function / [359](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L359) | `_claim`、`_persist`、`_validate_context`、`isinstance`、`raw_response.encode` |
| `PCDecisionGenerator` — `PCDecisionGenerator` | class / [367](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L367) | 无直接调用 |
| `PCDecisionGenerator.__init__` — `__init__(self, client, platform, store)` | function / [369](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L369) | 无直接调用 |
| `PCDecisionGenerator.generate` — `generate(self, context, attempt_id)` | function / [372](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L372) | `<dynamic>.encode`、`ValueError`、`_claim`、`_json_bytes`、`_persist`、`_runtime_stamp`、`asdict`、`content.encode`、`context.to_dict`、`decision_messages`、`isinstance`、`self.client.stream_chat`、`self.store.put_blob`、`type` |
| `read_verified_pc_assembly` — `read_verified_pc_assembly(store, ref)` | function / [394](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L394) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ArtifactRef`、`ContractRegistry`、`PlatformProfile`、`ValueError`、`_context_from_public`、`_hash`、`_json_bytes`、`_persist`、`_runtime_stamp`、`_validate_context`、`json.loads`、`payload.items`、`raw_ref.key.removesuffix`、`store.read_verified` |
| `main` — `main(argv)` | function / [418](../../../../agent/src/sr2fpga_agent/pc_assembly.py#L418) | `ArtifactStore`、`PlatformProfile`、`_validate_context`、`all`、`argparse.ArgumentParser`、`args.episode_pack.read_text`、`args.output_root.resolve`、`args.platform.read_text`、`args.response.read_bytes`、`context_from_validated_episode_pack`、`discover_repository_root`、`json.dumps`、`json.loads`、`parser.add_argument`、`parser.error`、`parser.parse_args`、`print`、`read_verified_pc_assembly`、`record_pc_assembly`、`ref.to_dict`、`root.exists`、`root.is_dir`、`root.is_relative_to`、`store.reference` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`dataclass`、`main`

## `agent/src/sr2fpga_agent/pre_candidate_outcome.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py) · 635 行 · SHA-256 `04e7c0f87e5233a85f4744a6977ad5cf2f52ada00b394c67ca2f86d4f7c073da`

> Fail-closed reducers for excluded M4 H-stage pre-candidate stops.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.system_his_capabilities`、`sr2fpga_agent.system_his_schema`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PreCandidateOutcomeError` — `PreCandidateOutcomeError` | class / [50](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L50) | 无直接调用 |
| `read_verified_development_pre_candidate_stop_outcome` — `read_verified_development_pre_candidate_stop_outcome(store, outcome_ref, registry)` | function / [54](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L54) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.validate`、`ArtifactRef`、`ContractRegistry`、`PlatformProfile`、`PreCandidateOutcomeError`、`_canonical_json`、`_read_json_object`、`contract_keys.get`、`contract_registry.load_schema`、`hashlib.sha256`、`payload.items`、`raw_payload.get`、`reconcile_development_pre_candidate_stop_outcome` |
| `reconcile_development_pre_candidate_stop_outcome` — `reconcile_development_pre_candidate_stop_outcome(store, episode_pack_ref, planning_artifact_ref, method_event_refs, trajectory_ref, platform, registry)` | function / [122](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L122) | `<dynamic>.hexdigest`、`<dynamic>.join`、`ArtifactRef`、`ContractRegistry`、`PreCandidateOutcomeError`、`_canonical_json`、`_expected_h_statuses`、`_read_json_object`、`_read_registered`、`_reconcile_stop_costs`、`_stage_outcomes`、`_verify_method_events`、`asdict`、`capability_profile_id`、`capability_profile_sha256`、`context_from_validated_episode_pack`、`episode_pack_ref.to_dict`、`first_failed_h_stage`、`h_report.get`、`hashlib.sha256`、`len`、`list`、`load_system_his_backend_capabilities`、`method_policy_sha256`、`planning_artifact_ref.to_dict`、`platform_profile_id`、`platform_profile_sha256`、`reconcile_attempt_trajectory`、`reference.to_dict`、`required_input_hashes.issubset`、`store.put_validated_json`、`str`、`trajectory.get`、`trajectory_ref.to_dict`、`tuple`、`validate_episode_pack`、`validate_frozen_system_his_payload_h_stages`、`validate_registered_system_his_schema` |
| `_verify_method_events` — `_verify_method_events(store, references, episode_id, planning_sha256, failure_stage, require_closed_episode_stream)` | function / [438](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L438) | `<dynamic>.hexdigest`、`PreCandidateOutcomeError`、`_canonical_json`、`_read_json_object`、`enumerate`、`event.get`、`event.items`、`hashlib.sha256`、`isinstance`、`len`、`reference.key.endswith`、`set`、`store.event_refs`、`store.has_event_id`、`tuple`、`zip` |
| `_reconcile_stop_costs` — `_reconcile_stop_costs(store, references, registry, allow_shared)` | function / [512](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L512) | `PreCandidateOutcomeError`、`_read_registered`、`any`、`axes.items`、`len`、`list`、`sorted` |
| `_expected_h_statuses` — `_expected_h_statuses(failure_stage)` | function / [552](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L552) | `PreCandidateOutcomeError`、`enumerate`、`stages.index` |
| `_stage_outcomes` — `_stage_outcomes(failure_stage)` | function / [569](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L569) | `_expected_h_statuses` |
| `_read_registered` — `_read_registered(store, reference, registry, contract_key, label)` | function / [606](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L606) | `<dynamic>.join`、`<dynamic>.validate`、`PreCandidateOutcomeError`、`_read_json_object`、`registry.load_schema` |
| `_read_json_object` — `_read_json_object(store, reference, label)` | function / [622](../../../../agent/src/sr2fpga_agent/pre_candidate_outcome.py#L622) | `PreCandidateOutcomeError`、`isinstance`、`json.loads`、`store.read_verified` |

## `agent/src/sr2fpga_agent/project_contract.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/project_contract.py) · 912 行 · SHA-256 `aa6ee66c08b9af864b8fc89e03d45c1c710199c1af019cc4e49be6a6b692e6fa`

> Registered project-package validation and trusted project-envelope building.

导入模块：`__future__`、`hashlib`、`json`、`jsonschema`、`pathlib`、`sr2fpga_agent.method_contract`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.repository_paths`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_registered_project_schema` — `load_registered_project_schema(contract_key, paths)` | function / [27](../../../../agent/src/sr2fpga_agent/project_contract.py#L27) | `<dynamic>.get`、`<dynamic>.resolve`、`<dynamic>.strip`、`Draft202012Validator.check_schema`、`Path`、`PurePosixPath`、`RepositoryPaths.discover`、`ValueError`、`entry.get`、`isinstance`、`json.loads`、`manifest_path.read_text`、`registry.get`、`relative.is_absolute`、`repository_paths.contracts_dir.resolve`、`schema.get`、`schema_path.read_text`、`str` |
| `validate_project_package_manifest` — `validate_project_package_manifest(manifest, paths)` | function / [74](../../../../agent/src/sr2fpga_agent/project_contract.py#L74) | `<dynamic>.join`、`_record_paths`、`_validate_registered_project_contract`、`errors.append`、`isinstance`、`manifest.get`、`set`、`sorted`、`top.get` |
| `validate_project_envelope` — `validate_project_envelope(envelope, paths)` | function / [102](../../../../agent/src/sr2fpga_agent/project_contract.py#L102) | `<dynamic>.join`、`_merkle_root`、`_sha256_json`、`_validate_registered_project_contract`、`casefold_collisions.add`、`duplicate_paths.add`、`enumerate`、`envelope.get`、`envelope.items`、`errors.append`、`isinstance`、`leaves.append`、`normalized_path.casefold`、`record.get`、`seen_casefold_paths.get`、`seen_paths.add`、`set`、`sorted`、`tuple`、`validate_project_relative_path` |
| `verify_project_envelope` — `verify_project_envelope(project, envelope, paths, event_ref_resolver)` | function / [169](../../../../agent/src/sr2fpga_agent/project_contract.py#L169) | `<dynamic>.get`、`<dynamic>.join`、`_manifest_file_roles`、`_merkle_root`、`_normalized_project_files`、`_project_manifest`、`_project_package_digest`、`_sha256_bytes`、`_sha256_json`、`_verify_composite_regions`、`actual_leaves.append`、`any`、`content.encode`、`envelope.get`、`errors.append`、`errors.extend`、`isinstance`、`method_contract`、`method_policy_sha256`、`normalized_project.items`、`record.get`、`records_by_path.get`、`records_by_path.setdefault`、`records_by_path.values`、`set`、`sorted`、`validate_project_envelope`、`validate_project_package_manifest`、`validate_project_relative_path` |
| `project_package_sha256` — `project_package_sha256(project, paths)` | function / [283](../../../../agent/src/sr2fpga_agent/project_contract.py#L283) | `<dynamic>.join`、`ValueError`、`_manifest_file_roles`、`_merkle_root`、`_normalized_project_files`、`_project_manifest`、`_project_package_digest`、`_sha256_bytes`、`_sha256_json`、`content.encode`、`errors.append`、`normalized.items`、`set`、`sorted`、`validate_project_package_manifest` |
| `build_project_envelope` — `build_project_envelope(project, episode_id, method_condition_id, method_policy_sha256, snapshot_id, file_policies, evaluator_material_refs, paths)` | function / [310](../../../../agent/src/sr2fpga_agent/project_contract.py#L310) | `<dynamic>.encode`、`<dynamic>.join`、`ValueError`、`_manifest_file_roles`、`_merkle_root`、`_normalized_project_files`、`_project_manifest`、`_project_package_digest`、`_require_non_empty`、`_require_sha256`、`_sha256_bytes`、`_sha256_json`、`dict`、`file_records.append`、`merkle_leaves.append`、`policy.get`、`set`、`sorted`、`validate_project_envelope`、`validate_project_package_manifest`、`validate_project_relative_path` |
| `build_composite_project_envelope` — `build_composite_project_envelope(project, episode_id, method_condition_id, snapshot_id, trusted_builder_event_id, model_generation_event_id, event_ref_resolver, paths)` | function / [437](../../../../agent/src/sr2fpga_agent/project_contract.py#L437) | `<dynamic>.join`、`ValueError`、`_derive_composite_regions`、`_manifest_file_roles`、`_merkle_root`、`_normalized_project_files`、`_project_manifest`、`_project_package_digest`、`_require_non_empty`、`_sha256_bytes`、`_sha256_json`、`content.encode`、`event_ref_resolver`、`isinstance`、`leaves.append`、`method_contract`、`method_policy_sha256`、`normalized_files.items`、`record.update`、`records.append`、`set`、`sorted`、`validate_project_package_manifest`、`verify_project_envelope` |
| `_derive_composite_regions` — `_derive_composite_regions(path, content, trusted_builder_event_id, model_generation_event_id)` | function / [546](../../../../agent/src/sr2fpga_agent/project_contract.py#L546) | `<dynamic>.join`、`ValueError`、`_region_record`、`_validate_behavior_marker_order`、`character.isalnum`、`content.find`、`len`、`regions.append` |
| `_validate_behavior_marker_order` — `_validate_behavior_marker_order(path, content)` | function / [615](../../../../agent/src/sr2fpga_agent/project_contract.py#L615) | `ValueError`、`content.find`、`len` |
| `_region_record` — `_region_record(region_id, owner, start, end, content, editable, event_id)` | function / [640](../../../../agent/src/sr2fpga_agent/project_contract.py#L640) | `ValueError`、`_sha256_bytes` |
| `_verify_composite_regions` — `_verify_composite_regions(path, content, record, errors, event_ref_resolver)` | function / [662](../../../../agent/src/sr2fpga_agent/project_contract.py#L662) | `_derive_composite_regions`、`_sha256_bytes`、`enumerate`、`errors.append`、`event_ref_resolver`、`isinstance`、`len`、`max`、`record.get`、`refs_by_owner.setdefault`、`region.get`、`str`、`tuple` |
| `_validate_registered_project_contract` — `_validate_registered_project_contract(contract_key, payload, paths)` | function / [760](../../../../agent/src/sr2fpga_agent/project_contract.py#L760) | `Draft202012Validator`、`_json_path`、`load_registered_project_schema`、`sorted`、`str`、`tuple`、`validator.iter_errors` |
| `_project_manifest` — `_project_manifest(project)` | function / [779](../../../../agent/src/sr2fpga_agent/project_contract.py#L779) | `ValueError`、`isinstance`、`json.loads`、`project.files.get` |
| `_manifest_file_roles` — `_manifest_file_roles(manifest)` | function / [792](../../../../agent/src/sr2fpga_agent/project_contract.py#L792) | `artifact.get`、`isinstance`、`manifest.get`、`source.get` |
| `_record_paths` — `_record_paths(value, label, errors)` | function / [807](../../../../agent/src/sr2fpga_agent/project_contract.py#L807) | `<dynamic>.join`、`duplicates.add`、`errors.append`、`isinstance`、`paths.append`、`record.get`、`seen.add`、`set`、`sorted`、`validate_project_relative_path` |
| `_normalized_project_files` — `_normalized_project_files(project, errors)` | function / [831](../../../../agent/src/sr2fpga_agent/project_contract.py#L831) | `<dynamic>.join`、`casefold_paths.get`、`collisions.add`、`errors.append`、`normalized_path.casefold`、`project.files.items`、`set`、`sorted`、`tuple`、`validate_project_relative_path` |
| `_merkle_root` — `_merkle_root(leaves)` | function / [859](../../../../agent/src/sr2fpga_agent/project_contract.py#L859) | `<dynamic>.digest`、`<dynamic>.encode`、`<dynamic>.hex`、`ValueError`、`hashlib.sha256`、`len`、`nodes.append`、`range`、`sorted` |
| `_project_package_digest` — `_project_package_digest(manifest_digest, project_merkle_root)` | function / [876](../../../../agent/src/sr2fpga_agent/project_contract.py#L876) | `_require_sha256`、`_sha256_bytes`、`bytes.fromhex` |
| `_sha256_bytes` — `_sha256_bytes(value)` | function / [887](../../../../agent/src/sr2fpga_agent/project_contract.py#L887) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `_require_non_empty` — `_require_non_empty(name, value)` | function / [891](../../../../agent/src/sr2fpga_agent/project_contract.py#L891) | `ValueError`、`isinstance`、`value.strip` |
| `_require_sha256` — `_require_sha256(name, value)` | function / [896](../../../../agent/src/sr2fpga_agent/project_contract.py#L896) | `ValueError`、`any`、`isinstance`、`len` |
| `_json_path` — `_json_path(parts)` | function / [905](../../../../agent/src/sr2fpga_agent/project_contract.py#L905) | `isinstance` |

## `agent/src/sr2fpga_agent/project_generator.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/project_generator.py) · 3115 行 · SHA-256 `0beadc6683708e78a2a6fd17ad8116bdacd27a7bffb445db996c5465af97fe84`

> Deterministic V1 project generator for small RTL tasks.

导入模块：`__future__`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.system_his_fidelity`、`sr2fpga_agent.task_catalog`、`sr2fpga_agent.task_families`、`sr2fpga_agent.task_families.basic`、`sr2fpga_agent.task_families.datapath`、`sr2fpga_agent.task_families.image`、`sr2fpga_agent.task_families.protocol`、`sr2fpga_agent.task_families.rl`、`sr2fpga_agent.task_families.stream`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ProjectGenerator` — `ProjectGenerator` | class / [607](../../../../agent/src/sr2fpga_agent/project_generator.py#L607) | 无直接调用 |
| `ProjectGenerator.generate` — `generate(self, request, platform)` | function / [610](../../../../agent/src/sr2fpga_agent/project_generator.py#L610) | `GeneratedProject`、`ValueError`、`_canonical_request`、`_manifest`、`_predicted_qor`、`_rtl_files`、`_system_his`、`_testbench`、`_timing_sdc`、`_to_json` |
| `_canonical_request` — `_canonical_request(request)` | function / [629](../../../../agent/src/sr2fpga_agent/project_generator.py#L629) | `ProjectRequest`、`TASK_TYPE_ALIASES.get` |
| `_to_json` — `_to_json(payload)` | function / [641](../../../../agent/src/sr2fpga_agent/project_generator.py#L641) | `json.dumps` |
| `_system_his` — `_system_his(request, platform, rtl_files)` | function / [645](../../../../agent/src/sr2fpga_agent/project_generator.py#L645) | `<dynamic>.requirement_trace_template`、`_architecture`、`_connections`、`_expected_behavior`、`_interface`、`_modules`、`_resolve_instance_parameter_values`、`_resource_shape`、`_test_pass_means`、`_top_parameters`、`_top_ports`、`_v12_actual_interfaces`、`_v12_components`、`_v12_control_flow`、`_v12_data_flow`、`_v12_instances`、`_v12_ports`、`_v12_state`、`_v12_task_specific_instances`、`_verification_scenarios`、`build_deterministic_requirement_trace`、`build_request_requirement_envelope`、`effective_request_requirement`、`list`、`rtl_files.keys`、`str` |
| `_v12_actual_interfaces` — `_v12_actual_interfaces(request)` | function / [783](../../../../agent/src/sr2fpga_agent/project_generator.py#L783) | `protocol_by_task.get` |
| `_v12_ports` — `_v12_ports(ports)` | function / [798](../../../../agent/src/sr2fpga_agent/project_generator.py#L798) | `port.get` |
| `_v12_components` — `_v12_components(modules, rtl_files)` | function / [809](../../../../agent/src/sr2fpga_agent/project_generator.py#L809) | `<dynamic>.items`、`_module_has_edge_triggered_state`、`_module_intent`、`_v12_ports`、`_v12_semantic_kind`、`dict`、`module.get`、`rtl_files.get`、`str` |
| `_module_has_edge_triggered_state` — `_module_has_edge_triggered_state(content, module_name)` | function / [833](../../../../agent/src/sr2fpga_agent/project_generator.py#L833) | `match.group`、`re.escape`、`re.search` |
| `_v12_semantic_kind` — `_v12_semantic_kind(module_name, role)` | function / [843](../../../../agent/src/sr2fpga_agent/project_generator.py#L843) | `module_name.lower` |
| `_v12_instances` — `_v12_instances(rtl_files, components, top_module, clock_name, reset_name)` | function / [867](../../../../agent/src/sr2fpga_agent/project_generator.py#L867) | `_top_instance_ports`、`_v12_component_parameter_values`、`components_by_name.get`、`instances.setdefault`、`instances.values`、`list`、`str` |
| `_v12_task_specific_instances` — `_v12_task_specific_instances(request, instances, components, clock_name, reset_name)` | function / [896](../../../../agent/src/sr2fpga_agent/project_generator.py#L896) | `<dynamic>.get`、`_v12_component_parameter_values`、`by_name.values`、`list`、`str` |
| `_v12_component_parameter_values` — `_v12_component_parameter_values(component)` | function / [935](../../../../agent/src/sr2fpga_agent/project_generator.py#L935) | `<dynamic>.strip`、`component.get`、`isinstance`、`parameter.get`、`str` |
| `_resolve_instance_parameter_values` — `_resolve_instance_parameter_values(instances, top_parameters, default_width)` | function / [949](../../../../agent/src/sr2fpga_agent/project_generator.py#L949) | `<dynamic>.strip`、`instance.get`、`isinstance`、`list`、`parameter.get`、`str`、`values.items` |
| `_v12_state` — `_v12_state(request, top_module, instances)` | function / [971](../../../../agent/src/sr2fpga_agent/project_generator.py#L971) | `buffers.append`、`counters.append`、`counters.extend`、`fsms.append`、`instance.get`、`max`、`memories.append`、`next`、`registers.append`、`registers.extend`、`str` |
| `_v12_data_flow` — `_v12_data_flow(request, top_ports, instances, components)` | function / [1267](../../../../agent/src/sr2fpga_agent/project_generator.py#L1267) | `_component_ports_by_instance`、`_pattern_trigger_data_flow`、`_primary_top_endpoint`、`_pulse_radar_data_flow`、`_v12_topology_edge_data_flow`、`_vision_defect_data_flow`、`any`、`flows.append`、`instance_ports.items`、`path.append`、`path.insert`、`port.get`、`ports.items`、`str` |
| `_pulse_radar_data_flow` — `_pulse_radar_data_flow(request)` | function / [1326](../../../../agent/src/sr2fpga_agent/project_generator.py#L1326) | `enumerate`、`source.rsplit` |
| `_vision_defect_data_flow` — `_vision_defect_data_flow()` | function / [1358](../../../../agent/src/sr2fpga_agent/project_generator.py#L1358) | `enumerate`、`source.rsplit` |
| `_pattern_trigger_data_flow` — `_pattern_trigger_data_flow(request)` | function / [1385](../../../../agent/src/sr2fpga_agent/project_generator.py#L1385) | `enumerate`、`source.rsplit` |
| `_v12_topology_edge_data_flow` — `_v12_topology_edge_data_flow(request, instances)` | function / [1411](../../../../agent/src/sr2fpga_agent/project_generator.py#L1411) | `<dynamic>.append`、`<dynamic>.strip`、`COMPONENT_TOPOLOGIES.get`、`_v12_resolve_topology_endpoint`、`any`、`component_to_instances.setdefault`、`edge.get`、`enumerate`、`flows.append`、`instance.get`、`sink.rsplit`、`source.rsplit`、`str`、`topology.get` |
| `_v12_resolve_topology_endpoint` — `_v12_resolve_topology_endpoint(endpoint, component_to_instances)` | function / [1450](../../../../agent/src/sr2fpga_agent/project_generator.py#L1450) | `component_to_instances.get`、`endpoint.split`、`len` |
| `_primary_top_endpoint` — `_primary_top_endpoint(top_ports, direction)` | function / [1462](../../../../agent/src/sr2fpga_agent/project_generator.py#L1462) | `port.get`、`str` |
| `_component_ports_by_instance` — `_component_ports_by_instance(instances, components)` | function / [1482](../../../../agent/src/sr2fpga_agent/project_generator.py#L1482) | `component.get`、`components_by_name.get`、`isinstance`、`port.get`、`str` |
| `_v12_control_flow` — `_v12_control_flow(request, data_flow)` | function / [1498](../../../../agent/src/sr2fpga_agent/project_generator.py#L1498) | `rules.extend`、`str` |
| `_modules` — `_modules(interface, architecture, rtl_files)` | function / [1651](../../../../agent/src/sr2fpga_agent/project_generator.py#L1651) | `_module_intent`、`_module_ports`、`_module_sources`、`_params_from_parameters`、`_top_instance_parameters`、`_top_ports`、`module_parameters.get`、`modules.append`、`set`、`str` |
| `_params_from_parameters` — `_params_from_parameters(parameters)` | function / [1693](../../../../agent/src/sr2fpga_agent/project_generator.py#L1693) | `parameters.items` |
| `_module_intent` — `_module_intent(module_name)` | function / [1697](../../../../agent/src/sr2fpga_agent/project_generator.py#L1697) | `module_name.replace` |
| `_top_ports` — `_top_ports(interface)` | function / [1702](../../../../agent/src/sr2fpga_agent/project_generator.py#L1702) | `ports.append` |
| `_top_parameters` — `_top_parameters(request)` | function / [1716](../../../../agent/src/sr2fpga_agent/project_generator.py#L1716) | 无直接调用 |
| `_verification_scenarios` — `_verification_scenarios(request)` | function / [1733](../../../../agent/src/sr2fpga_agent/project_generator.py#L1733) | 无直接调用 |
| `_connections` — `_connections(architecture, rtl_files, modules)` | function / [1776](../../../../agent/src/sr2fpga_agent/project_generator.py#L1776) | `<dynamic>.append`、`<dynamic>.get`、`_append_connection`、`_top_instance_ports`、`by_signal.items`、`by_signal.setdefault`、`ports_by_module.get`、`set`、`str`、`top_ports.get` |
| `_module_sources` — `_module_sources(rtl_files)` | function / [1814](../../../../agent/src/sr2fpga_agent/project_generator.py#L1814) | `<dynamic>.split`、`content.splitlines`、`line.strip`、`rtl_files.items`、`stripped.split`、`stripped.startswith` |
| `_module_ports` — `_module_ports(rtl_files)` | function / [1826](../../../../agent/src/sr2fpga_agent/project_generator.py#L1826) | `_parse_module_ports`、`re.findall`、`rtl_files.values` |
| `_parse_module_ports` — `_parse_module_ports(content, module_name)` | function / [1834](../../../../agent/src/sr2fpga_agent/project_generator.py#L1834) | `_module_port_body`、`_port_width`、`_split_port_declarations`、`match.group`、`ports.append`、`re.search` |
| `_module_port_body` — `_module_port_body(content, module_name)` | function / [1856](../../../../agent/src/sr2fpga_agent/project_generator.py#L1856) | `<dynamic>.isspace`、`_matching_paren`、`content.startswith`、`len`、`match.end`、`re.escape`、`re.search` |
| `_matching_paren` — `_matching_paren(text, open_index)` | function / [1877](../../../../agent/src/sr2fpga_agent/project_generator.py#L1877) | `ValueError`、`len`、`range` |
| `_split_port_declarations` — `_split_port_declarations(body)` | function / [1889](../../../../agent/src/sr2fpga_agent/project_generator.py#L1889) | `<dynamic>.join`、`<dynamic>.split`、`body.split`、`declarations.append`、`part.strip` |
| `_port_width` — `_port_width(range_text)` | function / [1898](../../../../agent/src/sr2fpga_agent/project_generator.py#L1898) | `int`、`numeric.group`、`range_text.strip`、`re.fullmatch` |
| `_top_instance_ports` — `_top_instance_ports(top_rtl, submodules)` | function / [1907](../../../../agent/src/sr2fpga_agent/project_generator.py#L1907) | `endpoints.append`、`match.group`、`pattern.finditer`、`re.compile`、`re.findall` |
| `_top_instance_parameters` — `_top_instance_parameters(top_rtl, submodules)` | function / [1924](../../../../agent/src/sr2fpga_agent/project_generator.py#L1924) | `_parameter_value`、`match.group`、`pattern.finditer`、`re.compile`、`re.findall` |
| `_parameter_value` — `_parameter_value(value)` | function / [1944](../../../../agent/src/sr2fpga_agent/project_generator.py#L1944) | `int`、`re.fullmatch`、`value.strip` |
| `_append_connection` — `_append_connection(connections, seen, signal, source, target, widths_by_module)` | function / [1951](../../../../agent/src/sr2fpga_agent/project_generator.py#L1951) | `_connection_endpoint`、`_connection_protocol`、`_connection_width`、`connections.append`、`seen.add` |
| `_connection_protocol` — `_connection_protocol(source_port, target_port)` | function / [1976](../../../../agent/src/sr2fpga_agent/project_generator.py#L1976) | `any` |
| `_connection_width` — `_connection_width(source, target, widths_by_module)` | function / [1983](../../../../agent/src/sr2fpga_agent/project_generator.py#L1983) | `<dynamic>.get`、`widths_by_module.get` |
| `_connection_endpoint` — `_connection_endpoint(endpoint)` | function / [1994](../../../../agent/src/sr2fpga_agent/project_generator.py#L1994) | 无直接调用 |
| `_architecture` — `_architecture(request)` | function / [2001](../../../../agent/src/sr2fpga_agent/project_generator.py#L2001) | `architecture.update`、`family_id_for_task_type`、`list`、`task_family_spec_for_family_id` |
| `_manifest` — `_manifest(request, platform, rtl_files)` | function / [2081](../../../../agent/src/sr2fpga_agent/project_generator.py#L2081) | `<dynamic>.keys`、`list` |
| `_rtl_files` — `_rtl_files(request)` | function / [2107](../../../../agent/src/sr2fpga_agent/project_generator.py#L2107) | `ValueError`、`_alu_control_unit_rtl_files`、`_composed_batch_rl_accelerator_shell_rtl_files`、`_composed_dual_stream_join_rtl_files`、`_composed_event_counter_rtl_files`、`_composed_host_protocol_shell_rtl_files`、`_composed_policy_value_shell_rtl_files`、`_composed_replay_arbiter_shell_rtl_files`、`_composed_replay_sample_shell_rtl_files`、`_composed_rl_accelerator_shell_rtl_files`、`_composed_stream_accumulator_rtl_files`、`_composed_stream_fork_rtl_files`、`_composed_td_update_core_rtl_files`、`_composed_vector_mac_pipeline_rtl_files`、`_counter_rtl`、`_crc_stream_checker_rtl_files`、`_fifo_rtl`、`_fir_filter_rtl_files`、`_matched_filter_rtl_files`、`_matrix_vector_mac_rtl_files`、`_pattern_matcher_rtl_files`、`_peak_detector_rtl_files`、`_pulse_radar_signal_rtl_files`、`_pwm_controller_rtl_files`、`_ram_read_write_rtl`、`_simple_fsm_rtl`、`_sobel_threshold_rtl_files`、`_spi_master_rtl_files`、`_stream_trigger_filter_rtl_files`、`_streaming_valid_ready_rtl_files`、`_uart_fifo_loopback_rtl_files`、`_uart_rx_rtl_files`、`_uart_tx_rtl_files`、`_vision_defect_core_rtl_files`、`max` |
| `_timing_sdc` — `_timing_sdc(platform)` | function / [2177](../../../../agent/src/sr2fpga_agent/project_generator.py#L2177) | 无直接调用 |
| `_testbench` — `_testbench(request)` | function / [2182](../../../../agent/src/sr2fpga_agent/project_generator.py#L2182) | `ValueError`、`_alu_control_unit_testbench`、`_composed_batch_rl_accelerator_shell_testbench`、`_composed_dual_stream_join_testbench`、`_composed_event_counter_testbench`、`_composed_host_protocol_shell_testbench`、`_composed_policy_value_shell_testbench`、`_composed_replay_arbiter_shell_testbench`、`_composed_replay_sample_shell_testbench`、`_composed_rl_accelerator_shell_testbench`、`_composed_stream_accumulator_testbench`、`_composed_stream_fork_testbench`、`_composed_td_update_core_testbench`、`_composed_vector_mac_pipeline_testbench`、`_counter_testbench`、`_crc_stream_checker_testbench`、`_fifo_testbench`、`_fir_filter_testbench`、`_matched_filter_testbench`、`_matrix_vector_mac_testbench`、`_pattern_matcher_testbench`、`_peak_detector_testbench`、`_pulse_radar_signal_testbench`、`_pwm_controller_testbench`、`_ram_read_write_testbench`、`_simple_fsm_testbench`、`_sobel_threshold_testbench`、`_spi_master_testbench`、`_streaming_valid_ready_testbench`、`_uart_fifo_loopback_testbench`、`_uart_rx_testbench`、`_uart_tx_testbench`、`_vision_defect_core_testbench`、`_with_testbench_timeout`、`max` |
| `_with_testbench_timeout` — `_with_testbench_timeout(testbench, timeout_ns)` | function / [2254](../../../../agent/src/sr2fpga_agent/project_generator.py#L2254) | `testbench.replace` |
| `_predicted_qor` — `_predicted_qor(request, platform)` | function / [2271](../../../../agent/src/sr2fpga_agent/project_generator.py#L2271) | `_resource_shape`、`min` |
| `_interface` — `_interface(request, platform)` | function / [2301](../../../../agent/src/sr2fpga_agent/project_generator.py#L2301) | `common.update`、`max` |
| `_expected_behavior` — `_expected_behavior(request)` | function / [2937](../../../../agent/src/sr2fpga_agent/project_generator.py#L2937) | 无直接调用 |
| `_test_pass_means` — `_test_pass_means(request)` | function / [3044](../../../../agent/src/sr2fpga_agent/project_generator.py#L3044) | `_expected_behavior` |
| `_resource_shape` — `_resource_shape(request)` | function / [3048](../../../../agent/src/sr2fpga_agent/project_generator.py#L3048) | `ValueError`、`max` |

## `agent/src/sr2fpga_agent/prompts.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/prompts.py) · 1780 行 · SHA-256 `892d2a8341dee6e15274f8d1a7374dd63447e101bbbee11a3a6f3e998b5a926c`

> Prompt construction helpers for SR2FPGA generation and repair.

导入模块：`__future__`、`json`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.contract_skeleton`、`sr2fpga_agent.family_recipe`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.system_his_capabilities`、`sr2fpga_agent.system_his_schema`、`sr2fpga_agent.system_his_v12_checker`、`sr2fpga_agent.task_catalog`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_h2_lowerability_prompt_guidance` — `_h2_lowerability_prompt_guidance()` | function / [45](../../../../agent/src/sr2fpga_agent/prompts.py#L45) | `<dynamic>.join`、`sorted` |
| `_system_his_v12_messages` — `_system_his_v12_messages(request, platform, requirement_envelope, requirement_route, family_recipe_decision)` | function / [64](../../../../agent/src/sr2fpga_agent/prompts.py#L64) | `ValueError`、`_h2_lowerability_prompt_guidance`、`_requirement_prompt_guidance`、`_system_his_v12_task_guidance`、`build_request_requirement_envelope`、`effective_request_requirement`、`json.dumps`、`load_exact_task_family_aliases`、`recipe_task_type`、`requirement_envelope.requirement_trace_template`、`route_requirement`、`select_family_recipe` |
| `_with_system_his_retry_feedback` — `_with_system_his_retry_feedback(messages, error, previous_content, task_type, family_recipe_task_type, requirement_trace_template)` | function / [266](../../../../agent/src/sr2fpga_agent/prompts.py#L266) | `_h2_lowerability_prompt_guidance`、`_requirement_trace_pointer_guidance`、`_system_his_v12_retry_guidance`、`json.dumps`、`previous_content.strip` |
| `_requirement_prompt_guidance` — `_requirement_prompt_guidance(envelope, route)` | function / [341](../../../../agent/src/sr2fpga_agent/prompts.py#L341) | `_requirement_trace_pointer_guidance`、`envelope.requirement_trace_template`、`envelope.to_prompt_payload`、`json.dumps`、`route.to_dict` |
| `_requirement_trace_pointer_guidance` — `_requirement_trace_pointer_guidance()` | function / [376](../../../../agent/src/sr2fpga_agent/prompts.py#L376) | `_requirement_trace_value_guidance` |
| `_requirement_trace_value_guidance` — `_requirement_trace_value_guidance()` | function / [388](../../../../agent/src/sr2fpga_agent/prompts.py#L388) | 无直接调用 |
| `_system_his_v12_task_guidance` — `_system_his_v12_task_guidance(task_type)` | function / [409](../../../../agent/src/sr2fpga_agent/prompts.py#L409) | 无直接调用 |
| `_system_his_v12_retry_guidance` — `_system_his_v12_retry_guidance(task_type)` | function / [627](../../../../agent/src/sr2fpga_agent/prompts.py#L627) | 无直接调用 |
| `_his_project_messages` — `_his_project_messages(request, platform, system_his)` | function / [792](../../../../agent/src/sr2fpga_agent/prompts.py#L792) | `<dynamic>.join`、`<dynamic>.rstrip`、`_icarus_testbench_rules`、`build_contract_skeleton_project`、`json.dumps`、`skeleton_files.items`、`sorted` |
| `_with_his_project_retry_feedback` — `_with_his_project_retry_feedback(messages, error, previous_content)` | function / [877](../../../../agent/src/sr2fpga_agent/prompts.py#L877) | `previous_content.strip` |
| `_project_messages` — `_project_messages(request, platform)` | function / [909](../../../../agent/src/sr2fpga_agent/prompts.py#L909) | `<dynamic>.to_prompt_payload`、`_additional_project_file_entries`、`_icarus_testbench_rules`、`_manifest_source_records_example`、`_rtl_contract_for_task`、`build_request_requirement_envelope`、`json.dumps` |
| `_canonical_project_manifest_guidance` — `_canonical_project_manifest_guidance(project_name)` | function / [983](../../../../agent/src/sr2fpga_agent/prompts.py#L983) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`json.dumps`、`schema.validate` |
| `_frozen_direct_project_messages` — `_frozen_direct_project_messages(context, project_name)` | function / [1013](../../../../agent/src/sr2fpga_agent/prompts.py#L1013) | `_canonical_project_manifest_guidance`、`_icarus_testbench_rules`、`context.to_dict`、`json.dumps` |
| `_frozen_untyped_plan_messages` — `_frozen_untyped_plan_messages(context)` | function / [1051](../../../../agent/src/sr2fpga_agent/prompts.py#L1051) | `context.to_dict`、`json.dumps` |
| `_frozen_project_from_untyped_plan_messages` — `_frozen_project_from_untyped_plan_messages(context, plan_text, project_name)` | function / [1072](../../../../agent/src/sr2fpga_agent/prompts.py#L1072) | `_canonical_project_manifest_guidance`、`context.to_dict`、`json.dumps` |
| `_frozen_system_his_messages` — `_frozen_system_his_messages(context)` | function / [1112](../../../../agent/src/sr2fpga_agent/prompts.py#L1112) | `_frozen_h1_well_formedness_guidance`、`_frozen_pc_trace_structure_guidance`、`_frozen_requirement_trace_pointer_guidance`、`_h2_lowerability_prompt_guidance`、`context.to_dict`、`frozen_requirement_trace_template`、`json.dumps`、`load_registered_system_his_schema` |
| `_frozen_pc_trace_structure_guidance` — `_frozen_pc_trace_structure_guidance(trace, schema)` | function / [1149](../../../../agent/src/sr2fpga_agent/prompts.py#L1149) | `<dynamic>.join`、`json.dumps`、`sorted` |
| `_pc_state_ownership_example` — `_pc_state_ownership_example()` | function / [1167](../../../../agent/src/sr2fpga_agent/prompts.py#L1167) | 无直接调用 |
| `_frozen_requirement_trace_pointer_guidance` — `_frozen_requirement_trace_pointer_guidance()` | function / [1178](../../../../agent/src/sr2fpga_agent/prompts.py#L1178) | `_requirement_trace_value_guidance` |
| `_frozen_h1_well_formedness_guidance` — `_frozen_h1_well_formedness_guidance()` | function / [1191](../../../../agent/src/sr2fpga_agent/prompts.py#L1191) | `_pc_state_ownership_example`、`json.dumps` |
| `_frozen_his_skeleton_messages` — `_frozen_his_skeleton_messages(context, system_his, skeleton_files)` | function / [1252](../../../../agent/src/sr2fpga_agent/prompts.py#L1252) | `context.to_dict`、`json.dumps`、`skeleton_files.items`、`sorted` |
| `_frozen_his_free_project_messages` — `_frozen_his_free_project_messages(context, system_his, project_name)` | function / [1285](../../../../agent/src/sr2fpga_agent/prompts.py#L1285) | `_canonical_project_manifest_guidance`、`context.to_dict`、`json.dumps` |
| `_frozen_system_his_correction_messages` — `_frozen_system_his_correction_messages(context, system_his, failed_h_stage, diagnostics)` | function / [1327](../../../../agent/src/sr2fpga_agent/prompts.py#L1327) | `_frozen_h1_well_formedness_guidance`、`_frozen_pc_trace_structure_guidance`、`_frozen_requirement_trace_pointer_guidance`、`_h2_lowerability_prompt_guidance`、`context.to_dict`、`frozen_requirement_trace_template`、`json.dumps`、`load_registered_system_his_schema` |
| `_frozen_project_repair_messages` — `_frozen_project_repair_messages(context, project, failed_stage, diagnostics, editable_sources)` | function / [1386](../../../../agent/src/sr2fpga_agent/prompts.py#L1386) | `context.to_dict`、`json.dumps`、`project.files.items`、`sorted` |
| `_repair_messages` — `_repair_messages(project, diagnosis)` | function / [1435](../../../../agent/src/sr2fpga_agent/prompts.py#L1435) | `<dynamic>.join`、`_functional_mismatch_repair_rules`、`_icarus_testbench_rules`、`_project_task_type`、`_repair_edit_surface_rules`、`_repair_rtl_contract`、`_repair_system_his_prompt`、`_unused_parameter_repair_rules`、`json.dumps`、`project.files.items`、`set`、`sorted` |
| `_repair_edit_surface_rules` — `_repair_edit_surface_rules(project, diagnosis)` | function / [1505](../../../../agent/src/sr2fpga_agent/prompts.py#L1505) | `<dynamic>.endswith`、`<dynamic>.join`、`any`、`diagnosis.get`、`path.lower`、`project.files.items`、`resolve_project_manifest`、`rules.append`、`rules.extend`、`set`、`str` |
| `_icarus_testbench_rules` — `_icarus_testbench_rules()` | function / [1543](../../../../agent/src/sr2fpga_agent/prompts.py#L1543) | 无直接调用 |
| `_functional_mismatch_repair_rules` — `_functional_mismatch_repair_rules(diagnosis)` | function / [1570](../../../../agent/src/sr2fpga_agent/prompts.py#L1570) | `diagnosis.get`、`str` |
| `_unused_parameter_repair_rules` — `_unused_parameter_repair_rules(diagnosis)` | function / [1582](../../../../agent/src/sr2fpga_agent/prompts.py#L1582) | `<dynamic>.lower`、`diagnosis.get`、`str` |
| `_rtl_contract_for_task` — `_rtl_contract_for_task(task_type)` | function / [1593](../../../../agent/src/sr2fpga_agent/prompts.py#L1593) | `MULTIMODULE_RTL_EXAMPLES.get`、`json.dumps` |
| `_manifest_sources_example` — `_manifest_sources_example(task_type)` | function / [1610](../../../../agent/src/sr2fpga_agent/prompts.py#L1610) | `MULTIMODULE_RTL_EXAMPLES.get`、`json.dumps` |
| `_manifest_source_records_example` — `_manifest_source_records_example(task_type)` | function / [1614](../../../../agent/src/sr2fpga_agent/prompts.py#L1614) | `MULTIMODULE_RTL_EXAMPLES.get`、`json.dumps` |
| `_artifact_sources_example` — `_artifact_sources_example(system_his, task_type)` | function / [1623](../../../../agent/src/sr2fpga_agent/prompts.py#L1623) | `MULTIMODULE_RTL_EXAMPLES.get`、`all`、`artifacts.get`、`isinstance`、`system_his.get` |
| `_additional_project_file_entries` — `_additional_project_file_entries(task_type, leading_comma)` | function / [1633](../../../../agent/src/sr2fpga_agent/prompts.py#L1633) | `<dynamic>.join`、`MULTIMODULE_RTL_EXAMPLES.get`、`_additional_file_entries` |
| `_additional_file_entries` — `_additional_file_entries(sources)` | function / [1648](../../../../agent/src/sr2fpga_agent/prompts.py#L1648) | `<dynamic>.join` |
| `_repair_rtl_contract` — `_repair_rtl_contract(files, task_type)` | function / [1655](../../../../agent/src/sr2fpga_agent/prompts.py#L1655) | `len`、`resolve_project_manifest` |
| `_repair_sources_example` — `_repair_sources_example(files, task_type)` | function / [1670](../../../../agent/src/sr2fpga_agent/prompts.py#L1670) | `<dynamic>.endswith`、`json.dumps`、`list`、`path.lower`、`resolve_project_manifest`、`sorted` |
| `_additional_repair_file_entries` — `_additional_repair_file_entries(files, task_type)` | function / [1683](../../../../agent/src/sr2fpga_agent/prompts.py#L1683) | `_additional_file_entries`、`_repair_sources_example`、`all`、`isinstance`、`json.loads` |
| `_repair_system_his_prompt` — `_repair_system_his_prompt(files, project_name)` | function / [1693](../../../../agent/src/sr2fpga_agent/prompts.py#L1693) | `<dynamic>.strip`、`_project_system_his_schema`、`_system_his_contract`、`files.get` |
| `_system_his_contract` — `_system_his_contract(project_name)` | function / [1712](../../../../agent/src/sr2fpga_agent/prompts.py#L1712) | `json.dumps` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`load_system_his_backend_capabilities`

## `agent/src/sr2fpga_agent/provider_seed_capability.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py) · 598 行 · SHA-256 `1a7fede70ee40471ca81ab7a282f10ac759d3a4d83bf464fb64e9ab55e64c0ad`

> Development-only qualification of provider decoding-seed capability.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ProviderSeedProbeObservation` — `ProviderSeedProbeObservation` | class / [65](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L65) | 无直接调用 |
| `ProviderSeedProbeObservation.__post_init__` — `__post_init__(self)` | function / [75](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L75) | `ValueError`、`_is_sha256`、`getattr`、`isinstance`、`self.system_fingerprint.strip` |
| `write_development_provider_seed_capability` — `write_development_provider_seed_capability(store, provider_adapter, provider_model, gateway_base_url, protocol, documentation_status, documentation_snapshot_sha256, observations, documentation_source_url_sha256, documentation_review)` | function / [118](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L118) | `ValueError`、`_derive_fields`、`_normalized_documentation`、`_normalized_protocol`、`_observation_payload`、`_sha256_text`、`_validate_capability_payload`、`enumerate`、`gateway_base_url.rstrip`、`isinstance`、`len`、`payload.update`、`provider_model.strip`、`store.put_validated_json` |
| `load_development_provider_seed_capability` — `load_development_provider_seed_capability(path)` | function / [184](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L184) | `<dynamic>.read_text`、`Path`、`ValueError`、`_validate_capability_payload`、`json.loads` |
| `read_verified_provider_seed_capability` — `read_verified_provider_seed_capability(store, reference)` | function / [195](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L195) | `_validate_capability_payload`、`json.loads`、`store.read_verified` |
| `require_paired_confirmatory_seed_capability` — `require_paired_confirmatory_seed_capability(payload, provider_adapter, provider_model, gateway_base_url)` | function / [204](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L204) | `ValueError`、`_sha256_text`、`_validate_capability_payload`、`gateway_base_url.rstrip`、`isinstance`、`payload.get`、`review.get`、`str` |
| `_validate_capability_payload` — `_validate_capability_payload(payload)` | function / [233](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L233) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_derive_fields`、`_normalized_documentation`、`_normalized_observation_payload`、`_normalized_protocol`、`enumerate`、`len`、`payload.get` |
| `_derive_fields` — `_derive_fields(payload)` | function / [271](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L271) | `_classify`、`_normalized_observation_payload`、`_normalized_protocol`、`_sha256_json`、`all`、`enumerate`、`len`、`set`、`sorted`、`str`、`sum`、`token_axes.items`、`token_axes.values` |
| `_normalized_protocol` — `_normalized_protocol(protocol)` | function / [380](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L380) | `TypeError`、`ValueError`、`_is_sha256`、`float`、`isinstance`、`set` |
| `_normalized_documentation` — `_normalized_documentation(documentation_status, documentation_snapshot_sha256, documentation_source_url_sha256, documentation_review)` | function / [431](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L431) | `ValueError`、`_is_sha256`、`any`、`isinstance`、`set` |
| `_observation_payload` — `_observation_payload(call_index, observation)` | function / [476](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L476) | `TypeError`、`isinstance` |
| `_normalized_observation_payload` — `_normalized_observation_payload(call_index, raw)` | function / [494](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L494) | `ProviderSeedProbeObservation`、`ValueError`、`_observation_payload`、`isinstance`、`set` |
| `_classify` — `_classify(documentation_status, documentation_review, probe_status, exact_output_match, fingerprint_status)` | function / [527](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L527) | `documentation_review.get`、`isinstance`、`limitations.append`、`limitations.extend` |
| `_sha256_text` — `_sha256_text(value)` | function / [587](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L587) | `<dynamic>.hexdigest`、`hashlib.sha256`、`value.encode` |
| `_is_sha256` — `_is_sha256(value)` | function / [591](../../../../agent/src/sr2fpga_agent/provider_seed_capability.py#L591) | `int`、`isinstance`、`len`、`value.lower` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/provider_seed_probe.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/provider_seed_probe.py) · 310 行 · SHA-256 `3ce45927945ce8fc74b1004eb208a30773a697c49a55d454f8c09eb11dc0a527`

> Bounded development probe for provider decoding-seed repeatability.

导入模块：`__future__`、`argparse`、`hashlib`、`json`、`os`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.models`、`sr2fpga_agent.provider_seed_capability`、`sr2fpga_agent.providers`、`sr2fpga_agent.runner`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `main` — `main(argv)` | function / [26](../../../../agent/src/sr2fpga_agent/provider_seed_probe.py#L26) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`<dynamic>.read_bytes`、`<dynamic>.read_verified`、`ArtifactStore`、`OpenAICompatibleClient`、`OpenAICompatibleConfig`、`Path`、`ProviderSeedProbeObservation`、`SystemExit`、`ValueError`、`_PROBE_PROMPT.encode`、`_categorize_probe_exception`、`_consume_probe_context`、`_consume_probe_context_after_failure`、`_load_env_file`、`_sha256_json`、`argparse.ArgumentParser`、`args.documentation_snapshot.read_bytes`、`args.documentation_source_url.strip`、`client.chat`、`hashlib.sha256`、`isinstance`、`json.dumps`、`json.loads`、`len`、`observations.append`、`os.environ.get`、`output.encode`、`output.strip`、`parser.add_argument`、`parser.parse_args`、`print`、`range`、`reference.to_dict`、`str`、`usage.get`、`write_development_provider_seed_capability` |
| `_consume_probe_context` — `_consume_probe_context(client)` | function / [227](../../../../agent/src/sr2fpga_agent/provider_seed_probe.py#L227) | `ValueError`、`client.consume_response_provenance`、`client.consume_token_usage`、`fingerprint.strip`、`isinstance`、`provenance.get` |
| `_consume_probe_context_after_failure` — `_consume_probe_context_after_failure(client)` | function / [246](../../../../agent/src/sr2fpga_agent/provider_seed_probe.py#L246) | `client.consume_response_provenance`、`client.consume_token_usage`、`fingerprint.strip`、`isinstance`、`provenance.get` |
| `_categorize_probe_exception` — `_categorize_probe_exception(exc)` | function / [272](../../../../agent/src/sr2fpga_agent/provider_seed_probe.py#L272) | `_categorize_probe_failure`、`isinstance`、`str` |
| `_categorize_probe_failure` — `_categorize_probe_failure(message)` | function / [278](../../../../agent/src/sr2fpga_agent/provider_seed_probe.py#L278) | `any`、`message.lower`、`range` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `agent/src/sr2fpga_agent/providers.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/providers.py) · 1028 行 · SHA-256 `4bb73d3bea2cab9a0728a8663656b8b5c404edcbe942c75fb0ef1b7184219e2c`

> Generic OpenAI- and Anthropic-compatible LLM providers.

导入模块：`__future__`、`certifi`、`contextlib`、`dataclasses`、`hashlib`、`http.client`、`json`、`select`、`signal`、`ssl`、`threading`、`time`、`typing`、`urllib.error`、`urllib.request`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ModelOutputTruncated` — `ModelOutputTruncated` | class / [23](../../../../agent/src/sr2fpga_agent/providers.py#L23) | 无直接调用 |
| `ModelOutputTruncated.__init__` — `__init__(self, content)` | function / [27](../../../../agent/src/sr2fpga_agent/providers.py#L27) | `<dynamic>.__init__`、`super` |
| `ModelOutputEmpty` — `ModelOutputEmpty` | class / [32](../../../../agent/src/sr2fpga_agent/providers.py#L32) | 无直接调用 |
| `ModelOutputEmpty.__init__` — `__init__(self, content)` | function / [35](../../../../agent/src/sr2fpga_agent/providers.py#L35) | `<dynamic>.__init__`、`super` |
| `OpenAICompatibleConfig` — `OpenAICompatibleConfig` | class / [40](../../../../agent/src/sr2fpga_agent/providers.py#L40) | 无直接调用 |
| `OpenAICompatibleConfig.__post_init__` — `__post_init__(self)` | function / [57](../../../../agent/src/sr2fpga_agent/providers.py#L57) | `ValueError`、`_validate_requested_seed`、`isinstance`、`self.model.startswith` |
| `OpenAICompatibleClient` — `OpenAICompatibleClient` | class / [89](../../../../agent/src/sr2fpga_agent/providers.py#L89) | 无直接调用 |
| `OpenAICompatibleClient.__init__` — `__init__(self, config)` | function / [92](../../../../agent/src/sr2fpga_agent/providers.py#L92) | `threading.local` |
| `OpenAICompatibleClient.with_output_format` — `with_output_format(self, response_format)` | function / [96](../../../../agent/src/sr2fpga_agent/providers.py#L96) | `<dynamic>`、`replace`、`type` |
| `OpenAICompatibleClient.consume_response_details` — `consume_response_details(self)` | function / [99](../../../../agent/src/sr2fpga_agent/providers.py#L99) | `getattr` |
| `OpenAICompatibleClient._store_response_details` — `_store_response_details(self, details)` | function / [104](../../../../agent/src/sr2fpga_agent/providers.py#L104) | 无直接调用 |
| `OpenAICompatibleClient.consume_transport_attempt_count` — `consume_transport_attempt_count(self)` | function / [107](../../../../agent/src/sr2fpga_agent/providers.py#L107) | `getattr`、`hasattr` |
| `OpenAICompatibleClient.consume_token_usage` — `consume_token_usage(self)` | function / [115](../../../../agent/src/sr2fpga_agent/providers.py#L115) | `_present_token_usage`、`dict`、`getattr`、`hasattr`、`isinstance` |
| `OpenAICompatibleClient.consume_response_provenance` — `consume_response_provenance(self)` | function / [123](../../../../agent/src/sr2fpga_agent/providers.py#L123) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`getattr`、`hashlib.sha256`、`len`、`self.config.base_url.rstrip`、`set`、`sorted`、`tuple` |
| `OpenAICompatibleClient.chat` — `chat(self, messages)` | function / [170](../../../../agent/src/sr2fpga_agent/providers.py#L170) | `RuntimeError`、`_check_final_content`、`_completion_details`、`_openai_token_usage`、`_provider_system_fingerprint`、`_read_chat_completion_json`、`_read_responses_text`、`self._chat_payload`、`self._request_with_retries`、`self._reset_response_provenance`、`self._reset_token_usage`、`self._store_response_details`、`self._store_system_fingerprint`、`self._store_token_usage`、`str` |
| `OpenAICompatibleClient.stream_chat` — `stream_chat(self, messages)` | function / [196](../../../../agent/src/sr2fpga_agent/providers.py#L196) | `ModelOutputEmpty`、`_read_streaming_chat_content`、`_read_streaming_responses_content`、`result.strip`、`self._chat_payload`、`self._request_with_retries`、`self._reset_response_provenance`、`self._reset_token_usage` |
| `OpenAICompatibleClient._store_token_usage` — `_store_token_usage(self, usage)` | function / [225](../../../../agent/src/sr2fpga_agent/providers.py#L225) | `_accumulate_token_usage`、`getattr` |
| `OpenAICompatibleClient._reset_token_usage` — `_reset_token_usage(self)` | function / [233](../../../../agent/src/sr2fpga_agent/providers.py#L233) | 无直接调用 |
| `OpenAICompatibleClient._reset_response_provenance` — `_reset_response_provenance(self)` | function / [237](../../../../agent/src/sr2fpga_agent/providers.py#L237) | `set` |
| `OpenAICompatibleClient._store_system_fingerprint` — `_store_system_fingerprint(self, fingerprint)` | function / [242](../../../../agent/src/sr2fpga_agent/providers.py#L242) | `fingerprint.strip`、`isinstance`、`self._transport_state.system_fingerprints.add` |
| `OpenAICompatibleClient._chat_payload` — `_chat_payload(self, messages)` | function / [250](../../../../agent/src/sr2fpga_agent/providers.py#L250) | `_messages_for_model`、`_model_supports_json_response_format` |
| `OpenAICompatibleClient._request_with_retries` — `_request_with_retries(self, payload, reader)` | function / [279](../../../../agent/src/sr2fpga_agent/providers.py#L279) | `RuntimeError`、`getattr`、`max`、`range`、`self._request_once`、`self._store_token_usage`、`str`、`time.sleep` |
| `OpenAICompatibleClient._request_once` — `_request_once(self, payload, reader)` | function / [306](../../../../agent/src/sr2fpga_agent/providers.py#L306) | `<dynamic>.decode`、`<dynamic>.encode`、`RuntimeError`、`_TransientOpenAICompatibleError`、`_default_ssl_context`、`_response_read_deadline`、`exc.read`、`json.dumps`、`reader`、`self.config.base_url.rstrip`、`urllib.request.Request`、`urllib.request.urlopen` |
| `AnthropicCompatibleConfig` — `AnthropicCompatibleConfig` | class / [348](../../../../agent/src/sr2fpga_agent/providers.py#L348) | 无直接调用 |
| `AnthropicCompatibleConfig.__post_init__` — `__post_init__(self)` | function / [361](../../../../agent/src/sr2fpga_agent/providers.py#L361) | `_validate_requested_seed` |
| `AnthropicCompatibleClient` — `AnthropicCompatibleClient` | class / [365](../../../../agent/src/sr2fpga_agent/providers.py#L365) | 无直接调用 |
| `AnthropicCompatibleClient.__init__` — `__init__(self, config)` | function / [368](../../../../agent/src/sr2fpga_agent/providers.py#L368) | `threading.local` |
| `AnthropicCompatibleClient.consume_transport_attempt_count` — `consume_transport_attempt_count(self)` | function / [372](../../../../agent/src/sr2fpga_agent/providers.py#L372) | `getattr`、`hasattr` |
| `AnthropicCompatibleClient.consume_token_usage` — `consume_token_usage(self)` | function / [380](../../../../agent/src/sr2fpga_agent/providers.py#L380) | `_present_token_usage`、`dict`、`getattr`、`hasattr`、`isinstance` |
| `AnthropicCompatibleClient.consume_response_provenance` — `consume_response_provenance(self)` | function / [388](../../../../agent/src/sr2fpga_agent/providers.py#L388) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`getattr`、`hashlib.sha256`、`self.config.base_url.rstrip` |
| `AnthropicCompatibleClient.chat` — `chat(self, messages)` | function / [413](../../../../agent/src/sr2fpga_agent/providers.py#L413) | `_anthropic_messages_payload`、`_anthropic_token_usage`、`_read_anthropic_message_text`、`_read_chat_completion_json`、`self._request_with_retries`、`self._reset_response_provenance`、`self._reset_token_usage`、`self._store_token_usage` |
| `AnthropicCompatibleClient.stream_chat` — `stream_chat(self, messages)` | function / [423](../../../../agent/src/sr2fpga_agent/providers.py#L423) | `_anthropic_messages_payload`、`_read_anthropic_streaming_text`、`self._request_with_retries`、`self._reset_response_provenance`、`self._reset_token_usage` |
| `AnthropicCompatibleClient._store_token_usage` — `_store_token_usage(self, usage)` | function / [437](../../../../agent/src/sr2fpga_agent/providers.py#L437) | `_accumulate_token_usage`、`getattr` |
| `AnthropicCompatibleClient._reset_token_usage` — `_reset_token_usage(self)` | function / [445](../../../../agent/src/sr2fpga_agent/providers.py#L445) | 无直接调用 |
| `AnthropicCompatibleClient._reset_response_provenance` — `_reset_response_provenance(self)` | function / [449](../../../../agent/src/sr2fpga_agent/providers.py#L449) | 无直接调用 |
| `AnthropicCompatibleClient._request_with_retries` — `_request_with_retries(self, payload, reader)` | function / [452](../../../../agent/src/sr2fpga_agent/providers.py#L452) | `RuntimeError`、`getattr`、`max`、`range`、`self._request_once`、`self._store_token_usage`、`str`、`time.sleep` |
| `AnthropicCompatibleClient._request_once` — `_request_once(self, payload, reader)` | function / [479](../../../../agent/src/sr2fpga_agent/providers.py#L479) | `<dynamic>.decode`、`<dynamic>.encode`、`RuntimeError`、`_TransientOpenAICompatibleError`、`_default_ssl_context`、`_response_read_deadline`、`exc.read`、`json.dumps`、`reader`、`self.config.base_url.rstrip`、`urllib.request.Request`、`urllib.request.urlopen` |
| `_default_ssl_context` — `_default_ssl_context()` | function / [520](../../../../agent/src/sr2fpga_agent/providers.py#L520) | `certifi.where`、`ssl.create_default_context` |
| `_TransientOpenAICompatibleError` — `_TransientOpenAICompatibleError` | class / [531](../../../../agent/src/sr2fpga_agent/providers.py#L531) | 无直接调用 |
| `_response_read_deadline` — `_response_read_deadline(timeout_seconds)` | function / [536](../../../../agent/src/sr2fpga_agent/providers.py#L536) | `hasattr`、`signal.getsignal`、`signal.setitimer`、`signal.signal`、`threading.current_thread`、`threading.main_thread` |
| `_response_read_deadline._raise_timeout` — `_raise_timeout(_signum, _frame)` | function / [541](../../../../agent/src/sr2fpga_agent/providers.py#L541) | `TimeoutError` |
| `_completion_details` — `_completion_details(data, content)` | function / [554](../../../../agent/src/sr2fpga_agent/providers.py#L554) | `_nonnegative_int`、`choice.get`、`data.get`、`isinstance`、`token_details.get`、`usage.get` |
| `_check_final_content` — `_check_final_content(content, finish_reason)` | function / [568](../../../../agent/src/sr2fpga_agent/providers.py#L568) | `ModelOutputEmpty`、`ModelOutputTruncated`、`content.strip` |
| `_model_supports_json_response_format` — `_model_supports_json_response_format(model)` | function / [575](../../../../agent/src/sr2fpga_agent/providers.py#L575) | `model.startswith` |
| `_validate_requested_seed` — `_validate_requested_seed(seed)` | function / [579](../../../../agent/src/sr2fpga_agent/providers.py#L579) | `ValueError`、`isinstance` |
| `_provider_system_fingerprint` — `_provider_system_fingerprint(data)` | function / [586](../../../../agent/src/sr2fpga_agent/providers.py#L586) | `isinstance` |
| `_messages_for_model` — `_messages_for_model(model, messages)` | function / [592](../../../../agent/src/sr2fpga_agent/providers.py#L592) | `<dynamic>.get`、`<dynamic>.join`、`first.get`、`message.get`、`model.startswith`、`rewritten.append`、`str`、`system_parts.append` |
| `_read_chat_completion_json` — `_read_chat_completion_json(response, timeout_seconds)` | function / [617](../../../../agent/src/sr2fpga_agent/providers.py#L617) | `<dynamic>.decode`、`_read_response_body`、`json.loads` |
| `_read_responses_text` — `_read_responses_text(data)` | function / [621](../../../../agent/src/sr2fpga_agent/providers.py#L621) | `<dynamic>.join`、`RuntimeError`、`chunks.append`、`data.get`、`isinstance`、`item.get`、`part.get`、`str` |
| `_read_response_body` — `_read_response_body(response, timeout_seconds)` | function / [644](../../../../agent/src/sr2fpga_agent/providers.py#L644) | `<dynamic>.join`、`_TransientOpenAICompatibleError`、`chunks.append`、`response.read`、`time.monotonic` |
| `_anthropic_messages_payload` — `_anthropic_messages_payload(config, messages)` | function / [657](../../../../agent/src/sr2fpga_agent/providers.py#L657) | `<dynamic>.join`、`anthropic_messages.append`、`message.get`、`str`、`system_parts.append` |
| `_read_anthropic_message_text` — `_read_anthropic_message_text(data)` | function / [683](../../../../agent/src/sr2fpga_agent/providers.py#L683) | `<dynamic>.join`、`RuntimeError`、`chunks.append`、`isinstance`、`item.get`、`str` |
| `_openai_token_usage` — `_openai_token_usage(data)` | function / [700](../../../../agent/src/sr2fpga_agent/providers.py#L700) | `_nonnegative_int`、`data.get`、`details.get`、`isinstance`、`usage.get` |
| `_anthropic_token_usage` — `_anthropic_token_usage(data)` | function / [727](../../../../agent/src/sr2fpga_agent/providers.py#L727) | `_nonnegative_int`、`data.get`、`isinstance`、`usage.get` |
| `_nonnegative_int` — `_nonnegative_int(value)` | function / [749](../../../../agent/src/sr2fpga_agent/providers.py#L749) | `isinstance` |
| `_read_anthropic_streaming_text` — `_read_anthropic_streaming_text(response, timeout_seconds, usage_sink)` | function / [755](../../../../agent/src/sr2fpga_agent/providers.py#L755) | `<dynamic>.join`、`<dynamic>.strip`、`RuntimeError`、`_TransientOpenAICompatibleError`、`_anthropic_token_usage`、`_merge_token_usage`、`_present_token_usage`、`_read_streaming_line`、`chunks.append`、`delta.get`、`error.get`、`event.get`、`isinstance`、`json.loads`、`line.removeprefix`、`line.startswith`、`raw_line.decode`、`str`、`time.monotonic`、`usage_sink` |
| `_read_streaming_chat_content` — `_read_streaming_chat_content(response, timeout_seconds, usage_sink, fingerprint_sink, response_details_sink)` | function / [813](../../../../agent/src/sr2fpga_agent/providers.py#L813) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.strip`、`ModelOutputTruncated`、`RuntimeError`、`_TransientOpenAICompatibleError`、`_completion_details`、`_merge_token_usage`、`_openai_token_usage`、`_present_token_usage`、`_provider_system_fingerprint`、`_read_streaming_line`、`chunks.append`、`delta.get`、`event.get`、`fingerprint_sink`、`isinstance`、`json.loads`、`line.removeprefix`、`line.startswith`、`raw_line.decode`、`response_details_sink`、`str`、`time.monotonic`、`usage_sink` |
| `_read_streaming_responses_content` — `_read_streaming_responses_content(response, timeout_seconds, usage_sink)` | function / [890](../../../../agent/src/sr2fpga_agent/providers.py#L890) | `<dynamic>.join`、`<dynamic>.strip`、`RuntimeError`、`_TransientOpenAICompatibleError`、`_merge_token_usage`、`_openai_token_usage`、`_present_token_usage`、`_read_streaming_line`、`chunks.append`、`event.get`、`isinstance`、`json.loads`、`line.removeprefix`、`line.startswith`、`raw_line.decode`、`str`、`time.monotonic`、`usage_sink` |
| `_merge_token_usage` — `_merge_token_usage(target, update)` | function / [943](../../../../agent/src/sr2fpga_agent/providers.py#L943) | `update.items` |
| `_present_token_usage` — `_present_token_usage(usage)` | function / [954](../../../../agent/src/sr2fpga_agent/providers.py#L954) | `any`、`usage.values` |
| `_accumulate_token_usage` — `_accumulate_token_usage(existing, update, has_existing_attempt)` | function / [960](../../../../agent/src/sr2fpga_agent/providers.py#L960) | `existing.get`、`isinstance`、`update.get` |
| `_read_streaming_line` — `_read_streaming_line(response, timeout_seconds, started_at)` | function / [1002](../../../../agent/src/sr2fpga_agent/providers.py#L1002) | `_TransientOpenAICompatibleError`、`_response_fileno`、`response.readline`、`select.select`、`time.monotonic` |
| `_response_fileno` — `_response_fileno(response)` | function / [1014](../../../../agent/src/sr2fpga_agent/providers.py#L1014) | `getattr`、`hasattr`、`int`、`response.fileno`、`sock.fileno` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`object`

## `agent/src/sr2fpga_agent/public_boundary.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/public_boundary.py) · 102 行 · SHA-256 `2c31c63d77820099cb09b14f823310e817938227c6609b8a879cfdef5a74a696`

> Scoped checks of the development public boundary, shared by all methods.

导入模块：`__future__`、`sr2fpga_agent.contract_registry`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `check_public_boundary_ports` — `check_public_boundary_ports(payload, registry)` | function / [14](../../../../agent/src/sr2fpga_agent/public_boundary.py#L14) | `<dynamic>.join`、`<dynamic>.validate`、`ContractRegistry`、`errors.append`、`registry.load_schema`、`set`、`sorted`、`tuple` |
| `check_public_boundary_domains` — `check_public_boundary_domains(payload, registry)` | function / [55](../../../../agent/src/sr2fpga_agent/public_boundary.py#L55) | `<dynamic>.join`、`<dynamic>.validate`、`ContractRegistry`、`errors.append`、`registry.load_schema`、`set`、`sorted`、`tuple` |

## `agent/src/sr2fpga_agent/public_evaluator.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/public_evaluator.py) · 961 行 · SHA-256 `311a1451d9376137f68bba01b23b559d0f690ad9958e1541ed343c5cfa4f56ab`

> Development-only terminal public-evaluator boundary and shadow runner.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.public_l2_harness`、`sr2fpga_agent.rtl_identifier_checker`、`sr2fpga_agent.tool_runner`、`typing`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PublicEvaluatorInput` — `PublicEvaluatorInput` | class / [37](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L37) | 无直接调用 |
| `AttemptPublicEvaluatorInput` — `AttemptPublicEvaluatorInput` | class / [46](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L46) | 无直接调用 |
| `PublicEvaluatorResult` — `PublicEvaluatorResult` | class / [55](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L55) | 无直接调用 |
| `DevelopmentPublicOutcome` — `DevelopmentPublicOutcome` | class / [65](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L65) | 无直接调用 |
| `DevelopmentTerminalPublicEvaluationAuthority` — `DevelopmentTerminalPublicEvaluationAuthority` | class / [70](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L70) | 无直接调用 |
| `DevelopmentTerminalPublicEvaluationAuthority.__init__` — `__init__(self, candidate_store, evaluator_store, evaluator)` | function / [77](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L77) | `ValueError`、`candidate_store.root.resolve`、`evaluator_store.root.resolve` |
| `DevelopmentTerminalPublicEvaluationAuthority.evaluate_once` — `evaluate_once(self, terminal_candidate_ref, public_contract_sha256, public_profile_sha256, tool_environment_policy_sha256)` | function / [89](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L89) | `<dynamic>.hexdigest`、`DevelopmentPublicOutcome`、`PublicEvaluatorInput`、`PublicEvaluatorResult`、`_canonical_json`、`_public_l2_harness_evidence`、`_read_terminal`、`_require_sha256`、`_stage`、`_validate_result`、`all`、`dict`、`hashlib.sha256`、`self._candidate_store.put_validated_json`、`self._candidate_store.read_sealed_project`、`self._evaluator`、`self._evaluator_store.consume_once`、`self._evaluator_store.put_blob`、`set`、`sorted`、`str`、`type` |
| `DevelopmentTerminalPublicEvaluationAuthority.candidate_store` — `candidate_store(self)` | function / [199](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L199) | 无直接调用 |
| `DevelopmentTerminalPublicEvaluationAuthority.evaluator_store` — `evaluator_store(self)` | function / [203](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L203) | 无直接调用 |
| `DevelopmentAttemptPublicEvaluationAuthority` — `DevelopmentAttemptPublicEvaluationAuthority` | class / [207](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L207) | 无直接调用 |
| `DevelopmentAttemptPublicEvaluationAuthority.__init__` — `__init__(self, candidate_store, evaluator_store, evaluator, authoritative)` | function / [210](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L210) | `ValueError`、`candidate_store.root.resolve`、`evaluator_store.root.resolve` |
| `DevelopmentAttemptPublicEvaluationAuthority.evaluate_once` — `evaluate_once(self, public_evaluation_candidate_ref, public_contract_sha256, public_profile_sha256, tool_environment_policy_sha256)` | function / [225](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L225) | `<dynamic>.hexdigest`、`AttemptPublicEvaluatorInput`、`DevelopmentPublicOutcome`、`PublicEvaluatorResult`、`_canonical_json`、`_public_l2_harness_evidence`、`_read_public_evaluation_candidate`、`_require_sha256`、`_stage`、`_validate_result`、`all`、`candidate.get`、`dict`、`hashlib.sha256`、`self._authoritative_outcome`、`self._candidate_store.put_validated_json`、`self._candidate_store.read_public_evaluation_candidate`、`self._evaluator`、`self._evaluator_store.consume_once`、`self._evaluator_store.put_blob`、`set`、`sorted`、`str`、`type` |
| `DevelopmentAttemptPublicEvaluationAuthority._authoritative_outcome` — `_authoritative_outcome(self, candidate, candidate_ref, ledger_ref, public_contract_sha256, public_profile_sha256, tool_environment_policy_sha256, result, complete_project, public_acceptance)` | function / [359](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L359) | `<dynamic>.hexdigest`、`DevelopmentPublicOutcome`、`_authoritative_repair_diagnosis`、`_canonical_json`、`_public_l2_harness_evidence`、`dict`、`hashlib.sha256`、`self._candidate_store.put_validated_json`、`set`、`sorted` |
| `DevelopmentAttemptPublicEvaluationAuthority.authoritative` — `authoritative(self)` | function / [419](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L419) | 无直接调用 |
| `DevelopmentAttemptPublicEvaluationAuthority.candidate_store` — `candidate_store(self)` | function / [423](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L423) | 无直接调用 |
| `DevelopmentAttemptPublicEvaluationAuthority.evaluator_store` — `evaluator_store(self)` | function / [427](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L427) | 无直接调用 |
| `DevelopmentPublicToolEvaluator` — `DevelopmentPublicToolEvaluator` | class / [431](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L431) | 无直接调用 |
| `DevelopmentPublicToolEvaluator.__init__` — `__init__(self, evaluator_workspace_root, command_runner, trusted_public_l2_harness)` | function / [434](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L434) | `CommandRunner`、`Path` |
| `DevelopmentPublicToolEvaluator.__call__` — `__call__(self, evaluator_input, evaluation_id)` | function / [445](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L445) | `<dynamic>.hexdigest`、`Path`、`PublicEvaluatorResult`、`_stage`、`_tool_infrastructure_reason`、`_trusted_public_l2_reserved_path_collisions`、`asdict`、`build_yosys_script`、`candidate_simulation_violations`、`check_project_package_l0`、`check_rtl_identifiers`、`diagnostics.append`、`diagnostics.extend`、`evaluation_id.encode`、`hashlib.sha256`、`list`、`path.split`、`project.files.items`、`resolve_project_manifest`、`self._command_runner.run`、`self._run_trusted_public_l2`、`self._trusted_public_l2_harness.public_evidence`、`set`、`sorted`、`str`、`target.parent.mkdir`、`target.write_text`、`tuple`、`type`、`unavailable_public_l2_harness_evidence`、`validate_project_relative_path`、`workspace.mkdir` |
| `DevelopmentPublicToolEvaluator._run_trusted_public_l2` — `_run_trusted_public_l2(self, workspace, sources, stage_outcomes, diagnostics, raw)` | function / [632](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L632) | `<dynamic>.as_posix`、`Path`、`ValueError`、`_stage`、`_tool_infrastructure_reason`、`asdict`、`diagnostics.append`、`instrument_trusted_completion`、`item.path.split`、`self._command_runner.run`、`simulation.stdout.splitlines`、`target.parent.mkdir`、`target.relative_to`、`target.write_text`、`trusted_paths.append`、`uuid.uuid4` |
| `_trusted_public_l2_reserved_path_collisions` — `_trusted_public_l2_reserved_path_collisions(project_files)` | function / [707](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L707) | `collisions.append`、`path.startswith`、`sorted`、`tuple`、`validate_project_relative_path` |
| `_read_verified_public_outcome` — `_read_verified_public_outcome(store, reference, contract_key, id_prefix, label, registry)` | function / [723](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L723) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_canonical_json`、`_validate_outcome_harness_binding`、`contract.validate`、`hashlib.sha256`、`json.loads`、`payload.items`、`store.read_verified` |
| `read_verified_development_public_outcome` — `read_verified_development_public_outcome(store, reference, registry)` | function / [750](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L750) | `_read_verified_public_outcome` |
| `read_verified_development_attempt_public_outcome` — `read_verified_development_attempt_public_outcome(store, reference, registry)` | function / [766](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L766) | `_read_verified_public_outcome` |
| `read_verified_development_authoritative_attempt_public_outcome` — `read_verified_development_authoritative_attempt_public_outcome(store, reference, registry)` | function / [782](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L782) | `_read_verified_public_outcome` |
| `_read_terminal` — `_read_terminal(store, reference)` | function / [798](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L798) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`json.loads`、`store.read_verified` |
| `_read_public_evaluation_candidate` — `_read_public_evaluation_candidate(store, reference)` | function / [809](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L809) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`json.loads`、`payload.get`、`store.read_verified` |
| `_validate_result` — `_validate_result(result)` | function / [827](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L827) | `TypeError`、`ValueError`、`_public_l2_harness_evidence`、`_validate_public_l2_harness_evidence`、`isinstance`、`re.fullmatch`、`result.stage_outcomes.items`、`set` |
| `_public_l2_harness_evidence` — `_public_l2_harness_evidence(result)` | function / [864](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L864) | `dict`、`unavailable_public_l2_harness_evidence` |
| `_validate_public_l2_harness_evidence` — `_validate_public_l2_harness_evidence(evidence)` | function / [872](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L872) | `ValueError`、`_require_sha256`、`isinstance`、`re.fullmatch`、`set`、`unavailable_public_l2_harness_evidence` |
| `_validate_outcome_harness_binding` — `_validate_outcome_harness_binding(payload)` | function / [898](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L898) | `ValueError`、`_validate_public_l2_harness_evidence`、`isinstance`、`payload.get` |
| `_authoritative_repair_diagnosis` — `_authoritative_repair_diagnosis(result, complete_project)` | function / [912](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L912) | `set`、`sorted`、`str` |
| `_tool_infrastructure_reason` — `_tool_infrastructure_reason(result)` | function / [939](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L939) | 无直接调用 |
| `_stage` — `_stage(status, reason)` | function / [947](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L947) | 无直接调用 |
| `_require_sha256` — `_require_sha256(label, value)` | function / [951](../../../../agent/src/sr2fpga_agent/public_evaluator.py#L951) | `ValueError`、`int`、`isinstance`、`len`、`value.lower` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/public_l2_harness.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/public_l2_harness.py) · 241 行 · SHA-256 `6e5ec31b357ba7c59c9eb211fc1816797657f67399664a5191cacd8f1283fe74`

> Evaluator-owned trusted public L2 harness loading and commitments.

导入模块：`__future__`、`collections.abc`、`dataclasses`、`hashlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PublicL2HarnessError` — `PublicL2HarnessError` | class / [17](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L17) | 无直接调用 |
| `_hdl_tokens` — `_hdl_tokens(content)` | function / [34](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L34) | `<dynamic>.startswith`、`_HDL_TOKEN.finditer`、`token.group` |
| `candidate_simulation_violations` — `candidate_simulation_violations(files, sources, trusted_sources)` | function / [41](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L41) | `<dynamic>.group`、`<dynamic>.removeprefix`、`<dynamic>.startswith`、`ValueError`、`_hdl_tokens`、`declaration.append`、`enumerate`、`include.endswith`、`include.startswith`、`item.group`、`len`、`list`、`pending.append`、`pending.pop`、`re.fullmatch`、`seen.add`、`set`、`sorted`、`token.group`、`trusted_names.add`、`tuple`、`validate_project_relative_path`、`value.startswith`、`violations.add` |
| `instrument_trusted_completion` — `instrument_trusted_completion(content, marker, paths)` | function / [105](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L105) | `PublicL2HarnessError`、`_hdl_tokens`、`edits.append`、`enumerate`、`include.end`、`include.group`、`include.start`、`item.end`、`item.group`、`len`、`next`、`sorted`、`token.group`、`token.start` |
| `TrustedPublicL2HarnessFile` — `TrustedPublicL2HarnessFile` | class / [128](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L128) | 无直接调用 |
| `DevelopmentTrustedPublicL2Harness` — `DevelopmentTrustedPublicL2Harness` | class / [135](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L135) | 无直接调用 |
| `DevelopmentTrustedPublicL2Harness.public_evidence` — `public_evidence(self)` | function / [144](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L144) | 无直接调用 |
| `load_development_public_l2_harness` — `load_development_public_l2_harness(manifest_path, registry)` | function / [154](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L154) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.resolve`、`<dynamic>.validate`、`ContractRegistry`、`DevelopmentTrustedPublicL2Harness`、`Path`、`PublicL2HarnessError`、`TrustedPublicL2HarnessFile`、`_canonical_json`、`content_bytes.decode`、`files.append`、`hashlib.sha256`、`isinstance`、`json.loads`、`path.parent.resolve`、`path.read_bytes`、`relative.split`、`seen.add`、`set`、`source.read_bytes`、`source.relative_to`、`str`、`tuple`、`validate_project_relative_path` |
| `unavailable_public_l2_harness_evidence` — `unavailable_public_l2_harness_evidence()` | function / [232](../../../../agent/src/sr2fpga_agent/public_l2_harness.py#L232) | 无直接调用 |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`、`re.compile`

## `agent/src/sr2fpga_agent/recorder.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/recorder.py) · 1376 行 · SHA-256 `65d62b3fe6df75460eccc9557dcaf141d3de71dc6f505157abcc331444051da0`

> Dataset recording utilities for SR2FPGA generated samples.

导入模块：`__future__`、`dataclasses`、`json`、`pathlib`、`re`、`shutil`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.system_his_compatibility`、`typing`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `AttemptRecord` — `AttemptRecord` | class / [24](../../../../agent/src/sr2fpga_agent/recorder.py#L24) | 无直接调用 |
| `DatasetRecorder` — `DatasetRecorder` | class / [35](../../../../agent/src/sr2fpga_agent/recorder.py#L35) | 无直接调用 |
| `DatasetRecorder.__init__` — `__init__(self, dataset_root)` | function / [38](../../../../agent/src/sr2fpga_agent/recorder.py#L38) | 无直接调用 |
| `DatasetRecorder.start_sample` — `start_sample(self, sample_id, requirement, platform_profile, metadata)` | function / [41](../../../../agent/src/sr2fpga_agent/recorder.py#L41) | `<dynamic>.write_text`、`_write_json`、`asdict`、`requirement.rstrip`、`sample_dir.mkdir`、`validate_sample_id` |
| `DatasetRecorder.write_attempt` — `write_attempt(self, sample_id, attempt)` | function / [57](../../../../agent/src/sr2fpga_agent/recorder.py#L57) | `<dynamic>.write_text`、`_write_json`、`_write_project`、`asdict`、`attempt.patch_metadata.to_dict`、`attempt.tool_results.items`、`eval_dir.mkdir`、`validate_sample_id` |
| `DatasetRecorder.update_patch_metadata` — `update_patch_metadata(self, sample_id, attempt_id, patch_metadata)` | function / [79](../../../../agent/src/sr2fpga_agent/recorder.py#L79) | `_write_json`、`patch_metadata.to_dict`、`validate_sample_id` |
| `DatasetRecorder.write_final` — `write_final(self, sample_id, generated_project, labels, measured_qor, tool_versions, trajectory)` | function / [86](../../../../agent/src/sr2fpga_agent/recorder.py#L86) | `_has_nonempty_text`、`_read_metadata`、`_system_his_episode`、`_training_view_eligibility`、`_write_json`、`_write_project`、`eval_dir.mkdir`、`sorted`、`validate_sample_id` |
| `DatasetRecorder.export_training_views` — `export_training_views(self, output_dir)` | function / [125](../../../../agent/src/sr2fpga_agent/recorder.py#L125) | `<dynamic>.strip`、`_episode_without_verification`、`_file_origin_from_episode`、`_is_independent_oracle_episode`、`_read_episode`、`_read_labels`、`_read_metadata`、`_read_project_files`、`_sanitize_training_payload`、`_source_episode_id`、`_training_view_eligibility`、`_write_json`、`_write_jsonl`、`attempts_dir.exists`、`attempts_dir.iterdir`、`bool`、`diagnosis_path.exists`、`diagnosis_path.read_text`、`diagnosis_rows.append`、`dict`、`eligibility_rows.append`、`final_project_dir.exists`、`his_path.exists`、`his_path.read_text`、`his_project_rows.append`、`json.loads`、`measured_qor_path.exists`、`measured_qor_path.read_text`、`measured_qor_rows.append`、`output_dir.mkdir`、`patch_metadata_path.exists`、`patch_metadata_path.read_text`、`patch_path.exists`、`patch_path.read_text`、`patch_rows.append`、`path.is_dir`、`predicted_qor_path.exists`、`predicted_qor_path.read_text`、`predicted_qor_rows.append`、`requirement_file_rows.append`、`requirement_path.exists`、`requirement_path.read_text`、`requirement_project_rows.append`、`requirement_rows.append`、`self.dataset_root.iterdir`、`sorted` |
| `_write_project` — `_write_project(project_dir, project, replace_existing)` | function / [310](../../../../agent/src/sr2fpga_agent/recorder.py#L310) | `project.files.items`、`project_dir.exists`、`project_file_target`、`shutil.rmtree`、`target.parent.mkdir`、`target.write_text` |
| `_write_json` — `_write_json(path, payload)` | function / [319](../../../../agent/src/sr2fpga_agent/recorder.py#L319) | `json.dumps`、`path.parent.mkdir`、`path.write_text` |
| `_write_jsonl` — `_write_jsonl(path, rows)` | function / [324](../../../../agent/src/sr2fpga_agent/recorder.py#L324) | `json.dumps`、`output.write`、`path.with_name`、`temp_path.exists`、`temp_path.open`、`temp_path.replace`、`temp_path.unlink`、`uuid.uuid4` |
| `_has_nonempty_text` — `_has_nonempty_text(path)` | function / [336](../../../../agent/src/sr2fpga_agent/recorder.py#L336) | `<dynamic>.strip`、`bool`、`path.is_file`、`path.read_text` |
| `_episode_without_verification` — `_episode_without_verification(episode)` | function / [340](../../../../agent/src/sr2fpga_agent/recorder.py#L340) | `dict`、`result.pop` |
| `_system_his_episode` — `_system_his_episode(sample_id, generated_project, labels, measured_qor, trajectory)` | function / [346](../../../../agent/src/sr2fpga_agent/recorder.py#L346) | `_data_release_tiers`、`_derived_training_views_metadata`、`_empty_req_his_fidelity`、`_his_validation_from_labels`、`_is_independent_oracle_episode`、`_merge_project_episode_metadata`、`_project_episode_metadata`、`_read_project_json`、`_sanitize_oracle_profile`、`_verification_episode_metadata`、`_verification_without_label_mismatches`、`dict`、`episode.get`、`episode.setdefault` |
| `_source_episode_id` — `_source_episode_id(sample_id, episode)` | function / [377](../../../../agent/src/sr2fpga_agent/recorder.py#L377) | `<dynamic>.strip`、`episode.get`、`str` |
| `_training_view_eligibility` — `_training_view_eligibility(sample_id, requirement_present, system_his_present, final_file_paths, metadata, episode, labels, decision_phase)` | function / [382](../../../../agent/src/sr2fpga_agent/recorder.py#L382) | `<dynamic>.strip`、`_automatic_pass_credit`、`_budget_compliance`、`_contains_contract_version`、`_explicit_compliance`、`_explicit_vpp_l3`、`_file_origin_from_episode`、`_his_positive_reasons`、`_patch_credit_is_incomplete`、`_source_episode_id`、`_training_h_stage_applicability`、`_verified_project_reasons`、`_view_eligibility`、`any`、`bool`、`boundary.get`、`common_reasons.append`、`file_origins.values`、`isinstance`、`labels.get`、`metadata.get`、`str` |
| `_view_eligibility` — `_view_eligibility(reasons)` | function / [506](../../../../agent/src/sr2fpga_agent/recorder.py#L506) | `dict.fromkeys`、`list` |
| `_contains_contract_version` — `_contains_contract_version(value, contract_version)` | function / [516](../../../../agent/src/sr2fpga_agent/recorder.py#L516) | `_contains_contract_version`、`any`、`isinstance`、`value.get`、`value.values` |
| `_automatic_pass_credit` — `_automatic_pass_credit(labels, episode)` | function / [528](../../../../agent/src/sr2fpga_agent/recorder.py#L528) | `episode.get`、`final.get`、`isinstance`、`labels.get`、`measurement.get` |
| `_explicit_compliance` — `_explicit_compliance(labels, episode, name)` | function / [538](../../../../agent/src/sr2fpga_agent/recorder.py#L538) | `episode.get`、`isinstance`、`labels.get`、`section.get`、`values.append` |
| `_explicit_vpp_l3` — `_explicit_vpp_l3(labels, episode)` | function / [560](../../../../agent/src/sr2fpga_agent/recorder.py#L560) | `episode.get`、`isinstance`、`labels.get`、`values.append`、`verification.get`、`vpp.get` |
| `_budget_compliance` — `_budget_compliance(labels, episode, metadata)` | function / [579](../../../../agent/src/sr2fpga_agent/recorder.py#L579) | `_explicit_compliance`、`all`、`call.get`、`enumerate`、`isinstance`、`len`、`metadata.get`、`sum`、`summary.get` |
| `_patch_credit_is_incomplete` — `_patch_credit_is_incomplete(episode)` | function / [616](../../../../agent/src/sr2fpga_agent/recorder.py#L616) | `any`、`episode.get`、`isinstance`、`patch.get` |
| `_training_h_stage_applicability` — `_training_h_stage_applicability(metadata, episode, system_his_present)` | function / [626](../../../../agent/src/sr2fpga_agent/recorder.py#L626) | `<dynamic>.replace`、`<dynamic>.split`、`<dynamic>.strip`、`<dynamic>.upper`、`episode.get`、`h0.get`、`int`、`isinstance`、`metadata.get`、`method_condition.replace`、`method_match.group`、`re.fullmatch`、`str`、`validation.get` |
| `_his_positive_reasons` — `_his_positive_reasons(episode)` | function / [650](../../../../agent/src/sr2fpga_agent/recorder.py#L650) | `episode.get`、`h3.get`、`isinstance`、`reasons.append`、`record.get`、`validation.get` |
| `_verified_project_reasons` — `_verified_project_reasons(episode, vpp_l3)` | function / [667](../../../../agent/src/sr2fpga_agent/recorder.py#L667) | `episode.get`、`hidden.get`、`isinstance`、`l2.get`、`public.get`、`reasons.append`、`reasons.extend`、`record.get`、`verification.get` |
| `_file_origin_from_episode` — `_file_origin_from_episode(episode, path)` | function / [698](../../../../agent/src/sr2fpga_agent/recorder.py#L698) | `episode.get`、`files.get`、`isinstance`、`metadata.get`、`project.get` |
| `_sanitize_oracle_profile` — `_sanitize_oracle_profile(value)` | function / [717](../../../../agent/src/sr2fpga_agent/recorder.py#L717) | `_SAFE_SHA256.fullmatch`、`_is_non_negative_int`、`_safe_token`、`_sanitize_oracle_fields`、`class_status.items`、`isinstance`、`raw.get`、`raw_scenario.get`、`scenario_counts.items`、`scenarios.append` |
| `_sanitize_oracle_fields` — `_sanitize_oracle_fields(value)` | function / [801](../../../../agent/src/sr2fpga_agent/recorder.py#L801) | `_is_non_negative_int`、`_safe_token`、`fields.append`、`isinstance`、`raw.get` |
| `_safe_token` — `_safe_token(value)` | function / [823](../../../../agent/src/sr2fpga_agent/recorder.py#L823) | `_SAFE_TOKEN.fullmatch`、`isinstance` |
| `_is_non_negative_int` — `_is_non_negative_int(value)` | function / [827](../../../../agent/src/sr2fpga_agent/recorder.py#L827) | `isinstance` |
| `_sanitize_training_payload` — `_sanitize_training_payload(value, withheld, independent_oracle, _scope)` | function / [882](../../../../agent/src/sr2fpga_agent/recorder.py#L882) | `<dynamic>.replace`、`_is_raw_training_key`、`_safe_diagnostic_scalar`、`_safe_token`、`_sanitize_training_payload`、`isinstance`、`key.lower`、`str`、`value.get`、`value.items` |
| `_safe_diagnostic_scalar` — `_safe_diagnostic_scalar(key, value, scope)` | function / [955](../../../../agent/src/sr2fpga_agent/recorder.py#L955) | `_is_non_negative_int`、`_safe_token`、`isinstance`、`len` |
| `_is_raw_training_key` — `_is_raw_training_key(key)` | function / [976](../../../../agent/src/sr2fpga_agent/recorder.py#L976) | `key.endswith`、`key.startswith` |
| `_is_independent_oracle_episode` — `_is_independent_oracle_episode(episode)` | function / [982](../../../../agent/src/sr2fpga_agent/recorder.py#L982) | `episode.get`、`isinstance`、`profile.get` |
| `_verification_without_label_mismatches` — `_verification_without_label_mismatches(value)` | function / [991](../../../../agent/src/sr2fpga_agent/recorder.py#L991) | `dict`、`isinstance`、`l2_core.get`、`verification.get` |
| `_derived_training_views_metadata` — `_derived_training_views_metadata(sample_id, existing)` | function / [1001](../../../../agent/src/sr2fpga_agent/recorder.py#L1001) | `dict`、`isinstance`、`req2file.update`、`views.get` |
| `_read_project_json` — `_read_project_json(project, path)` | function / [1017](../../../../agent/src/sr2fpga_agent/recorder.py#L1017) | `isinstance`、`json.loads`、`project.files.get` |
| `_empty_req_his_fidelity` — `_empty_req_his_fidelity()` | function / [1028](../../../../agent/src/sr2fpga_agent/recorder.py#L1028) | 无直接调用 |
| `_his_validation_from_labels` — `_his_validation_from_labels(labels)` | function / [1039](../../../../agent/src/sr2fpga_agent/recorder.py#L1039) | `labels.get`、`str` |
| `_merge_project_episode_metadata` — `_merge_project_episode_metadata(existing, defaults)` | function / [1046](../../../../agent/src/sr2fpga_agent/recorder.py#L1046) | `<dynamic>.items`、`_project_provenance_summary`、`dict`、`existing.get`、`explicit_files.get`、`explicit_metadata.get`、`isinstance`、`merged.update` |
| `_project_episode_metadata` — `_project_episode_metadata(project)` | function / [1070](../../../../agent/src/sr2fpga_agent/recorder.py#L1070) | `_project_file_metadata`、`_project_provenance_summary`、`files.values`、`project.files.items`、`sorted`、`sum` |
| `_project_file_metadata` — `_project_file_metadata(path, content)` | function / [1082](../../../../agent/src/sr2fpga_agent/recorder.py#L1082) | `_behavior_hole_count`、`_project_file_origin`、`content.encode`、`len` |
| `_project_file_origin` — `_project_file_origin(path)` | function / [1091](../../../../agent/src/sr2fpga_agent/recorder.py#L1091) | 无直接调用 |
| `_project_provenance_summary` — `_project_provenance_summary(files)` | function / [1096](../../../../agent/src/sr2fpga_agent/recorder.py#L1096) | `files.items`、`files.values`、`isinstance`、`item.get`、`round`、`sum` |
| `_behavior_hole_count` — `_behavior_hole_count(content)` | function / [1127](../../../../agent/src/sr2fpga_agent/recorder.py#L1127) | `<dynamic>.count`、`content.count`、`content.replace` |
| `_verification_episode_metadata` — `_verification_episode_metadata(labels, measured_qor)` | function / [1134](../../../../agent/src/sr2fpga_agent/recorder.py#L1134) | `_check_status`、`_dict_list`、`_l2_core_verification_metadata`、`_l4_commercial_verification_metadata`、`_l4_open_verification_metadata`、`_string_list`、`bool`、`checks.get`、`isinstance`、`labels.get`、`measured_qor.get`、`str` |
| `_l2_core_verification_metadata` — `_l2_core_verification_metadata(labels, checks)` | function / [1166](../../../../agent/src/sr2fpga_agent/recorder.py#L1166) | `_check_status`、`_dict_list`、`_int_list`、`checks.get`、`isinstance`、`labels.get` |
| `_l4_open_verification_metadata` — `_l4_open_verification_metadata(labels, measured_qor, checks)` | function / [1195](../../../../agent/src/sr2fpga_agent/recorder.py#L1195) | `_first_present`、`_string_list`、`checks.get`、`dict`、`isinstance`、`labels.get`、`measured_qor.get`、`qor.get`、`str` |
| `_l4_commercial_verification_metadata` — `_l4_commercial_verification_metadata(labels, measured_qor, checks)` | function / [1238](../../../../agent/src/sr2fpga_agent/recorder.py#L1238) | `_check_status`、`_first_present`、`_string_list`、`checks.get`、`dict`、`isinstance`、`labels.get`、`measured_qor.get`、`qor.get`、`str` |
| `_first_present` — `_first_present(mapping, *keys)` | function / [1274](../../../../agent/src/sr2fpga_agent/recorder.py#L1274) | 无直接调用 |
| `_int_list` — `_int_list(value)` | function / [1281](../../../../agent/src/sr2fpga_agent/recorder.py#L1281) | `isinstance` |
| `_string_list` — `_string_list(value)` | function / [1287](../../../../agent/src/sr2fpga_agent/recorder.py#L1287) | `isinstance` |
| `_dict_list` — `_dict_list(value)` | function / [1293](../../../../agent/src/sr2fpga_agent/recorder.py#L1293) | `isinstance` |
| `_check_status` — `_check_status(value)` | function / [1299](../../../../agent/src/sr2fpga_agent/recorder.py#L1299) | 无直接调用 |
| `_data_release_tiers` — `_data_release_tiers()` | function / [1307](../../../../agent/src/sr2fpga_agent/recorder.py#L1307) | 无直接调用 |
| `_read_metadata` — `_read_metadata(sample_dir)` | function / [1323](../../../../agent/src/sr2fpga_agent/recorder.py#L1323) | `<dynamic>.classify`、`json.loads`、`load_system_his_compatibility_envelope`、`metadata.get`、`path.exists`、`path.read_text`、`str` |
| `_read_labels` — `_read_labels(sample_dir)` | function / [1338](../../../../agent/src/sr2fpga_agent/recorder.py#L1338) | `isinstance`、`json.loads`、`path.exists`、`path.read_text` |
| `_read_episode` — `_read_episode(sample_dir)` | function / [1346](../../../../agent/src/sr2fpga_agent/recorder.py#L1346) | `_is_independent_oracle_episode`、`_sanitize_oracle_profile`、`_verification_without_label_mismatches`、`dict`、`isinstance`、`json.loads`、`path.exists`、`path.read_text`、`result.get` |
| `_read_project_files` — `_read_project_files(project_dir, episode)` | function / [1361](../../../../agent/src/sr2fpga_agent/recorder.py#L1361) | `_file_origin_from_episode`、`any`、`files.append`、`item.is_file`、`part.startswith`、`path.read_text`、`path.relative_to`、`project_dir.rglob`、`relative_path.as_posix`、`sorted` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`、`re.compile`

## `agent/src/sr2fpga_agent/repair.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/repair.py) · 171 行 · SHA-256 `8231dabef653ca8b15c07c052ad253b9599d0132f8a09a6da4d53eaffc5f0c6c`

> LLM-backed generated-project repair.

导入模块：`__future__`、`sr2fpga_agent.family_recipe`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.prompts`、`sr2fpga_agent.providers`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.system_his_v12_checker`、`sr2fpga_agent.task_catalog`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SystemHisRepairer` — `SystemHisRepairer` | class / [46](../../../../agent/src/sr2fpga_agent/repair.py#L46) | 无直接调用 |
| `SystemHisRepairer.__init__` — `__init__(self, client)` | function / [49](../../../../agent/src/sr2fpga_agent/repair.py#L49) | 无直接调用 |
| `SystemHisRepairer.repair` — `repair(self, request, platform, candidate_output, validation_report, requirement_envelope, requirement_route, family_recipe_decision)` | function / [52](../../../../agent/src/sr2fpga_agent/repair.py#L52) | `<dynamic>.join`、`ValueError`、`_system_his_v12_messages`、`_with_system_his_retry_feedback`、`build_request_requirement_envelope`、`failed_stage.upper`、`first_failed_h_stage`、`isinstance`、`list`、`load_exact_task_family_aliases`、`recipe_task_type`、`requirement_envelope.requirement_trace_template`、`route_requirement`、`select_family_recipe`、`self.client.stream_chat`、`stage_report.get`、`validate_system_his_candidate`、`validation_report.get` |
| `ProjectRepairer` — `ProjectRepairer` | class / [114](../../../../agent/src/sr2fpga_agent/repair.py#L114) | 无直接调用 |
| `ProjectRepairer.__init__` — `__init__(self, client, max_attempts)` | function / [117](../../../../agent/src/sr2fpga_agent/repair.py#L117) | 无直接调用 |
| `ProjectRepairer.repair` — `repair(self, project, diagnosis)` | function / [121](../../../../agent/src/sr2fpga_agent/repair.py#L121) | `GeneratedProject`、`RepairResult`、`RuntimeError`、`ValueError`、`_diagnosis_mentions_path`、`_manifest_policy_for_project`、`_minimize_repaired_project`、`_project_system_his_schema`、`_project_task_type`、`_repair_messages`、`_validate_repair_preserves_l0_when_not_repairing_l0`、`_validate_system_his_contract_unchanged`、`build_patch_metadata`、`diff_projects`、`parse_project_files`、`parse_system_his_v12`、`range`、`record_parser_schema_retry`、`self.client.chat` |

## `agent/src/sr2fpga_agent/repository_paths.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/repository_paths.py) · 116 行 · SHA-256 `00f0e8cd35c8d1c38a2a0c6abbdabade198dfe617e550012e0c2500b65856086`

> Resolve repository-owned resources without relying on the process CWD.

导入模块：`__future__`、`dataclasses`、`os`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_has_repository_marker` — `_has_repository_marker(candidate)` | function / [14](../../../../agent/src/sr2fpga_agent/repository_paths.py#L14) | `<dynamic>.is_file` |
| `file_identity` — `file_identity(path)` | function / [18](../../../../agent/src/sr2fpga_agent/repository_paths.py#L18) | `os.stat`、`str` |
| `discover_repository_root` — `discover_repository_root(start)` | function / [33](../../../../agent/src/sr2fpga_agent/repository_paths.py#L33) | `<dynamic>.expanduser`、`<dynamic>.resolve`、`FileNotFoundError`、`Path`、`REPOSITORY_MARKER.as_posix`、`_ROOT_CACHE.get`、`_has_repository_marker`、`candidate.is_file`、`os.environ.get`、`str` |
| `RepositoryPaths` — `RepositoryPaths` | class / [68](../../../../agent/src/sr2fpga_agent/repository_paths.py#L68) | 无直接调用 |
| `RepositoryPaths.discover` — `discover(cls, start)` | function / [74](../../../../agent/src/sr2fpga_agent/repository_paths.py#L74) | `cls`、`discover_repository_root` |
| `RepositoryPaths.contracts_dir` — `contracts_dir(self)` | function / [78](../../../../agent/src/sr2fpga_agent/repository_paths.py#L78) | 无直接调用 |
| `RepositoryPaths.task_catalog` — `task_catalog(self)` | function / [82](../../../../agent/src/sr2fpga_agent/repository_paths.py#L82) | 无直接调用 |
| `RepositoryPaths.agent_scripts_dir` — `agent_scripts_dir(self)` | function / [90](../../../../agent/src/sr2fpga_agent/repository_paths.py#L90) | 无直接调用 |
| `RepositoryPaths.artifacts_dir` — `artifacts_dir(self)` | function / [94](../../../../agent/src/sr2fpga_agent/repository_paths.py#L94) | 无直接调用 |
| `RepositoryPaths.agent_artifacts_dir` — `agent_artifacts_dir(self)` | function / [98](../../../../agent/src/sr2fpga_agent/repository_paths.py#L98) | 无直接调用 |
| `RepositoryPaths.reports_dir` — `reports_dir(self)` | function / [102](../../../../agent/src/sr2fpga_agent/repository_paths.py#L102) | 无直接调用 |
| `RepositoryPaths.datasets_dir` — `datasets_dir(self)` | function / [106](../../../../agent/src/sr2fpga_agent/repository_paths.py#L106) | 无直接调用 |
| `RepositoryPaths.task_evidence` — `task_evidence(self)` | function / [110](../../../../agent/src/sr2fpga_agent/repository_paths.py#L110) | 无直接调用 |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`Path`、`dataclass`

## `agent/src/sr2fpga_agent/req2file_eval.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/req2file_eval.py) · 906 行 · SHA-256 `1ab07b90c6c484eabcc60a8be9dfb0fcb213b466149bf48fe89109c9a5a2d179`

> Build and score SR2FPGA REQ2FILE evaluation files.

导入模块：`__future__`、`argparse`、`http.client`、`json`、`pathlib`、`re`、`shutil`、`sr2fpga_agent.log_parser`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.rtl_identifier_checker`、`sr2fpga_agent.system_his_checker`、`sr2fpga_agent.testbench_checker`、`sr2fpga_agent.tool_runner`、`time`、`typing`、`urllib.error`、`urllib.request`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ChatClient` — `ChatClient` | class / [28](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L28) | 无直接调用 |
| `ChatClient.chat` — `chat(self, messages)` | function / [29](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L29) | 无直接调用 |
| `build_eval_set` — `build_eval_set(source, target, sample_id_prefix, exclude_file_paths, limit)` | function / [33](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L33) | `<dynamic>.replace`、`<dynamic>.startswith`、`<dynamic>.strip`、`_req2file_prompt`、`_source_episode_id`、`dict`、`json.dumps`、`json.loads`、`line.strip`、`output_file.write`、`row.get`、`set`、`source.open`、`str`、`target.open`、`target.parent.mkdir` |
| `score_predictions` — `score_predictions(predictions)` | function / [75](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L75) | `<dynamic>.replace`、`<dynamic>.strip`、`_is_valid_json`、`_prediction_text`、`_ratio`、`dict`、`enumerate`、`file_path.endswith`、`int`、`json.loads`、`line.strip`、`predictions.open`、`re.search`、`round`、`row.get`、`str` |
| `run_inference` — `run_inference(eval_path, output_path, client, limit)` | function / [137](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L137) | `_validate_eval_messages`、`client.chat`、`dict`、`eval_path.open`、`json.dumps`、`json.loads`、`line.strip`、`output_file.write`、`output_path.open`、`output_path.parent.mkdir`、`row.get` |
| `assemble_predictions` — `assemble_predictions(predictions, output_root, reference_dataset_root, backfill_reference_paths, clean_output_root)` | function / [163](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L163) | `<dynamic>.exists`、`<dynamic>.format`、`<dynamic>.join`、`<dynamic>.replace`、`<dynamic>.strip`、`Path`、`ValueError`、`_assembly_manifest`、`_predicted_required_project_paths`、`_prediction_text`、`_reference_project_paths`、`_write_json`、`_write_project_file`、`available_backfills.add`、`enumerate`、`files.items`、`grouped.items`、`grouped.setdefault`、`json.loads`、`len`、`line.strip`、`missing_backfills.append`、`output_root.exists`、`output_root.mkdir`、`predictions.open`、`project_file_target`、`reference_path.exists`、`reference_path.read_text`、`row.get`、`set`、`shutil.rmtree`、`sorted`、`str`、`validate_sample_id` |
| `verify_assembled_projects` — `verify_assembled_projects(project_root)` | function / [273](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L273) | `GeneratedProject`、`_assembly_manifest_error`、`_assembly_manifest_static_failure`、`_read_project_files`、`_req2file_project_result`、`_req2file_report_metadata`、`_verify_one_project`、`len`、`project_results.append`、`project_root.glob`、`sorted`、`sum` |
| `verify_assembled_projects_with_tools` — `verify_assembled_projects_with_tools(project_root, command_runner)` | function / [301](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L301) | `CommandRunner`、`_assembly_manifest_error`、`_assembly_manifest_tools_failure`、`_req2file_project_result`、`_req2file_report_metadata`、`_stage_status`、`_verify_one_project_with_tools`、`len`、`project_results.append`、`project_root.glob`、`sorted`、`sum` |
| `verify_assembled_projects_with_synth` — `verify_assembled_projects_with_synth(project_root, command_runner)` | function / [330](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L330) | `CommandRunner`、`_assembly_manifest_error`、`_assembly_manifest_synth_failure`、`_req2file_project_result`、`_req2file_report_metadata`、`_verify_one_project_with_synth`、`len`、`project_results.append`、`project_root.glob`、`sorted`、`sum` |
| `_req2file_prompt` — `_req2file_prompt(row)` | function / [355](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L355) | `<dynamic>.strip`、`row.get`、`str` |
| `_source_episode_id` — `_source_episode_id(row)` | function / [363](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L363) | `<dynamic>.strip`、`episode.get`、`isinstance`、`row.get`、`str` |
| `_reference_project_paths` — `_reference_project_paths(project_dir)` | function / [372](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L372) | `<dynamic>.as_posix`、`any`、`part.startswith`、`path.is_file`、`path.relative_to`、`project_dir.exists`、`project_dir.rglob`、`set` |
| `_predicted_required_project_paths` — `_predicted_required_project_paths(files)` | function / [382](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L382) | `<dynamic>.strip`、`_load_manifest`、`constraints.get`、`files.get`、`isinstance`、`manifest.get`、`path.replace`、`required.add`、`required.update`、`simulation.get`、`str` |
| `_assembly_manifest` — `_assembly_manifest(sample_id, plan)` | function / [397](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L397) | `_req2file_report_metadata` |
| `_write_json` — `_write_json(path, payload)` | function / [410](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L410) | `json.dumps`、`path.parent.mkdir`、`path.write_text` |
| `_req2file_report_metadata` — `_req2file_report_metadata()` | function / [415](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L415) | 无直接调用 |
| `_req2file_project_result` — `_req2file_project_result(result)` | function / [424](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L424) | `_req2file_report_metadata`、`contextual.pop`、`contextual.update`、`dict` |
| `_assembly_manifest_error` — `_assembly_manifest_error(project_dir)` | function / [432](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L432) | `<dynamic>.format`、`<dynamic>.is_file`、`<dynamic>.join`、`_manifest_file_set`、`isinstance`、`json.loads`、`manifest.get`、`manifest_path.exists`、`manifest_path.read_text`、`sorted` |
| `_manifest_file_set` — `_manifest_file_set(value)` | function / [461](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L461) | `<dynamic>.replace`、`<dynamic>.strip`、`isinstance`、`str` |
| `_assembly_manifest_static_failure` — `_assembly_manifest_static_failure(sample_id, error)` | function / [467](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L467) | 无直接调用 |
| `_assembly_manifest_tools_failure` — `_assembly_manifest_tools_failure(sample_id, error)` | function / [480](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L480) | 无直接调用 |
| `_assembly_manifest_synth_failure` — `_assembly_manifest_synth_failure(sample_id, error)` | function / [489](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L489) | `ToolResult`、`_tool_result_dict` |
| `_prediction_text` — `_prediction_text(row, line_number)` | function / [508](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L508) | `ValueError`、`isinstance`、`message.get`、`reversed`、`row.get`、`str` |
| `_validate_eval_messages` — `_validate_eval_messages(messages)` | function / [520](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L520) | `<dynamic>.strip`、`ValueError`、`isinstance`、`message.get`、`normalized.append`、`str` |
| `_write_project_file` — `_write_project_file(project_dir, relative_path, content)` | function / [537](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L537) | `project_file_target`、`target.parent.mkdir`、`target.write_text` |
| `_read_project_files` — `_read_project_files(project_dir)` | function / [543](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L543) | `<dynamic>.as_posix`、`path.is_file`、`path.read_text`、`path.relative_to`、`project_dir.rglob`、`sorted` |
| `_verify_one_project` — `_verify_one_project(sample_id, project)` | function / [551](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L551) | `<dynamic>.get`、`_load_manifest`、`all`、`check_project_l0`、`check_rtl_identifiers`、`check_testbench_static_issues`、`checks.values`、`isinstance`、`manifest.get`、`project.files.get`、`str` |
| `_verify_one_project_with_tools` — `_verify_one_project_with_tools(project_dir, runner)` | function / [598](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L598) | `<dynamic>.exists`、`<dynamic>.get`、`<dynamic>.read_text`、`_load_manifest`、`_replace_tool_status`、`_tool_result_dict`、`isinstance`、`manifest.get`、`runner.run`、`stages.append`、`str` |
| `_verify_one_project_with_synth` — `_verify_one_project_with_synth(project_dir, runner)` | function / [636](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L636) | `<dynamic>.exists`、`<dynamic>.read_text`、`ToolResult`、`_load_manifest`、`_tool_result_dict`、`build_yosys_script`、`isinstance`、`manifest.get`、`parse_yosys_stats`、`runner.run`、`str` |
| `_tool_result_dict` — `_tool_result_dict(result)` | function / [671](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L671) | 无直接调用 |
| `_replace_tool_status` — `_replace_tool_status(result, status, stderr)` | function / [682](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L682) | `<dynamic>`、`type` |
| `_stage_status` — `_stage_status(project_result, stage)` | function / [694](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L694) | `item.get`、`project_result.get`、`str` |
| `_load_manifest` — `_load_manifest(content)` | function / [701](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L701) | `isinstance`、`json.loads` |
| `_is_valid_json` — `_is_valid_json(text)` | function / [709](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L709) | `json.loads` |
| `_ratio` — `_ratio(numerator, denominator)` | function / [717](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L717) | `round` |
| `OpenAIChatCompletionsClient` — `OpenAIChatCompletionsClient` | class / [721](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L721) | 无直接调用 |
| `OpenAIChatCompletionsClient.__init__` — `__init__(self, base_url, api_key, model, timeout_seconds, max_tokens, temperature, transport_attempts)` | function / [724](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L724) | `max` |
| `OpenAIChatCompletionsClient.chat` — `chat(self, messages)` | function / [743](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L743) | `RuntimeError`、`self._request_with_retries`、`str` |
| `OpenAIChatCompletionsClient._request_with_retries` — `_request_with_retries(self, payload)` | function / [757](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L757) | `RuntimeError`、`range`、`self._request_once`、`time.sleep` |
| `OpenAIChatCompletionsClient._request_once` — `_request_once(self, payload)` | function / [769](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L769) | `<dynamic>.decode`、`<dynamic>.encode`、`RuntimeError`、`exc.read`、`json.dumps`、`json.loads`、`response.read`、`self.base_url.rstrip`、`urllib.request.Request`、`urllib.request.urlopen` |
| `main` — `main()` | function / [787](../../../../agent/src/sr2fpga_agent/req2file_eval.py#L787) | `OpenAIChatCompletionsClient`、`argparse.ArgumentParser`、`args.output.parent.mkdir`、`args.output.write_text`、`assemble_parser.add_argument`、`assemble_predictions`、`build_eval_set`、`build_parser.add_argument`、`infer_parser.add_argument`、`json.dumps`、`parser.add_subparsers`、`parser.parse_args`、`print`、`run_inference`、`score_parser.add_argument`、`score_predictions`、`set`、`subparsers.add_parser`、`verify_assembled_projects`、`verify_assembled_projects_with_synth`、`verify_assembled_projects_with_tools`、`verify_parser.add_argument`、`verify_synth_parser.add_argument`、`verify_tools_parser.add_argument` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `agent/src/sr2fpga_agent/requirement_audit.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/requirement_audit.py) · 293 行 · SHA-256 `8fcbd8b86b1d9a870cb1558054dc7535a2eda0e03c709f89ce5a6da3e01198eb`

> Offline, stop-before-generation ambiguity audit artifacts for Paper-1 RQ0.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`jsonschema`、`pathlib`、`sr2fpga_agent.models`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.requirement_envelope`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ClarificationAnswerBranch` — `ClarificationAnswerBranch` | class / [27](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L27) | 无直接调用 |
| `RequirementAuditGold` — `RequirementAuditGold` | class / [34](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L34) | 无直接调用 |
| `build_requirement_audit_case` — `build_requirement_audit_case(request, platform, base_requirement_cluster_id, ambiguity_case_id, gold)` | function / [42](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L42) | `ValueError`、`_fact_record`、`_gold_projection`、`_sha256`、`asdict`、`boundary.route.to_dict`、`effective_request_requirement`、`evaluate_requirement_boundary`、`list`、`replace`、`request.description.strip`、`time.monotonic` |
| `build_requirement_audit_artifact` — `build_requirement_audit_artifact(audit_run_id, cases)` | function / [119](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L119) | `ValueError`、`_sha256`、`_summarize`、`validate_requirement_audit_artifact` |
| `load_requirement_audit_manifest` — `load_requirement_audit_manifest(path)` | function / [137](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L137) | `Path`、`ValueError`、`isinstance`、`json.loads`、`manifest_path.exists`、`manifest_path.is_file`、`manifest_path.read_text`、`validate_requirement_audit_artifact` |
| `validate_requirement_audit_artifact` — `validate_requirement_audit_artifact(artifact)` | function / [162](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L162) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`RepositoryPaths.discover`、`ValueError`、`_sha256`、`artifact.get`、`artifact.items`、`json.loads`、`schema_path.read_text` |
| `write_requirement_audit_artifact` — `write_requirement_audit_artifact(path, artifact)` | function / [173](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L173) | `json.dumps`、`path.parent.mkdir`、`path.write_text`、`validate_requirement_audit_artifact` |
| `_fact_record` — `_fact_record(fact)` | function / [182](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L182) | `_json_value` |
| `_gold_projection` — `_gold_projection(gold)` | function / [196](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L196) | `ValueError`、`_json_value`、`_sha256`、`list` |
| `_summarize` — `_summarize(cases)` | function / [220](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L220) | `<dynamic>.items`、`_disposition_counts`、`bool`、`int`、`len`、`result.get` |
| `_disposition_counts` — `_disposition_counts(values)` | function / [273](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L273) | `str` |
| `_json_value` — `_json_value(value)` | function / [280](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L280) | `_json_value`、`isinstance`、`str`、`value.items` |
| `_sha256` — `_sha256(value)` | function / [288](../../../../agent/src/sr2fpga_agent/requirement_audit.py#L288) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`hashlib.sha256`、`isinstance`、`json.dumps`、`value.encode` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/requirement_boundary.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/requirement_boundary.py) · 183 行 · SHA-256 `0e22540ff7557495a09d573bcf6b71b75083fbbfb642bc3524b312163762ff68`

> Method-neutral requirement disposition before project generation.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.models`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.system_his_capabilities`、`sr2fpga_agent.task_catalog`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RequirementBoundaryDecision` — `RequirementBoundaryDecision` | class / [48](../../../../agent/src/sr2fpga_agent/requirement_boundary.py#L48) | 无直接调用 |
| `RequirementBoundaryDecision.to_dict` — `to_dict(self)` | function / [65](../../../../agent/src/sr2fpga_agent/requirement_boundary.py#L65) | `_sha256`、`list`、`self.envelope.to_dict`、`self.route.to_dict` |
| `evaluate_requirement_boundary` — `evaluate_requirement_boundary(request, platform, backend, clarification_facts)` | function / [89](../../../../agent/src/sr2fpga_agent/requirement_boundary.py#L89) | `RequirementBoundaryDecision`、`_sha256`、`build_request_requirement_envelope`、`capability_profile_sha256`、`envelope.to_dict`、`load_exact_task_family_aliases`、`load_system_his_backend_capabilities`、`requirement_capability_gaps`、`route_requirement`、`tuple` |
| `requirement_capability_gaps` — `requirement_capability_gaps(envelope, backend)` | function / [143](../../../../agent/src/sr2fpga_agent/requirement_boundary.py#L143) | `_CAPABILITY_MECHANISMS.get`、`gaps.append`、`tuple` |
| `capability_profile_sha256` — `capability_profile_sha256(backend)` | function / [166](../../../../agent/src/sr2fpga_agent/requirement_boundary.py#L166) | `_sha256`、`dict`、`sorted` |
| `_sha256` — `_sha256(value)` | function / [181](../../../../agent/src/sr2fpga_agent/requirement_boundary.py#L181) | `<dynamic>.hexdigest`、`canonical.encode`、`hashlib.sha256`、`json.dumps` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/requirement_envelope.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/requirement_envelope.py) · 684 行 · SHA-256 `5c0fc8b20f6c3a47e6fad86e50a6ff2a5a0fc909e797940c95da5cac600d92a4`

> Deterministic normalization and routing for open FPGA requirements.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.task_families`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RequirementFact` — `RequirementFact` | class / [156](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L156) | 无直接调用 |
| `CriticalAmbiguity` — `CriticalAmbiguity` | class / [164](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L164) | 无直接调用 |
| `RequirementEnvelope` — `RequirementEnvelope` | class / [171](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L171) | 无直接调用 |
| `RequirementEnvelope.explicit_facts` — `explicit_facts(self)` | function / [179](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L179) | 无直接调用 |
| `RequirementEnvelope.default_facts` — `default_facts(self)` | function / [183](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L183) | 无直接调用 |
| `RequirementEnvelope.assumption_facts` — `assumption_facts(self)` | function / [187](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L187) | 无直接调用 |
| `RequirementEnvelope.unknown_facts` — `unknown_facts(self)` | function / [191](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L191) | `tuple` |
| `RequirementEnvelope.to_prompt_payload` — `to_prompt_payload(self)` | function / [194](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L194) | `_json_value`、`asdict`、`list` |
| `RequirementEnvelope.requirement_trace_template` — `requirement_trace_template(self)` | function / [208](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L208) | `_json_value` |
| `RequirementEnvelope.to_dict` — `to_dict(self)` | function / [226](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L226) | `_json_value`、`asdict`、`self.to_prompt_payload` |
| `ExactFamilyMetadata` — `ExactFamilyMetadata` | class / [233](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L233) | 无直接调用 |
| `RequirementRouteResult` — `RequirementRouteResult` | class / [240](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L240) | 无直接调用 |
| `RequirementRouteResult.to_dict` — `to_dict(self)` | function / [248](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L248) | `_json_value`、`asdict` |
| `build_requirement_envelope` — `build_requirement_envelope(description, defaults, assumptions, clarifications)` | function / [252](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L252) | `<dynamic>.intersection`、`<dynamic>.join`、`RequirementEnvelope`、`RequirementFact`、`ValueError`、`_CONDITIONAL_FACTS.get`、`_ambiguities`、`_clarified_capabilities`、`_detect`、`_explicit_opaque_protocols`、`_extract_facts`、`_freeze`、`_requirement_id`、`bool`、`description.strip`、`dict`、`dict.fromkeys`、`facts.append`、`keys.append`、`keys.extend`、`list`、`re.search`、`set`、`sorted`、`supplied_assumptions.get`、`supplied_clarifications.get`、`supplied_defaults.get`、`tuple` |
| `build_request_requirement_envelope` — `build_request_requirement_envelope(request, platform, clarification_facts)` | function / [384](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L384) | `_canonical_task_type`、`build_requirement_envelope`、`effective_request_requirement` |
| `effective_request_requirement` — `effective_request_requirement(request)` | function / [411](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L411) | `<dynamic>.strip`、`_canonical_task_type`、`request.description.strip` |
| `_canonical_task_type` — `_canonical_task_type(task_type)` | function / [421](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L421) | `TASK_TYPE_ALIASES.get` |
| `route_requirement` — `route_requirement(envelope, declared_family, exact_family_aliases)` | function / [427](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L427) | `<dynamic>.items`、`<dynamic>.strip`、`ExactFamilyMetadata`、`RequirementRouteResult`、`ValueError`、`_normalize`、`aliases.get`、`tuple` |
| `_extract_facts` — `_extract_facts(text, interface_protocols)` | function / [466](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L466) | `<dynamic>.casefold`、`<dynamic>.strip`、`_evidence`、`_extract_conditional_facts`、`_hz`、`dict.fromkeys`、`int`、`item.group`、`len`、`match.group`、`re.finditer`、`re.search`、`tuple` |
| `_extract_conditional_facts` — `_extract_conditional_facts(text, facts)` | function / [518](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L518) | `<dynamic>.casefold`、`_normalize`、`int`、`match.group`、`re.search` |
| `_ambiguities` — `_ambiguities(capabilities, facts, vague_interface_clause)` | function / [542](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L542) | `<dynamic>.intersection`、`CriticalAmbiguity`、`_unknown`、`items.append`、`items.extend`、`seen.add`、`tuple` |
| `_detect` — `_detect(text, patterns)` | function / [589](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L589) | `re.search`、`tuple` |
| `_clarified_capabilities` — `_clarified_capabilities(value)` | function / [593](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L593) | `ValueError`、`_normalize`、`capabilities.append`、`dict.fromkeys`、`isinstance`、`tuple` |
| `_explicit_opaque_protocols` — `_explicit_opaque_protocols(text, known_protocols, known_capabilities)` | function / [609](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L609) | `<dynamic>.join`、`<dynamic>.union`、`_detect`、`_normalize`、`capability.split`、`dict.fromkeys`、`excluded.update`、`list`、`match.group`、`name.split`、`names.append`、`parts.pop`、`re.finditer`、`set`、`tuple` |
| `_unknown` — `_unknown(facts, key)` | function / [640](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L640) | 无直接调用 |
| `_evidence` — `_evidence(matches)` | function / [644](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L644) | `match.group`、`tuple` |
| `_hz` — `_hz(value, unit)` | function / [648](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L648) | `float`、`int`、`round`、`unit.casefold` |
| `_normalize` — `_normalize(value)` | function / [653](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L653) | `<dynamic>.casefold`、`<dynamic>.strip`、`re.sub`、`value.strip` |
| `_freeze` — `_freeze(value)` | function / [657](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L657) | `_freeze`、`isinstance`、`sorted`、`str`、`tuple`、`value.items` |
| `_requirement_id` — `_requirement_id(text, facts)` | function / [665](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L665) | `<dynamic>.hexdigest`、`<dynamic>.join`、`_json_value`、`canonical.encode`、`hashlib.sha256`、`json.dumps`、`text.split` |
| `_json_value` — `_json_value(value)` | function / [679](../../../../agent/src/sr2fpga_agent/requirement_envelope.py#L679) | `_json_value`、`isinstance`、`str`、`value.items` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`

## `agent/src/sr2fpga_agent/rtl_identifier_checker.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py) · 121 行 · SHA-256 `1c74dc4ab4fb9b490681d4ec938682ada332343e58d409029cb789fec50c1cc9`

> Lightweight Verilog identifier checks before external lint tools run.

导入模块：`__future__`、`dataclasses`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.system_his_v12_checker`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RtlIdentifierIssue` — `RtlIdentifierIssue` | class / [30](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L30) | 无直接调用 |
| `check_rtl_identifiers` — `check_rtl_identifiers(project, sources)` | function / [39](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L39) | `_declaration_issues`、`_instance_issues`、`_module_name_issues`、`_strip_line_comment`、`content.splitlines`、`enumerate`、`issues.extend`、`line.strip`、`project.files.get`、`source.endswith` |
| `rtl_identifier_tool_result` — `rtl_identifier_tool_result(issues)` | function / [57](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L57) | `<dynamic>.join`、`ToolResult` |
| `_strip_line_comment` — `_strip_line_comment(line)` | function / [82](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L82) | `line.split` |
| `_module_name_issues` — `_module_name_issues(path, line_number, line)` | function / [86](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L86) | `RtlIdentifierIssue`、`match.group`、`re.match` |
| `_declaration_issues` — `_declaration_issues(path, line_number, line)` | function / [93](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L93) | `RtlIdentifierIssue`、`declaration.rstrip`、`issues.append`、`line.strip`、`re.findall`、`re.sub`、`stripped.split` |
| `_instance_issues` — `_instance_issues(path, line_number, line)` | function / [109](../../../../agent/src/sr2fpga_agent/rtl_identifier_checker.py#L109) | `RtlIdentifierIssue`、`match.groups`、`re.match` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/rtl_introspect.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/rtl_introspect.py) · 218 行 · SHA-256 `5105894781cebe707cc3e68c4af1445c8fb4694b956228b1b97c7b07334a98e1`

> Shared lightweight RTL introspection helpers for System-HIS checkers.

导入模块：`__future__`、`re`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `declared_modules` — `declared_modules(files, sources)` | function / [9](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L9) | `files.get`、`modules.update`、`pattern.findall`、`re.compile`、`set` |
| `declared_module_parameters` — `declared_module_parameters(files, sources)` | function / [19](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L19) | `files.get`、`module_parameter_names`、`re.findall` |
| `declared_module_ports` — `declared_module_ports(files, sources)` | function / [30](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L30) | `files.get`、`parse_module_ports`、`re.findall` |
| `parse_module_ports` — `parse_module_ports(content, module_name)` | function / [41](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L41) | `match.group`、`module_port_body`、`name_match.group`、`port_width`、`re.search`、`split_port_declarations`、`strip_line_comments` |
| `module_port_body` — `module_port_body(content, module_name)` | function / [75](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L75) | `<dynamic>.isspace`、`len`、`match.end`、`matching_paren`、`re.escape`、`re.search` |
| `split_port_declarations` — `split_port_declarations(body)` | function / [98](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L98) | `<dynamic>.join`、`<dynamic>.split`、`body.split`、`declarations.append`、`part.strip` |
| `strip_line_comments` — `strip_line_comments(text)` | function / [109](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L109) | `re.sub` |
| `port_width` — `port_width(range_text)` | function / [113](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L113) | `concrete_minus_one.group`、`int`、`numeric.group`、`range_text.strip`、`re.fullmatch` |
| `module_parameter_names` — `module_parameter_names(content, module_name)` | function / [128](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L128) | `<dynamic>.isspace`、`len`、`match.end`、`matching_paren`、`re.escape`、`re.findall`、`re.search`、`set` |
| `matching_paren` — `matching_paren(text, open_index)` | function / [149](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L149) | `len`、`range` |
| `normalize_width` — `normalize_width(value)` | function / [163](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L163) | `<dynamic>.strip`、`bracketed_range.group`、`concrete_minus_one_range.group`、`expression_minus_one_range.group`、`int`、`isinstance`、`normalize_width`、`numeric_range.group`、`re.fullmatch`、`str`、`symbolic_range.group`、`unbracketed_concrete_minus_one_range.group`、`unbracketed_expression_minus_one_range.group`、`unbracketed_numeric_range.group`、`unbracketed_symbolic_range.group` |
| `width_candidates` — `width_candidates(value)` | function / [202](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L202) | `candidates.update`、`isinstance`、`normalize_width`、`set`、`width_candidates` |
| `widths_equivalent` — `widths_equivalent(left, right)` | function / [215](../../../../agent/src/sr2fpga_agent/rtl_introspect.py#L215) | `bool`、`width_candidates` |

## `agent/src/sr2fpga_agent/runner.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/runner.py) · 5669 行 · SHA-256 `308bf4ea7743b6fe73691e4837aba8694c5afaba9842964f5aee94d118ddc422`

> Autonomous batch runner for SR2FPGA trajectory generation.

导入模块：`__future__`、`argparse`、`dataclasses`、`datetime`、`hashlib`、`json`、`os`、`pathlib`、`re`、`shutil`、`sr2fpga_agent.agent`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.baseline_report`、`sr2fpga_agent.block_cost_accounting`、`sr2fpga_agent.block_preparation`、`sr2fpga_agent.budget_allocation`、`sr2fpga_agent.checkpoint_stop_outcome`、`sr2fpga_agent.cli`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.cost_accounting`、`sr2fpga_agent.episode_executor`、`sr2fpga_agent.episode_outcome`、`sr2fpga_agent.evaluator_dispatch`、`sr2fpga_agent.failure_injector`、`sr2fpga_agent.family_recipe`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.generation`、`sr2fpga_agent.generation.context_his`、`sr2fpga_agent.generation.context_plan`、`sr2fpga_agent.his_correction_outcome`、`sr2fpga_agent.l4_tool_environment`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.measurement_freeze`、`sr2fpga_agent.method_adapters`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.model_gateway_provenance`、`sr2fpga_agent.models`、`sr2fpga_agent.paired_block`、`sr2fpga_agent.paired_measurement`、`sr2fpga_agent.pre_candidate_outcome`、`sr2fpga_agent.project_contract`、`sr2fpga_agent.project_generator`、`sr2fpga_agent.provider_seed_capability`、`sr2fpga_agent.providers`、`sr2fpga_agent.public_l2_harness`、`sr2fpga_agent.recorder`、`sr2fpga_agent.requirement_audit`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.system_his_compatibility`、`sr2fpga_agent.task_catalog`、`sr2fpga_agent.testbench_checker`、`sr2fpga_agent.tool_environment`、`typing`、`yaml`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TaskConfig` — `TaskConfig` | class / [184](../../../../agent/src/sr2fpga_agent/runner.py#L184) | `field` |
| `SourceConnection` — `SourceConnection` | class / [210](../../../../agent/src/sr2fpga_agent/runner.py#L210) | 无直接调用 |
| `L4OpenConfig` — `L4OpenConfig` | class / [229](../../../../agent/src/sr2fpga_agent/runner.py#L229) | 无直接调用 |
| `L4CommercialConfig` — `L4CommercialConfig` | class / [239](../../../../agent/src/sr2fpga_agent/runner.py#L239) | 无直接调用 |
| `RunnerConfig` — `RunnerConfig` | class / [248](../../../../agent/src/sr2fpga_agent/runner.py#L248) | `Path`、`field` |
| `PlannedSample` — `PlannedSample` | class / [282](../../../../agent/src/sr2fpga_agent/runner.py#L282) | `field` |
| `PlannedSample.metadata` — `metadata(self, config, paired_block_ref)` | function / [311](../../../../agent/src/sr2fpga_agent/runner.py#L311) | `<dynamic>.to_dict`、`_contract_skeleton_mode`、`_measurement_point_for_method`、`_platform_profile_for_config`、`_project_request_for_sample`、`_sample_failure_origin`、`_sample_method_condition`、`_sample_model_call_ceiling`、`_sample_system_his_schema_version`、`_training_split`、`boundary.to_dict`、`build_development_episode_pack`、`evaluate_requirement_boundary`、`freeze_ready_requirement_context`、`list`、`paired_block_ref.to_dict`、`resolve_source_connection`、`select_family_recipe` |
| `_PlannedPairedBlock` — `_PlannedPairedBlock` | class / [425](../../../../agent/src/sr2fpga_agent/runner.py#L425) | 无直接调用 |
| `PreparedBlockRuntime` — `PreparedBlockRuntime` | class / [432](../../../../agent/src/sr2fpga_agent/runner.py#L432) | `field` |
| `_RunnerDirectMethodProjectGenerator` — `_RunnerDirectMethodProjectGenerator` | class / [440](../../../../agent/src/sr2fpga_agent/runner.py#L440) | 无直接调用 |
| `_RunnerDirectMethodProjectGenerator.__init__` — `__init__(self, method_condition, context, services, coordinator, pairing, direct, prepared_initial_project)` | function / [445](../../../../agent/src/sr2fpga_agent/runner.py#L445) | `<dynamic>.create`、`MethodAdapterRegistry` |
| `_RunnerDirectMethodProjectGenerator.generate` — `generate(self, _request, _platform)` | function / [465](../../../../agent/src/sr2fpga_agent/runner.py#L465) | `<dynamic>.emit_candidate`、`EpisodeExecutor`、`RuntimeError`、`SharedArtifactRefs`、`ValueError`、`self._coordinator.materialize_initial_project`、`self._direct.emit_project`、`self._pairing.digest`、`self._services.artifacts.read_project` |
| `_RunnerUntypedPlanProjectGenerator` — `_RunnerUntypedPlanProjectGenerator` | class / [498](../../../../agent/src/sr2fpga_agent/runner.py#L498) | 无直接调用 |
| `_RunnerUntypedPlanProjectGenerator.__init__` — `__init__(self, context, services)` | function / [503](../../../../agent/src/sr2fpga_agent/runner.py#L503) | `<dynamic>.create`、`MethodAdapterRegistry` |
| `_RunnerUntypedPlanProjectGenerator.generate` — `generate(self, _request, _platform)` | function / [509](../../../../agent/src/sr2fpga_agent/runner.py#L509) | `<dynamic>.emit_candidate`、`EpisodeExecutor`、`RuntimeError`、`self._services.artifacts.read_project` |
| `RunState` — `RunState` | class / [527](../../../../agent/src/sr2fpga_agent/runner.py#L527) | 无直接调用 |
| `load_runner_config` — `load_runner_config(path)` | function / [537](../../../../agent/src/sr2fpga_agent/runner.py#L537) | `<dynamic>.intersection`、`<dynamic>.join`、`<dynamic>.strip`、`Path`、`RunnerConfig`、`SystemExit`、`_load_l4_commercial_config`、`_load_l4_open_config`、`_load_mapping`、`_load_sources`、`_load_task_config`、`_parse_bool`、`dict`、`int`、`raw.get`、`sorted`、`str` |
| `main` — `main(argv)` | function / [606](../../../../agent/src/sr2fpga_agent/runner.py#L606) | `<dynamic>.get`、`SystemExit`、`argparse.ArgumentParser`、`json.dumps`、`len`、`load_runner_config`、`parser.add_argument`、`parser.parse_args`、`print`、`run_batch`、`runner_preflight` |
| `runner_preflight` — `runner_preflight(config, run_id, validate_provider)` | function / [635](../../../../agent/src/sr2fpga_agent/runner.py#L635) | `<dynamic>.join`、`Path`、`_analysis_population_errors`、`_api_key_diagnostics`、`_discover_tool_statuses`、`_env_file_label`、`_load_env_file`、`_paired_block_refs_by_sample`、`_plan_block_preparation_policy`、`_plan_development_paired_blocks`、`_preflight_sample_preview`、`_seed_capability_diagnostics`、`_source_auth_diagnostics`、`errors.append`、`errors.extend`、`len`、`load_development_public_l2_harness`、`paired_block_plans.items`、`planned_block_refs.get`、`planned_samples`、`providers.add`、`run_dir.exists`、`sorted`、`str`、`tools.items`、`warnings.append` |
| `_preflight_sample_preview` — `_preflight_sample_preview(sample, config, paired_block_ref)` | function / [715](../../../../agent/src/sr2fpga_agent/runner.py#L715) | `paired_block_ref.to_dict`、`sample.metadata`、`str` |
| `_discover_tool_statuses` — `_discover_tool_statuses(tools)` | function / [779](../../../../agent/src/sr2fpga_agent/runner.py#L779) | `resolve_executable`、`shutil.which` |
| `_project_request_for_sample` — `_project_request_for_sample(sample)` | function / [786](../../../../agent/src/sr2fpga_agent/runner.py#L786) | `ProjectRequest` |
| `_platform_profile_for_config` — `_platform_profile_for_config(config)` | function / [795](../../../../agent/src/sr2fpga_agent/runner.py#L795) | `PlatformProfile` |
| `run_batch` — `run_batch(config, run_id, resume)` | function / [799](../../../../agent/src/sr2fpga_agent/runner.py#L799) | `<dynamic>.exists`、`<dynamic>.export_training_views`、`<dynamic>.join`、`<dynamic>.strftime`、`<dynamic>.strip`、`<dynamic>.upper`、`<dynamic>.write_text`、`ArtifactRef`、`ArtifactStore`、`AttemptCostLedgerRouter`、`DataGenerationAgent`、`DatasetRecorder`、`ModelCallBudget`、`PairedArtifactCoordinator`、`Path`、`RunState`、`RuntimeError`、`SystemExit`、`_analysis_population_errors`、`_append_event`、`_config_fingerprint`、`_development_hidden_authority_for_run`、`_development_hidden_private_commitment`、`_generation_event_sink`、`_l4_commercial_enabled_for_sample`、`_l4_open_enabled_for_sample`、`_l4_version_probe_authorized`、`_load_env_file`、`_materialize_development_paired_blocks`、`_measurement_freeze_manifest`、`_measurement_tool_versions`、`_method_artifact_completion_record`、`_order_samples_by_paired_blocks`、`_paired_block_refs_by_sample`、`_paired_execution_ordinals`、`_plan_block_preparation_policy`、`_plan_development_paired_blocks`、`_platform_profile_for_config`、`_preflight_existing_block_preparation_resume`、`_prepare_complete_blocks`、`_prepared_block_audit_record`、`_prepared_runtime_accounting_input_hashes`、`_project_generator_for_sample`、`_project_request_for_sample`、`_read_labels`、`_record_blocked_by_shared_checkpoint`、`_record_completed`、`_record_rejected`、`_repairer_for_sample`、`_run_config_projection`、`_sample_attempt_limit`、`_sample_failure_origin`、`_sample_has_measurement`、`_seed_capability_diagnostics`、`_summary`、`_update_sample_model_budget`、`_verified_missing_terminal_reason`、`_write_json`、`accounting_input_hashes.add`、`accounting_input_hashes.update`、`agent.run_one`、`all`、`any`、`baseline_rows`、`block_preparation_audit.get`、`blocked_event.update`、`boundary.get`、`checkpoint_stop_ref.to_dict`、`classify_sample_bucket`、`collect_development_l4_tool_environment`、`collect_development_tool_environment`、`collect_paired_results`、`completion_event.get`、`completion_event.update`、`correction_outcome_ref.to_dict`、`datetime.now`、`dict`、`enumerate`、`episode_outcome_ref.to_dict`、`episode_pack.get`、`episode_pack_ref.to_dict`、`failure_record.get`、`initial_run_state`、`int`、`isinstance`、`l4_tool_environment_ref.to_dict`、`l4_tool_version_projection`、`list`、`load_development_public_l2_harness`、`method_artifact_record.get`、`method_artifact_store.put_validated_json`、`model_budget.summary`、`next`、`openxc7_tool_probe_command`、`os.environ.get`、`paired_block_ref.to_dict`、`paired_block_refs_by_sample.get`、`paired_execution_ordinals.get`、`planned_samples`、`prepared_block_runtime.blocked_method_checkpoints.get`、`prepared_blocks.get`、`prepared_blocks.items`、`project_development_public_evaluation`、`protocol_errors.extend`、`public_context.get`、`public_evaluation_ref.to_dict`、`read_development_shared_checkpoint_manifest`、`read_run_state`、`reconcile_checkpoint_stop_outcome`、`reconcile_development_episode_outcome`、`reconcile_development_his_correction_outcome`、`reconcile_development_pre_candidate_stop_outcome`、`render_markdown`、`required_refs.values`、`result.get`、`run_dir.mkdir`、`sample.metadata`、`sample_metadata.get`、`set`、`should_skip_sample`、`sorted`、`state_path.exists`、`stop_outcome_ref.to_dict`、`str`、`tool_environment_ref.to_dict`、`tool_versions.update`、`write_or_validate_freeze`、`write_run_state` |
| `run_batch.attempt_cost_ledger_factory` — `attempt_cost_ledger_factory(attempt_id)` | function / [1171](../../../../agent/src/sr2fpga_agent/runner.py#L1171) | `AttemptCostLedger`、`str` |
| `_analysis_population_errors` — `_analysis_population_errors(samples)` | function / [1513](../../../../agent/src/sr2fpga_agent/runner.py#L1513) | `any`、`errors.append`、`load_requirement_audit_manifest`、`set`、`validated.add` |
| `_development_hidden_authority_for_run` — `_development_hidden_authority_for_run(run_dir, candidate_store)` | function / [1547](../../../../agent/src/sr2fpga_agent/runner.py#L1547) | `ArtifactStore`、`DevelopmentHiddenEvaluationAuthority` |
| `_development_hidden_evaluator` — `_development_hidden_evaluator(_input)` | function / [1561](../../../../agent/src/sr2fpga_agent/runner.py#L1561) | 无直接调用 |
| `_development_hidden_private_commitment` — `_development_hidden_private_commitment(dataset_root, sample, metadata, run_id)` | function / [1569](../../../../agent/src/sr2fpga_agent/runner.py#L1569) | `<dynamic>.digest`、`<dynamic>.get`、`digest.encode`、`hashlib.sha256`、`isinstance`、`json.dumps`、`metadata.get`、`payload.update`、`str` |
| `initial_run_state` — `initial_run_state(run_id, config_fingerprint)` | function / [1606](../../../../agent/src/sr2fpga_agent/runner.py#L1606) | `RunState` |
| `read_run_state` — `read_run_state(path)` | function / [1623](../../../../agent/src/sr2fpga_agent/runner.py#L1623) | `<dynamic>.items`、`RunState`、`bool`、`data.get`、`int`、`json.loads`、`path.read_text`、`str` |
| `write_run_state` — `write_run_state(path, state)` | function / [1636](../../../../agent/src/sr2fpga_agent/runner.py#L1636) | `asdict`、`json.dumps`、`path.parent.mkdir`、`path.write_text` |
| `should_skip_sample` — `should_skip_sample(state, sample_id)` | function / [1641](../../../../agent/src/sr2fpga_agent/runner.py#L1641) | `set` |
| `classify_sample_bucket` — `classify_sample_bucket(labels)` | function / [1645](../../../../agent/src/sr2fpga_agent/runner.py#L1645) | `_passes_at_least`、`int`、`labels.get`、`str` |
| `_config_to_jsonable` — `_config_to_jsonable(config)` | function / [1657](../../../../agent/src/sr2fpga_agent/runner.py#L1657) | `_env_file_label`、`_seed_capability_manifest_ref`、`asdict`、`config.sources.items`、`str` |
| `_run_config_projection` — `_run_config_projection(config, block_preparation_audit)` | function / [1675](../../../../agent/src/sr2fpga_agent/runner.py#L1675) | `_config_to_jsonable`、`block_preparation_audit.items`、`dict`、`sorted` |
| `_config_fingerprint` — `_config_fingerprint(config)` | function / [1692](../../../../agent/src/sr2fpga_agent/runner.py#L1692) | `<dynamic>.hexdigest`、`_config_to_jsonable`、`hashlib.sha256`、`json.dumps`、`payload.encode` |
| `_measurement_freeze_manifest` — `_measurement_freeze_manifest(config, run_id, config_fingerprint, samples, tool_versions, tool_environment_ref, l4_tool_environment_ref, paired_block_refs, paired_execution_ordinals, block_preparation_policies)` | function / [1697](../../../../agent/src/sr2fpga_agent/runner.py#L1697) | `_measurement_freeze_sample_record`、`_measurement_tool_versions`、`_seed_capability_manifest_ref`、`block_preparation_policies.items`、`block_refs.get`、`build_measurement_freeze`、`dict`、`execution_ordinals.get`、`getattr`、`int`、`list`、`resolve_source_connection`、`sorted`、`source_records.append` |
| `_measurement_freeze_sample_record` — `_measurement_freeze_sample_record(sample, config, paired_block_ref, execution_ordinal)` | function / [1772](../../../../agent/src/sr2fpga_agent/runner.py#L1772) | `_sample_method_condition`、`_sample_model_call_ceiling`、`metadata.get`、`paired_block_ref.to_dict`、`record.update`、`sample.metadata` |
| `_measurement_tool_versions` — `_measurement_tool_versions(config, tool_environment)` | function / [1831](../../../../agent/src/sr2fpga_agent/runner.py#L1831) | `collect_development_tool_environment`、`tool_version_projection` |
| `_l4_version_probe_authorized` — `_l4_version_probe_authorized()` | function / [1843](../../../../agent/src/sr2fpga_agent/runner.py#L1843) | `<dynamic>.lower`、`<dynamic>.strip`、`os.environ.get` |
| `_load_env_file` — `_load_env_file(path)` | function / [1851](../../../../agent/src/sr2fpga_agent/runner.py#L1851) | `<dynamic>.splitlines`、`Path`、`_strip_env_value`、`key.strip`、`line.strip`、`loaded.add`、`path.is_file`、`path.read_text`、`set`、`stripped.split`、`stripped.startswith`、`value.strip` |
| `_strip_env_value` — `_strip_env_value(value)` | function / [1868](../../../../agent/src/sr2fpga_agent/runner.py#L1868) | `len` |
| `_env_file_label` — `_env_file_label(path)` | function / [1874](../../../../agent/src/sr2fpga_agent/runner.py#L1874) | `Path`、`str` |
| `_api_key_diagnostics` — `_api_key_diagnostics(config, loaded_env_keys)` | function / [1878](../../../../agent/src/sr2fpga_agent/runner.py#L1878) | `_env_file_label`、`_secret_fingerprint`、`bool`、`os.environ.get` |
| `_secret_fingerprint` — `_secret_fingerprint(value)` | function / [1892](../../../../agent/src/sr2fpga_agent/runner.py#L1892) | `<dynamic>.hexdigest`、`hashlib.sha256`、`value.encode` |
| `_seed_capability_diagnostics` — `_seed_capability_diagnostics(config, samples)` | function / [1896](../../../../agent/src/sr2fpga_agent/runner.py#L1896) | `errors.append`、`load_development_provider_seed_capability`、`payload.get`、`require_paired_confirmatory_seed_capability`、`resolve_source_connection`、`sorted`、`source_names.add`、`str` |
| `_seed_capability_manifest_ref` — `_seed_capability_manifest_ref(connection)` | function / [1978](../../../../agent/src/sr2fpga_agent/runner.py#L1978) | `<dynamic>.hexdigest`、`Path`、`ValueError`、`bool`、`hashlib.sha256`、`load_development_provider_seed_capability`、`manifest_path.read_bytes`、`str` |
| `_source_auth_diagnostics` — `_source_auth_diagnostics(config, samples, validate_provider)` | function / [2006](../../../../agent/src/sr2fpga_agent/runner.py#L2006) | `_check_source_auth`、`set` |
| `_check_source_auth` — `_check_source_auth(config, source, seen, diagnostics, errors, validate_provider)` | function / [2021](../../../../agent/src/sr2fpga_agent/runner.py#L2021) | `_preflight_client`、`_sanitize_secret`、`client.stream_chat`、`errors.append`、`os.environ.get`、`resolve_source_connection`、`seen.add`、`sorted`、`str` |
| `_provider_auth_timeout_seconds` — `_provider_auth_timeout_seconds(connection)` | function / [2070](../../../../agent/src/sr2fpga_agent/runner.py#L2070) | `max`、`min` |
| `_preflight_client` — `_preflight_client(connection, api_key)` | function / [2074](../../../../agent/src/sr2fpga_agent/runner.py#L2074) | `AnthropicCompatibleClient`、`AnthropicCompatibleConfig`、`OpenAICompatibleClient`、`OpenAICompatibleConfig`、`_provider_auth_timeout_seconds` |
| `_sanitize_secret` — `_sanitize_secret(text, secret)` | function / [2103](../../../../agent/src/sr2fpga_agent/runner.py#L2103) | `text.replace` |
| `_record_completed` — `_record_completed(state, sample_id, next_index, bucket, sample_dir)` | function / [2109](../../../../agent/src/sr2fpga_agent/runner.py#L2109) | `<dynamic>.append`、`<dynamic>.items`、`RunState`、`_sample_failure_types`、`buckets.setdefault`、`completed_samples.append`、`dict`、`failure_types.get`、`list`、`state.buckets.items` |
| `_record_rejected` — `_record_rejected(state, sample_id, next_index, failure_type)` | function / [2140](../../../../agent/src/sr2fpga_agent/runner.py#L2140) | `<dynamic>.append`、`RunState`、`buckets.setdefault`、`completed_samples.append`、`dict`、`failure_types.get`、`list`、`state.buckets.items` |
| `_record_blocked_by_shared_checkpoint` — `_record_blocked_by_shared_checkpoint(state, sample_id, next_index)` | function / [2164](../../../../agent/src/sr2fpga_agent/runner.py#L2164) | `<dynamic>.append`、`RunState`、`buckets.setdefault`、`completed_samples.append`、`dict`、`failure_types.get`、`list`、`state.buckets.items` |
| `_read_labels` — `_read_labels(sample_dir)` | function / [2188](../../../../agent/src/sr2fpga_agent/runner.py#L2188) | `<dynamic>.read_text`、`json.loads` |
| `_sample_has_measurement` — `_sample_has_measurement(sample_dir)` | function / [2192](../../../../agent/src/sr2fpga_agent/runner.py#L2192) | `isinstance`、`json.loads`、`path.exists`、`path.read_text`、`payload.get` |
| `_sample_failure_types` — `_sample_failure_types(sample_dir)` | function / [2203](../../../../agent/src/sr2fpga_agent/runner.py#L2203) | `attempts_dir.exists`、`attempts_dir.glob`、`counts.get`、`diagnosis.get`、`diagnosis_path.read_text`、`json.loads`、`sorted`、`str` |
| `_failure_family` — `_failure_family(failure_type, stage)` | function / [2215](../../../../agent/src/sr2fpga_agent/runner.py#L2215) | 无直接调用 |
| `_sample_failure_families` — `_sample_failure_families(sample_dir)` | function / [2242](../../../../agent/src/sr2fpga_agent/runner.py#L2242) | `_failure_family`、`attempts_dir.exists`、`attempts_dir.glob`、`diagnosis.get`、`diagnosis_path.read_text`、`families.add`、`json.loads`、`set`、`sorted`、`str` |
| `_sample_attempt_stage_transitions` — `_sample_attempt_stage_transitions(sample_dir)` | function / [2258](../../../../agent/src/sr2fpga_agent/runner.py#L2258) | `<dynamic>.strip`、`attempts_dir.exists`、`attempts_dir.glob`、`diagnosis.get`、`diagnosis_path.read_text`、`json.loads`、`sorted`、`stages.append`、`str`、`transitions.get`、`zip` |
| `_sample_latent_testbench_issues` — `_sample_latent_testbench_issues(sample_dir)` | function / [2276](../../../../agent/src/sr2fpga_agent/runner.py#L2276) | `check_testbench_static_issues`、`counts.get`、`sample_dir.glob`、`sorted`、`testbench_path.read_text` |
| `_summary` — `_summary(config, state)` | function / [2285](../../../../agent/src/sr2fpga_agent/runner.py#L2285) | `_calibration_breakdown`、`len`、`planned_samples` |
| `_calibration_breakdown` — `_calibration_breakdown(dataset_root, sample_ids)` | function / [2320](../../../../agent/src/sr2fpga_agent/runner.py#L2320) | `<dynamic>.get`、`<dynamic>.items`、`<dynamic>.strip`、`_calibration_rates`、`_count_derived_training_views`、`_count_generated_his_credit`、`_count_h_stage_labels`、`_count_independent_oracle`、`_count_level_labels`、`_count_oracle_strength`、`_count_repair_metrics`、`_finalize_oracle_strength`、`_finalize_repair_metrics`、`_l4_commercial_skip_reason`、`_l4_commercial_status`、`_l4_open_skip_reason`、`_l4_open_status`、`_read_sample_metadata`、`_record_calibration_cell`、`_sample_attempt_stage_transitions`、`_sample_failure_families`、`_sample_latent_testbench_issues`、`attempt_stage_transition_breakdown.get`、`failure_family_breakdown.get`、`json.loads`、`l4_commercial_skip_reasons.get`、`l4_open_skip_reasons.get`、`labels.get`、`labels_path.exists`、`labels_path.read_text`、`latent_testbench_issue_breakdown.get`、`metadata.get`、`pass_level_breakdown.get`、`sorted`、`str`、`toolchain_environment_failures.get` |
| `_count_oracle_strength` — `_count_oracle_strength(summary, sample_dir)` | function / [2484](../../../../agent/src/sr2fpga_agent/runner.py#L2484) | `_safe_nonnegative_int`、`counts.get`、`int`、`isinstance`、`json.loads`、`path.exists`、`path.read_text`、`payload.get`、`strength.get` |
| `_finalize_oracle_strength` — `_finalize_oracle_strength(summary)` | function / [2518](../../../../agent/src/sr2fpga_agent/runner.py#L2518) | `int`、`round` |
| `_count_independent_oracle` — `_count_independent_oracle(summary, labels, metadata)` | function / [2539](../../../../agent/src/sr2fpga_agent/runner.py#L2539) | `<dynamic>.setdefault`、`<dynamic>.strip`、`_ORACLE_DOMAIN_BY_FAMILY.get`、`int`、`labels.get`、`metadata.get`、`str` |
| `_count_repair_metrics` — `_count_repair_metrics(summary, sample_dir)` | function / [2565](../../../../agent/src/sr2fpga_agent/runner.py#L2565) | `any`、`bool`、`int`、`isinstance`、`json.loads`、`patch.get`、`path.exists`、`path.read_text`、`payload.get`、`regression.get`、`str` |
| `_finalize_repair_metrics` — `_finalize_repair_metrics(summary)` | function / [2600](../../../../agent/src/sr2fpga_agent/runner.py#L2600) | `int`、`round` |
| `_l4_open_status` — `_l4_open_status(labels)` | function / [2610](../../../../agent/src/sr2fpga_agent/runner.py#L2610) | `checks.get`、`isinstance`、`labels.get` |
| `_l4_open_skip_reason` — `_l4_open_skip_reason(labels, status)` | function / [2624](../../../../agent/src/sr2fpga_agent/runner.py#L2624) | `checks.get`、`isinstance`、`labels.get` |
| `_l4_commercial_status` — `_l4_commercial_status(labels)` | function / [2635](../../../../agent/src/sr2fpga_agent/runner.py#L2635) | `checks.get`、`isinstance`、`labels.get` |
| `_l4_commercial_skip_reason` — `_l4_commercial_skip_reason(labels, status)` | function / [2644](../../../../agent/src/sr2fpga_agent/runner.py#L2644) | `checks.get`、`isinstance`、`labels.get` |
| `_count_h_stage_labels` — `_count_h_stage_labels(h_stage, labels)` | function / [2655](../../../../agent/src/sr2fpga_agent/runner.py#L2655) | `labels.get` |
| `_count_level_labels` — `_count_level_labels(levels, labels)` | function / [2671](../../../../agent/src/sr2fpga_agent/runner.py#L2671) | `<dynamic>.get`、`_l4_open_status`、`checks.get`、`isinstance`、`labels.get`、`level_checks.items` |
| `_count_generated_his_credit` — `_count_generated_his_credit(generated_his_credit, generated_his_pass_level_breakdown, labels, pass_level)` | function / [2696](../../../../agent/src/sr2fpga_agent/runner.py#L2696) | `generated_his_credit.get`、`generated_his_pass_level_breakdown.get`、`labels.get`、`str` |
| `_count_derived_training_views` — `_count_derived_training_views(views, sample_dir)` | function / [2713](../../../../agent/src/sr2fpga_agent/runner.py#L2713) | `_derived_training_view_rows`、`_safe_nonnegative_int`、`bool`、`isinstance`、`json.loads`、`sample_views.items`、`str`、`trajectory.get`、`trajectory_path.exists`、`trajectory_path.read_text`、`value.get`、`views.setdefault` |
| `_derived_training_view_rows` — `_derived_training_view_rows(view_name, value, sample_dir)` | function / [2758](../../../../agent/src/sr2fpga_agent/runner.py#L2758) | `_safe_nonnegative_int`、`any`、`part.startswith`、`path.is_file`、`path.relative_to`、`project_dir.exists`、`project_dir.rglob`、`sum`、`value.get` |
| `_safe_nonnegative_int` — `_safe_nonnegative_int(value, default)` | function / [2775](../../../../agent/src/sr2fpga_agent/runner.py#L2775) | `int`、`isinstance` |
| `_record_calibration_cell` — `_record_calibration_cell(cells, value, pass_level, l0_contract_failed)` | function / [2785](../../../../agent/src/sr2fpga_agent/runner.py#L2785) | `<dynamic>.get`、`cells.setdefault` |
| `_calibration_rates` — `_calibration_rates(counts)` | function / [2798](../../../../agent/src/sr2fpga_agent/runner.py#L2798) | `<dynamic>.items`、`_passes_at_least`、`cell.get`、`cells.items`、`counts.items`、`int`、`str`、`sum` |
| `_passes_at_least` — `_passes_at_least(pass_level, minimum)` | function / [2825](../../../../agent/src/sr2fpga_agent/runner.py#L2825) | `_PASS_LEVEL_ORDER.get` |
| `_read_sample_metadata` — `_read_sample_metadata(sample_dir)` | function / [2829](../../../../agent/src/sr2fpga_agent/runner.py#L2829) | `json.loads`、`path.exists`、`path.read_text` |
| `_write_json` — `_write_json(path, payload)` | function / [2836](../../../../agent/src/sr2fpga_agent/runner.py#L2836) | `json.dumps`、`path.parent.mkdir`、`path.write_text` |
| `_append_event` — `_append_event(path, payload)` | function / [2841](../../../../agent/src/sr2fpga_agent/runner.py#L2841) | `json.dumps`、`output.write`、`path.open`、`path.parent.mkdir` |
| `_parse_bool` — `_parse_bool(value, name)` | function / [2847](../../../../agent/src/sr2fpga_agent/runner.py#L2847) | `<dynamic>.lower`、`SystemExit`、`isinstance`、`value.strip` |
| `_load_l4_open_config` — `_load_l4_open_config(raw, default_run_policy)` | function / [2859](../../../../agent/src/sr2fpga_agent/runner.py#L2859) | `<dynamic>.strip`、`L4OpenConfig`、`SystemExit`、`all`、`family_id.strip`、`int`、`isinstance`、`raw.get`、`str`、`tuple` |
| `_load_l4_commercial_config` — `_load_l4_commercial_config(raw, default_run_policy)` | function / [2883](../../../../agent/src/sr2fpga_agent/runner.py#L2883) | `L4CommercialConfig`、`SystemExit`、`int`、`isinstance`、`raw.get`、`str` |
| `_l4_open_enabled_for_config` — `_l4_open_enabled_for_config(config)` | function / [2903](../../../../agent/src/sr2fpga_agent/runner.py#L2903) | 无直接调用 |
| `_l4_open_enabled_for_sample` — `_l4_open_enabled_for_sample(config, sample)` | function / [2909](../../../../agent/src/sr2fpga_agent/runner.py#L2909) | `_l4_open_enabled_for_config`、`task_family_spec_for_alias` |
| `_l4_commercial_enabled_for_config` — `_l4_commercial_enabled_for_config(config)` | function / [2925](../../../../agent/src/sr2fpga_agent/runner.py#L2925) | 无直接调用 |
| `_l4_commercial_enabled_for_sample` — `_l4_commercial_enabled_for_sample(config, sample)` | function / [2931](../../../../agent/src/sr2fpga_agent/runner.py#L2931) | `_l4_commercial_enabled_for_config`、`task_family_spec_for_alias` |
| `_load_optional_string` — `_load_optional_string(item, field_name)` | function / [2940](../../../../agent/src/sr2fpga_agent/runner.py#L2940) | `SystemExit`、`isinstance`、`value.strip` |
| `_load_task_config` — `_load_task_config(item, raw)` | function / [2949](../../../../agent/src/sr2fpga_agent/runner.py#L2949) | `<dynamic>.join`、`<dynamic>.strip`、`SystemExit`、`TaskConfig`、`_load_optional_string`、`_validate_task_pairing_identity`、`int`、`isinstance`、`item.get`、`raw.get`、`requirement.strip`、`sorted`、`str` |
| `resolve_source_connection` — `resolve_source_connection(config, source)` | function / [3062](../../../../agent/src/sr2fpga_agent/runner.py#L3062) | `SourceConnection`、`source.startswith` |
| `_load_sources` — `_load_sources(raw)` | function / [3095](../../../../agent/src/sr2fpga_agent/runner.py#L3095) | `<dynamic>.startswith`、`SourceConnection`、`SystemExit`、`_GENERATION_MODE_BY_KIND.get`、`int`、`isinstance`、`item.get`、`raw.items`、`str` |
| `_load_mapping` — `_load_mapping(path)` | function / [3167](../../../../agent/src/sr2fpga_agent/runner.py#L3167) | `SystemExit`、`isinstance`、`json.loads`、`path.read_text`、`yaml.safe_load` |
| `_validate_task_pairing_identity` — `_validate_task_pairing_identity(analysis_population, method_condition, count, semantic_instance_id, replicate_id, decoding_seed, decoding_seed_supplied, paired_block_id, execution_schedule_seed, decoding_control_mode)` | function / [3182](../../../../agent/src/sr2fpga_agent/runner.py#L3182) | `SystemExit`、`_PAIRED_ID_RE.fullmatch`、`all`、`any`、`bool`、`isinstance` |
| `_resolve_planned_pairing_identity` — `_resolve_planned_pairing_identity(task, requirement_sha256)` | function / [3264](../../../../agent/src/sr2fpga_agent/runner.py#L3264) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`hashlib.sha256`、`int` |
| `_validate_planned_pairing_blocks` — `_validate_planned_pairing_blocks(samples)` | function / [3297](../../../../agent/src/sr2fpga_agent/runner.py#L3297) | `<dynamic>.append`、`SystemExit`、`block_methods.items`、`block_methods.setdefault`、`blocks.setdefault`、`build_balanced_method_orders`、`len`、`methods.add`、`set`、`tuple` |
| `planned_samples` — `planned_samples(config)` | function / [3348](../../../../agent/src/sr2fpga_agent/runner.py#L3348) | `<dynamic>.hexdigest`、`<dynamic>.join`、`PlannedSample`、`SystemExit`、`_default_requirement`、`_resolve_planned_pairing_identity`、`_task_expansion_items`、`_validate_paired_block_truncation`、`_validate_planned_pairing_blocks`、`_validate_task_pairing_identity`、`config.line_b_targets.get`、`hashlib.sha256`、`int`、`len`、`list`、`requirement.encode`、`samples.append`、`sorted`、`task.requirement.strip` |
| `_validate_paired_block_truncation` — `_validate_paired_block_truncation(all_samples, selected_samples)` | function / [3442](../../../../agent/src/sr2fpga_agent/runner.py#L3442) | `SystemExit`、`declared_counts.get`、`declared_counts.items`、`len`、`selected_counts.get` |
| `_task_expansion_items` — `_task_expansion_items(task)` | function / [3469](../../../../agent/src/sr2fpga_agent/runner.py#L3469) | `SystemExit`、`_topology_id_to_task_type`、`items.append`、`sorted`、`task_family_spec_for_alias` |
| `_topology_id_to_task_type` — `_topology_id_to_task_type()` | function / [3492](../../../../agent/src/sr2fpga_agent/runner.py#L3492) | `COMPONENT_TOPOLOGIES.items`、`str` |
| `_default_requirement` — `_default_requirement(task_type, width, topology_id, requirement_style)` | function / [3496](../../../../agent/src/sr2fpga_agent/runner.py#L3496) | `_natural_component_requirement`、`_simple_prompt_requirement`、`_topology_requirement_clause` |
| `_simple_prompt_requirement` — `_simple_prompt_requirement(task_type, width)` | function / [3515](../../../../agent/src/sr2fpga_agent/runner.py#L3515) | `prompts.get` |
| `_natural_component_requirement` — `_natural_component_requirement(task_type, width, topology_id)` | function / [3602](../../../../agent/src/sr2fpga_agent/runner.py#L3602) | `<dynamic>.join`、`_natural_component_summary`、`_natural_component_title`、`_topology_expected_behavior` |
| `_natural_component_title` — `_natural_component_title(task_type)` | function / [3619](../../../../agent/src/sr2fpga_agent/runner.py#L3619) | 无直接调用 |
| `_natural_component_summary` — `_natural_component_summary(task_type)` | function / [3637](../../../../agent/src/sr2fpga_agent/runner.py#L3637) | 无直接调用 |
| `_topology_requirement_clause` — `_topology_requirement_clause(task_type, topology_id)` | function / [3679](../../../../agent/src/sr2fpga_agent/runner.py#L3679) | `<dynamic>.join`、`_topology_expected_behavior` |
| `_topology_expected_behavior` — `_topology_expected_behavior(task_type)` | function / [3694](../../../../agent/src/sr2fpga_agent/runner.py#L3694) | 无直接调用 |
| `_sample_failure_origin` — `_sample_failure_origin(sample, config)` | function / [3744](../../../../agent/src/sr2fpga_agent/runner.py#L3744) | `SystemExit`、`resolve_source_connection`、`str`、`validate_accounting_failure_origin` |
| `_sample_method_condition` — `_sample_method_condition(sample, config)` | function / [3766](../../../../agent/src/sr2fpga_agent/runner.py#L3766) | `SystemExit`、`resolve_source_connection` |
| `_sample_model_call_ceiling` — `_sample_model_call_ceiling(sample, config, method_condition)` | function / [3799](../../../../agent/src/sr2fpga_agent/runner.py#L3799) | `SystemExit`、`_sample_method_condition`、`assert_b4_conformant`、`budget_allocation`、`max` |
| `_exclusive_model_call_ceiling` — `_exclusive_model_call_ceiling(config, sample, method_condition)` | function / [3841](../../../../agent/src/sr2fpga_agent/runner.py#L3841) | `SystemExit`、`_sample_model_call_ceiling` |
| `_sample_attempt_limit` — `_sample_attempt_limit(config, method_condition)` | function / [3861](../../../../agent/src/sr2fpga_agent/runner.py#L3861) | `max` |
| `_sample_system_his_schema_version` — `_sample_system_his_schema_version(sample, config)` | function / [3867](../../../../agent/src/sr2fpga_agent/runner.py#L3867) | `resolve_source_connection` |
| `_contract_skeleton_mode` — `_contract_skeleton_mode(sample, config)` | function / [3882](../../../../agent/src/sr2fpga_agent/runner.py#L3882) | `_sample_method_condition`、`resolve_source_connection` |
| `_training_split` — `_training_split(schema_version)` | function / [3898](../../../../agent/src/sr2fpga_agent/runner.py#L3898) | `<dynamic>.classify`、`load_system_his_compatibility_envelope` |
| `_measurement_point` — `_measurement_point(config)` | function / [3902](../../../../agent/src/sr2fpga_agent/runner.py#L3902) | 无直接调用 |
| `_measurement_point_for_method` — `_measurement_point_for_method(config, method_condition)` | function / [3908](../../../../agent/src/sr2fpga_agent/runner.py#L3908) | `_measurement_point` |
| `_project_generator_for_sample` — `_project_generator_for_sample(project_generators, config, sample, events_path, model_budget, metadata, method_artifact_store, paired_artifact_coordinator, paired_block_ref, execution_ordinal, prepared_block_runtime, block_preparation_audit)` | function / [3917](../../../../agent/src/sr2fpga_agent/runner.py#L3917) | `<dynamic>.get`、`FailureInjectingProjectGenerator`、`ProjectGenerator`、`SystemExit`、`_bind_frozen_direct_generator`、`_bind_runner_method_generator`、`_generation_event_sink`、`_model_client_for_sample`、`_validated_block_preparation_audit`、`build_project_generator_for_connection`、`metadata.get`、`resolve_source_connection`、`str` |
| `_validated_block_preparation_audit` — `_validated_block_preparation_audit(metadata, prepared_block_runtime, block_preparation_audit)` | function / [4022](../../../../agent/src/sr2fpga_agent/runner.py#L4022) | `SystemExit`、`TypeError`、`any`、`dict`、`expected_refs.items`、`isinstance`、`metadata.get`、`prepared.manifest_ref.to_dict`、`prepared.paired_block_ref.to_dict`、`re.fullmatch`、`reference.to_dict`、`set` |
| `_model_client_for_sample` — `_model_client_for_sample(config, sample, model_budget, stage)` | function / [4092](../../../../agent/src/sr2fpga_agent/runner.py#L4092) | `AnthropicCompatibleClient`、`AnthropicCompatibleConfig`、`OpenAICompatibleClient`、`OpenAICompatibleConfig`、`SystemExit`、`model_budget.client`、`os.environ.get`、`resolve_source_connection` |
| `_bind_frozen_direct_generator` — `_bind_frozen_direct_generator(generator, metadata)` | function / [4141](../../../../agent/src/sr2fpga_agent/runner.py#L4141) | `FrozenContextDirectProjectGenerator`、`SystemExit`、`context_from_validated_episode_pack`、`isinstance`、`metadata.get` |
| `_bind_runner_method_generator` — `_bind_runner_method_generator(generator, metadata, config, sample, method_artifact_store, paired_artifact_coordinator, prepared_block_runtime, exclusive_model_client)` | function / [4157](../../../../agent/src/sr2fpga_agent/runner.py#L4157) | `<dynamic>.get`、`ArtifactRef`、`FrozenContextDirectProjectFacade`、`FrozenContextHisGeneratorBridge`、`FrozenContextSystemHisCorrectionFacade`、`FrozenContextSystemHisFacade`、`FrozenContextSystemHisValidationFacade`、`FrozenContextUntypedPlanFacade`、`GenerationServices`、`MethodArtifactGateway`、`RuntimeError`、`SharedArtifactRefs`、`SystemExit`、`_RunnerDirectMethodProjectGenerator`、`_RunnerUntypedPlanProjectGenerator`、`_platform_profile_for_config`、`_runner_pairing_key`、`client_for_stage`、`context_from_validated_episode_pack`、`getattr`、`isinstance`、`str` |
| `_runner_model_provenance_sha256` — `_runner_model_provenance_sha256(config, sample)` | function / [4324](../../../../agent/src/sr2fpga_agent/runner.py#L4324) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`_runner_block_model_identity`、`hashlib.sha256`、`json.dumps` |
| `_plan_development_paired_blocks` — `_plan_development_paired_blocks(config, samples)` | function / [4338](../../../../agent/src/sr2fpga_agent/runner.py#L4338) | `<dynamic>.append`、`<dynamic>.encode`、`<dynamic>.hexdigest`、`SystemExit`、`_PlannedPairedBlock`、`_runner_block_model_identity`、`all`、`any`、`build_development_paired_block`、`development_paired_block_reference`、`grouped.items`、`grouped.setdefault`、`hashlib.sha256`、`int`、`isinstance`、`item.get`、`iter`、`json.dumps`、`len`、`next`、`sample.metadata`、`tuple` |
| `_plan_block_preparation_policy` — `_plan_block_preparation_policy(config, samples, paired_blocks)` | function / [4414](../../../../agent/src/sr2fpga_agent/runner.py#L4414) | `<dynamic>.encode`、`<dynamic>.get`、`<dynamic>.hexdigest`、`SystemExit`、`_exclusive_model_call_ceiling`、`_runner_block_model_identity`、`_runner_pairing_key`、`any`、`by_method.items`、`context_from_validated_episode_pack`、`first.metadata`、`hashlib.sha256`、`identities.values`、`isinstance`、`json.dumps`、`list`、`paired_blocks.items`、`pairing.digest`、`plan.artifact_ref.to_dict`、`resolve_source_connection`、`set`、`sorted` |
| `_prepare_complete_blocks` — `_prepare_complete_blocks(config, samples, paired_block_plans, paired_block_refs, store, freeze_fingerprint)` | function / [4505](../../../../agent/src/sr2fpga_agent/runner.py#L4505) | `<dynamic>.get`、`BlockPreparationCostLedger`、`BlockPreparationFacades`、`FrozenContextDirectProjectFacade`、`FrozenContextSystemHisFacade`、`FrozenContextSystemHisValidationFacade`、`ModelCallBudget`、`PreparedBlockRuntime`、`RuntimeError`、`SystemExit`、`ValueError`、`_load_prepared_block_runtime`、`_model_client_for_sample`、`_plan_block_preparation_policy`、`_platform_profile_for_config`、`_runner_pairing_key`、`_sample_failure_origin`、`blocked_methods_from_verified_manifest`、`context_from_validated_episode_pack`、`dict`、`direct_sample.metadata`、`his_sample.metadata`、`isinstance`、`paired_block_plans.items`、`paired_block_ref.to_dict`、`prepare_development_paired_block`、`re.fullmatch`、`sorted`、`str`、`validate_development_block_preparation_policy`、`verify_development_shared_checkpoint_manifest_against_policy` |
| `_preflight_existing_block_preparation_resume` — `_preflight_existing_block_preparation_resume(run_dir, dataset_root, state, paired_block_plans, block_preparation_policies)` | function / [4627](../../../../agent/src/sr2fpga_agent/runner.py#L4627) | `<dynamic>.read_text`、`ArtifactRef`、`ArtifactStore`、`TypeError`、`ValueError`、`_event_recorded_block_preparation_audits`、`_load_prepared_block_runtime`、`_prepared_block_audit_record`、`_shared_checkpoint_resume_error`、`_validated_resume_sample_records`、`block_preparation_policies.items`、`config_path.read_text`、`dict`、`frozen.get`、`isinstance`、`json.loads`、`measurement_freeze_fingerprint`、`original_audit.get`、`plan.artifact_ref.to_dict`、`set`、`sorted`、`store_root.is_dir`、`str` |
| `_event_recorded_block_preparation_audits` — `_event_recorded_block_preparation_audits(events_path, expected_records, expected_audits, freeze_fingerprint, state, dataset_root, store)` | function / [4752](../../../../agent/src/sr2fpga_agent/runner.py#L4752) | `<dynamic>.append`、`<dynamic>.splitlines`、`_read_labels`、`_shared_checkpoint_resume_error`、`_validate_completed_resume_event`、`any`、`classify_sample_bucket`、`completions.append`、`dict`、`enumerate`、`event.get`、`events_path.exists`、`events_path.read_text`、`expected_audits.items`、`int`、`isinstance`、`json.loads`、`len`、`line.strip`、`owners.get`、`raw_audit.get`、`sample_dir.exists`、`sample_dir.is_dir`、`set`、`state.buckets.items` |
| `_validated_resume_sample_records` — `_validated_resume_sample_records(frozen, paired_block_plans)` | function / [4919](../../../../agent/src/sr2fpga_agent/runner.py#L4919) | `_shared_checkpoint_resume_error`、`all`、`enumerate`、`frozen.get`、`isinstance`、`len`、`paired_block_plans.items`、`paired_block_plans.values`、`plan.artifact_ref.to_dict`、`record.get`、`set`、`tuple`、`zip` |
| `_validate_completed_resume_event` — `_validate_completed_resume_event(event, record, expected_audit, dataset_root, store)` | function / [4971](../../../../agent/src/sr2fpga_agent/runner.py#L4971) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.read_text`、`<dynamic>.validate`、`ArtifactRef`、`ContractRegistry`、`ValueError`、`_project_emission_from_ref`、`_require_resume_store_reference`、`_shared_checkpoint_resume_error`、`event.get`、`json.loads`、`metadata.get`、`method_artifacts.get`、`store.read_verified`、`str`、`trajectory.get` |
| `_require_resume_store_reference` — `_require_resume_store_reference(store, reference, label)` | function / [5064](../../../../agent/src/sr2fpga_agent/runner.py#L5064) | `ValueError`、`store.read_verified`、`store.reference` |
| `_prepared_block_audit_record` — `_prepared_block_audit_record(policy, runtime)` | function / [5074](../../../../agent/src/sr2fpga_agent/runner.py#L5074) | `dict`、`reference.to_dict`、`runtime.prepared.manifest_ref.to_dict`、`runtime.prepared.paired_block_ref.to_dict` |
| `_prepared_runtime_accounting_input_hashes` — `_prepared_runtime_accounting_input_hashes(method_condition, runtime, store)` | function / [5100](../../../../agent/src/sr2fpga_agent/runner.py#L5100) | `ArtifactRef`、`MethodArtifactGateway`、`RuntimeError`、`SystemExit`、`artifacts.read_planning`、`artifacts.read_project`、`input_hashes.add`、`read_development_shared_checkpoint_manifest`、`tuple`、`verify_development_shared_checkpoint_manifest_against_policy` |
| `_load_prepared_block_runtime` — `_load_prepared_block_runtime(store, expected_preparation_policy, member_sample_ids, exclusive_model_call_ceilings, expected_manifest_ref)` | function / [5181](../../../../agent/src/sr2fpga_agent/runner.py#L5181) | `ArtifactRef`、`PlanningArtifactEmission`、`PreparedBlockArtifacts`、`PreparedBlockRuntime`、`_project_emission_from_checkpoint`、`_project_emission_from_ref`、`_shared_checkpoint_resume_error`、`dict`、`read_complete_development_shared_checkpoint_resume`、`store.read_verified`、`store.reference`、`str`、`tuple` |
| `_shared_checkpoint_resume_error` — `_shared_checkpoint_resume_error(reason)` | function / [5262](../../../../agent/src/sr2fpga_agent/runner.py#L5262) | `SharedCheckpointResumeError` |
| `_project_emission_from_checkpoint` — `_project_emission_from_checkpoint(store, node)` | function / [5268](../../../../agent/src/sr2fpga_agent/runner.py#L5268) | `ArtifactRef`、`ValueError`、`_project_emission_from_ref` |
| `_project_emission_from_ref` — `_project_emission_from_ref(store, reference)` | function / [5279](../../../../agent/src/sr2fpga_agent/runner.py#L5279) | `GeneratedProject`、`ProjectCandidateEmission`、`ValueError`、`dict`、`isinstance`、`json.loads`、`project_package_sha256`、`store.read_verified`、`str` |
| `_materialize_development_paired_blocks` — `_materialize_development_paired_blocks(plans, store)` | function / [5293](../../../../agent/src/sr2fpga_agent/runner.py#L5293) | `RuntimeError`、`load_development_paired_block`、`plans.items`、`tuple`、`write_development_paired_block` |
| `_runner_block_model_identity` — `_runner_block_model_identity(config, sample)` | function / [5325](../../../../agent/src/sr2fpga_agent/runner.py#L5325) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`connection.base_url.rstrip`、`hashlib.sha256`、`resolve_source_connection` |
| `_order_samples_by_paired_blocks` — `_order_samples_by_paired_blocks(samples, plans, paired_block_refs, store)` | function / [5352](../../../../agent/src/sr2fpga_agent/runner.py#L5352) | `SystemExit`、`enumerate`、`list`、`load_development_paired_block`、`paired_block_refs.items`、`set`、`zip` |
| `_paired_execution_ordinals` — `_paired_execution_ordinals(samples, plans, paired_block_refs, store)` | function / [5377](../../../../agent/src/sr2fpga_agent/runner.py#L5377) | `enumerate`、`load_development_paired_block`、`paired_block_refs.items`、`set` |
| `_paired_block_refs_by_sample` — `_paired_block_refs_by_sample(plans, paired_block_refs)` | function / [5394](../../../../agent/src/sr2fpga_agent/runner.py#L5394) | `plans.items` |
| `_runner_pairing_key` — `_runner_pairing_key(config, sample, context)` | function / [5405](../../../../agent/src/sr2fpga_agent/runner.py#L5405) | `PairingKey`、`SystemExit`、`_runner_model_provenance_sha256`、`isinstance` |
| `_verified_missing_terminal_reason` — `_verified_missing_terminal_reason(store, reference, episode_id)` | function / [5425](../../../../agent/src/sr2fpga_agent/runner.py#L5425) | `<dynamic>.load_schema`、`<dynamic>.validate`、`ArtifactRef`、`ContractRegistry`、`RuntimeError`、`isinstance`、`json.loads`、`len`、`reason.startswith`、`reconcile_attempt_trajectory`、`store.read_verified`、`trajectory.get` |
| `_method_artifact_completion_record` — `_method_artifact_completion_record(generator, metadata)` | function / [5457](../../../../agent/src/sr2fpga_agent/runner.py#L5457) | `candidate.artifact_ref.to_dict`、`current.last_initial_planning_artifact.artifact_ref.to_dict`、`getattr`、`h_report.get`、`int`、`isinstance`、`planning.artifact_ref.to_dict`、`record.update`、`reference.to_dict`、`skeleton.artifact_ref.to_dict`、`str` |
| `_repairer_for_sample` — `_repairer_for_sample(repairers, config, sample, model_budget)` | function / [5543](../../../../agent/src/sr2fpga_agent/runner.py#L5543) | `build_repairer_for_connection`、`resolve_source_connection` |
| `_generation_event_sink` — `_generation_event_sink(events_path, sample, config, artifact_store, paired_block_ref, execution_ordinal, block_preparation_audit)` | function / [5570](../../../../agent/src/sr2fpga_agent/runner.py#L5570) | `TypeError`、`artifact_store.put_validated_json`、`isinstance`、`load_development_provider_seed_capability`、`resolve_source_connection` |
| `_generation_event_sink.emit` — `emit(payload)` | function / [5605](../../../../agent/src/sr2fpga_agent/runner.py#L5605) | `_append_event`、`_sample_failure_origin`、`_sample_method_condition`、`dict`、`enriched.get`、`enriched.update`、`paired_block_ref.to_dict`、`provenance_ref.to_dict`、`seed_control_evidence_refs.get`、`write_model_gateway_provenance` |
| `_update_sample_model_budget` — `_update_sample_model_budget(sample_dir, summary)` | function / [5657](../../../../agent/src/sr2fpga_agent/runner.py#L5657) | `ValueError`、`_write_json`、`isinstance`、`json.loads`、`metadata_path.exists`、`metadata_path.read_text` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`、`main`、`re.compile`

## `agent/src/sr2fpga_agent/semantic_trace.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/semantic_trace.py) · 104 行 · SHA-256 `ea4cde1aaeddfb7223335e3df4cda94369ce49bfc55cda149a6c2e117d064126`

> Semantic trace helpers for valid-ready simulation logs.

导入模块：`__future__`、`re`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `parse_semantic_trace` — `parse_semantic_trace(log_text)` | function / [17](../../../../agent/src/sr2fpga_agent/semantic_trace.py#L17) | `<dynamic>.append`、`TRACE_GROUPS.get`、`_parse_trace_fields`、`log_text.splitlines`、`match.group`、`raw_line.strip`、`re.match` |
| `summarize_semantic_trace` — `summarize_semantic_trace(trace)` | function / [37](../../../../agent/src/sr2fpga_agent/semantic_trace.py#L37) | `len`、`output.get`、`trace.get` |
| `diagnose_semantic_trace` — `diagnose_semantic_trace(trace)` | function / [61](../../../../agent/src/sr2fpga_agent/semantic_trace.py#L61) | `_duplicate_input_accepts`、`summarize_semantic_trace`、`trace.get` |
| `_duplicate_input_accepts` — `_duplicate_input_accepts(input_accepts)` | function / [77](../../../../agent/src/sr2fpga_agent/semantic_trace.py#L77) | `duplicates.append`、`event.get`、`previous.get`、`previous_by_lane.get` |
| `_parse_trace_fields` — `_parse_trace_fields(field_text)` | function / [100](../../../../agent/src/sr2fpga_agent/semantic_trace.py#L100) | `int`、`re.findall` |

## `agent/src/sr2fpga_agent/system_his_capabilities.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py) · 266 行 · SHA-256 `60fbfd0e182ee234978c6d1964af59e70ca5544b73d50dde5a504f5b0c548f17`

> Load the versioned System-HIS backend capability contract.

导入模块：`__future__`、`collections.abc`、`dataclasses`、`json`、`pathlib`、`sr2fpga_agent.repository_paths`、`types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SystemHisCapabilityRegistryError` — `SystemHisCapabilityRegistryError` | class / [27](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L27) | 无直接调用 |
| `SystemHisBackendCapabilities` — `SystemHisBackendCapabilities` | class / [32](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L32) | 无直接调用 |
| `SystemHisBackendCapabilities.__post_init__` — `__post_init__(self)` | function / [44](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L44) | `MappingProxyType`、`dict`、`frozenset`、`object.__setattr__` |
| `load_system_his_backend_capabilities` — `load_system_his_backend_capabilities(repository_paths)` | function / [72](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L72) | `RepositoryPaths.discover`、`SystemHisBackendCapabilities`、`SystemHisCapabilityRegistryError`、`_contract_record`、`_load_json_object`、`_load_named_capabilities`、`_require_exact_keys`、`_require_object`、`_require_string`、`_require_unique_strings`、`_resolve_registered_path`、`_validate_relative_posix_path`、`capability_record.get`、`frozenset`、`manifest.get`、`payload.get`、`system_his_record.get`、`verification.get` |
| `_load_json_object` — `_load_json_object(path, label)` | function / [153](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L153) | `SystemHisCapabilityRegistryError`、`_require_object`、`json.load`、`path.open` |
| `_object_without_duplicate_keys` — `_object_without_duplicate_keys(pairs)` | function / [162](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L162) | `SystemHisCapabilityRegistryError` |
| `_contract_record` — `_contract_record(contracts, name)` | function / [171](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L171) | `_require_exact_keys`、`_require_object`、`contracts.get`、`frozenset` |
| `_resolve_registered_path` — `_resolve_registered_path(root, relative_path)` | function / [177](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L177) | `<dynamic>.resolve`、`SystemHisCapabilityRegistryError`、`_validate_relative_posix_path`、`resolved_path.is_relative_to`、`resolved_root.joinpath`、`root.resolve` |
| `_validate_relative_posix_path` — `_validate_relative_posix_path(value, label)` | function / [188](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L188) | `PurePosixPath`、`SystemHisCapabilityRegistryError`、`posix_path.as_posix`、`posix_path.is_absolute` |
| `_load_named_capabilities` — `_load_named_capabilities(value, label)` | function / [203](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L203) | `<dynamic>.difference`、`SystemHisCapabilityRegistryError`、`_require_exact_keys`、`_require_object`、`_require_string_mapping`、`_require_unique_strings`、`aliases.values`、`frozenset`、`section.get`、`set`、`sorted`、`supported.intersection` |
| `_require_object` — `_require_object(value, label)` | function / [224](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L224) | `SystemHisCapabilityRegistryError`、`isinstance` |
| `_require_exact_keys` — `_require_exact_keys(value, expected, label)` | function / [230](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L230) | `SystemHisCapabilityRegistryError`、`actual.difference`、`expected.difference`、`set`、`sorted` |
| `_require_string` — `_require_string(value, label)` | function / [245](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L245) | `SystemHisCapabilityRegistryError`、`isinstance`、`value.strip` |
| `_require_unique_strings` — `_require_unique_strings(value, label)` | function / [251](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L251) | `SystemHisCapabilityRegistryError`、`_require_string`、`frozenset`、`isinstance`、`len`、`set`、`tuple` |
| `_require_string_mapping` — `_require_string_mapping(value, label)` | function / [260](../../../../agent/src/sr2fpga_agent/system_his_capabilities.py#L260) | `MappingProxyType`、`_require_object`、`_require_string`、`mapping.items` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`

## `agent/src/sr2fpga_agent/system_his_checker.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/system_his_checker.py) · 663 行 · SHA-256 `bc73ce592e60e3e625911b3f69708aa2be71471fee4fbff6917b0c6c8c80af4d`

> System-HIS contract checks for project-level L0 validation.

导入模块：`__future__`、`dataclasses`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.rtl_introspect`、`sr2fpga_agent.system_his_v12_checker`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `L0CheckResult` — `L0CheckResult` | class / [25](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L25) | `field` |
| `check_project_l0` — `check_project_l0(project)` | function / [33](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L33) | `L0CheckResult`、`check_his_project_consistency`、`check_project_package_l0` |
| `check_his_project_consistency` — `check_his_project_consistency(project)` | function / [49](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L49) | `<dynamic>.strip`、`L0CheckResult`、`_check_project_l0_v12`、`_manifest_artifact_paths`、`_read_json_file`、`_require_manifest_artifact_role`、`_string_list`、`_validate_clocks`、`_validate_his_connections`、`_validate_his_modules`、`_validate_qor_intent`、`_validate_resets`、`_validate_testbench_instantiates_top`、`_validate_timing_constraint_ports`、`_validate_top_ports`、`_validate_verification`、`architecture.get`、`declared_module_parameters`、`declared_module_ports`、`declared_modules`、`errors.append`、`isinstance`、`list`、`project_record.get`、`resolve_project_manifest`、`set`、`str`、`system_his.get`、`verification.get`、`warnings.append` |
| `_check_project_l0_v12` — `_check_project_l0_v12(system_his, manifest, project)` | function / [179](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L179) | `<dynamic>.strip`、`L0CheckResult`、`_manifest_artifact_paths`、`_require_manifest_artifact_role`、`_v12_rtl_check_project`、`_validate_timing_constraint_ports`、`_validate_v12_transitional_fields`、`all`、`artifacts.get`、`check_system_his_v12_against_rtl`、`constraint.strip`、`declared_module_ports`、`errors.append`、`errors.extend`、`isinstance`、`list`、`set`、`str`、`system_his.get`、`warnings.extend` |
| `_manifest_artifact_paths` — `_manifest_artifact_paths(manifest, role)` | function / [272](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L272) | `manifest.artifact_paths_by_role.get` |
| `_require_manifest_artifact_role` — `_require_manifest_artifact_role(manifest, role, expected_path, context, errors)` | function / [279](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L279) | `_manifest_artifact_paths`、`errors.append` |
| `_v12_rtl_check_project` — `_v12_rtl_check_project(project, manifest)` | function / [293](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L293) | `GeneratedProject`、`_manifest_artifact_paths`、`dict`、`json.dumps`、`list` |
| `_validate_v12_transitional_fields` — `_validate_v12_transitional_fields(system_his, manifest_sources, project, manifest_top, errors)` | function / [313](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L313) | `_validate_clocks`、`_validate_his_connections`、`_validate_his_modules`、`_validate_qor_intent`、`_validate_resets`、`_validate_top_ports`、`_validate_verification`、`any`、`declared_module_parameters`、`declared_module_ports`、`declared_modules`、`isinstance`、`set`、`system_his.get` |
| `_read_json_file` — `_read_json_file(project, path, errors)` | function / [352](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L352) | `errors.append`、`isinstance`、`json.loads`、`project.files.get` |
| `_string_list` — `_string_list(value, name, errors)` | function / [368](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L368) | `errors.append`、`isinstance`、`item.strip`、`strings.append` |
| `_validate_his_modules` — `_validate_his_modules(value, manifest_sources, declared_modules, declared_parameters, declared_ports, errors)` | function / [381](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L381) | `<dynamic>.strip`、`_params_to_parameters`、`_port_names`、`declared_parameters.get`、`declared_ports.get`、`enumerate`、`errors.append`、`his_modules.add`、`isinstance`、`item.get`、`set`、`sorted`、`str` |
| `_params_to_parameters` — `_params_to_parameters(params)` | function / [442](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L442) | `isinstance`、`item.get`、`str` |
| `_port_names` — `_port_names(value, module_name, rtl_ports, errors)` | function / [450](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L450) | `<dynamic>.strip`、`enumerate`、`errors.append`、`isinstance`、`item.get`、`names.add`、`normalize_width`、`set`、`str` |
| `_validate_his_connections` — `_validate_his_connections(value, his_modules, ports_by_module, errors)` | function / [489](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L489) | `<dynamic>.strip`、`_is_valid_width_value`、`endpoint.get`、`enumerate`、`errors.append`、`isinstance`、`item.get`、`str` |
| `_is_valid_width_value` — `_is_valid_width_value(value)` | function / [531](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L531) | `bool`、`isinstance`、`value.strip` |
| `_validate_clocks` — `_validate_clocks(value, errors)` | function / [539](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L539) | `<dynamic>.strip`、`enumerate`、`errors.append`、`isinstance`、`item.get`、`str` |
| `_validate_resets` — `_validate_resets(value, errors)` | function / [554](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L554) | `<dynamic>.strip`、`enumerate`、`errors.append`、`isinstance`、`item.get`、`str` |
| `_validate_qor_intent` — `_validate_qor_intent(value, errors)` | function / [570](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L570) | `errors.append`、`isinstance`、`value.get` |
| `_validate_verification` — `_validate_verification(value, errors)` | function / [585](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L585) | `<dynamic>.strip`、`all`、`errors.append`、`isinstance`、`item.strip`、`str`、`value.get` |
| `_validate_top_ports` — `_validate_top_ports(value, top_module, declared_ports, errors)` | function / [600](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L600) | `_normalized_port_list`、`declared_ports.get`、`errors.append`、`isinstance`、`str` |
| `_normalized_port_list` — `_normalized_port_list(ports)` | function / [619](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L619) | `<dynamic>.strip`、`normalize_width`、`normalized.append`、`port.get`、`ports.items`、`sorted`、`str` |
| `_validate_testbench_instantiates_top` — `_validate_testbench_instantiates_top(project, testbench, top_module, errors)` | function / [631](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L631) | `errors.append`、`pattern.search`、`re.compile`、`re.escape` |
| `_validate_timing_constraint_ports` — `_validate_timing_constraint_ports(project, timing_constraint, top_module, declared_ports, errors)` | function / [648](../../../../agent/src/sr2fpga_agent/system_his_checker.py#L648) | `declared_ports.get`、`errors.append`、`re.findall`、`set` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/system_his_compatibility.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py) · 258 行 · SHA-256 `7a98b1cc10daef8e66596c9aa109944990788bf9efc3895df70b730e35ce947d`

> Load and apply the registered System-HIS compatibility envelope.

导入模块：`__future__`、`collections.abc`、`dataclasses`、`json`、`pathlib`、`sr2fpga_agent.repository_paths`、`types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SystemHisCompatibilityError` — `SystemHisCompatibilityError` | class / [40](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L40) | 无直接调用 |
| `SystemHisCompatibilityDisposition` — `SystemHisCompatibilityDisposition` | class / [45](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L45) | 无直接调用 |
| `SystemHisCompatibilityEnvelope` — `SystemHisCompatibilityEnvelope` | class / [55](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L55) | 无直接调用 |
| `SystemHisCompatibilityEnvelope.__post_init__` — `__post_init__(self)` | function / [61](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L61) | `MappingProxyType`、`dict`、`object.__setattr__` |
| `SystemHisCompatibilityEnvelope.classify` — `classify(self, representation_id)` | function / [64](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L64) | `SystemHisCompatibilityDisposition`、`isinstance`、`representation_id.strip`、`self.representations.get` |
| `load_system_his_compatibility_envelope` — `load_system_his_compatibility_envelope(repository_paths)` | function / [80](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L80) | `RepositoryPaths.discover`、`SystemHisCompatibilityEnvelope`、`SystemHisCompatibilityError`、`_contract_record`、`_load_object`、`_parse_disposition`、`_require_exact_keys`、`_require_object`、`_require_string`、`_resolve_contract_path`、`enumerate`、`isinstance`、`manifest.get`、`payload.get`、`record.get`、`set`、`system_his_record.get` |
| `_parse_disposition` — `_parse_disposition(value)` | function / [168](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L168) | `SystemHisCompatibilityDisposition`、`_require_choice`、`_require_string`、`value.get` |
| `_load_object` — `_load_object(path, label)` | function / [201](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L201) | `SystemHisCompatibilityError`、`_require_object`、`json.load`、`path.open` |
| `_reject_duplicate_keys` — `_reject_duplicate_keys(pairs)` | function / [210](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L210) | `SystemHisCompatibilityError` |
| `_contract_record` — `_contract_record(contracts, key)` | function / [219](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L219) | `_require_exact_keys`、`_require_object`、`contracts.get`、`frozenset` |
| `_resolve_contract_path` — `_resolve_contract_path(root, raw_path)` | function / [225](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L225) | `<dynamic>.resolve`、`PurePosixPath`、`SystemHisCompatibilityError`、`_require_string`、`posix.as_posix`、`posix.is_absolute`、`resolved.is_relative_to`、`resolved_root.joinpath`、`root.resolve` |
| `_require_object` — `_require_object(value, label)` | function / [237](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L237) | `SystemHisCompatibilityError`、`isinstance` |
| `_require_exact_keys` — `_require_exact_keys(value, expected, label)` | function / [243](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L243) | `SystemHisCompatibilityError`、`set` |
| `_require_string` — `_require_string(value, label)` | function / [248](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L248) | `SystemHisCompatibilityError`、`isinstance`、`value.strip` |
| `_require_choice` — `_require_choice(value, label, choices)` | function / [254](../../../../agent/src/sr2fpga_agent/system_his_compatibility.py#L254) | `SystemHisCompatibilityError`、`_require_string` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`

## `agent/src/sr2fpga_agent/system_his_fidelity.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py) · 1417 行 · SHA-256 `05997c79ff3339fd4388dcea455f45979bba02ec7bff29ffc6d56133caf9a1ea`

> REQ-to-System-HIS fidelity checks for known synthetic tasks.

导入模块：`__future__`、`collections`、`dataclasses`、`json`、`re`、`sr2fpga_agent.family_recipe`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.models`、`sr2fpga_agent.project_generator`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.rtl_introspect`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SystemHisReqFidelityResult` — `SystemHisReqFidelityResult` | class / [22](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L22) | `field` |
| `check_system_his_req_fidelity` — `check_system_his_req_fidelity(request, payload, platform)` | function / [293](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L293) | `SystemHisReqFidelityResult`、`_check_requirement_trace`、`_merge_fidelity_results`、`_metrics_from_errors`、`build_request_requirement_envelope`、`check_system_his_family_recipe_fidelity`、`recipe_task_type`、`replace`、`select_family_recipe` |
| `check_system_his_family_recipe_fidelity` — `check_system_his_family_recipe_fidelity(request, payload)` | function / [323](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L323) | `SystemHisReqFidelityResult`、`_metrics_from_errors`、`_not_applicable_metrics`、`_validate_clock_reset`、`_validate_component_ports`、`_validate_components`、`_validate_constraints`、`_validate_forbidden_component_alias_ports`、`_validate_instances`、`_validate_top_ports`、`_validate_verification` |
| `_check_requirement_trace` — `_check_requirement_trace(request, payload, platform)` | function / [348](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L348) | `<dynamic>.requirement_trace_template`、`SystemHisReqFidelityResult`、`_check_requirement_trace_against_expected`、`_metrics_from_errors`、`build_request_requirement_envelope`、`errors.append` |
| `check_frozen_context_system_his_fidelity` — `check_frozen_context_system_his_fidelity(context, payload)` | function / [380](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L380) | `_check_requirement_trace_against_expected`、`frozen_requirement_trace_template` |
| `build_frozen_requirement_trace` — `build_frozen_requirement_trace(context, payload)` | function / [393](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L393) | `<dynamic>.items`、`_mapped_values_preserve_required_fact`、`_pointer_matches_required_fact`、`_semantic_pointer_candidates`、`frozen_requirement_trace_template`、`mappings.items` |
| `_check_requirement_trace_against_expected` — `_check_requirement_trace_against_expected(expected_trace, payload)` | function / [429](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L429) | `<dynamic>.difference`、`SystemHisReqFidelityResult`、`_metrics_from_errors`、`_validate_fact_to_his`、`_validate_required_facts`、`errors.append`、`expected_keys.difference`、`intent.get`、`isinstance`、`payload.get`、`set`、`sorted`、`trace.get` |
| `build_deterministic_requirement_trace` — `build_deterministic_requirement_trace(request, payload, platform)` | function / [496](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L496) | `<dynamic>.items`、`<dynamic>.requirement_trace_template`、`_mapped_values_preserve_required_fact`、`_pointer_matches_required_fact`、`_semantic_pointer_candidates`、`build_request_requirement_envelope`、`mappings.items` |
| `_semantic_pointer_candidates` — `_semantic_pointer_candidates(value, tokens)` | function / [535](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L535) | `<dynamic>.join`、`_json_pointer_escape`、`_semantic_pointer_candidates`、`enumerate`、`isinstance`、`items.append`、`items.extend`、`str`、`value.items` |
| `_json_pointer_escape` — `_json_pointer_escape(token)` | function / [552](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L552) | `<dynamic>.replace`、`token.replace` |
| `_merge_fidelity_results` — `_merge_fidelity_results(trace_result, family_result)` | function / [556](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L556) | `SystemHisReqFidelityResult`、`family_metric.get`、`family_result.metrics.get`、`list`、`trace_metric.get`、`trace_result.metrics.get` |
| `_validate_required_facts` — `_validate_required_facts(actual, expected, errors)` | function / [581](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L581) | `<dynamic>.difference`、`<dynamic>.intersection`、`errors.append`、`set`、`sorted` |
| `_validate_fact_to_his` — `_validate_fact_to_his(actual, expected_facts, payload, errors)` | function / [604](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L604) | `<dynamic>.difference`、`<dynamic>.get`、`<dynamic>.intersection`、`_mapped_values_preserve_required_fact`、`_pointer_matches_required_fact`、`_resolve_json_pointer`、`errors.append`、`isinstance`、`resolved_values.append`、`set`、`sorted` |
| `_pointer_matches_required_fact` — `_pointer_matches_required_fact(key, tokens)` | function / [668](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L668) | `_normalize_semantic_text`、`any` |
| `_mapped_values_preserve_required_fact` — `_mapped_values_preserve_required_fact(key, expected, resolved_values)` | function / [773](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L773) | `_acceptance_criteria_present`、`_all_semantic_values_present`、`_canonical_reset_polarity`、`_field_number_present`、`_frequency_hz_values`、`_normalize_semantic_text`、`_normalized_value_present`、`_numbers_equal`、`_scalar_values`、`_semantic_value_present`、`_throughput_present`、`actual_counts.append`、`all`、`any`、`bool`、`int`、`isinstance`、`len`、`match.group`、`re.fullmatch`、`str`、`widths_equivalent` |
| `_all_semantic_values_present` — `_all_semantic_values_present(expected, resolved_values, marker_map)` | function / [889](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L889) | `_scalar_values`、`_semantic_marker_matches`、`all`、`any`、`isinstance`、`marker_map.get`、`str` |
| `_semantic_value_present` — `_semantic_value_present(expected, resolved_values)` | function / [911](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L911) | `_scalar_values`、`_semantic_marker_matches`、`any`、`isinstance`、`str` |
| `_normalized_value_present` — `_normalized_value_present(expected, resolved_values)` | function / [923](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L923) | `_normalize_semantic_text`、`_scalar_values`、`any`、`isinstance`、`str` |
| `_field_number_present` — `_field_number_present(expected, resolved_values, field_markers)` | function / [936](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L936) | `_field_number_values`、`_numbers_equal`、`any` |
| `_field_number_values` — `_field_number_values(value, field_name, field_markers)` | function / [953](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L953) | `_field_number_values`、`_normalize_semantic_text`、`any`、`float`、`isinstance`、`str`、`value.items` |
| `_throughput_present` — `_throughput_present(expected, resolved_values)` | function / [980](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L980) | `_field_number_present`、`_scalar_values`、`_semantic_marker_matches`、`_semantic_value_present`、`any`、`isinstance`、`str` |
| `_acceptance_criteria_present` — `_acceptance_criteria_present(expected, resolved_values)` | function / [1008](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1008) | `<dynamic>.removesuffix`、`_scalar_values`、`expected.strip`、`expected_text.casefold`、`isinstance`、`re.fullmatch`、`re.search`、`re.sub`、`text.casefold`、`value.strip` |
| `_semantic_marker_matches` — `_semantic_marker_matches(value, marker)` | function / [1050](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1050) | `_normalize_semantic_text`、`bool` |
| `_normalize_semantic_text` — `_normalize_semantic_text(value)` | function / [1059](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1059) | `<dynamic>.strip`、`re.sub`、`value.casefold` |
| `_scalar_values` — `_scalar_values(value)` | function / [1063](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1063) | `_scalar_values`、`isinstance`、`value.values` |
| `_frequency_hz_values` — `_frequency_hz_values(value, field_name)` | function / [1071](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1071) | `_frequency_hz_values`、`_normalize_semantic_text`、`float`、`isinstance`、`normalized_field.endswith`、`str`、`value.items` |
| `_numbers_equal` — `_numbers_equal(left, right)` | function / [1098](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1098) | `abs`、`float`、`isinstance`、`max` |
| `_canonical_reset_polarity` — `_canonical_reset_polarity(value)` | function / [1106](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1106) | `<dynamic>.get`、`_normalize_semantic_text`、`str` |
| `_resolve_json_pointer` — `_resolve_json_pointer(document, pointer)` | function / [1116](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1116) | `<dynamic>.split`、`ValueError`、`_decode_json_pointer_token`、`int`、`isinstance`、`len`、`pointer.startswith`、`token.isdigit`、`token.startswith`、`tuple` |
| `_decode_json_pointer_token` — `_decode_json_pointer_token(token)` | function / [1145](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1145) | `<dynamic>.replace`、`ValueError`、`len`、`token.replace` |
| `_not_applicable_metrics` — `_not_applicable_metrics()` | function / [1157](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1157) | 无直接调用 |
| `_metrics_from_errors` — `_metrics_from_errors(errors)` | function / [1161](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1161) | `<dynamic>.append`、`_not_applicable_metrics` |
| `_validate_components` — `_validate_components(request, payload, errors)` | function / [1200](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1200) | `<dynamic>.strip`、`_required_components`、`component.get`、`errors.append`、`isinstance`、`payload.get`、`str` |
| `_validate_component_ports` — `_validate_component_ports(request, payload, errors)` | function / [1212](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1212) | `<dynamic>.strip`、`_expected_component_ports`、`_port_direction`、`_validate_data_flow_component_ports`、`actual_components.get`、`actual_ports.get`、`component.get`、`errors.append`、`expected.get`、`expected_components.items`、`expected_ports.items`、`isinstance`、`payload.get`、`port.get`、`str` |
| `_validate_data_flow_component_ports` — `_validate_data_flow_component_ports(payload, expected_components, errors)` | function / [1244](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1244) | `<dynamic>.strip`、`endpoint.split`、`errors.append`、`flow.get`、`instance.get`、`instance_components.get`、`isinstance`、`payload.get`、`str` |
| `_validate_forbidden_component_alias_ports` — `_validate_forbidden_component_alias_ports(payload, errors)` | function / [1268](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1268) | `<dynamic>.strip`、`_FORBIDDEN_COMPONENT_ALIAS_PORTS.get`、`endpoint.split`、`errors.append`、`flow.get`、`instance.get`、`instance_components.get`、`isinstance`、`payload.get`、`set`、`str` |
| `_expected_component_ports` — `_expected_component_ports(request)` | function / [1286](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1286) | `<dynamic>.generate`、`<dynamic>.strip`、`PlatformProfile`、`ProjectGenerator`、`_port_direction`、`component.get`、`isinstance`、`json.loads`、`port.get`、`str`、`system_his.get` |
| `_validate_instances` — `_validate_instances(request, payload, errors)` | function / [1306](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1306) | `<dynamic>.strip`、`Counter`、`_required_instance_counts`、`errors.append`、`instance.get`、`isinstance`、`payload.get`、`required_counts.items`、`str` |
| `_required_components` — `_required_components(task_type)` | function / [1322](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1322) | `_SUPPLEMENTAL_TASK_COMPONENTS.get`、`list` |
| `_required_instance_counts` — `_required_instance_counts(task_type)` | function / [1328](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1328) | `<dynamic>.strip`、`Counter`、`_SUPPLEMENTAL_TASK_COMPONENTS.get`、`isinstance`、`node.get`、`str`、`topology.get` |
| `_validate_top_ports` — `_validate_top_ports(request, payload, errors)` | function / [1339](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1339) | `<dynamic>.strip`、`_TASK_TOP_PORTS.get`、`_port_direction`、`errors.append`、`expected.get`、`expected_ports.items`、`isinstance`、`payload.get`、`port.get`、`ports_by_name.get`、`str`、`top.get`、`widths_equivalent` |
| `_validate_clock_reset` — `_validate_clock_reset(payload, errors)` | function / [1365](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1365) | `<dynamic>.strip`、`clock.get`、`errors.append`、`isinstance`、`payload.get`、`reset.get`、`reset_by_name.get`、`rst_n.get`、`str`、`top.get` |
| `_validate_verification` — `_validate_verification(payload, errors)` | function / [1391](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1391) | `<dynamic>.strip`、`errors.append`、`isinstance`、`payload.get`、`str`、`verification.get` |
| `_validate_constraints` — `_validate_constraints(payload, errors)` | function / [1404](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1404) | `<dynamic>.strip`、`errors.append`、`isinstance`、`payload.get`、`str`、`timing.get` |
| `_port_direction` — `_port_direction(port)` | function / [1416](../../../../agent/src/sr2fpga_agent/system_his_fidelity.py#L1416) | `<dynamic>.strip`、`port.get`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/system_his_schema.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/system_his_schema.py) · 72 行 · SHA-256 `4eb058733fc1f7e2549faa9aab733edb8b082b9c7e02e0702ac7e31c934571e9`

> Execute the registered System-HIS JSON Schema contract with System-HIS diagnostics.

导入模块：`__future__`、`jsonschema`、`re`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.repository_paths`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_registered_system_his_schema` — `load_registered_system_his_schema(paths)` | function / [22](../../../../agent/src/sr2fpga_agent/system_his_schema.py#L22) | `<dynamic>.load_schema`、`ContractRegistry`、`ValueError` |
| `validate_registered_system_his_schema` — `validate_registered_system_his_schema(payload, paths)` | function / [33](../../../../agent/src/sr2fpga_agent/system_his_schema.py#L33) | `Draft202012Validator`、`_format_error`、`load_registered_system_his_schema`、`sorted`、`str`、`tuple`、`validator.iter_errors` |
| `_format_error` — `_format_error(error)` | function / [47](../../../../agent/src/sr2fpga_agent/system_his_schema.py#L47) | `<dynamic>.get`、`_json_path`、`isinstance`、`match.group`、`re.match` |
| `_json_path` — `_json_path(parts)` | function / [65](../../../../agent/src/sr2fpga_agent/system_his_schema.py#L65) | `isinstance` |

## `agent/src/sr2fpga_agent/system_his_v12_checker.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py) · 1506 行 · SHA-256 `0d07e61fb2ba4140e7f74de9487b5613f776b3cf9e49dd8bc2308bbe29bb5244`

> Structural checks for the canonical System-HIS v1.2 schema.

导入模块：`__future__`、`ast`、`dataclasses`、`json`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.rtl_introspect`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SystemHisV12CheckResult` — `SystemHisV12CheckResult` | class / [69](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L69) | `field` |
| `SystemHisWellFormednessRuleResult` — `SystemHisWellFormednessRuleResult` | class / [78](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L78) | `field` |
| `check_system_his_v12` — `check_system_his_v12(payload)` | function / [85](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L85) | `<dynamic>.items`、`<dynamic>.strip`、`SystemHisV12CheckResult`、`_artifact_rtl_sources`、`_component_parameters`、`_component_ports`、`_data_flow_names`、`_instance_components`、`_list`、`_mapping`、`_parameter_names`、`_state_names`、`_top_clock_reset_names`、`_top_ports`、`_validate_artifacts`、`_validate_control_flow`、`_validate_fsms`、`_validate_instance_state_ownership`、`_validate_intent`、`_validate_required_keys`、`_validate_resources`、`_validate_timing`、`_validate_top_clock_reset`、`_validate_top_clock_reset_ports`、`_validate_verification`、`check_system_his_well_formedness`、`component_ports.get`、`errors.append`、`instance_components.items`、`isinstance`、`payload.get`、`set`、`str`、`top.get`、`valid_fsm_owners.discard` |
| `check_system_his_well_formedness` — `check_system_his_well_formedness(payload)` | function / [160](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L160) | `SystemHisWellFormednessRuleResult`、`_w10_artifact_reproducibility`、`_w1_component_references`、`_w2_endpoint_references`、`_w3_connection_types`、`_w4_state_clock_reset_bindings`、`_w5_combinational_state`、`_w6_cdc_paths`、`_w7_memory_intent`、`_w8_verification_references`、`_w9_constraint_references`、`rules.items` |
| `check_system_his_v12_against_rtl` — `check_system_his_v12_against_rtl(payload, project)` | function / [191](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L191) | `<dynamic>.strip`、`SystemHisV12CheckResult`、`_v12_instance_components`、`_v12_string_list`、`_validate_v12_artifacts_against_project`、`_validate_v12_components_against_rtl`、`_validate_v12_data_flow_against_rtl`、`_validate_v12_fsm_states_against_rtl`、`_validate_v12_instances_in_top`、`_validate_v12_top_against_rtl`、`artifacts.get`、`check_system_his_v12`、`declared_module_ports`、`declared_modules`、`errors.append`、`isinstance`、`list`、`payload.get`、`str` |
| `_validate_required_keys` — `_validate_required_keys(payload, errors)` | function / [232](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L232) | `errors.append` |
| `_validate_intent` — `_validate_intent(intent, errors)` | function / [238](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L238) | `<dynamic>.strip`、`_list`、`errors.append`、`intent.get`、`str` |
| `_validate_top_clock_reset` — `_validate_top_clock_reset(top, errors)` | function / [245](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L245) | `<dynamic>.strip`、`_is_positive_number`、`_list`、`clock.get`、`enumerate`、`errors.append`、`isinstance`、`reset.get`、`str`、`top.get` |
| `_validate_timing` — `_validate_timing(timing, errors)` | function / [271](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L271) | `<dynamic>.strip`、`_is_positive_number`、`_list`、`errors.append`、`str`、`timing.get` |
| `_validate_resources` — `_validate_resources(resources, errors)` | function / [279](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L279) | `<dynamic>.strip`、`_mapping`、`errors.append`、`resources.get`、`str` |
| `_validate_verification` — `_validate_verification(verification, errors)` | function / [285](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L285) | `<dynamic>.strip`、`_list`、`errors.append`、`str`、`verification.get` |
| `_mapping` — `_mapping(value, name, errors)` | function / [293](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L293) | `errors.append`、`isinstance` |
| `_list` — `_list(value, name, errors)` | function / [300](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L300) | `errors.append`、`isinstance` |
| `_top_ports` — `_top_ports(top, errors)` | function / [307](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L307) | `<dynamic>.strip`、`_list`、`enumerate`、`errors.append`、`isinstance`、`port.get`、`port_names.add`、`set`、`str`、`top.get` |
| `_validate_top_clock_reset_ports` — `_validate_top_clock_reset_ports(top, top_ports, errors)` | function / [327](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L327) | `<dynamic>.strip`、`enumerate`、`errors.append`、`isinstance`、`item.get`、`str`、`top.get` |
| `_top_clock_reset_names` — `_top_clock_reset_names(top)` | function / [346](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L346) | `<dynamic>.strip`、`isinstance`、`item.get`、`names.add`、`set`、`str`、`top.get` |
| `_component_ports` — `_component_ports(components, rtl_sources, errors)` | function / [361](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L361) | `<dynamic>.strip`、`_list`、`component.get`、`enumerate`、`errors.append`、`isinstance`、`port.get`、`port_names.add`、`set`、`str` |
| `_parameter_names` — `_parameter_names(value, path, errors)` | function / [398](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L398) | `_list`、`enumerate`、`errors.append`、`isinstance`、`names.add`、`raw_name.strip`、`set` |
| `_component_parameters` — `_component_parameters(components, errors)` | function / [420](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L420) | `<dynamic>.strip`、`_parameter_names`、`component.get`、`enumerate`、`isinstance`、`str` |
| `_instance_components` — `_instance_components(instances, component_ports, component_parameters, errors)` | function / [439](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L439) | `<dynamic>.strip`、`_mapping`、`component_parameters.get`、`enumerate`、`errors.append`、`instance.get`、`isinstance`、`set`、`str` |
| `_state_names` — `_state_names(state, errors)` | function / [479](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L479) | `<dynamic>.strip`、`_list`、`enumerate`、`errors.append`、`isinstance`、`item.get`、`names.add`、`set`、`state.get`、`str` |
| `_validate_fsms` — `_validate_fsms(state, state_names, valid_owners, errors)` | function / [500](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L500) | `<dynamic>.strip`、`enumerate`、`errors.append`、`fsm.get`、`isinstance`、`name.split`、`set`、`state.get`、`state_names.add`、`states.add`、`str` |
| `_data_flow_names` — `_data_flow_names(data_flow, top_ports, instance_ports, errors)` | function / [549](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L549) | `<dynamic>.strip`、`_is_valid_endpoint`、`_list`、`_mapping`、`_validate_data_flow_timing`、`enumerate`、`errors.append`、`flow.get`、`isinstance`、`names.add`、`set`、`str` |
| `_validate_data_flow_timing` — `_validate_data_flow_timing(flow_name, timing, errors)` | function / [582](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L582) | `<dynamic>.strip`、`_is_non_bool_int`、`errors.append`、`isinstance`、`str`、`timing.get` |
| `_is_non_bool_int` — `_is_non_bool_int(value)` | function / [596](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L596) | `isinstance` |
| `_is_positive_number` — `_is_positive_number(value)` | function / [600](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L600) | `isinstance` |
| `_is_valid_endpoint` — `_is_valid_endpoint(endpoint, top_ports, instance_ports)` | function / [604](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L604) | `endpoint.split`、`instance_ports.get`、`set` |
| `_validate_instance_state_ownership` — `_validate_instance_state_ownership(instances, state_names, errors, state)` | function / [613](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L613) | `<dynamic>.add`、`<dynamic>.strip`、`_list`、`_object_list`、`_v12_state_owner`、`enumerate`、`errors.append`、`instance.get`、`isinstance`、`item.get`、`owners.get`、`owners.setdefault`、`set`、`state.get`、`str`、`tuple` |
| `_validate_control_flow` — `_validate_control_flow(control_flow, state_names, data_flow_names, top_ports, instance_ports, fsm_defs, errors)` | function / [639](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L639) | `<dynamic>.strip`、`_effect_targets`、`_guard_signals`、`_list`、`_validate_fsm_transition`、`_validate_structured_enable_rule`、`enumerate`、`errors.append`、`isinstance`、`rule.get`、`str` |
| `_guard_signals` — `_guard_signals(top_ports, instance_ports, state_names, data_flow_names)` | function / [679](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L679) | `instance_ports.items`、`set`、`signals.add` |
| `_effect_targets` — `_effect_targets(instance_ports, state_names, data_flow_names)` | function / [695](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L695) | `set` |
| `_validate_fsm_transition` — `_validate_fsm_transition(rule, name, fsm_defs, guard_signals, effect_targets, errors)` | function / [703](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L703) | `<dynamic>.strip`、`_validate_effect`、`_validate_guard`、`errors.append`、`fsm_defs.get`、`rule.get`、`set`、`str` |
| `_validate_structured_enable_rule` — `_validate_structured_enable_rule(rule, name, guard_signals, effect_targets, errors)` | function / [725](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L725) | `_validate_effect`、`_validate_guard`、`rule.get` |
| `_validate_guard` — `_validate_guard(guard, valid_signals, context, errors, depth)` | function / [736](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L736) | `<dynamic>.strip`、`_validate_guard`、`errors.append`、`guard.get`、`isinstance`、`str` |
| `_validate_effect` — `_validate_effect(effect, valid_targets, context, errors)` | function / [769](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L769) | `<dynamic>.strip`、`effect.get`、`errors.append`、`isinstance`、`str` |
| `_validate_v12_artifacts_against_project` — `_validate_v12_artifacts_against_project(artifacts, project, sources, top_module, rtl_ports, errors)` | function / [778](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L778) | `<dynamic>.strip`、`_manifest_testbench_v12`、`_manifest_timing_constraint_v12`、`_read_v12_project_json`、`_v12_string_list`、`_validate_v12_testbench_instantiates_top`、`_validate_v12_timing_constraint_ports`、`artifacts.get`、`errors.append`、`manifest.get`、`str` |
| `_validate_v12_top_against_rtl` — `_validate_v12_top_against_rtl(top, top_module, rtl_ports, errors)` | function / [814](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L814) | `<dynamic>.strip`、`_his_port_records`、`_validate_v12_port_records`、`errors.append`、`isinstance`、`rtl_ports.get`、`str`、`top.get` |
| `_validate_v12_components_against_rtl` — `_validate_v12_components_against_rtl(components, sources, rtl_modules, rtl_ports, project, errors)` | function / [828](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L828) | `<dynamic>.strip`、`_his_port_records`、`_validate_v12_port_records`、`component.get`、`declared_modules`、`enumerate`、`errors.append`、`isinstance`、`rtl_ports.get`、`set`、`str` |
| `_validate_v12_port_records` — `_validate_v12_port_records(owner, his_ports, rtl_ports, errors)` | function / [861](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L861) | `<dynamic>.get`、`<dynamic>.strip`、`_his_direction`、`_his_width`、`errors.append`、`port.get`、`str`、`widths_equivalent` |
| `_his_port_records` — `_his_port_records(value)` | function / [880](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L880) | `<dynamic>.strip`、`isinstance`、`port.get`、`records.append`、`str` |
| `_his_direction` — `_his_direction(port)` | function / [892](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L892) | `<dynamic>.strip`、`port.get`、`str` |
| `_his_width` — `_his_width(value)` | function / [901](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L901) | 无直接调用 |
| `_v12_instance_components` — `_v12_instance_components(instances, component_ports, errors)` | function / [905](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L905) | `<dynamic>.strip`、`errors.append`、`instance.get`、`isinstance`、`str` |
| `_validate_v12_instances_in_top` — `_validate_v12_instances_in_top(instance_components, component_ports, top_module, project, errors)` | function / [926](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L926) | `_module_source_content`、`errors.append`、`instance_components.items`、`pattern.search`、`re.compile`、`re.escape` |
| `_validate_v12_data_flow_against_rtl` — `_validate_v12_data_flow_against_rtl(data_flow, top_module, rtl_ports, instance_components, errors)` | function / [947](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L947) | `<dynamic>.strip`、`endpoint_text.split`、`errors.append`、`flow.get`、`instance_components.get`、`isinstance`、`rtl_ports.get`、`str` |
| `_validate_v12_fsm_states_against_rtl` — `_validate_v12_fsm_states_against_rtl(state, instance_components, top_module, rtl_ports, project, errors)` | function / [977](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L977) | `<dynamic>.strip`、`_module_source_content`、`_v12_state_owner`、`errors.append`、`fsm.get`、`instance_components.get`、`isinstance`、`re.escape`、`re.search`、`state.get`、`str` |
| `_v12_state_owner` — `_v12_state_owner(state_item)` | function / [1007](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1007) | `<dynamic>.strip`、`name.split`、`state_item.get`、`str` |
| `_read_v12_project_json` — `_read_v12_project_json(project, path, errors)` | function / [1017](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1017) | `errors.append`、`isinstance`、`json.loads`、`project.files.get` |
| `_v12_string_list` — `_v12_string_list(value, name, errors)` | function / [1035](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1035) | `errors.append`、`isinstance`、`item.strip`、`strings.append` |
| `_manifest_testbench_v12` — `_manifest_testbench_v12(manifest)` | function / [1048](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1048) | `<dynamic>.strip`、`isinstance`、`manifest.get`、`simulation.get`、`str` |
| `_manifest_timing_constraint_v12` — `_manifest_timing_constraint_v12(manifest)` | function / [1055](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1055) | `<dynamic>.strip`、`constraints.get`、`isinstance`、`manifest.get`、`str` |
| `_validate_v12_testbench_instantiates_top` — `_validate_v12_testbench_instantiates_top(project, testbench, top_module, errors)` | function / [1062](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1062) | `errors.append`、`pattern.search`、`re.compile`、`re.escape` |
| `_validate_v12_timing_constraint_ports` — `_validate_v12_timing_constraint_ports(project, timing_constraint, top_module, rtl_ports, errors)` | function / [1079](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1079) | `errors.append`、`re.findall`、`rtl_ports.get`、`set` |
| `_module_source_content` — `_module_source_content(project, module_name)` | function / [1095](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1095) | `pattern.search`、`project.files.values`、`re.compile`、`re.escape` |
| `_validate_artifacts` — `_validate_artifacts(artifacts, errors)` | function / [1105](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1105) | `<dynamic>.strip`、`_list`、`artifacts.get`、`errors.append`、`str` |
| `_artifact_rtl_sources` — `_artifact_rtl_sources(artifacts, errors)` | function / [1115](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1115) | `artifacts.get`、`enumerate`、`errors.append`、`isinstance`、`sources.append`、`value.strip` |
| `_w1_component_references` — `_w1_component_references(payload)` | function / [1128](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1128) | `<dynamic>.strip`、`_named_objects`、`_object_list`、`components.get`、`diagnostics.append`、`enumerate`、`instance.get`、`len`、`payload.get`、`str` |
| `_w2_endpoint_references` — `_w2_endpoint_references(payload)` | function / [1138](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1138) | `_endpoint_contracts`、`_object_list`、`_string_list`、`diagnostics.append`、`enumerate`、`flow.get`、`payload.get` |
| `_w3_connection_types` — `_w3_connection_types(payload)` | function / [1150](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1150) | `_endpoint_contracts`、`_object_list`、`_resolved_width`、`_typed_endpoint_name`、`connection.get`、`contracts.get`、`diagnostics.append`、`enumerate`、`flow.get`、`isinstance`、`payload.get`、`widths_equivalent` |
| `_typed_endpoint_name` — `_typed_endpoint_name(value, payload)` | function / [1201](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1201) | `<dynamic>.strip`、`isinstance`、`payload.get`、`str`、`top.get`、`value.get`、`value.strip` |
| `_w4_state_clock_reset_bindings` — `_w4_state_clock_reset_bindings(payload)` | function / [1215](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1215) | `<dynamic>.get`、`<dynamic>.strip`、`_object_list`、`_object_names`、`bool`、`diagnostics.append`、`enumerate`、`instance.get`、`isinstance`、`item.get`、`payload.get`、`set`、`sorted`、`state.get`、`state_owners.add`、`str`、`top.get` |
| `_w5_combinational_state` — `_w5_combinational_state(payload)` | function / [1248](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1248) | `<dynamic>.strip`、`_object_list`、`_object_names`、`component.get`、`diagnostics.append`、`instance.get`、`isinstance`、`item.get`、`payload.get`、`set`、`sorted`、`state.get`、`str`、`top.get` |
| `_w6_cdc_paths` — `_w6_cdc_paths(payload)` | function / [1290](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1290) | `<dynamic>.lower`、`<dynamic>.strip`、`_endpoint_contracts`、`_object_list`、`_string_list`、`any`、`component.get`、`component_kinds.get`、`diagnostics.append`、`flow.get`、`instance.get`、`instance_components.get`、`len`、`payload.get`、`set`、`str` |
| `_w7_memory_intent` — `_w7_memory_intent(payload)` | function / [1321](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1321) | `_is_non_bool_int`、`_object_list`、`_resolved_width`、`diagnostics.append`、`enumerate`、`isinstance`、`memory.get`、`payload.get`、`state.get`、`value.strip` |
| `_w8_verification_references` — `_w8_verification_references(payload)` | function / [1342](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1342) | `_endpoint_contracts`、`_object_list`、`_object_names`、`_string_list`、`diagnostics.append`、`enumerate`、`isinstance`、`payload.get`、`scenario.get`、`set`、`verification.get` |
| `_w9_constraint_references` — `_w9_constraint_references(payload)` | function / [1362](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1362) | `<dynamic>.strip`、`_object_names`、`_string_list`、`artifacts.get`、`diagnostics.append`、`isinstance`、`payload.get`、`set`、`sorted`、`str`、`timing.get`、`top.get` |
| `_w10_artifact_reproducibility` — `_w10_artifact_reproducibility(payload)` | function / [1377](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1377) | `<dynamic>.strip`、`_object_list`、`_string_list`、`artifacts.get`、`component.get`、`diagnostics.append`、`isinstance`、`payload.get`、`set`、`str`、`timing.get`、`top.get`、`verification.get` |
| `_endpoint_contracts` — `_endpoint_contracts(payload)` | function / [1399](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1399) | `<dynamic>.get`、`<dynamic>.strip`、`_normalized_direction`、`_object_list`、`_resolved_width`、`component.get`、`component_ports.get`、`component_ports.setdefault`、`contracts.setdefault`、`instance.get`、`isinstance`、`parameter.get`、`payload.get`、`port.get`、`str`、`top.get` |
| `_normalized_direction` — `_normalized_direction(port)` | function / [1440](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1440) | `<dynamic>.get`、`<dynamic>.strip`、`port.get`、`str` |
| `_resolved_width` — `_resolved_width(value, parameters)` | function / [1445](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1445) | `_evaluate_width_expression`、`isinstance`、`range_match.group`、`re.fullmatch`、`value.get`、`value.strip` |
| `_evaluate_width_expression` — `_evaluate_width_expression(expression, parameters)` | function / [1459](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1459) | `ast.parse`、`evaluate` |
| `_evaluate_width_expression.evaluate` — `evaluate(node)` | function / [1465](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1465) | `evaluate`、`isinstance`、`parameters.get` |
| `_named_objects` — `_named_objects(value)` | function / [1490](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1490) | `<dynamic>.append`、`<dynamic>.strip`、`_object_list`、`item.get`、`result.setdefault`、`str` |
| `_object_names` — `_object_names(value)` | function / [1497](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1497) | `<dynamic>.strip`、`_object_list`、`item.get`、`str` |
| `_object_list` — `_object_list(value)` | function / [1501](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1501) | `isinstance` |
| `_string_list` — `_string_list(value)` | function / [1505](../../../../agent/src/sr2fpga_agent/system_his_v12_checker.py#L1505) | `<dynamic>.strip`、`isinstance`、`item.strip`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/target_profile_pairs.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py) · 517 行 · SHA-256 `deccbf5f2b71cc8eed301a9a9406276be031772a03dea8d9a6101f00352cc1b9`

> Development-only target-profile pair contracts and reconciliation.

导入模块：`__future__`、`hashlib`、`json`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_pilot_target_profile_pair_manifest` — `build_pilot_target_profile_pair_manifest(manifest_id, protocol_sha256, pairs)` | function / [50](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L50) | `_sha256`、`dict`、`len`、`validate_pilot_target_profile_pair_manifest` |
| `validate_pilot_target_profile_pair_manifest` — `validate_pilot_target_profile_pair_manifest(artifact)` | function / [74](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L74) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_require_unique`、`_sha256`、`_validate_pair_rules`、`dict`、`len`、`payload.items` |
| `build_development_target_profile_pair_outcome` — `build_development_target_profile_pair_outcome(manifest, profile_pair_id, method_condition, member_observations, store)` | function / [100](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L100) | `ValueError`、`_aggregate_cost_axes`、`_pair_by_id`、`_records_by_role`、`_require_exact_observation_keys`、`_sha256`、`_tpa_l4_reasons`、`_validate_member_identity`、`_validate_observation_semantics`、`_validated_cost_summary`、`_validated_optional_ref`、`all`、`any`、`cost_refs.append`、`dict`、`len`、`member_axes.append`、`member_records.append`、`paired_axes.values`、`validate_development_target_profile_pair_outcome`、`validate_pilot_target_profile_pair_manifest` |
| `validate_development_target_profile_pair_outcome` — `validate_development_target_profile_pair_outcome(artifact, manifest)` | function / [205](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L205) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_pair_by_id`、`_records_by_role`、`_sha256`、`_validate_member_identity`、`_validate_outcome_reconciliation`、`dict`、`payload.items`、`validate_pilot_target_profile_pair_manifest` |
| `_validate_pair_rules` — `_validate_pair_rules(pair)` | function / [236](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L236) | `ValueError`、`_records_by_role`、`allowed.intersection`、`len`、`required.issubset`、`set` |
| `_validate_observation_semantics` — `_validate_observation_semantics(observation)` | function / [260](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L260) | `ValueError`、`any` |
| `_validate_outcome_reconciliation` — `_validate_outcome_reconciliation(payload)` | function / [290](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L290) | `ValueError`、`_aggregate_cost_axes`、`_sha256`、`_tpa_l4_reasons`、`_validate_observation_semantics`、`all`、`any`、`dict`、`expected_axes.values`、`len`、`list` |
| `_validated_cost_summary` — `_validated_cost_summary(store, raw_ref, method_condition, label)` | function / [356](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L356) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_artifact_ref`、`_unavailable_axes`、`dict`、`json.loads`、`reference.to_dict`、`store.read_verified` |
| `_validated_optional_ref` — `_validated_optional_ref(store, raw_ref, label)` | function / [378](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L378) | `_artifact_ref`、`reference.to_dict`、`store.read_verified` |
| `_artifact_ref` — `_artifact_ref(raw_ref, label)` | function / [388](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L388) | `ArtifactRef`、`ValueError`、`int`、`isinstance`、`str` |
| `_aggregate_cost_axes` — `_aggregate_cost_axes(member_axes)` | function / [402](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L402) | `all`、`float`、`len`、`sum` |
| `_unavailable_axes` — `_unavailable_axes(reason)` | function / [421](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L421) | 无直接调用 |
| `_tpa_l4_reasons` — `_tpa_l4_reasons(member_records, paired_cost_complete)` | function / [428](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L428) | `any`、`reasons.add`、`set`、`sorted` |
| `_require_exact_observation_keys` — `_require_exact_observation_keys(observations)` | function / [466](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L466) | `ValueError`、`len`、`set`、`sorted` |
| `_records_by_role` — `_records_by_role(records, label)` | function / [479](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L479) | `ValueError`、`record.get`、`set`、`str` |
| `_validate_member_identity` — `_validate_member_identity(expected, actual)` | function / [491](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L491) | `ValueError`、`actual.get` |
| `_pair_by_id` — `_pair_by_id(manifest, profile_pair_id)` | function / [502](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L502) | `ValueError`、`len` |
| `_require_unique` — `_require_unique(values, label)` | function / [509](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L509) | `ValueError`、`len`、`list`、`set` |
| `_sha256` — `_sha256(value)` | function / [515](../../../../agent/src/sr2fpga_agent/target_profile_pairs.py#L515) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

## `agent/src/sr2fpga_agent/task_catalog.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_catalog.py) · 335 行 · SHA-256 `ad3a6dfe1f7228f06264a2b96526bcb77b92801971c575969bbbd3f6bb7a4308`

> Runtime access to the authoritative SR2FPGA task-family catalog.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.task_families`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TaskFamilySpec` — `TaskFamilySpec` | class / [21](../../../../agent/src/sr2fpga_agent/task_catalog.py#L21) | 无直接调用 |
| `FamilyRecipeDenyPolicy` — `FamilyRecipeDenyPolicy` | class / [41](../../../../agent/src/sr2fpga_agent/task_catalog.py#L41) | 无直接调用 |
| `ExactTaskFamilyResolution` — `ExactTaskFamilyResolution` | class / [55](../../../../agent/src/sr2fpga_agent/task_catalog.py#L55) | 无直接调用 |
| `_load_catalog` — `_load_catalog()` | function / [66](../../../../agent/src/sr2fpga_agent/task_catalog.py#L66) | `CATALOG_PATH.open`、`_CATALOG_CACHE.get`、`file_identity`、`json.load` |
| `load_task_family_specs` — `load_task_family_specs()` | function / [82](../../../../agent/src/sr2fpga_agent/task_catalog.py#L82) | `TaskFamilySpec`、`ValueError`、`_SPEC_CACHE.get`、`_load_catalog`、`family.get`、`file_identity`、`float`、`tuple` |
| `task_family_spec_for_alias` — `task_family_spec_for_alias(alias)` | function / [120](../../../../agent/src/sr2fpga_agent/task_catalog.py#L120) | `KeyError`、`load_task_family_specs` |
| `task_family_spec_for_family_id` — `task_family_spec_for_family_id(family_id)` | function / [128](../../../../agent/src/sr2fpga_agent/task_catalog.py#L128) | `KeyError`、`load_task_family_specs` |
| `current_research_family_specs` — `current_research_family_specs()` | function / [136](../../../../agent/src/sr2fpga_agent/task_catalog.py#L136) | `ValueError`、`_load_catalog`、`any`、`isinstance`、`len`、`set`、`task_family_spec_for_family_id`、`tuple` |
| `load_exact_task_family_aliases` — `load_exact_task_family_aliases()` | function / [163](../../../../agent/src/sr2fpga_agent/task_catalog.py#L163) | `ValueError`、`exact_aliases.get`、`load_task_family_specs` |
| `resolve_exact_task_family` — `resolve_exact_task_family(alias, exact_catalog_aliases)` | function / [176](../../../../agent/src/sr2fpga_agent/task_catalog.py#L176) | `<dynamic>.get`、`ExactTaskFamilyResolution`、`declared_alias.strip`、`family_id_for_task_type`、`isinstance`、`load_exact_task_family_aliases` |
| `load_family_recipe_deny_policy` — `load_family_recipe_deny_policy()` | function / [251](../../../../agent/src/sr2fpga_agent/task_catalog.py#L251) | `<dynamic>.difference`、`<dynamic>.encode`、`<dynamic>.hexdigest`、`<dynamic>.join`、`FamilyRecipeDenyPolicy`、`ValueError`、`_load_catalog`、`any`、`catalog.get`、`family.get`、`family_id.strip`、`hashlib.sha256`、`isinstance`、`json.dumps`、`len`、`list`、`raw_policy.get`、`set`、`sorted`、`string_fields.items`、`tuple`、`value.strip` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`RepositoryPaths.discover`、`dataclass`

## `agent/src/sr2fpga_agent/task_evidence.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/task_evidence.py) · 1513 行 · SHA-256 `dd41347135abde6d95016a2f9c95838698717544ae6aeeb7d02c4ec7386ef715`

> Runtime access to the SR2FPGA task-family evidence ledger.

导入模块：`__future__`、`argparse`、`collections.abc`、`dataclasses`、`hashlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.task_catalog`、`sr2fpga_agent.task_families`、`sys`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `MutationEvidence` — `MutationEvidence` | class / [60](../../../../agent/src/sr2fpga_agent/task_evidence.py#L60) | 无直接调用 |
| `IndependentOracleEvidence` — `IndependentOracleEvidence` | class / [67](../../../../agent/src/sr2fpga_agent/task_evidence.py#L67) | 无直接调用 |
| `IndependentOracleEvidence.__post_init__` — `__post_init__(self)` | function / [74](../../../../agent/src/sr2fpga_agent/task_evidence.py#L74) | `object.__setattr__`、`tuple` |
| `TaskFamilyEvidence` — `TaskFamilyEvidence` | class / [79](../../../../agent/src/sr2fpga_agent/task_evidence.py#L79) | `IndependentOracleEvidence` |
| `TaskFamilyEvidence.__post_init__` — `__post_init__(self)` | function / [99](../../../../agent/src/sr2fpga_agent/task_evidence.py#L99) | `TypeError`、`all`、`isinstance`、`object.__setattr__`、`tuple` |
| `TaskAliasEvidence` — `TaskAliasEvidence` | class / [109](../../../../agent/src/sr2fpga_agent/task_evidence.py#L109) | 无直接调用 |
| `L4OpenEvidence` — `L4OpenEvidence` | class / [122](../../../../agent/src/sr2fpga_agent/task_evidence.py#L122) | 无直接调用 |
| `load_task_family_evidence` — `load_task_family_evidence(path, catalog_path)` | function / [133](../../../../agent/src/sr2fpga_agent/task_evidence.py#L133) | `EVIDENCE_PATH.resolve`、`_parse_alias_entry`、`_parse_entry`、`_parse_l4_entry`、`catalog_path.open`、`document.get`、`json.load`、`path.open`、`path.resolve`、`tuple`、`validate_task_family_evidence`、`verify_l4_open_artifact_hashes`、`verify_task_alias_artifacts` |
| `load_task_alias_evidence` — `load_task_alias_evidence(path, catalog_path)` | function / [159](../../../../agent/src/sr2fpga_agent/task_evidence.py#L159) | `EVIDENCE_PATH.resolve`、`_parse_alias_entry`、`_parse_entry`、`_validate_alias_evidence`、`catalog_path.open`、`document.get`、`family.get`、`json.load`、`path.open`、`path.resolve`、`tuple`、`verify_task_alias_artifacts` |
| `load_l4_open_evidence` — `load_l4_open_evidence(path, catalog_path)` | function / [180](../../../../agent/src/sr2fpga_agent/task_evidence.py#L180) | `EVIDENCE_PATH.resolve`、`_parse_entry`、`_parse_l4_entry`、`_validate_l4_evidence`、`catalog_path.open`、`document.get`、`family.get`、`json.load`、`path.open`、`path.resolve`、`tuple`、`verify_l4_open_artifact_hashes` |
| `validate_task_family_evidence` — `validate_task_family_evidence(document, entries, catalog, alias_entries, l4_entries)` | function / [201](../../../../agent/src/sr2fpga_agent/task_evidence.py#L201) | `<dynamic>.join`、`ValueError`、`_validate_alias_evidence`、`_validate_entry`、`_validate_l4_evidence`、`document.get`、`family.get`、`len`、`set`、`sorted`、`tuple` |
| `_parse_entry` — `_parse_entry(item)` | function / [242](../../../../agent/src/sr2fpga_agent/task_evidence.py#L242) | `IndependentOracleEvidence`、`MutationEvidence`、`TaskFamilyEvidence`、`ValueError`、`float`、`independent_oracle.get`、`isinstance`、`item.get`、`tuple` |
| `_parse_alias_entry` — `_parse_alias_entry(item)` | function / [285](../../../../agent/src/sr2fpga_agent/task_evidence.py#L285) | `TaskAliasEvidence`、`tuple` |
| `_parse_l4_entry` — `_parse_l4_entry(item)` | function / [299](../../../../agent/src/sr2fpga_agent/task_evidence.py#L299) | `L4OpenEvidence`、`ValueError`、`artifacts.items`、`isinstance`、`tuple` |
| `_validate_alias_evidence` — `_validate_alias_evidence(alias_entries, aliases_by_family, family_entries)` | function / [315](../../../../agent/src/sr2fpga_agent/task_evidence.py#L315) | `ValueError`、`_require_status`、`_require_trimmed`、`aliases_by_family.get`、`any`、`len`、`set` |
| `_validate_l4_evidence` — `_validate_l4_evidence(l4_entries, aliases_by_family, family_entries)` | function / [377](../../../../agent/src/sr2fpga_agent/task_evidence.py#L377) | `<dynamic>.is_absolute`、`Path`、`SHA256_RE.fullmatch`、`ValueError`、`_require_trimmed`、`isinstance`、`len`、`set` |
| `verify_task_alias_artifacts` — `verify_task_alias_artifacts(entries)` | function / [411](../../../../agent/src/sr2fpga_agent/task_evidence.py#L411) | `<dynamic>.exists`、`<dynamic>.read_text`、`Path`、`ValueError`、`_resolve_evidence_ref`、`_summary_sample_ids`、`json.loads`、`len` |
| `verify_l4_open_artifact_hashes` — `verify_l4_open_artifact_hashes(entries)` | function / [430](../../../../agent/src/sr2fpga_agent/task_evidence.py#L430) | `<dynamic>.hexdigest`、`ValueError`、`_resolve_evidence_ref`、`hashlib.sha256`、`path.is_file`、`path.read_bytes` |
| `_validate_entry` — `_validate_entry(entry, aliases)` | function / [441](../../../../agent/src/sr2fpga_agent/task_evidence.py#L441) | `ValueError`、`_require_status`、`_require_trimmed`、`_validate_independent_oracle`、`isinstance` |
| `_validate_independent_oracle` — `_validate_independent_oracle(entry)` | function / [492](../../../../agent/src/sr2fpga_agent/task_evidence.py#L492) | `SHA256_RE.fullmatch`、`ValueError`、`_require_status`、`_require_trimmed`、`all`、`isinstance`、`len`、`set` |
| `_require_status` — `_require_status(value, allowed, field)` | function / [532](../../../../agent/src/sr2fpga_agent/task_evidence.py#L532) | `ValueError`、`isinstance` |
| `_require_trimmed` — `_require_trimmed(value)` | function / [537](../../../../agent/src/sr2fpga_agent/task_evidence.py#L537) | `ValueError`、`isinstance`、`value.strip` |
| `render_task_evidence_markdown` — `render_task_evidence_markdown(catalog_path, evidence_path)` | function / [542](../../../../agent/src/sr2fpga_agent/task_evidence.py#L542) | `<dynamic>.join`、`_markdown_row`、`catalog_path.open`、`json.load`、`len`、`lines.append`、`lines.extend`、`load_l4_open_evidence`、`load_task_alias_evidence`、`load_task_family_evidence`、`str`、`sum` |
| `audit_local_run_artifacts` — `audit_local_run_artifacts(entries, run_root)` | function / [758](../../../../agent/src/sr2fpga_agent/task_evidence.py#L758) | `Path`、`_audit_entry_artifacts`、`_declared_run_ids`、`_fallback_summary_paths`、`_is_lexically_within`、`_record_summary`、`_referenced_export_paths`、`_resolve_evidence_ref`、`export_paths_by_run.get`、`issues.extend`、`run_root.is_dir`、`summaries.get`、`summaries.keys`、`tuple` |
| `_record_summary` — `_record_summary(summary_path, summaries, summary_paths)` | function / [801](../../../../agent/src/sr2fpga_agent/task_evidence.py#L801) | `isinstance`、`json.load`、`summary.get`、`summary_path.open` |
| `_is_lexically_within` — `_is_lexically_within(path, root)` | function / [817](../../../../agent/src/sr2fpga_agent/task_evidence.py#L817) | `<dynamic>.relative_to`、`path.absolute`、`root.absolute` |
| `_fallback_summary_paths` — `_fallback_summary_paths(run_root)` | function / [825](../../../../agent/src/sr2fpga_agent/task_evidence.py#L825) | `candidates.update`、`run_root.glob`、`set`、`sorted`、`tuple` |
| `_referenced_export_paths` — `_referenced_export_paths(summary_paths, run_root)` | function / [837](../../../../agent/src/sr2fpga_agent/task_evidence.py#L837) | `conventional_root.is_dir`、`conventional_root.rglob`、`export_root.is_dir`、`export_root.rglob`、`exports_by_run.setdefault`、`iter`、`len`、`next`、`summary_paths.items`、`tuple` |
| `_audit_entry_artifacts` — `_audit_entry_artifacts(entry, summary, summaries, export_paths)` | function / [853](../../../../agent/src/sr2fpga_agent/task_evidence.py#L853) | `Path`、`_audit_retained_l4_evidence`、`_audit_trajectory`、`_resolve_evidence_ref`、`_summary_sample_ids`、`issues.append`、`issues.extend`、`mutation_root.is_dir`、`set` |
| `_audit_retained_l4_evidence` — `_audit_retained_l4_evidence(entry, summaries)` | function / [908](../../../../agent/src/sr2fpga_agent/task_evidence.py#L908) | `<dynamic>.is_file`、`<dynamic>.read_text`、`Path`、`_resolve_evidence_ref`、`_same_path`、`_summary_sample_ids`、`all`、`any`、`isinstance`、`json.loads`、`labels.get`、`labels_path.read_text`、`level.get`、`metadata.get`、`payload.get`、`referenced_run_ids.add`、`set`、`summaries.get`、`summary_path.read_text`、`trajectory.get`、`trajectory_path.read_text`、`verification.get` |
| `_audit_trajectory` — `_audit_trajectory(entry, summary, trajectory_path, mutation_roots, export_paths)` | function / [992](../../../../agent/src/sr2fpga_agent/task_evidence.py#L992) | `_audit_qualified_independent_oracle`、`_audit_qualified_oracle`、`_audit_sample_labels`、`_canonical_family_id`、`_summary_sample_ids`、`isinstance`、`issues.append`、`issues.extend`、`json.load`、`metadata.get`、`metadata_path.open`、`oracle.get`、`trajectory.get`、`trajectory_path.is_file`、`trajectory_path.open` |
| `_audit_withheld_oracle_exports` — `_audit_withheld_oracle_exports(family_id, bundle, export_paths)` | function / [1051](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1051) | `<dynamic>.join`、`<dynamic>.strip`、`_exported_value_matches_seed`、`_nested_json_values`、`_normalize_export_text`、`any`、`export_path.read_text`、`exported_text.append`、`exported_values.extend`、`isinstance`、`issues.append`、`json.loads`、`text.splitlines`、`vector_path.read_text` |
| `_exported_value_matches_seed` — `_exported_value_matches_seed(value, seed)` | function / [1114](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1114) | `int`、`isinstance`、`re.fullmatch`、`value.strip` |
| `_normalize_export_text` — `_normalize_export_text(value)` | function / [1122](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1122) | `<dynamic>.replace`、`value.replace` |
| `_nested_json_values` — `_nested_json_values(value)` | function / [1126](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1126) | `_nested_json_values`、`isinstance`、`value.items`、`values.append`、`values.extend` |
| `_audit_sample_labels` — `_audit_sample_labels(entry, summary, sample_dir)` | function / [1140](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1140) | `_summary_success_l3_ids`、`all`、`any`、`isinstance`、`issues.append`、`json.load`、`labels.get`、`labels_path.open` |
| `_audit_qualified_oracle` — `_audit_qualified_oracle(entry, oracle, sample_dir, mutation_roots)` | function / [1180](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1180) | `_audit_mutation_tool_evidence`、`_is_within`、`_same_path`、`all`、`any`、`artifact_path.is_dir`、`detail.get`、`details.items`、`details.values`、`float`、`isinstance`、`issues.append`、`issues.extend`、`len`、`oracle.get` |
| `_audit_mutation_tool_evidence` — `_audit_mutation_tool_evidence(name, artifact_path)` | function / [1237](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1237) | `_read_json_object`、`compile_result.get`、`issues.append`、`run_result.get` |
| `_read_json_object` — `_read_json_object(path)` | function / [1261](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1261) | `isinstance`、`json.loads`、`path.read_text` |
| `_audit_qualified_independent_oracle` — `_audit_qualified_independent_oracle(entry, trajectory, sample_dir, export_paths)` | function / [1269](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1269) | `_audit_oracle_scenario_classes`、`_audit_withheld_oracle_exports`、`actual.get`、`actual_scenarios.get`、`evidence.get`、`evidence_path.open`、`expected.get`、`expected_scenarios.items`、`isinstance`、`issues.append`、`issues.extend`、`json.load`、`legacy_path.is_file`、`len`、`load_oracle_bundle`、`load_oracle_manifest_commitment`、`path.is_file`、`profile.get`、`sanitize_oracle_profile`、`scenario.get`、`sum`、`trajectory.get`、`tuple` |
| `_audit_oracle_scenario_classes` — `_audit_oracle_scenario_classes(source, label, family_id)` | function / [1402](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1402) | `counts.get`、`isinstance`、`issues.append`、`source.get`、`statuses.get` |
| `_summary_sample_ids` — `_summary_sample_ids(summary)` | function / [1424](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1424) | `buckets.values`、`isinstance`、`set`、`summary.get` |
| `_summary_success_l3_ids` — `_summary_success_l3_ids(summary)` | function / [1437](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1437) | `buckets.get`、`isinstance`、`set`、`summary.get` |
| `_resolve_evidence_ref` — `_resolve_evidence_ref(reference)` | function / [1445](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1445) | `Path`、`path.is_absolute` |
| `_same_path` — `_same_path(left, right)` | function / [1450](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1450) | `left.resolve`、`right.resolve` |
| `_is_within` — `_is_within(path, root)` | function / [1454](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1454) | `<dynamic>.relative_to`、`path.resolve`、`root.resolve` |
| `_canonical_family_id` — `_canonical_family_id(task_family)` | function / [1462](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1462) | `family_id_for_task_type`、`isinstance` |
| `main` — `main(argv)` | function / [1471](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1471) | `EVIDENCE_PATH.resolve`、`argparse.ArgumentParser`、`args.output.resolve`、`args.output.write_text`、`audit_local_run_artifacts`、`load_task_family_evidence`、`parser.add_argument`、`parser.error`、`parser.parse_args`、`print`、`render_task_evidence_markdown` |
| `_declared_run_ids` — `_declared_run_ids(entries)` | function / [1495](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1495) | `run_ids.append`、`tuple` |
| `_markdown_row` — `_markdown_row(*values)` | function / [1508](../../../../agent/src/sr2fpga_agent/task_evidence.py#L1508) | `<dynamic>.join` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`RepositoryPaths.discover`、`SystemExit`、`dataclass`、`frozenset`、`main`、`re.compile`

## `agent/src/sr2fpga_agent/terminal_selection.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/terminal_selection.py) · 202 行 · SHA-256 `d836974c50ee36650f9bb97e36f9a9d37dd0ebd50f2ee68a25a0e3c5f4962b12`

> Fail-closed development terminal selection from public-evaluator outcomes.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`re`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.public_evaluator`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TerminalSelectionError` — `TerminalSelectionError` | class / [19](../../../../agent/src/sr2fpga_agent/terminal_selection.py#L19) | 无直接调用 |
| `TerminalSelectionCandidate` — `TerminalSelectionCandidate` | class / [24](../../../../agent/src/sr2fpga_agent/terminal_selection.py#L24) | 无直接调用 |
| `DevelopmentTerminalSelection` — `DevelopmentTerminalSelection` | class / [30](../../../../agent/src/sr2fpga_agent/terminal_selection.py#L30) | 无直接调用 |
| `select_development_terminal_candidate` — `select_development_terminal_candidate(store, episode_id, method_condition, evaluation_scope, attempt_profile, candidates, registry)` | function / [35](../../../../agent/src/sr2fpga_agent/terminal_selection.py#L35) | `<dynamic>.hexdigest`、`ContractRegistry`、`DevelopmentTerminalSelection`、`TerminalSelectionError`、`_canonical_json`、`_read_candidate`、`attempt_match.group`、`hashlib.sha256`、`int`、`item.public_evaluation_candidate_ref.to_dict`、`item.public_outcome_ref.to_dict`、`len`、`re.fullmatch`、`read_verified_development_authoritative_attempt_public_outcome`、`records.append`、`seen_attempts.add`、`seen_candidates.add`、`set`、`store.put_validated_json`、`tuple` |
| `read_verified_development_terminal_selection` — `read_verified_development_terminal_selection(store, reference, registry)` | function / [160](../../../../agent/src/sr2fpga_agent/terminal_selection.py#L160) | `<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`TerminalSelectionError`、`_canonical_json`、`contract.validate`、`hashlib.sha256`、`json.loads`、`payload.items`、`store.read_verified` |
| `_read_candidate` — `_read_candidate(store, reference, registry)` | function / [184](../../../../agent/src/sr2fpga_agent/terminal_selection.py#L184) | `<dynamic>.join`、`<dynamic>.validate`、`TerminalSelectionError`、`json.loads`、`payload.get`、`registry.load_schema`、`store.read_verified` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/testbench_checker.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/testbench_checker.py) · 240 行 · SHA-256 `69bacae534be2243bd9fd90419a567b5a42f546936e849dc2a6480f11e5063ef`

> Static checks for generated self-checking Verilog testbenches.

导入模块：`__future__`、`dataclasses`、`re`、`sr2fpga_agent.models`、`sr2fpga_agent.task_catalog`、`sr2fpga_agent.task_families`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TestbenchObservationIssue` — `TestbenchObservationIssue` | class / [14](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L14) | 无直接调用 |
| `build_oracle_strength` — `build_oracle_strength(reference_pass, mutation_results, task_type)` | function / [20](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L20) | `_mutation_outcome`、`len`、`mutation_results.items`、`oracle_strength_ready`、`oracle_strength_threshold`、`outcomes.items`、`outcomes.values`、`round`、`sorted`、`sum` |
| `oracle_strength_threshold` — `oracle_strength_threshold(task_type)` | function / [51](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L51) | `family_id_for_task_type`、`task_family_spec_for_family_id` |
| `oracle_strength_ready` — `oracle_strength_ready(task_type, mutation_score)` | function / [63](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L63) | `oracle_strength_threshold` |
| `_mutation_outcome` — `_mutation_outcome(status)` | function / [69](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L69) | 无直接调用 |
| `check_testbench_observation_races` — `check_testbench_observation_races(testbench)` | function / [77](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L77) | `TestbenchObservationIssue`、`_normalize`、`enumerate`、`issues.append`、`len`、`min`、`range`、`testbench.splitlines` |
| `check_testbench_static_issues` — `check_testbench_static_issues(testbench)` | function / [106](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L106) | `check_testbench_internal_signal_access`、`check_testbench_missing_functional_oracle`、`check_testbench_observation_races`、`check_testbench_stimulus_reaccept_risks` |
| `check_testbench_internal_signal_access` — `check_testbench_internal_signal_access(testbench)` | function / [116](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L116) | `<dynamic>.count`、`TestbenchObservationIssue`、`enumerate`、`issues.append`、`match.group`、`re.finditer`、`re.sub`、`scrubbed.splitlines` |
| `check_testbench_missing_functional_oracle` — `check_testbench_missing_functional_oracle(testbench)` | function / [143](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L143) | `<dynamic>.count`、`TestbenchObservationIssue`、`pass_match.start`、`re.search` |
| `check_testbench_stimulus_reaccept_risks` — `check_testbench_stimulus_reaccept_risks(testbench)` | function / [165](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L165) | `<dynamic>.join`、`TestbenchObservationIssue`、`_assigns_valid_signal`、`_normalize`、`_valid_signals_assigned`、`enumerate`、`issues.append`、`len`、`list`、`live_valids.remove`、`live_valids.update`、`min`、`range`、`set`、`sorted`、`testbench.splitlines` |
| `testbench_observation_tool_result` — `testbench_observation_tool_result(issues)` | function / [201](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L201) | `<dynamic>.join`、`ToolResult` |
| `_normalize` — `_normalize(line)` | function / [227](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L227) | `<dynamic>.join`、`<dynamic>.split`、`line.strip` |
| `_valid_signals_assigned` — `_valid_signals_assigned(line, value)` | function / [231](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L231) | `match.group`、`re.escape`、`re.finditer` |
| `_assigns_valid_signal` — `_assigns_valid_signal(line, signal, value)` | function / [238](../../../../agent/src/sr2fpga_agent/testbench_checker.py#L238) | `re.escape`、`re.search` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/tool_environment.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tool_environment.py) · 235 行 · SHA-256 `4a369f5d2ae4ac973da769222113e1952a66378f45d359a7752b06c51db6ff00`

> Deterministic, path-sanitized development tool-environment snapshots.

导入模块：`__future__`、`hashlib`、`pathlib`、`re`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.local_tools`、`subprocess`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `collect_development_tool_environment` — `collect_development_tool_environment(timeout_seconds, resolver, command_executor)` | function / [25](../../../../agent/src/sr2fpga_agent/tool_environment.py#L25) | `CORE_TOOL_VERSION_COMMANDS.items`、`TypeError`、`ValueError`、`_probe_tool`、`all`、`isinstance`、`sorted`、`validate_development_tool_environment` |
| `validate_development_tool_environment` — `validate_development_tool_environment(snapshot)` | function / [67](../../../../agent/src/sr2fpga_agent/tool_environment.py#L67) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_validate_tool_record_status`、`all`、`list` |
| `tool_version_projection` — `tool_version_projection(snapshot)` | function / [97](../../../../agent/src/sr2fpga_agent/tool_environment.py#L97) | `validate_development_tool_environment` |
| `_probe_tool` — `_probe_tool(name, command, timeout_seconds, resolver, command_executor)` | function / [114](../../../../agent/src/sr2fpga_agent/tool_environment.py#L114) | `<dynamic>.hexdigest`、`Path`、`_combined_output`、`_empty_record`、`combined_output.encode`、`combined_output.splitlines`、`command_executor`、`executable_env`、`hashlib.sha256`、`int`、`len`、`line.strip`、`next`、`resolved.read_bytes`、`resolver`、`sanitize_version_line`、`str` |
| `_empty_record` — `_empty_record(name, command)` | function / [175](../../../../agent/src/sr2fpga_agent/tool_environment.py#L175) | `list` |
| `_combined_output` — `_combined_output(stdout, stderr)` | function / [190](../../../../agent/src/sr2fpga_agent/tool_environment.py#L190) | `<dynamic>.join`、`isinstance`、`value.strip` |
| `sanitize_version_line` — `sanitize_version_line(value)` | function / [195](../../../../agent/src/sr2fpga_agent/tool_environment.py#L195) | `_POSIX_ABSOLUTE_PATH_RE.sub`、`_WINDOWS_ABSOLUTE_PATH_RE.sub` |
| `_validate_tool_record_status` — `_validate_tool_record_status(record)` | function / [200](../../../../agent/src/sr2fpga_agent/tool_environment.py#L200) | `ValueError`、`any` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`re.compile`

## `agent/src/sr2fpga_agent/tool_runner.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tool_runner.py) · 68 行 · SHA-256 `4588152cf06248a8e761f3a854ee8b9fb0d833dba936d5b03817b08644c989fa`

> Command-line tool execution helpers.

导入模块：`__future__`、`pathlib`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.models`、`subprocess`、`time`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `CommandRunner` — `CommandRunner` | class / [13](../../../../agent/src/sr2fpga_agent/tool_runner.py#L13) | 无直接调用 |
| `CommandRunner.run` — `run(self, command, cwd, stage, timeout_seconds)` | function / [16](../../../../agent/src/sr2fpga_agent/tool_runner.py#L16) | `ToolResult`、`executable_env`、`list`、`resolve_executable`、`str`、`subprocess.run`、`time.monotonic` |

## `agent/src/sr2fpga_agent/training_eligibility.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/training_eligibility.py) · 364 行 · SHA-256 `3a27744e0369ba697f43ebf462a2507a797293824e03af23eced51ca188cca8d`

> Evaluator-owned eligibility certificates for CD8 candidate training pools.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.project_contract`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TrainingEligibilityPolicy` — `TrainingEligibilityPolicy` | class / [40](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L40) | 无直接调用 |
| `TrainingEligibilityPolicy.create` — `create(cls, policy_id, training_split_id, episode_ids, allowed_source_classes, allowed_failure_origins)` | function / [49](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L49) | `_sha256`、`cls`、`set`、`sorted`、`tuple` |
| `EvaluatorEligibilityEvidence` — `EvaluatorEligibilityEvidence` | class / [76](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L76) | 无直接调用 |
| `build_training_eligibility_certificate` — `build_training_eligibility_certificate(episode_pack, initial_project_envelope, terminal_candidate, terminal_project_envelope, qualification_outcome, policy, evidence)` | function / [88](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L88) | `_exclusion_reasons`、`_official_hidden_refs`、`_sha256`、`_single_snapshot_id`、`_source_policy_allowed`、`_trusted_surface`、`_validate_input_artifacts`、`_validate_policy`、`asdict`、`len`、`qualification_outcome.get`、`set`、`sorted`、`validate_training_eligibility_certificate` |
| `validate_training_eligibility_certificate` — `validate_training_eligibility_certificate(artifact)` | function / [178](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L178) | `<dynamic>.join`、`<dynamic>.load_schema`、`ContractRegistry`、`ValueError`、`_exclusion_reasons`、`_sha256`、`artifact.items`、`contract.validate` |
| `write_training_eligibility_certificate` — `write_training_eligibility_certificate(path, artifact)` | function / [198](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L198) | `json.dumps`、`path.parent.mkdir`、`path.write_text`、`validate_training_eligibility_certificate` |
| `_validate_policy` — `_validate_policy(policy)` | function / [209](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L209) | `ValueError`、`_sha256`、`set`、`sorted` |
| `_validate_input_artifacts` — `_validate_input_artifacts(episode_pack, initial_project_envelope, terminal_candidate, terminal_project_envelope, qualification_outcome, policy)` | function / [225](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L225) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_sha256`、`_single_snapshot_id`、`validate_episode_pack`、`validate_project_envelope` |
| `_single_snapshot_id` — `_single_snapshot_id(envelope)` | function / [309](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L309) | `ValueError`、`iter`、`len`、`next` |
| `_trusted_surface` — `_trusted_surface(envelope)` | function / [316](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L316) | `file.get`、`records.append`、`sorted`、`tuple` |
| `_source_policy_allowed` — `_source_policy_allowed(policy, evidence)` | function / [327](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L327) | `evidence.failure_origin.lower`、`evidence.source_class.lower` |
| `_official_hidden_refs` — `_official_hidden_refs(qualification, evidence)` | function / [341](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L341) | `<dynamic>.replace`、`ref.lower`、`refs.add`、`set`、`sorted`、`tuple` |
| `_exclusion_reasons` — `_exclusion_reasons(checks, official_hidden_outcome_ref_count)` | function / [353](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L353) | `_CHECK_REASON_IDS.items`、`reasons.append`、`sorted` |
| `_sha256` — `_sha256(value)` | function / [362](../../../../agent/src/sr2fpga_agent/training_eligibility.py#L362) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`

## `agent/src/sr2fpga_agent/training_pool.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/training_pool.py) · 372 行 · SHA-256 `5968f8d0187362183c5b45a8a38105099f3addcb3069b7f3a8ba9613c11a6759`

> Evaluator-owned E_final/E_traj candidate pool assembly for CD8.

导入模块：`__future__`、`hashlib`、`json`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.training_view_exporter`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_training_pool_manifest` — `build_training_pool_manifest(exports, family_by_episode, forbidden_canaries)` | function / [17](../../../../agent/src/sr2fpga_agent/training_pool.py#L17) | `<dynamic>.issubset`、`ValueError`、`_index_exports`、`_mixture_strata`、`_pool_identity`、`_row_ref`、`_set_sha256`、`_sha256`、`certificates.values`、`iter`、`len`、`next`、`set`、`sorted`、`validate_training_pool_exports`、`validate_training_pool_manifest` |
| `validate_training_pool_manifest` — `validate_training_pool_manifest(manifest)` | function / [115](../../../../agent/src/sr2fpga_agent/training_pool.py#L115) | `<dynamic>.issubset`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_pool_identity`、`_set_sha256`、`_sha256`、`_validate_mixture`、`_validate_transition_pairs`、`any`、`len`、`manifest.items`、`seen_row_ids.add`、`set`、`sorted` |
| `validate_training_pool_exports` — `validate_training_pool_exports(manifest, exports, forbidden_canaries)` | function / [170](../../../../agent/src/sr2fpga_agent/training_pool.py#L170) | `<dynamic>.items`、`ValueError`、`_family_assignments`、`_index_exports`、`_mixture_strata`、`_row_ref`、`certificates.items`、`certificates.values`、`indexed.items`、`set`、`validate_training_pool_manifest` |
| `_index_exports` — `_index_exports(treatment, exports, forbidden_canaries)` | function / [239](../../../../agent/src/sr2fpga_agent/training_pool.py#L239) | `ValueError`、`validate_training_view_export` |
| `_row_ref` — `_row_ref(row, sidecar, certificate)` | function / [262](../../../../agent/src/sr2fpga_agent/training_pool.py#L262) | 无直接调用 |
| `_mixture_strata` — `_mixture_strata(episode_ids, certificates, family_by_episode)` | function / [278](../../../../agent/src/sr2fpga_agent/training_pool.py#L278) | `<dynamic>.append`、`ValueError`、`groups.items`、`groups.setdefault`、`isinstance`、`len`、`sorted` |
| `_validate_mixture` — `_validate_mixture(strata, e_final)` | function / [303](../../../../agent/src/sr2fpga_agent/training_pool.py#L303) | `ValueError`、`covered.extend`、`keys.append`、`len`、`set`、`sorted` |
| `_validate_transition_pairs` — `_validate_transition_pairs(manifest)` | function / [324](../../../../agent/src/sr2fpga_agent/training_pool.py#L324) | `ValueError` |
| `_family_assignments` — `_family_assignments(strata)` | function / [337](../../../../agent/src/sr2fpga_agent/training_pool.py#L337) | 无直接调用 |
| `_pool_identity` — `_pool_identity(policy_sha256, training_split_id, e_final_set_sha256, e_traj_set_sha256, treatment_rows, mixture_strata)` | function / [345](../../../../agent/src/sr2fpga_agent/training_pool.py#L345) | `_sha256` |
| `_set_sha256` — `_set_sha256(episode_ids)` | function / [366](../../../../agent/src/sr2fpga_agent/training_pool.py#L366) | `_sha256`、`sorted` |
| `_sha256` — `_sha256(value)` | function / [370](../../../../agent/src/sr2fpga_agent/training_pool.py#L370) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

## `agent/src/sr2fpga_agent/training_release.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/training_release.py) · 458 行 · SHA-256 `e3e7e15c7cfb05e320ed532a2a9805179dad337add88efec8f8c4a63d3046b0d`

> CD8 candidate training-release builder and read-only integrity verifier.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`shutil`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.training_pool`、`typing`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ReleaseLeakagePolicy` — `ReleaseLeakagePolicy` | class / [30](../../../../agent/src/sr2fpga_agent/training_release.py#L30) | 无直接调用 |
| `ReleaseLeakagePolicy.create` — `create(cls, policy_id, forbidden_canaries)` | function / [37](../../../../agent/src/sr2fpga_agent/training_release.py#L37) | `ValueError`、`_sha256_json`、`any`、`cls`、`isinstance`、`set`、`sorted`、`tuple` |
| `build_candidate_training_release` — `build_candidate_training_release(output_root, pool_manifest, exports, leakage_policy, paths)` | function / [56](../../../../agent/src/sr2fpga_agent/training_release.py#L56) | `<dynamic>.resolve`、`FileExistsError`、`Path`、`RepositoryPaths.discover`、`ValueError`、`_candidate_files`、`_file_inventory`、`_release_identity`、`_sha256_json`、`_validate_leakage_policy`、`_write_json`、`files.items`、`final_release.exists`、`relative_path.split`、`repository_paths.artifacts_dir.resolve`、`resolved_output.mkdir`、`shutil.rmtree`、`sorted`、`staging.exists`、`staging.mkdir`、`staging.rename`、`target.parent.mkdir`、`target.write_bytes`、`uuid.uuid4`、`validate_training_pool_exports`、`validate_training_release_manifest` |
| `verify_candidate_training_release` — `verify_candidate_training_release(release_root, leakage_policy, paths)` | function / [131](../../../../agent/src/sr2fpga_agent/training_release.py#L131) | `<dynamic>.as_posix`、`<dynamic>.read_bytes`、`<dynamic>.resolve`、`POOL_PATH.split`、`Path`、`RepositoryPaths.discover`、`ValueError`、`_load_object`、`_load_release_exports`、`_sha256_bytes`、`_validate_file_record_semantics`、`_validate_leakage_policy`、`_validate_treatment_summaries`、`inventory.items`、`len`、`path.is_file`、`path.relative_to`、`relative_path.split`、`repository_paths.artifacts_dir.resolve`、`root.rglob`、`set`、`validate_training_pool_exports`、`validate_training_pool_manifest`、`validate_training_release_manifest` |
| `validate_training_release_manifest` — `validate_training_release_manifest(manifest)` | function / [215](../../../../agent/src/sr2fpga_agent/training_release.py#L215) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError`、`_release_identity`、`_sha256_json`、`len`、`list`、`manifest.items`、`set`、`sorted` |
| `_candidate_files` — `_candidate_files(pool_manifest, exports)` | function / [241](../../../../agent/src/sr2fpga_agent/training_release.py#L241) | `<dynamic>.join`、`_add_unique`、`_compact_json_bytes`、`_json_bytes`、`_sha256_bytes`、`_sha256_json`、`len`、`sorted`、`treatments.append` |
| `_file_inventory` — `_file_inventory(files)` | function / [278](../../../../agent/src/sr2fpga_agent/training_release.py#L278) | `_file_role`、`_sha256_bytes`、`files.items`、`len`、`path.startswith`、`sorted` |
| `_load_release_exports` — `_load_release_exports(root, manifest, pool_manifest)` | function / [293](../../../../agent/src/sr2fpga_agent/training_release.py#L293) | `<dynamic>.append`、`<dynamic>.get`、`Path`、`ValueError`、`_load_jsonl`、`_load_object`、`certificate_path.split`、`referenced.add`、`referenced.update`、`row.get`、`sidecar_path.split`、`view_path.split` |
| `_validate_treatment_summaries` — `_validate_treatment_summaries(manifest, pool_manifest, exports)` | function / [328](../../../../agent/src/sr2fpga_agent/training_release.py#L328) | `ValueError`、`_sha256_json`、`len`、`next`、`sorted` |
| `_validate_file_record_semantics` — `_validate_file_record_semantics(record)` | function / [366](../../../../agent/src/sr2fpga_agent/training_release.py#L366) | `<dynamic>.startswith`、`ValueError`、`_file_role` |
| `_file_role` — `_file_role(path)` | function / [375](../../../../agent/src/sr2fpga_agent/training_release.py#L375) | `ValueError`、`path.startswith` |
| `_release_identity` — `_release_identity(pool_manifest_sha256, leakage_policy_sha256, release_files)` | function / [387](../../../../agent/src/sr2fpga_agent/training_release.py#L387) | `_sha256_json` |
| `_validate_leakage_policy` — `_validate_leakage_policy(policy)` | function / [400](../../../../agent/src/sr2fpga_agent/training_release.py#L400) | `ReleaseLeakagePolicy.create`、`ValueError` |
| `_add_unique` — `_add_unique(files, path, content)` | function / [409](../../../../agent/src/sr2fpga_agent/training_release.py#L409) | `ValueError`、`files.get` |
| `_load_jsonl` — `_load_jsonl(path)` | function / [416](../../../../agent/src/sr2fpga_agent/training_release.py#L416) | `<dynamic>.splitlines`、`ValueError`、`enumerate`、`isinstance`、`json.loads`、`line.strip`、`path.read_text`、`rows.append` |
| `_load_object` — `_load_object(path)` | function / [431](../../../../agent/src/sr2fpga_agent/training_release.py#L431) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_json_bytes` — `_json_bytes(value)` | function / [441](../../../../agent/src/sr2fpga_agent/training_release.py#L441) | `<dynamic>.encode`、`json.dumps` |
| `_compact_json_bytes` — `_compact_json_bytes(value)` | function / [447](../../../../agent/src/sr2fpga_agent/training_release.py#L447) | `<dynamic>.encode`、`json.dumps` |
| `_write_json` — `_write_json(path, value)` | function / [453](../../../../agent/src/sr2fpga_agent/training_release.py#L453) | `_json_bytes`、`path.write_bytes` |
| `_sha256_bytes` — `_sha256_bytes(value)` | function / [457](../../../../agent/src/sr2fpga_agent/training_release.py#L457) | `<dynamic>.hexdigest`、`hashlib.sha256` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/training_view_exporter.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/training_view_exporter.py) · 459 行 · SHA-256 `96822c25cbd34c0f0fba77b4d486b5a73522ea34155fbb53b630457ab971712e`

> Canonical CD8 training-view-row-v2 exporter and eligibility sidecars.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`re`、`shutil`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.models`、`sr2fpga_agent.project_contract`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.training_eligibility`、`typing`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PublicTransitionEvidence` — `PublicTransitionEvidence` | class / [41](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L41) | 无直接调用 |
| `build_project_training_view` — `build_project_training_view(treatment, eligibility_certificate, project, project_envelope, prompt_messages, transition, forbidden_canaries, event_ref_resolver)` | function / [51](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L51) | `ValueError`、`_assert_no_visibility_leak`、`_build_row`、`_build_sidecar`、`_model_visible_project_files`、`_prompt_messages`、`_sha256`、`_validate_snapshot_binding`、`_validate_transition`、`asdict`、`tuple`、`validate_training_view_export` |
| `build_transition_training_view` — `build_transition_training_view(eligibility_certificate, terminal_project, terminal_project_envelope, prompt_messages, transition, forbidden_canaries, event_ref_resolver)` | function / [107](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L107) | `_assert_no_visibility_leak`、`_build_row`、`_build_sidecar`、`_model_visible_project_files`、`_prompt_messages`、`_sha256`、`_validate_snapshot_binding`、`_validate_transition`、`asdict`、`dict`、`tuple`、`validate_training_view_export` |
| `validate_training_view_export` — `validate_training_view_export(row, sidecar, eligibility_certificate, forbidden_canaries)` | function / [163](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L163) | `ValueError`、`_assert_no_visibility_leak`、`_sha256`、`_validate_registered`、`row.items`、`sidecar.items`、`tuple`、`validate_training_eligibility_certificate` |
| `write_training_view_export` — `write_training_view_export(output_root, row, sidecar, eligibility_certificate, forbidden_canaries, paths)` | function / [226](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L226) | `<dynamic>.resolve`、`FileExistsError`、`Path`、`RepositoryPaths.discover`、`ValueError`、`_write_json`、`final_bundle.exists`、`repository_paths.artifacts_dir.resolve`、`resolved_output.mkdir`、`shutil.rmtree`、`staging.exists`、`staging.mkdir`、`staging.rename`、`uuid.uuid4`、`validate_training_view_export` |
| `_validate_snapshot_binding` — `_validate_snapshot_binding(treatment, eligibility_certificate, project, project_envelope, event_ref_resolver)` | function / [266](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L266) | `<dynamic>.join`、`ValueError`、`iter`、`len`、`next`、`validate_training_eligibility_certificate`、`verify_project_envelope` |
| `_model_visible_project_files` — `_model_visible_project_files(project, project_envelope)` | function / [307](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L307) | `<dynamic>.decode`、`<dynamic>.encode`、`ValueError`、`record.get`、`sorted`、`targets.append` |
| `_prompt_messages` — `_prompt_messages(messages)` | function / [336](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L336) | `ValueError`、`enumerate`、`isinstance`、`rendered.append`、`set` |
| `_validate_transition` — `_validate_transition(transition)` | function / [351](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L351) | `ValueError`、`transition.public_patch.strip` |
| `_build_row` — `_build_row(source_episode_id, snapshot_id, treatment, payload)` | function / [364](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L364) | `_sha256` |
| `_build_sidecar` — `_build_sidecar(row, eligibility_certificate, snapshot_envelope_sha256, transition_evidence_sha256)` | function / [390](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L390) | `_sha256` |
| `_validate_registered` — `_validate_registered(key, artifact)` | function / [416](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L416) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError` |
| `_assert_no_visibility_leak` — `_assert_no_visibility_leak(payload, treatment, forbidden_canaries)` | function / [422](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L422) | `ValueError`、`_M6U_JSON_FIELD_PATTERN.search`、`_walk`、`any`、`isinstance`、`value.lower` |
| `_walk` — `_walk(value, path)` | function / [440](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L440) | `_walk`、`enumerate`、`isinstance`、`value.items` |
| `_sha256` — `_sha256(value)` | function / [450](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L450) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |
| `_write_json` — `_write_json(path, artifact)` | function / [455](../../../../agent/src/sr2fpga_agent/training_view_exporter.py#L455) | `json.dumps`、`path.write_text` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`、`re.compile`

## `agent/src/sr2fpga_agent/vivado_report.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/vivado_report.py) · 243 行 · SHA-256 `468eb1fc60c83441e060c564ae21545cb3a5cf085142892bef9f45e1f6d33fe5`

> Vivado representative-flow Tcl generation and normalized report parsing.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`re`、`subprocess`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_vivado_tcl` — `build_vivado_tcl(project_dir, part, target_period_ns)` | function / [14](../../../../agent/src/sr2fpga_agent/vivado_report.py#L14) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.read_text`、`ValueError`、`_tcl_atom`、`_tcl_brace`、`isinstance`、`json.loads`、`manifest.get`、`project_dir.resolve`、`str`、`system_his.get`、`system_his_path.is_file`、`system_his_path.read_text` |
| `parse_vivado_reports` — `parse_vivado_reports(timing_report, utilization_report, target_period_ns, drc_report, methodology_report)` | function / [54](../../../../agent/src/sr2fpga_agent/vivado_report.py#L54) | `_parse_report_rules`、`_parse_utilization_value`、`_parse_wns`、`drc_rules.items`、`sorted` |
| `run_vivado_reference` — `run_vivado_reference(project_dir, vivado_command, part, target_period_ns, timeout_seconds)` | function / [98](../../../../agent/src/sr2fpga_agent/vivado_report.py#L98) | `<dynamic>.as_posix`、`<dynamic>.write_text`、`build_vivado_tcl`、`json.dumps`、`normalize_existing_vivado_reports`、`path.is_file`、`path.relative_to`、`project_dir.resolve`、`report.update`、`report_dir.iterdir`、`report_dir.mkdir`、`sorted`、`str`、`subprocess.run`、`tcl_path.write_text`、`time.monotonic` |
| `normalize_existing_vivado_reports` — `normalize_existing_vivado_reports(project_dir, target_period_ns)` | function / [153](../../../../agent/src/sr2fpga_agent/vivado_report.py#L153) | `<dynamic>.as_posix`、`<dynamic>.write_text`、`json.dumps`、`parse_vivado_reports`、`path.is_file`、`path.relative_to`、`project_dir.resolve`、`read_report`、`report_dir.iterdir`、`sorted` |
| `normalize_existing_vivado_reports.read_report` — `read_report(name)` | function / [157](../../../../agent/src/sr2fpga_agent/vivado_report.py#L157) | `path.is_file`、`path.read_text` |
| `main` — `main(argv)` | function / [181](../../../../agent/src/sr2fpga_agent/vivado_report.py#L181) | `SystemExit`、`argparse.ArgumentParser`、`json.dumps`、`parser.add_argument`、`parser.parse_args`、`print`、`run_vivado_reference` |
| `_parse_wns` — `_parse_wns(report)` | function / [201](../../../../agent/src/sr2fpga_agent/vivado_report.py#L201) | `enumerate`、`float`、`match.group`、`re.match`、`report.splitlines` |
| `_parse_utilization_value` — `_parse_utilization_value(report, label_pattern)` | function / [213](../../../../agent/src/sr2fpga_agent/vivado_report.py#L213) | `float`、`int`、`match.group`、`re.search`、`value.is_integer` |
| `_parse_report_rules` — `_parse_report_rules(report)` | function / [221](../../../../agent/src/sr2fpga_agent/vivado_report.py#L221) | `match.group`、`re.finditer` |
| `_tcl_brace` — `_tcl_brace(path)` | function / [232](../../../../agent/src/sr2fpga_agent/vivado_report.py#L232) | `<dynamic>.as_posix`、`_tcl_atom`、`path.resolve` |
| `_tcl_atom` — `_tcl_atom(value)` | function / [236](../../../../agent/src/sr2fpga_agent/vivado_report.py#L236) | `ValueError` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`
