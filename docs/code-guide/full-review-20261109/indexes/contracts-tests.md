# contracts-tests：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `contracts/tests/test_accounting_schemas.py`

[打开源文件](../../../../contracts/tests/test_accounting_schemas.py) · 115 行 · SHA-256 `7e85eda734a44000bdfa822524dd26a3ead84d437f40335efe0d2b678f38537f`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator(relative)` | function / [27](../../../../contracts/tests/test_accounting_schemas.py#L27) | `<dynamic>.read_text`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`json.loads` |
| `_close_event` — `_close_event()` | function / [33](../../../../contracts/tests/test_accounting_schemas.py#L33) | 无直接调用 |
| `_summary` — `_summary()` | function / [58](../../../../contracts/tests/test_accounting_schemas.py#L58) | 无直接调用 |
| `test_accounting_contracts_accept_closed_full_axis_shapes` — `test_accounting_contracts_accept_closed_full_axis_shapes()` | function / [78](../../../../contracts/tests/test_accounting_schemas.py#L78) | `<dynamic>.validate`、`_close_event`、`_summary`、`_validator` |
| `test_attempt_event_rejects_incomplete_close_and_raw_extra_fields` — `test_attempt_event_rejects_incomplete_close_and_raw_extra_fields()` | function / [87](../../../../contracts/tests/test_accounting_schemas.py#L87) | `<dynamic>.pop`、`_close_event`、`_validator`、`copy.deepcopy`、`pytest.raises`、`validator.validate` |
| `test_cost_summary_preserves_unavailable_instead_of_zero` — `test_cost_summary_preserves_unavailable_instead_of_zero()` | function / [100](../../../../contracts/tests/test_accounting_schemas.py#L100) | `_summary`、`_validator`、`pytest.raises`、`validator.validate` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_ambiguity_audit_events_schema.py`

[打开源文件](../../../../contracts/tests/test_ambiguity_audit_events_schema.py) · 89 行 · SHA-256 `b656d55876f3f4e5bedb13f69f11ce6558e42c5940264ddd113c9f970cc73674`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_artifact` — `_artifact()` | function / [17](../../../../contracts/tests/test_ambiguity_audit_events_schema.py#L17) | 无直接调用 |
| `test_ambiguity_audit_events_schema_is_closed_and_valid` — `test_ambiguity_audit_events_schema_is_closed_and_valid()` | function / [58](../../../../contracts/tests/test_ambiguity_audit_events_schema.py#L58) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`_artifact` |
| `test_downstream_attempt_requires_kind_and_enforcement_status` — `test_downstream_attempt_requires_kind_and_enforcement_status()` | function / [64](../../../../contracts/tests/test_ambiguity_audit_events_schema.py#L64) | `<dynamic>.pop`、`<dynamic>.validate`、`Draft202012Validator`、`_artifact`、`copy.deepcopy`、`pytest.raises` |
| `test_phase_event_rejects_downstream_fields` — `test_phase_event_rejects_downstream_fields()` | function / [71](../../../../contracts/tests/test_ambiguity_audit_events_schema.py#L71) | `<dynamic>.validate`、`Draft202012Validator`、`_artifact`、`copy.deepcopy`、`pytest.raises` |
| `test_not_run_completion_requires_reason_and_nonavailable_infrastructure` — `test_not_run_completion_requires_reason_and_nonavailable_infrastructure()` | function / [78](../../../../contracts/tests/test_ambiguity_audit_events_schema.py#L78) | `<dynamic>.validate`、`Draft202012Validator`、`_artifact`、`completion.pop`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_ambiguity_case_manifest_schema.py`

[打开源文件](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py) · 92 行 · SHA-256 `1a353561736ea6160a3ab93c59959b4636a1ba76258ad7d6b1e36c4a98eec9f0`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_manifest` — `_manifest()` | function / [17](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py#L17) | 无直接调用 |
| `test_ambiguity_case_manifest_schema_is_closed_and_valid` — `test_ambiguity_case_manifest_schema_is_closed_and_valid()` | function / [50](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py#L50) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`_manifest` |
| `test_public_projection_rejects_private_fields` — `test_public_projection_rejects_private_fields(field)` | function / [57](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py#L57) | `<dynamic>.validate`、`Draft202012Validator`、`_manifest`、`copy.deepcopy`、`pytest.raises` |
| `test_clarification_case_requires_one_precommitted_answer_branch` — `test_clarification_case_requires_one_precommitted_answer_branch()` | function / [64](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py#L64) | `<dynamic>.validate`、`Draft202012Validator`、`_manifest`、`pytest.raises` |
| `test_clarification_case_rejects_multiple_answer_branches` — `test_clarification_case_rejects_multiple_answer_branches()` | function / [73](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py#L73) | `<dynamic>.validate`、`Draft202012Validator`、`_manifest`、`pytest.raises` |
| `test_audit_stratum_must_match_gold_disposition` — `test_audit_stratum_must_match_gold_disposition()` | function / [88](../../../../contracts/tests/test_ambiguity_case_manifest_schema.py#L88) | `<dynamic>.validate`、`Draft202012Validator`、`_manifest`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`、`pytest.mark.parametrize`

## `contracts/tests/test_ambiguity_outcome_schema.py`

[打开源文件](../../../../contracts/tests/test_ambiguity_outcome_schema.py) · 138 行 · SHA-256 `1737ce1fd3e1a2e3e02bb8e3d96bcd4e160115530f6dc97d1b1826d6b95ff95c`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_rate` — `_rate()` | function / [17](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L17) | 无直接调用 |
| `_precision_recall` — `_precision_recall()` | function / [21](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L21) | 无直接调用 |
| `_audit_cost` — `_audit_cost()` | function / [31](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L31) | 无直接调用 |
| `_artifact` — `_artifact()` | function / [49](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L49) | `_audit_cost`、`_precision_recall`、`_rate`、`dict` |
| `test_ambiguity_outcome_schema_is_closed_and_valid` — `test_ambiguity_outcome_schema_is_closed_and_valid()` | function / [118](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L118) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`_artifact` |
| `test_outcome_rejects_invented_frozen_interval` — `test_outcome_rejects_invented_frozen_interval()` | function / [124](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L124) | `<dynamic>.validate`、`Draft202012Validator`、`_artifact`、`copy.deepcopy`、`pytest.raises` |
| `test_outcome_allows_null_rate_only_when_runtime_has_no_denominator_shape` — `test_outcome_allows_null_rate_only_when_runtime_has_no_denominator_shape()` | function / [131](../../../../contracts/tests/test_ambiguity_outcome_schema.py#L131) | `<dynamic>.validate`、`Draft202012Validator`、`_artifact`、`copy.deepcopy` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_ambiguity_witness_schema.py`

[打开源文件](../../../../contracts/tests/test_ambiguity_witness_schema.py) · 84 行 · SHA-256 `d3392dc5162e7a793ad34191c9cb9b220c540c227e3665a9d1020eea7512e66d`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_witness` — `_witness()` | function / [18](../../../../contracts/tests/test_ambiguity_witness_schema.py#L18) | 无直接调用 |
| `test_ambiguity_witness_schema_is_closed_and_valid` — `test_ambiguity_witness_schema_is_closed_and_valid()` | function / [67](../../../../contracts/tests/test_ambiguity_witness_schema.py#L67) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`_witness` |
| `test_material_interpretation_adjudication_requires_two_witnesses` — `test_material_interpretation_adjudication_requires_two_witnesses()` | function / [73](../../../../contracts/tests/test_ambiguity_witness_schema.py#L73) | `<dynamic>.pop`、`<dynamic>.validate`、`Draft202012Validator`、`_witness`、`copy.deepcopy`、`pytest.raises` |
| `test_non_ready_gold_cannot_claim_resolved_requirement_basis` — `test_non_ready_gold_cannot_claim_resolved_requirement_basis()` | function / [80](../../../../contracts/tests/test_ambiguity_witness_schema.py#L80) | `<dynamic>.validate`、`Draft202012Validator`、`_witness`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_clarification_replay_schema.py`

[打开源文件](../../../../contracts/tests/test_clarification_replay_schema.py) · 73 行 · SHA-256 `86609fada7c575fa10ee2d6d97d01542090957a229525176e91eafc56711a513`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_artifact` — `_artifact()` | function / [17](../../../../contracts/tests/test_clarification_replay_schema.py#L17) | 无直接调用 |
| `test_clarification_replay_schema_is_closed_and_valid` — `test_clarification_replay_schema_is_closed_and_valid()` | function / [52](../../../../contracts/tests/test_clarification_replay_schema.py#L52) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`_artifact` |
| `test_replay_may_record_failure_to_close_as_needs_clarification` — `test_replay_may_record_failure_to_close_as_needs_clarification()` | function / [58](../../../../contracts/tests/test_clarification_replay_schema.py#L58) | `<dynamic>.validate`、`Draft202012Validator`、`_artifact` |
| `test_replay_rejects_boundary_escape_and_invalid_semantic_status` — `test_replay_rejects_boundary_escape_and_invalid_semantic_status(field, value)` | function / [69](../../../../contracts/tests/test_clarification_replay_schema.py#L69) | `<dynamic>.validate`、`Draft202012Validator`、`_artifact`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`、`pytest.mark.parametrize`

## `contracts/tests/test_contract_fixtures.py`

[打开源文件](../../../../contracts/tests/test_contract_fixtures.py) · 104 行 · SHA-256 `33923e67a003574c097957b8e03ff1f91c0f4910a7951f983d2f30067923a500`

导入模块：`json`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_json` — `load_json(path)` | function / [36](../../../../contracts/tests/test_contract_fixtures.py#L36) | `json.loads`、`path.read_text` |
| `path_values` — `path_values(node, parent_key)` | function / [40](../../../../contracts/tests/test_contract_fixtures.py#L40) | `isinstance`、`key.endswith`、`node.items`、`path_values`、`values.append`、`values.extend` |
| `test_contract_fixtures_parse_and_cover_schema_requirements` — `test_contract_fixtures_parse_and_cover_schema_requirements()` | function / [60](../../../../contracts/tests/test_contract_fixtures.py#L60) | `<dynamic>.items`、`FIXTURES.items`、`load_json`、`set` |
| `test_all_fixture_paths_are_repository_relative` — `test_all_fixture_paths_are_repository_relative()` | function / [73](../../../../contracts/tests/test_contract_fixtures.py#L73) | `<dynamic>.is_absolute`、`FIXTURES.items`、`Path`、`PurePosixPath`、`load_json`、`path.is_absolute`、`path_values` |
| `test_req2file_fixture_has_no_standalone_pass_credit` — `test_req2file_fixture_has_no_standalone_pass_credit()` | function / [83](../../../../contracts/tests/test_contract_fixtures.py#L83) | `load_json` |
| `test_trajectory_not_run_stages_explain_why` — `test_trajectory_not_run_stages_explain_why()` | function / [91](../../../../contracts/tests/test_contract_fixtures.py#L91) | `<dynamic>.values`、`all`、`load_json`、`stage.get` |
| `test_infrastructure_error_is_distinct_from_model_failure` — `test_infrastructure_error_is_distinct_from_model_failure()` | function / [99](../../../../contracts/tests/test_contract_fixtures.py#L99) | `<dynamic>.values`、`load_json` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_contract_manifest.py`

[打开源文件](../../../../contracts/tests/test_contract_manifest.py) · 119 行 · SHA-256 `e7e5b85ca3ee47d11ca61e723aac6fa3fd84c4d8d26fa9b953ed9cbf845dba95`

导入模块：`json`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_manifest` — `load_manifest()` | function / [8](../../../../contracts/tests/test_contract_manifest.py#L8) | `MANIFEST_PATH.read_text`、`json.loads` |
| `test_contract_manifest_declares_required_contracts` — `test_contract_manifest_declares_required_contracts()` | function / [12](../../../../contracts/tests/test_contract_manifest.py#L12) | `load_manifest`、`set` |
| `test_registered_contract_paths_are_repository_relative` — `test_registered_contract_paths_are_repository_relative()` | function / [106](../../../../contracts/tests/test_contract_manifest.py#L106) | `<dynamic>.is_absolute`、`<dynamic>.is_relative_to`、`<dynamic>.resolve`、`<dynamic>.values`、`Path`、`PurePosixPath`、`load_manifest`、`posix_path.is_absolute` |
| `test_all_registered_contracts_exist` — `test_all_registered_contracts_exist()` | function / [117](../../../../contracts/tests/test_contract_manifest.py#L117) | `<dynamic>.is_file`、`<dynamic>.items`、`load_manifest` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_curate_legacy_evidence.py`

[打开源文件](../../../../contracts/tests/test_curate_legacy_evidence.py) · 315 行 · SHA-256 `f82b3de2e77fa4b9a32836fc80f6c01dd870f82e18f2cd774e23b6241e60190f`

导入模块：`contracts.tools.curate_legacy_evidence`、`hashlib`、`json`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_sha256` — `_sha256(data)` | function / [13](../../../../contracts/tests/test_curate_legacy_evidence.py#L13) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `_write_json` — `_write_json(path, payload)` | function / [17](../../../../contracts/tests/test_curate_legacy_evidence.py#L17) | `json.dumps`、`path.parent.mkdir`、`path.write_text` |
| `_fixture` — `_fixture(tmp_path)` | function / [22](../../../../contracts/tests/test_curate_legacy_evidence.py#L22) | `<dynamic>.mkdir`、`<dynamic>.read_bytes`、`Path`、`_sha256`、`_write_json`、`backup.resolve`、`files.items`、`len`、`path.parent.mkdir`、`path.write_bytes`、`records.append`、`relative.split`、`repository.resolve`、`sorted`、`str`、`workspace.mkdir` |
| `_refresh_recheck_manifest_hash` — `_refresh_recheck_manifest_hash(backup, recheck_path)` | function / [120](../../../../contracts/tests/test_curate_legacy_evidence.py#L120) | `<dynamic>.read_bytes`、`_sha256`、`_write_json`、`json.loads`、`recheck_path.read_text` |
| `test_preview_expands_only_planned_files` — `test_preview_expands_only_planned_files(tmp_path)` | function / [131](../../../../contracts/tests/test_curate_legacy_evidence.py#L131) | `<dynamic>.exists`、`_fixture`、`all`、`build_curation_preview` |
| `test_apply_copies_exact_files_and_is_idempotent` — `test_apply_copies_exact_files_and_is_idempotent(tmp_path)` | function / [163](../../../../contracts/tests/test_curate_legacy_evidence.py#L163) | `<dynamic>.split`、`Path`、`_fixture`、`_sha256`、`apply_curation`、`build_curation_preview`、`destination.is_file`、`destination.read_bytes` |
| `test_recheck_for_another_backup_is_rejected` — `test_recheck_for_another_backup_is_rejected(tmp_path)` | function / [186](../../../../contracts/tests/test_curate_legacy_evidence.py#L186) | `<dynamic>.resolve`、`_fixture`、`_write_json`、`build_curation_preview`、`json.loads`、`pytest.raises`、`recheck_path.read_text`、`str` |
| `test_secret_content_blocks_apply` — `test_secret_content_blocks_apply(tmp_path)` | function / [201](../../../../contracts/tests/test_curate_legacy_evidence.py#L201) | `<dynamic>.endswith`、`_fixture`、`_refresh_recheck_manifest_hash`、`_sha256`、`_write_json`、`apply_curation`、`build_curation_preview`、`json.loads`、`len`、`manifest_path.read_text`、`pytest.raises`、`summary_file.write_bytes` |
| `test_private_absolute_path_requires_review` — `test_private_absolute_path_requires_review(tmp_path)` | function / [231](../../../../contracts/tests/test_curate_legacy_evidence.py#L231) | `<dynamic>.endswith`、`_fixture`、`_refresh_recheck_manifest_hash`、`_sha256`、`_write_json`、`build_curation_preview`、`json.loads`、`len`、`manifest_path.read_text`、`summary_file.write_bytes` |
| `test_conflicting_destination_is_rejected_before_copy` — `test_conflicting_destination_is_rejected_before_copy(tmp_path)` | function / [266](../../../../contracts/tests/test_curate_legacy_evidence.py#L266) | `<dynamic>.split`、`Path`、`_fixture`、`apply_curation`、`build_curation_preview`、`destination.parent.mkdir`、`destination.write_text`、`pytest.raises` |
| `test_apply_rejects_destination_outside_curated_root` — `test_apply_rejects_destination_outside_curated_root(tmp_path)` | function / [286](../../../../contracts/tests/test_curate_legacy_evidence.py#L286) | `_fixture`、`apply_curation`、`build_curation_preview`、`pytest.raises` |
| `test_manifest_change_after_recheck_is_rejected` — `test_manifest_change_after_recheck_is_rejected(tmp_path)` | function / [302](../../../../contracts/tests/test_curate_legacy_evidence.py#L302) | `_fixture`、`_write_json`、`build_curation_preview`、`json.loads`、`manifest_path.read_text`、`pytest.raises` |

## `contracts/tests/test_dataset_release_policy.py`

[打开源文件](../../../../contracts/tests/test_dataset_release_policy.py) · 161 行 · SHA-256 `83215d48415c2bf3539a186b388ad2fbcbf8f4fb41c3bece6099617a8939ed63`

导入模块：`hashlib`、`json`、`pathlib`、`subprocess`、`sys`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_manifest` — `load_manifest()` | function / [29](../../../../contracts/tests/test_dataset_release_policy.py#L29) | `DATASET_MANIFEST.read_text`、`json.loads` |
| `repository_path` — `repository_path(relative_path)` | function / [33](../../../../contracts/tests/test_dataset_release_policy.py#L33) | `<dynamic>.is_absolute`、`<dynamic>.resolve`、`Path`、`PurePosixPath`、`posix_path.is_absolute`、`resolved.is_relative_to` |
| `parse_inventory` — `parse_inventory(path)` | function / [44](../../../../contracts/tests/test_dataset_release_policy.py#L44) | `<dynamic>.splitlines`、`int`、`len`、`line.partition`、`path.read_text`、`records.append` |
| `sha256` — `sha256(path)` | function / [55](../../../../contracts/tests/test_dataset_release_policy.py#L55) | `digest.hexdigest`、`digest.update`、`hashlib.sha256`、`iter`、`path.open`、`stream.read` |
| `test_dataset_manifest_declares_exact_legacy_releases` — `test_dataset_manifest_declares_exact_legacy_releases()` | function / [63](../../../../contracts/tests/test_dataset_release_policy.py#L63) | `len`、`load_manifest` |
| `test_checksum_manifests_are_pinned_to_lf_in_git` — `test_checksum_manifests_are_pinned_to_lf_in_git()` | function / [71](../../../../contracts/tests/test_dataset_release_policy.py#L71) | `<dynamic>.splitlines`、`GIT_ATTRIBUTES.read_text`、`line.strip` |
| `test_dataset_release_metadata_and_paths_are_safe` — `test_dataset_release_metadata_and_paths_are_safe()` | function / [79](../../../../contracts/tests/test_dataset_release_policy.py#L79) | `<dynamic>.exists`、`load_manifest`、`repository_path`、`set` |
| `test_checksum_manifests_match_deterministic_samples` — `test_checksum_manifests_match_deterministic_samples()` | function / [90](../../../../contracts/tests/test_dataset_release_policy.py#L90) | `any`、`len`、`load_manifest`、`parse_inventory`、`relative_path.startswith`、`repository_path`、`sha256`、`sorted` |
| `test_inventory_tool_writes_sorted_lf_manifest` — `test_inventory_tool_writes_sorted_lf_manifest(tmp_path)` | function / [111](../../../../contracts/tests/test_dataset_release_policy.py#L111) | `<dynamic>.write_bytes`、`exports.mkdir`、`output_path.read_bytes`、`parse_inventory`、`payload.mkdir`、`str`、`subprocess.run` |
| `test_inventory_tool_rejects_missing_or_unsafe_releases` — `test_inventory_tool_rejects_missing_or_unsafe_releases(tmp_path)` | function / [146](../../../../contracts/tests/test_dataset_release_policy.py#L146) | `str`、`subprocess.run` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_development_block_preparation_event_schema.py`

[打开源文件](../../../../contracts/tests/test_development_block_preparation_event_schema.py) · 212 行 · SHA-256 `824615fa4da14faef8a48ceef8f2d51a86b51edd9cdb1f32a70edfc9c1394388`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [33](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L33) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_ref` — `_ref(key)` | function / [39](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L39) | 无直接调用 |
| `_event` — `_event()` | function / [48](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L48) | `_ref` |
| `_close_event` — `_close_event()` | function / [83](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L83) | `_event`、`payload.update` |
| `test_block_preparation_event_is_method_neutral` — `test_block_preparation_event_is_method_neutral()` | function / [100](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L100) | `<dynamic>.validate`、`_close_event`、`_event`、`_validator` |
| `test_block_preparation_event_rejects_method_or_ordinal_owner` — `test_block_preparation_event_rejects_method_or_ordinal_owner(field, value)` | function / [111](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L111) | `<dynamic>.validate`、`_event`、`_validator`、`pytest.raises` |
| `test_block_preparation_event_rejects_unknown_checkpoint_and_invalid_parent` — `test_block_preparation_event_rejects_unknown_checkpoint_and_invalid_parent()` | function / [121](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L121) | `<dynamic>.validate`、`_event`、`_validator`、`pytest.raises` |
| `test_block_preparation_event_rejects_missing_axis_and_unavailable_without_reason` — `test_block_preparation_event_rejects_missing_axis_and_unavailable_without_reason()` | function / [133](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L133) | `<dynamic>.pop`、`<dynamic>.validate`、`_close_event`、`_event`、`_validator`、`pytest.raises` |
| `test_non_close_events_require_a_checkpoint_and_matching_stage` — `test_non_close_events_require_a_checkpoint_and_matching_stage()` | function / [145](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L145) | `<dynamic>.validate`、`_event`、`_validator`、`mismatched_stage.update`、`no_checkpoint.update`、`pytest.raises` |
| `test_unavailable_axes_require_exact_null_delta_correspondence` — `test_unavailable_axes_require_exact_null_delta_correspondence()` | function / [166](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L166) | `<dynamic>.pop`、`<dynamic>.validate`、`_event`、`_validator`、`copy.deepcopy`、`pytest.raises`、`valid_unavailable.update` |
| `test_block_preparation_event_rejects_authority_escalation` — `test_block_preparation_event_rejects_authority_escalation(field)` | function / [195](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L195) | `<dynamic>.validate`、`_event`、`_validator`、`pytest.raises` |
| `test_block_preparation_event_rejects_wrong_version_and_unknown_field` — `test_block_preparation_event_rejects_wrong_version_and_unknown_field()` | function / [203](../../../../contracts/tests/test_development_block_preparation_event_schema.py#L203) | `<dynamic>.validate`、`_event`、`_validator`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_development_l4_qor_provenance_schema.py`

[打开源文件](../../../../contracts/tests/test_development_l4_qor_provenance_schema.py) · 83 行 · SHA-256 `5f46f7dc719132371c4702682eef7fdf3d8891f7968fcdf654d2d437be3018e3`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [17](../../../../contracts/tests/test_development_l4_qor_provenance_schema.py#L17) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_incomplete_payload` — `_incomplete_payload()` | function / [23](../../../../contracts/tests/test_development_l4_qor_provenance_schema.py#L23) | 无直接调用 |
| `test_incomplete_l4_provenance_preserves_raw_hashes_without_overclaim` — `test_incomplete_l4_provenance_preserves_raw_hashes_without_overclaim()` | function / [58](../../../../contracts/tests/test_development_l4_qor_provenance_schema.py#L58) | `<dynamic>.validate`、`_incomplete_payload`、`_validator` |
| `test_complete_l4_provenance_requires_version_raw_evidence_and_no_gap` — `test_complete_l4_provenance_requires_version_raw_evidence_and_no_gap()` | function / [62](../../../../contracts/tests/test_development_l4_qor_provenance_schema.py#L62) | `<dynamic>.validate`、`_incomplete_payload`、`_validator`、`pytest.raises` |
| `test_development_l4_provenance_rejects_authority_escalation` — `test_development_l4_provenance_rejects_authority_escalation(field, value)` | function / [78](../../../../contracts/tests/test_development_l4_qor_provenance_schema.py#L78) | `<dynamic>.validate`、`_incomplete_payload`、`_validator`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_development_oracle_run_evidence_schema.py`

[打开源文件](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py) · 145 行 · SHA-256 `775a4c7aea33a7219ce90671f7d635d3bdc36c2f151420982d6e6c41cb35b798`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [24](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L24) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_scenario` — `_scenario(scenario_class)` | function / [30](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L30) | 无直接调用 |
| `_payload` — `_payload()` | function / [46](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L46) | `_scenario` |
| `test_development_oracle_run_evidence_accepts_current_payload` — `test_development_oracle_run_evidence_accepts_current_payload()` | function / [64](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L64) | `<dynamic>.validate`、`_payload`、`_validator` |
| `test_failed_run_accepts_each_registered_execution_origin` — `test_failed_run_accepts_each_registered_execution_origin(failure_origin, failure_type)` | function / [76](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L76) | `<dynamic>.validate`、`_payload`、`_validator` |
| `test_failed_run_requires_registered_origin_and_fine_grained_type` — `test_failed_run_requires_registered_origin_and_fine_grained_type(failure_origin, failure_type)` | function / [102](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L102) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_passed_scenario_cannot_carry_failure_metadata` — `test_passed_scenario_cannot_carry_failure_metadata()` | function / [115](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L115) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_development_oracle_evidence_cannot_claim_authority` — `test_development_oracle_evidence_cannot_claim_authority(field, value)` | function / [132](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L132) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_development_oracle_evidence_is_closed_against_hidden_material_fields` — `test_development_oracle_evidence_is_closed_against_hidden_material_fields()` | function / [140](../../../../contracts/tests/test_development_oracle_run_evidence_schema.py#L140) | `<dynamic>.validate`、`_payload`、`_validator`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_development_paired_block_cost_reconciliation_schema.py`

[打开源文件](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py) · 427 行 · SHA-256 `db9d9c944938ca0d09d22c16f0d994c784d68bedbfb3a787d37051f5dfadb835`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [50](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L50) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_ref` — `_ref(key)` | function / [56](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L56) | 无直接调用 |
| `_axes` — `_axes(value)` | function / [65](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L65) | 无直接调用 |
| `_method` — `_method(method)` | function / [72](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L72) | `_axes`、`_ref` |
| `_contrast` — `_contrast(contrast_id, checkpoint_id, treatment, baseline)` | function / [87](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L87) | `_axes` |
| `_complete_reconciliation` — `_complete_reconciliation()` | function / [105](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L105) | `_axes`、`_contrast`、`_method`、`_ref`、`enumerate`、`list` |
| `_incomplete_reconciliation` — `_incomplete_reconciliation()` | function / [142](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L142) | `_axes`、`_complete_reconciliation`、`blocked.update` |
| `_method_failed_reconciliation` — `_method_failed_reconciliation(status)` | function / [177](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L177) | `_complete_reconciliation` |
| `test_complete_and_incomplete_reconciliations_are_valid` — `test_complete_and_incomplete_reconciliations_are_valid()` | function / [187](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L187) | `<dynamic>.validate`、`_complete_reconciliation`、`_incomplete_reconciliation`、`_validator` |
| `test_signed_delta_allows_negative_measured_value` — `test_signed_delta_allows_negative_measured_value()` | function / [192](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L192) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator` |
| `test_count_axes_reject_fractional_values` — `test_count_axes_reject_fractional_values(axis, result_kind)` | function / [204](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L204) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_duration_axes_accept_fractional_values` — `test_duration_axes_accept_fractional_values(axis, result_kind)` | function / [218](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L218) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator` |
| `test_reconciliation_requires_all_methods_contrasts_and_axes` — `test_reconciliation_requires_all_methods_contrasts_and_axes(mutation)` | function / [248](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L248) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`mutation`、`pytest.raises` |
| `test_non_delta_axes_are_non_negative` — `test_non_delta_axes_are_non_negative()` | function / [256](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L256) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_axis_missingness_is_not_encoded_as_zero_or_without_reason` — `test_axis_missingness_is_not_encoded_as_zero_or_without_reason(axis_payload)` | function / [274](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L274) | `<dynamic>.validate`、`_incomplete_reconciliation`、`_validator`、`pytest.raises` |
| `test_complete_record_requires_trajectories_and_full_pack` — `test_complete_record_requires_trajectories_and_full_pack()` | function / [282](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L282) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_incomplete_record_requires_a_named_reason_and_null_full_pack` — `test_incomplete_record_requires_a_named_reason_and_null_full_pack()` | function / [293](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L293) | `<dynamic>.validate`、`_incomplete_reconciliation`、`_ref`、`_validator`、`pytest.raises` |
| `test_incomplete_record_accepts_nonblocked_terminal_method_with_trajectory` — `test_incomplete_record_accepts_nonblocked_terminal_method_with_trajectory(status)` | function / [305](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L305) | `<dynamic>.validate`、`_method_failed_reconciliation`、`_validator` |
| `test_incomplete_record_requires_a_noncompleted_method` — `test_incomplete_record_requires_a_noncompleted_method()` | function / [311](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L311) | `<dynamic>.validate`、`_complete_reconciliation`、`_incomplete_reconciliation`、`_validator`、`pytest.raises` |
| `test_measured_contrast_requires_every_dependent_axis_measured` — `test_measured_contrast_requires_every_dependent_axis_measured(dependent_axis)` | function / [324](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L324) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_unavailable_contrast_requires_an_unavailable_dependent_axis` — `test_unavailable_contrast_requires_an_unavailable_dependent_axis()` | function / [344](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L344) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_unavailable_contrast_requires_a_nonempty_reason` — `test_unavailable_contrast_requires_a_nonempty_reason()` | function / [354](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L354) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_partially_unavailable_contrast_is_valid` — `test_partially_unavailable_contrast_is_valid()` | function / [369](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L369) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator` |
| `test_reconciliation_rejects_partial_or_escalated_authority_group` — `test_reconciliation_rejects_partial_or_escalated_authority_group(field)` | function / [389](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L389) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`missing.pop`、`pytest.raises` |
| `test_reconciliation_rejects_unknown_fields` — `test_reconciliation_rejects_unknown_fields()` | function / [400](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L400) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`copy.deepcopy`、`pytest.raises` |
| `test_reconciliation_rejects_wrong_version` — `test_reconciliation_rejects_wrong_version()` | function / [408](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L408) | `<dynamic>.validate`、`_complete_reconciliation`、`_validator`、`pytest.raises` |
| `test_reconciliation_rejects_unknown_or_renamed_axis` — `test_reconciliation_rejects_unknown_or_renamed_axis()` | function / [416](../../../../contracts/tests/test_development_paired_block_cost_reconciliation_schema.py#L416) | `<dynamic>.pop`、`<dynamic>.validate`、`_axes`、`_complete_reconciliation`、`_validator`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.pop`、`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_development_provider_seed_capability_schema.py`

[打开源文件](../../../../contracts/tests/test_development_provider_seed_capability_schema.py) · 151 行 · SHA-256 `ba53555104d4ab52f9da01b6c6ef9ea0b44dd782b47a6fed404006adfce08e16`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [12](../../../../contracts/tests/test_development_provider_seed_capability_schema.py#L12) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_best_effort_payload` — `_best_effort_payload()` | function / [18](../../../../contracts/tests/test_development_provider_seed_capability_schema.py#L18) | `range` |
| `test_best_effort_observation_validates_without_eligibility` — `test_best_effort_observation_validates_without_eligibility()` | function / [87](../../../../contracts/tests/test_development_provider_seed_capability_schema.py#L87) | `<dynamic>.validate`、`_best_effort_payload`、`_validator` |
| `test_best_effort_documentation_cannot_claim_confirmatory_eligibility` — `test_best_effort_documentation_cannot_claim_confirmatory_eligibility()` | function / [91](../../../../contracts/tests/test_development_provider_seed_capability_schema.py#L91) | `<dynamic>.validate`、`_best_effort_payload`、`_validator`、`pytest.raises` |
| `test_capability_artifact_rejects_authority_escalation` — `test_capability_artifact_rejects_authority_escalation(field)` | function / [103](../../../../contracts/tests/test_development_provider_seed_capability_schema.py#L103) | `<dynamic>.validate`、`_best_effort_payload`、`_validator`、`copy.deepcopy`、`pytest.raises` |
| `test_infrastructure_error_requires_failure_category` — `test_infrastructure_error_requires_failure_category()` | function / [111](../../../../contracts/tests/test_development_provider_seed_capability_schema.py#L111) | `<dynamic>.validate`、`_best_effort_payload`、`_validator`、`payload.update`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_development_public_boundary.py`

[打开源文件](../../../../contracts/tests/test_development_public_boundary.py) · 142 行 · SHA-256 `d5d1ce02c7da3bf7a6c23b1ef8d58747fa10aa57b904aa2ce10a14394f4b9e68`

> Public boundary shape only; neither ready-task nor hardware qualification.

导入模块：`copy`、`json`、`pathlib`、`pytest`、`referencing.exceptions`、`socket`、`sr2fpga_agent.contract_registry`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `example` — `example()` | function / [16](../../../../contracts/tests/test_development_public_boundary.py#L16) | `EXAMPLE.read_text`、`json.loads` |
| `contract` — `contract()` | function / [20](../../../../contracts/tests/test_development_public_boundary.py#L20) | `<dynamic>.load_schema`、`ContractRegistry` |
| `test_registered_boundary_example_reuses_pc_types` — `test_registered_boundary_example_reuses_pc_types()` | function / [24](../../../../contracts/tests/test_development_public_boundary.py#L24) | `boundary.validate`、`contract`、`example` |
| `test_boundary_requires_each_field` — `test_boundary_requires_each_field(field)` | function / [36](../../../../contracts/tests/test_development_public_boundary.py#L36) | `<dynamic>.validate`、`contract`、`example` |
| `test_closed_objects_reject_unknown_fields` — `test_closed_objects_reject_unknown_fields(path)` | function / [47](../../../../contracts/tests/test_development_public_boundary.py#L47) | `<dynamic>.validate`、`contract`、`example` |
| `test_stream_mapping_requires_all_three_signal_names` — `test_stream_mapping_requires_all_three_signal_names(field)` | function / [57](../../../../contracts/tests/test_development_public_boundary.py#L57) | `<dynamic>.validate`、`contract`、`example` |
| `test_top_parameter_values_are_concrete_nonnegative_integers` — `test_top_parameter_values_are_concrete_nonnegative_integers(value)` | function / [64](../../../../contracts/tests/test_development_public_boundary.py#L64) | `<dynamic>.validate`、`contract`、`example` |
| `test_inherited_pc_signature_validation_is_active` — `test_inherited_pc_signature_validation_is_active()` | function / [70](../../../../contracts/tests/test_development_public_boundary.py#L70) | `<dynamic>.validate`、`contract`、`example` |
| `test_value_ports_and_nonconsuming_domain_pin_shapes` — `test_value_ports_and_nonconsuming_domain_pin_shapes()` | function / [76](../../../../contracts/tests/test_development_public_boundary.py#L76) | `<dynamic>.validate`、`contract`、`example` |
| `test_scope_cannot_claim_task_readiness` — `test_scope_cannot_claim_task_readiness()` | function / [91](../../../../contracts/tests/test_development_public_boundary.py#L91) | `<dynamic>.validate`、`contract`、`example` |
| `test_cross_field_errors_are_explicitly_outside_shape_scope` — `test_cross_field_errors_are_explicitly_outside_shape_scope()` | function / [100](../../../../contracts/tests/test_development_public_boundary.py#L100) | `<dynamic>.validate`、`contract`、`example` |
| `test_unregistered_schema_uri_never_fetches_network` — `test_unregistered_schema_uri_never_fetches_network(tmp_path, monkeypatch)` | function / [110](../../../../contracts/tests/test_development_public_boundary.py#L110) | `RegisteredContract`、`json.dumps`、`monkeypatch.setattr`、`path.write_text`、`pytest.raises`、`unregistered.validate` |
| `test_unregistered_schema_uri_never_fetches_network.forbidden_network` — `forbidden_network(*args, **kwargs)` | function / [111](../../../../contracts/tests/test_development_public_boundary.py#L111) | `pytest.fail` |
| `test_dependency_change_invalidates_parent_validator_cache` — `test_dependency_change_invalidates_parent_validator_cache(tmp_path)` | function / [124](../../../../contracts/tests/test_development_public_boundary.py#L124) | `ContractRegistry`、`RegisteredContract`、`deepcopy`、`dep_path.write_text`、`json.dumps`、`parent.validate`、`parent2.validate`、`parent_path.write_text`、`registry.load_schema` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_development_shared_checkpoint_manifest_schema.py`

[打开源文件](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py) · 217 行 · SHA-256 `fab653327cc585c1f38cf4670ce76f62d429f97d98f544c9bb8b71498b046615`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [18](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L18) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_ref` — `_ref(key)` | function / [24](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L24) | 无直接调用 |
| `_node` — `_node(checkpoint_id)` | function / [33](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L33) | `_ref` |
| `_complete_manifest` — `_complete_manifest()` | function / [69](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L69) | `_node`、`_ref` |
| `test_manifest_requires_exact_checkpoint_graph` — `test_manifest_requires_exact_checkpoint_graph()` | function / [93](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L93) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`copy.deepcopy`、`pytest.raises` |
| `test_manifest_rejects_authority_escalation` — `test_manifest_rejects_authority_escalation(field)` | function / [114](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L114) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_requires_checkpoint_artifact_key_suffixes` — `test_manifest_requires_checkpoint_artifact_key_suffixes()` | function / [122](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L122) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_rejects_wrong_consumer_set` — `test_manifest_rejects_wrong_consumer_set()` | function / [135](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L135) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_rejects_wrong_parent_edge` — `test_manifest_rejects_wrong_parent_edge()` | function / [143](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L143) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_rejects_missing_parent` — `test_manifest_rejects_missing_parent()` | function / [151](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L151) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_rejects_graph_cycle` — `test_manifest_rejects_graph_cycle()` | function / [159](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L159) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_rejects_missing_node_source_events` — `test_manifest_rejects_missing_node_source_events()` | function / [167](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L167) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_requires_completed_artifacts_and_keeps_incomplete_refs_null` — `test_manifest_requires_completed_artifacts_and_keeps_incomplete_refs_null()` | function / [175](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L175) | `<dynamic>.update`、`<dynamic>.validate`、`_complete_manifest`、`_ref`、`_validator`、`copy.deepcopy`、`pytest.raises` |
| `test_manifest_rejects_trusted_skeleton_substitution` — `test_manifest_rejects_trusted_skeleton_substitution()` | function / [200](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L200) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |
| `test_manifest_rejects_wrong_version_and_unknown_field` — `test_manifest_rejects_wrong_version_and_unknown_field()` | function / [208](../../../../contracts/tests/test_development_shared_checkpoint_manifest_schema.py#L208) | `<dynamic>.validate`、`_complete_manifest`、`_validator`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_episode_pack_schema.py`

[打开源文件](../../../../contracts/tests/test_episode_pack_schema.py) · 91 行 · SHA-256 `2bc54428c5671714fa668d4593e057b2ccdf011911de9e353f89f6ef54b164c5`

导入模块：`json`、`jsonschema`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_payload` — `_payload()` | function / [10](../../../../contracts/tests/test_episode_pack_schema.py#L10) | 无直接调用 |
| `test_episode_pack_schema_is_valid_and_accepts_closed_fixture` — `test_episode_pack_schema_is_valid_and_accepts_closed_fixture()` | function / [44](../../../../contracts/tests/test_episode_pack_schema.py#L44) | `<dynamic>.iter_errors`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`_payload`、`json.loads`、`list` |
| `test_generation_visible_context_rejects_evaluator_fields` — `test_generation_visible_context_rejects_evaluator_fields()` | function / [51](../../../../contracts/tests/test_episode_pack_schema.py#L51) | `<dynamic>.iter_errors`、`Draft202012Validator`、`SCHEMA_PATH.read_text`、`_payload`、`any`、`json.loads`、`list` |
| `test_episode_pack_accepts_paired_block_ref_only_in_audit_projection` — `test_episode_pack_accepts_paired_block_ref_only_in_audit_projection()` | function / [62](../../../../contracts/tests/test_episode_pack_schema.py#L62) | `Draft202012Validator`、`SCHEMA_PATH.read_text`、`_payload`、`json.loads`、`list`、`validator.iter_errors` |
| `test_episode_pack_rejects_malformed_paired_block_ref` — `test_episode_pack_rejects_malformed_paired_block_ref()` | function / [81](../../../../contracts/tests/test_episode_pack_schema.py#L81) | `<dynamic>.iter_errors`、`Draft202012Validator`、`SCHEMA_PATH.read_text`、`_payload`、`json.loads`、`list` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_evaluation_boundary_schemas.py`

[打开源文件](../../../../contracts/tests/test_evaluation_boundary_schemas.py) · 220 行 · SHA-256 `122b1ef6d2344731109896a469e52c0ce155f55fdaf62e107efbb067bddd0a17`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_schema` — `_schema(relative)` | function / [12](../../../../contracts/tests/test_evaluation_boundary_schemas.py#L12) | `<dynamic>.read_text`、`Draft202012Validator.check_schema`、`json.loads` |
| `_official` — `_official()` | function / [18](../../../../contracts/tests/test_evaluation_boundary_schemas.py#L18) | 无直接调用 |
| `_training` — `_training()` | function / [37](../../../../contracts/tests/test_evaluation_boundary_schemas.py#L37) | 无直接调用 |
| `test_official_and_training_outcomes_are_incompatible_closed_contracts` — `test_official_and_training_outcomes_are_incompatible_closed_contracts()` | function / [54](../../../../contracts/tests/test_evaluation_boundary_schemas.py#L54) | `<dynamic>.validate`、`Draft202012Validator`、`_official`、`_schema`、`_training`、`pytest.raises` |
| `test_official_outcome_rejects_hidden_raw_material_and_invalid_missingness` — `test_official_outcome_rejects_hidden_raw_material_and_invalid_missingness()` | function / [68](../../../../contracts/tests/test_evaluation_boundary_schemas.py#L68) | `Draft202012Validator`、`_official`、`_schema`、`copy.deepcopy`、`not_run.pop`、`pytest.raises`、`validator.validate` |
| `test_development_outcome_contracts_are_closed_and_non_official` — `test_development_outcome_contracts_are_closed_and_non_official()` | function / [87](../../../../contracts/tests/test_evaluation_boundary_schemas.py#L87) | `_schema` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_full_pack_smoke_report_schema.py`

[打开源文件](../../../../contracts/tests/test_full_pack_smoke_report_schema.py) · 172 行 · SHA-256 `a669e86ae2ea9db64b25b7bcec855bf67d49e8c156216e7493013cb0c21692d9`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [13](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L13) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_method_record` — `_method_record(method)` | function / [19](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L19) | `method.lower` |
| `_scenario` — `_scenario(kind, method, status, facts)` | function / [48](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L48) | `kind.replace` |
| `_report` — `_report()` | function / [60](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L60) | `_method_record`、`_scenario` |
| `test_full_pack_smoke_report_accepts_closed_excluded_shape` — `test_full_pack_smoke_report_accepts_closed_excluded_shape()` | function / [145](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L145) | `<dynamic>.validate`、`_report`、`_validator` |
| `test_full_pack_smoke_report_rejects_claim_escalation_and_private_details` — `test_full_pack_smoke_report_rejects_claim_escalation_and_private_details()` | function / [149](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L149) | `_report`、`_validator`、`copy.deepcopy`、`pytest.raises`、`validator.validate` |
| `test_full_pack_smoke_report_rejects_unregistered_or_incomplete_pack` — `test_full_pack_smoke_report_rejects_unregistered_or_incomplete_pack()` | function / [162](../../../../contracts/tests/test_full_pack_smoke_report_schema.py#L162) | `<dynamic>.pop`、`_report`、`_validator`、`copy.deepcopy`、`pytest.raises`、`validator.validate` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_inventory_tracked_tmp.py`

[打开源文件](../../../../contracts/tests/test_inventory_tracked_tmp.py) · 127 行 · SHA-256 `759725bb6fcfce15125db7d5cbf11287874376c92ff5ef51ab9575e88984c4bb`

导入模块：`importlib.util`、`json`、`pathlib`、`pytest`、`subprocess`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_git` — `_git(root, *arguments)` | function / [20](../../../../contracts/tests/test_inventory_tracked_tmp.py#L20) | `subprocess.run` |
| `_repository` — `_repository(tmp_path)` | function / [29](../../../../contracts/tests/test_inventory_tracked_tmp.py#L29) | `<dynamic>.mkdir`、`<dynamic>.write_text`、`_git` |
| `_classification` — `_classification(root, destination)` | function / [44](../../../../contracts/tests/test_inventory_tracked_tmp.py#L44) | `json.dumps`、`path.write_text` |
| `test_inventory_classifies_only_explicit_curated_files` — `test_inventory_classifies_only_explicit_curated_files(tmp_path)` | function / [66](../../../../contracts/tests/test_inventory_tracked_tmp.py#L66) | `_classification`、`_repository`、`all`、`inventory_tracked_tmp.build_inventory`、`records.values` |
| `test_inventory_rejects_destination_outside_curated_reports` — `test_inventory_rejects_destination_outside_curated_reports(tmp_path)` | function / [97](../../../../contracts/tests/test_inventory_tracked_tmp.py#L97) | `_classification`、`_repository`、`inventory_tracked_tmp.build_inventory`、`pytest.raises` |
| `test_inventory_output_is_deterministic` — `test_inventory_output_is_deterministic(tmp_path)` | function / [114](../../../../contracts/tests/test_inventory_tracked_tmp.py#L114) | `_repository`、`first.read_bytes`、`inventory_tracked_tmp.build_inventory`、`inventory_tracked_tmp.write_inventory`、`second.read_bytes` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`SPEC.loader.exec_module`、`importlib.util.module_from_spec`、`importlib.util.spec_from_file_location`

## `contracts/tests/test_model_gateway_provenance_schema.py`

[打开源文件](../../../../contracts/tests/test_model_gateway_provenance_schema.py) · 90 行 · SHA-256 `6568aabd76d89965d7e10b65864f457200e5c60f44971051ebe5b8557e394a15`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [12](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L12) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_payload` — `_payload()` | function / [18](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L18) | 无直接调用 |
| `test_requested_unverified_seed_and_reported_fingerprint_validate` — `test_requested_unverified_seed_and_reported_fingerprint_validate()` | function / [45](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L45) | `<dynamic>.validate`、`_payload`、`_validator` |
| `test_negative_call_id_is_rejected` — `test_negative_call_id_is_rejected()` | function / [49](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L49) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_supported_seed_requires_hash_bound_capability_evidence` — `test_supported_seed_requires_hash_bound_capability_evidence()` | function / [57](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L57) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_provenance_rejects_authority_escalation` — `test_provenance_rejects_authority_escalation(field)` | function / [69](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L69) | `<dynamic>.validate`、`_payload`、`_validator`、`copy.deepcopy`、`pytest.raises` |
| `test_missing_seed_cannot_claim_forwarding` — `test_missing_seed_cannot_claim_forwarding()` | function / [77](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L77) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_requested_seed_cannot_be_recorded_as_not_requested` — `test_requested_seed_cannot_be_recorded_as_not_requested()` | function / [85](../../../../contracts/tests/test_model_gateway_provenance_schema.py#L85) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_paired_block_schema.py`

[打开源文件](../../../../contracts/tests/test_paired_block_schema.py) · 141 行 · SHA-256 `a1cb865de98657e5ba41786b6e146302f56fa7d7f91216df22cf22d2c66a1ca9`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validator` — `_validator()` | function / [12](../../../../contracts/tests/test_paired_block_schema.py#L12) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_PATH.read_text`、`json.loads` |
| `_payload` — `_payload()` | function / [18](../../../../contracts/tests/test_paired_block_schema.py#L18) | 无直接调用 |
| `test_canonical_paired_block_validates` — `test_canonical_paired_block_validates()` | function / [39](../../../../contracts/tests/test_paired_block_schema.py#L39) | `<dynamic>.validate`、`_payload`、`_validator` |
| `test_stochastic_block_allows_absent_requested_seed` — `test_stochastic_block_allows_absent_requested_seed()` | function / [43](../../../../contracts/tests/test_paired_block_schema.py#L43) | `<dynamic>.validate`、`_payload`、`_validator` |
| `test_documented_seed_control_requires_requested_seed` — `test_documented_seed_control_requires_requested_seed()` | function / [50](../../../../contracts/tests/test_paired_block_schema.py#L50) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_authority_escalation_is_rejected` — `test_authority_escalation_is_rejected(field)` | function / [69](../../../../contracts/tests/test_paired_block_schema.py#L69) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_invalid_identity_or_seed_is_rejected` — `test_invalid_identity_or_seed_is_rejected(field, value)` | function / [86](../../../../contracts/tests/test_paired_block_schema.py#L86) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_incomplete_duplicate_or_unknown_method_order_is_rejected` — `test_incomplete_duplicate_or_unknown_method_order_is_rejected(method_order)` | function / [102](../../../../contracts/tests/test_paired_block_schema.py#L102) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_family_id_cannot_replace_semantic_instance_id` — `test_family_id_cannot_replace_semantic_instance_id()` | function / [112](../../../../contracts/tests/test_paired_block_schema.py#L112) | `<dynamic>.validate`、`_payload`、`_validator`、`pytest.raises` |
| `test_unknown_field_and_wrong_version_are_rejected` — `test_unknown_field_and_wrong_version_are_rejected()` | function / [121](../../../../contracts/tests/test_paired_block_schema.py#L121) | `<dynamic>.validate`、`_payload`、`_validator`、`copy.deepcopy`、`pytest.raises` |
| `test_contract_manifest_registers_paired_block` — `test_contract_manifest_registers_paired_block()` | function / [133](../../../../contracts/tests/test_paired_block_schema.py#L133) | `<dynamic>.read_text`、`json.loads` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_pc_2_1_registration.py`

[打开源文件](../../../../contracts/tests/test_pc_2_1_registration.py) · 108 行 · SHA-256 `1436506401e4cdff6bbb691cecc23dd015706a73491025ac3ae8c5b6c0741e2f`

> PC 2.1 is the active Project Contract serialization under 'paper1-v2.2'.

导入模块：`__future__`、`json`、`pathlib`、`pytest`、`sr2fpga_agent.contract_registry`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `registry` — `registry()` | function / [24](../../../../contracts/tests/test_pc_2_1_registration.py#L24) | `ContractRegistry` |
| `test_both_pc_2_1_schemas_are_registered_and_resolve` — `test_both_pc_2_1_schemas_are_registered_and_resolve(registry)` | function / [28](../../../../contracts/tests/test_pc_2_1_registration.py#L28) | `registry.load_schema` |
| `test_registered_versions_match_what_the_schema_files_declare` — `test_registered_versions_match_what_the_schema_files_declare()` | function / [36](../../../../contracts/tests/test_pc_2_1_registration.py#L36) | `<dynamic>.read_text`、`json.loads` |
| `test_schemas_live_in_the_layout_the_spec_requires` — `test_schemas_live_in_the_layout_the_spec_requires()` | function / [50](../../../../contracts/tests/test_pc_2_1_registration.py#L50) | `<dynamic>.exists`、`<dynamic>.is_file` |
| `test_wrong_schema_version_is_rejected` — `test_wrong_schema_version_is_rejected(registry, schema_version)` | function / [63](../../../../contracts/tests/test_pc_2_1_registration.py#L63) | `contract.validate`、`registry.load_schema` |
| `test_empty_and_structurally_absent_documents_are_rejected` — `test_empty_and_structurally_absent_documents_are_rejected(registry)` | function / [73](../../../../contracts/tests/test_pc_2_1_registration.py#L73) | `contract.validate`、`registry.load_schema` |
| `test_pc_2_1_requires_bindings_and_design` — `test_pc_2_1_requires_bindings_and_design(registry)` | function / [81](../../../../contracts/tests/test_pc_2_1_registration.py#L81) | `any`、`contract.validate`、`registry.load_schema` |
| `test_system_his_stays_registered_for_existing_artifacts` — `test_system_his_stays_registered_for_existing_artifacts(registry)` | function / [91](../../../../contracts/tests/test_pc_2_1_registration.py#L91) | `registry.load_schema` |
| `test_pc_2_0_schemas_are_not_registered` — `test_pc_2_0_schemas_are_not_registered()` | function / [103](../../../../contracts/tests/test_pc_2_1_registration.py#L103) | `<dynamic>.read_text`、`<dynamic>.values`、`json.loads` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.fixture`、`pytest.mark.parametrize`

## `contracts/tests/test_plan_legacy_evidence_migration.py`

[打开源文件](../../../../contracts/tests/test_plan_legacy_evidence_migration.py) · 187 行 · SHA-256 `2a43275594e8074922d56f7d531b9cee61a10ec82cd346283dea67019d82188c`

导入模块：`importlib.util`、`json`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_ledger` — `_ledger(*families)` | function / [37](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L37) | `list` |
| `_family` — `_family(family_id, refs)` | function / [44](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L44) | 无直接调用 |
| `test_plan_covers_each_unique_reference_once` — `test_plan_covers_each_unique_reference_once()` | function / [48](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L48) | `_family`、`_ledger`、`all`、`plan_legacy_evidence_migration.build_plan`、`records.values` |
| `test_plan_rejects_unsafe_reference` — `test_plan_rejects_unsafe_reference()` | function / [88](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L88) | `_family`、`_ledger`、`plan_legacy_evidence_migration.build_plan`、`pytest.raises` |
| `test_plan_requires_one_run_summary_per_source_root` — `test_plan_requires_one_run_summary_per_source_root()` | function / [106](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L106) | `_family`、`_ledger`、`plan_legacy_evidence_migration.build_plan`、`pytest.raises` |
| `test_plan_output_is_deterministic` — `test_plan_output_is_deterministic(tmp_path)` | function / [124](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L124) | `_family`、`_ledger`、`first.read_bytes`、`first.read_text`、`json.loads`、`plan_legacy_evidence_migration.build_plan`、`plan_legacy_evidence_migration.write_plan`、`second.read_bytes` |
| `test_empty_plan_is_complete` — `test_empty_plan_is_complete()` | function / [148](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L148) | `_family`、`_ledger`、`plan_legacy_evidence_migration.build_plan` |
| `test_active_evidence_ledger_requires_no_legacy_migration` — `test_active_evidence_ledger_requires_no_legacy_migration()` | function / [159](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L159) | `<dynamic>.as_posix`、`LEDGER_PATH.read_text`、`LEDGER_PATH.relative_to`、`json.loads`、`plan_legacy_evidence_migration.build_plan` |
| `test_historical_repository_plan_remains_self_consistent` — `test_historical_repository_plan_remains_self_consistent()` | function / [176](../../../../contracts/tests/test_plan_legacy_evidence_migration.py#L176) | `PLAN_PATH.read_text`、`json.loads`、`len` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`SPEC.loader.exec_module`、`importlib.util.module_from_spec`、`importlib.util.spec_from_file_location`

## `contracts/tests/test_project_contract_schemas.py`

[打开源文件](../../../../contracts/tests/test_project_contract_schemas.py) · 308 行 · SHA-256 `e663b9ae20209b0a349d7ada8c8d2872d1237a9ada2a1e119e7040d79dbea85a`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_json` — `load_json(path)` | function / [21](../../../../contracts/tests/test_project_contract_schemas.py#L21) | `json.loads`、`path.read_text` |
| `validate` — `validate(schema_path, instance)` | function / [25](../../../../contracts/tests/test_project_contract_schemas.py#L25) | `<dynamic>.validate`、`Draft202012Validator`、`load_json` |
| `minimal_package` — `minimal_package()` | function / [29](../../../../contracts/tests/test_project_contract_schemas.py#L29) | 无直接调用 |
| `model_file` — `model_file()` | function / [58](../../../../contracts/tests/test_project_contract_schemas.py#L58) | 无直接调用 |
| `minimal_envelope` — `minimal_envelope()` | function / [70](../../../../contracts/tests/test_project_contract_schemas.py#L70) | `model_file` |
| `test_project_schemas_are_closed_draft_2020_12` — `test_project_schemas_are_closed_draft_2020_12(schema_path, schema_id)` | function / [109](../../../../contracts/tests/test_project_contract_schemas.py#L109) | `Draft202012Validator.check_schema`、`load_json` |
| `test_project_contracts_are_registered_with_contained_paths` — `test_project_contracts_are_registered_with_contained_paths()` | function / [120](../../../../contracts/tests/test_project_contract_schemas.py#L120) | `<dynamic>.is_absolute`、`<dynamic>.is_file`、`<dynamic>.is_relative_to`、`<dynamic>.resolve`、`Path`、`PurePosixPath`、`expected.items`、`load_json`、`posix_path.is_absolute` |
| `test_minimal_project_package_needs_no_conditional_artifacts` — `test_minimal_project_package_needs_no_conditional_artifacts()` | function / [146](../../../../contracts/tests/test_project_contract_schemas.py#L146) | `minimal_package`、`validate` |
| `test_project_package_accepts_nonstandard_top_path` — `test_project_package_accepts_nonstandard_top_path()` | function / [156](../../../../contracts/tests/test_project_contract_schemas.py#L156) | `minimal_package`、`validate` |
| `test_contract_identifiers_accept_underscores` — `test_contract_identifiers_accept_underscores()` | function / [160](../../../../contracts/tests/test_project_contract_schemas.py#L160) | `minimal_envelope`、`minimal_package`、`validate` |
| `test_conditional_artifact_requires_a_condition_id` — `test_conditional_artifact_requires_a_condition_id()` | function / [171](../../../../contracts/tests/test_project_contract_schemas.py#L171) | `<dynamic>.append`、`minimal_package`、`pytest.raises`、`validate` |
| `test_project_package_rejects_unsafe_paths` — `test_project_package_rejects_unsafe_paths(path)` | function / [191](../../../../contracts/tests/test_project_contract_schemas.py#L191) | `minimal_package`、`pytest.raises`、`validate` |
| `test_project_package_rejects_unregistered_fields` — `test_project_package_rejects_unregistered_fields()` | function / [198](../../../../contracts/tests/test_project_contract_schemas.py#L198) | `minimal_package`、`pytest.raises`、`validate` |
| `test_minimal_trusted_outer_envelope_validates` — `test_minimal_trusted_outer_envelope_validates()` | function / [205](../../../../contracts/tests/test_project_contract_schemas.py#L205) | `minimal_envelope`、`validate` |
| `test_envelope_integrity_scheme_is_frozen` — `test_envelope_integrity_scheme_is_frozen()` | function / [209](../../../../contracts/tests/test_project_contract_schemas.py#L209) | `load_json` |
| `test_project_manifest_role_is_bound_to_manifest_path` — `test_project_manifest_role_is_bound_to_manifest_path()` | function / [216](../../../../contracts/tests/test_project_contract_schemas.py#L216) | `minimal_envelope`、`pytest.raises`、`validate` |
| `test_envelope_digest_contract_omits_its_own_value` — `test_envelope_digest_contract_omits_its_own_value()` | function / [228](../../../../contracts/tests/test_project_contract_schemas.py#L228) | `load_json` |
| `test_envelope_rejects_evaluator_as_a_candidate_file_owner` — `test_envelope_rejects_evaluator_as_a_candidate_file_owner()` | function / [234](../../../../contracts/tests/test_project_contract_schemas.py#L234) | `minimal_envelope`、`pytest.raises`、`validate` |
| `test_evaluator_material_is_an_opaque_reference_without_a_path` — `test_evaluator_material_is_an_opaque_reference_without_a_path()` | function / [241](../../../../contracts/tests/test_project_contract_schemas.py#L241) | `<dynamic>.append`、`minimal_envelope`、`pytest.raises`、`validate` |
| `test_composite_file_requires_model_and_trusted_region_provenance` — `test_composite_file_requires_model_and_trusted_region_provenance()` | function / [257](../../../../contracts/tests/test_project_contract_schemas.py#L257) | `copy.deepcopy`、`minimal_envelope`、`pytest.raises`、`validate` |
| `test_noncomposite_file_cannot_claim_region_ownership` — `test_noncomposite_file_cannot_claim_region_ownership()` | function / [296](../../../../contracts/tests/test_project_contract_schemas.py#L296) | `minimal_envelope`、`pytest.raises`、`validate` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_project_dependency_boundaries.py`

[打开源文件](../../../../contracts/tests/test_project_dependency_boundaries.py) · 101 行 · SHA-256 `da64405e9ac5808def5cac3368ba1fdf4026d628cc5b69c8292642702eaceef3`

导入模块：`ast`、`pathlib`、`re`、`sr2fpga_agent.repository_paths`、`sr2fpga_training.contracts`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_import_roots` — `_import_roots(path)` | function / [35](../../../../contracts/tests/test_project_dependency_boundaries.py#L35) | `alias.name.split`、`ast.parse`、`ast.walk`、`isinstance`、`node.module.split`、`path.read_text`、`roots.add`、`roots.update`、`set`、`str` |
| `_source_violations` — `_source_violations(source_root, forbidden_imports)` | function / [46](../../../../contracts/tests/test_project_dependency_boundaries.py#L46) | `_import_roots`、`path.relative_to`、`sorted`、`source_root.rglob`、`str` |
| `_private_value_violations` — `_private_value_violations(source_root)` | function / [58](../../../../contracts/tests/test_project_dependency_boundaries.py#L58) | `any`、`ast.parse`、`ast.walk`、`isinstance`、`path.read_text`、`path.relative_to`、`pattern.search`、`source_root.rglob`、`str`、`violations.append` |
| `test_agent_does_not_depend_on_training_or_heavy_ml_stack` — `test_agent_does_not_depend_on_training_or_heavy_ml_stack()` | function / [76](../../../../contracts/tests/test_project_dependency_boundaries.py#L76) | `_source_violations` |
| `test_training_does_not_depend_on_agent_or_legacy_namespace` — `test_training_does_not_depend_on_agent_or_legacy_namespace()` | function / [81](../../../../contracts/tests/test_project_dependency_boundaries.py#L81) | `_source_violations` |
| `test_both_projects_discover_the_versioned_contract_registry` — `test_both_projects_discover_the_versioned_contract_registry()` | function / [88](../../../../contracts/tests/test_project_dependency_boundaries.py#L88) | `discover_agent_root`、`discover_training_root`、`manifest.is_file` |
| `test_canonical_source_contains_no_private_paths_or_keys` — `test_canonical_source_contains_no_private_paths_or_keys()` | function / [95](../../../../contracts/tests/test_project_dependency_boundaries.py#L95) | `_private_value_violations` |
| `test_retired_llm_compatibility_source_is_absent` — `test_retired_llm_compatibility_source_is_absent()` | function / [100](../../../../contracts/tests/test_project_dependency_boundaries.py#L100) | `<dynamic>.exists` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`re.compile`

## `contracts/tests/test_promote_regenerated_evidence.py`

[打开源文件](../../../../contracts/tests/test_promote_regenerated_evidence.py) · 317 行 · SHA-256 `fb5fffedcece96d23d30e1ed326d429c10da0b4fbe0ba131821ce7622d35da7e`

导入模块：`contracts.tools.promote_regenerated_evidence`、`json`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_write_json` — `_write_json(path, payload)` | function / [12](../../../../contracts/tests/test_promote_regenerated_evidence.py#L12) | `json.dumps`、`path.parent.mkdir`、`path.write_text` |
| `_fixture` — `_fixture(tmp_path, strip_prefix, legacy_sample_id, current_sample_id)` | function / [17](../../../../contracts/tests/test_promote_regenerated_evidence.py#L17) | `<dynamic>.as_posix`、`<dynamic>.mkdir`、`<dynamic>.write_bytes`、`<dynamic>.write_text`、`_write_json`、`candidate_root.relative_to`、`run_root.relative_to`、`str` |
| `test_preview_sanitizes_paths_and_excludes_hidden_vectors_and_binaries` — `test_preview_sanitizes_paths_and_excludes_hidden_vectors_and_binaries(tmp_path)` | function / [170](../../../../contracts/tests/test_promote_regenerated_evidence.py#L170) | `<dynamic>.endswith`、`<dynamic>.exists`、`_fixture`、`all`、`build_promotion_preview`、`next` |
| `test_apply_copies_curated_files_and_rewrites_ledger_references` — `test_apply_copies_curated_files_and_rewrites_ledger_references(tmp_path)` | function / [201](../../../../contracts/tests/test_promote_regenerated_evidence.py#L201) | `<dynamic>.rglob`、`_fixture`、`all`、`any`、`apply_promotion`、`build_promotion_preview`、`curated_trajectory.read_text`、`json.loads`、`ledger_path.read_text`、`reference.startswith`、`str` |
| `test_preview_applies_phase_b_style_prefix_and_sample_replacement` — `test_preview_applies_phase_b_style_prefix_and_sample_replacement(tmp_path)` | function / [239](../../../../contracts/tests/test_promote_regenerated_evidence.py#L239) | `<dynamic>.endswith`、`_fixture`、`build_promotion_preview` |
| `test_secret_content_blocks_promotion` — `test_secret_content_blocks_promotion(tmp_path)` | function / [265](../../../../contracts/tests/test_promote_regenerated_evidence.py#L265) | `_fixture`、`_write_json`、`apply_promotion`、`build_promotion_preview`、`pytest.raises` |
| `test_apply_rejects_source_changed_after_preview` — `test_apply_rejects_source_changed_after_preview(tmp_path)` | function / [297](../../../../contracts/tests/test_promote_regenerated_evidence.py#L297) | `_fixture`、`_write_json`、`apply_promotion`、`build_promotion_preview`、`pytest.raises` |

## `contracts/tests/test_repository_boundaries.py`

[打开源文件](../../../../contracts/tests/test_repository_boundaries.py) · 52 行 · SHA-256 `268b6d3968f84df3778862b1667961d39e70fecb5d3b046f187b6804a84b4b03`

导入模块：`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `read_root_file` — `read_root_file(relative_path)` | function / [7](../../../../contracts/tests/test_repository_boundaries.py#L7) | `<dynamic>.read_text` |
| `test_repository_project_directories_have_readmes` — `test_repository_project_directories_have_readmes()` | function / [11](../../../../contracts/tests/test_repository_boundaries.py#L11) | `<dynamic>.is_file`、`project_root.is_dir` |
| `test_runtime_and_local_config_paths_are_root_scoped_ignores` — `test_runtime_and_local_config_paths_are_root_scoped_ignores()` | function / [20](../../../../contracts/tests/test_repository_boundaries.py#L20) | `<dynamic>.isdisjoint`、`<dynamic>.splitlines`、`<dynamic>.startswith`、`line.lstrip`、`line.strip`、`read_root_file` |
| `test_datasets_and_reports_are_not_globally_ignored` — `test_datasets_and_reports_are_not_globally_ignored()` | function / [43](../../../../contracts/tests/test_repository_boundaries.py#L43) | `<dynamic>.splitlines`、`<dynamic>.startswith`、`line.lstrip`、`line.strip`、`read_root_file` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_requirement_audit_schema.py`

[打开源文件](../../../../contracts/tests/test_requirement_audit_schema.py) · 298 行 · SHA-256 `51eeb385f7c0e333afa3f0acea6a202557ec5a25d7e14aff1b3baaa4766ec676`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_schema` — `load_schema()` | function / [20](../../../../contracts/tests/test_requirement_audit_schema.py#L20) | `SCHEMA_PATH.read_text`、`json.loads` |
| `counters` — `counters()` | function / [24](../../../../contracts/tests/test_requirement_audit_schema.py#L24) | 无直接调用 |
| `ready_case` — `ready_case()` | function / [35](../../../../contracts/tests/test_requirement_audit_schema.py#L35) | `counters` |
| `artifact` — `artifact(case)` | function / [94](../../../../contracts/tests/test_requirement_audit_schema.py#L94) | `counters`、`int`、`ready_case` |
| `validate` — `validate(instance)` | function / [146](../../../../contracts/tests/test_requirement_audit_schema.py#L146) | `<dynamic>.validate`、`Draft202012Validator`、`load_schema` |
| `clarification_case` — `clarification_case(boundary_crossed)` | function / [150](../../../../contracts/tests/test_requirement_audit_schema.py#L150) | `<dynamic>.append`、`<dynamic>.update`、`ready_case` |
| `test_requirement_audit_schema_is_draft_2020_12` — `test_requirement_audit_schema_is_draft_2020_12()` | function / [190](../../../../contracts/tests/test_requirement_audit_schema.py#L190) | `Draft202012Validator.check_schema`、`load_schema` |
| `test_requirement_audit_is_registered_with_contained_path` — `test_requirement_audit_is_registered_with_contained_path()` | function / [200](../../../../contracts/tests/test_requirement_audit_schema.py#L200) | `<dynamic>.is_absolute`、`<dynamic>.is_file`、`<dynamic>.is_relative_to`、`<dynamic>.resolve`、`MANIFEST_PATH.read_text`、`Path`、`PurePosixPath`、`json.loads`、`posix_path.is_absolute` |
| `test_minimal_requirement_audit_artifact_validates` — `test_minimal_requirement_audit_artifact_validates()` | function / [215](../../../../contracts/tests/test_requirement_audit_schema.py#L215) | `artifact`、`validate` |
| `test_schema_freezes_dispositions_and_visibility_classes` — `test_schema_freezes_dispositions_and_visibility_classes()` | function / [219](../../../../contracts/tests/test_requirement_audit_schema.py#L219) | `load_schema`、`set` |
| `test_generation_visible_projection_rejects_evaluator_only_fields` — `test_generation_visible_projection_rejects_evaluator_only_fields(forbidden_field)` | function / [240](../../../../contracts/tests/test_requirement_audit_schema.py#L240) | `artifact`、`pytest.raises`、`validate` |
| `test_generation_visible_projection_requires_structured_public_width` — `test_generation_visible_projection_requires_structured_public_width()` | function / [251](../../../../contracts/tests/test_requirement_audit_schema.py#L251) | `<dynamic>.pop`、`artifact`、`pytest.raises`、`validate` |
| `test_clarification_gold_requires_evaluator_only_answer_branch` — `test_clarification_gold_requires_evaluator_only_answer_branch()` | function / [259](../../../../contracts/tests/test_requirement_audit_schema.py#L259) | `<dynamic>.pop`、`artifact`、`clarification_case`、`pytest.raises`、`validate` |
| `test_audit_can_record_false_proceed_without_rejecting_the_artifact` — `test_audit_can_record_false_proceed_without_rejecting_the_artifact()` | function / [268](../../../../contracts/tests/test_requirement_audit_schema.py#L268) | `artifact`、`clarification_case`、`validate` |
| `test_capability_gap_requires_a_capability_id` — `test_capability_gap_requires_a_capability_id()` | function / [272](../../../../contracts/tests/test_requirement_audit_schema.py#L272) | `<dynamic>.update`、`artifact`、`pytest.raises`、`ready_case`、`validate` |
| `test_not_run_has_reason_and_no_predicted_disposition` — `test_not_run_has_reason_and_no_predicted_disposition()` | function / [286](../../../../contracts/tests/test_requirement_audit_schema.py#L286) | `artifact`、`copy.deepcopy`、`pytest.raises`、`ready_case`、`result.pop`、`validate` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_system_his_schema.py`

[打开源文件](../../../../contracts/tests/test_system_his_schema.py) · 190 行 · SHA-256 `1c5d5645d338ba2a833ba243cb8ae5e17db3580bac69717ab51236b4abba1742`

导入模块：`json`、`jsonschema`、`pathlib`、`pytest`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_schema` — `load_schema()` | function / [32](../../../../contracts/tests/test_system_his_schema.py#L32) | `SCHEMA_PATH.read_text`、`json.loads` |
| `load_fixture` — `load_fixture()` | function / [36](../../../../contracts/tests/test_system_his_schema.py#L36) | `FIXTURE_PATH.read_text`、`json.loads` |
| `validate` — `validate(instance)` | function / [40](../../../../contracts/tests/test_system_his_schema.py#L40) | `<dynamic>.validate`、`Draft202012Validator`、`load_schema` |
| `nested_errors` — `nested_errors(error)` | function / [44](../../../../contracts/tests/test_system_his_schema.py#L44) | `nested_errors` |
| `test_system_his_schema_identity_and_closed_top_level` — `test_system_his_schema_identity_and_closed_top_level()` | function / [50](../../../../contracts/tests/test_system_his_schema.py#L50) | `Draft202012Validator.check_schema`、`load_schema` |
| `test_system_his_schema_requires_canonical_v12_fields` — `test_system_his_schema_requires_canonical_v12_fields()` | function / [59](../../../../contracts/tests/test_system_his_schema.py#L59) | `load_schema`、`set` |
| `test_system_his_fixture_validates_as_draft_2020_12_instance` — `test_system_his_fixture_validates_as_draft_2020_12_instance()` | function / [65](../../../../contracts/tests/test_system_his_schema.py#L65) | `load_fixture`、`validate` |
| `test_system_his_accepts_canonical_parameterized_width` — `test_system_his_accepts_canonical_parameterized_width()` | function / [69](../../../../contracts/tests/test_system_his_schema.py#L69) | `load_fixture`、`validate` |
| `test_system_his_accepts_compatibility_direction_and_reset_spellings` — `test_system_his_accepts_compatibility_direction_and_reset_spellings()` | function / [78](../../../../contracts/tests/test_system_his_schema.py#L78) | `load_fixture`、`port.pop`、`validate` |
| `test_system_his_accepts_typed_connection_and_combinational_declaration` — `test_system_his_accepts_typed_connection_and_combinational_declaration()` | function / [88](../../../../contracts/tests/test_system_his_schema.py#L88) | `load_fixture`、`validate` |
| `test_system_his_rejects_invalid_typed_connection_shape` — `test_system_his_rejects_invalid_typed_connection_shape()` | function / [98](../../../../contracts/tests/test_system_his_schema.py#L98) | `<dynamic>.iter_errors`、`Draft202012Validator`、`any`、`list`、`load_fixture`、`load_schema` |
| `test_system_his_rejects_non_boolean_combinational_declaration` — `test_system_his_rejects_non_boolean_combinational_declaration()` | function / [110](../../../../contracts/tests/test_system_his_schema.py#L110) | `<dynamic>.iter_errors`、`Draft202012Validator`、`any`、`list`、`load_fixture`、`load_schema` |
| `test_system_his_rejects_invalid_parameterized_width` — `test_system_his_rejects_invalid_parameterized_width(width, expected_validator)` | function / [129](../../../../contracts/tests/test_system_his_schema.py#L129) | `<dynamic>.iter_errors`、`Draft202012Validator`、`any`、`list`、`load_fixture`、`load_schema`、`nested_errors` |
| `test_system_his_rejects_port_without_direction` — `test_system_his_rejects_port_without_direction()` | function / [146](../../../../contracts/tests/test_system_his_schema.py#L146) | `<dynamic>.iter_errors`、`<dynamic>.pop`、`Draft202012Validator`、`any`、`list`、`load_fixture`、`load_schema` |
| `test_system_his_rejects_unknown_port_direction` — `test_system_his_rejects_unknown_port_direction()` | function / [156](../../../../contracts/tests/test_system_his_schema.py#L156) | `<dynamic>.iter_errors`、`Draft202012Validator`、`any`、`list`、`load_fixture`、`load_schema` |
| `test_system_his_rejects_unknown_reset_spelling` — `test_system_his_rejects_unknown_reset_spelling(field, value)` | function / [173](../../../../contracts/tests/test_system_his_schema.py#L173) | `<dynamic>.iter_errors`、`Draft202012Validator`、`any`、`list`、`load_fixture`、`load_schema` |
| `test_system_his_rejects_missing_required_top_level_section` — `test_system_his_rejects_missing_required_top_level_section()` | function / [183](../../../../contracts/tests/test_system_his_schema.py#L183) | `<dynamic>.iter_errors`、`Draft202012Validator`、`any`、`instance.pop`、`list`、`load_fixture`、`load_schema` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `contracts/tests/test_system_his_well_formedness_contract.py`

[打开源文件](../../../../contracts/tests/test_system_his_well_formedness_contract.py) · 55 行 · SHA-256 `a2c72ccd4890b31243015dd280879dce0503ce94bac471046f766ada4a1a8031`

导入模块：`json`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `test_well_formedness_contract_is_closed_and_ordered` — `test_well_formedness_contract_is_closed_and_ordered()` | function / [9](../../../../contracts/tests/test_system_his_well_formedness_contract.py#L9) | `CONTRACT_PATH.read_text`、`json.loads`、`range`、`set` |
| `test_conformance_matrix_references_existing_tests` — `test_conformance_matrix_references_existing_tests()` | function / [35](../../../../contracts/tests/test_system_his_well_formedness_contract.py#L35) | `<dynamic>.read_text`、`<dynamic>.split`、`CONTRACT_PATH.read_text`、`json.loads`、`set` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_task_catalog_contract.py`

[打开源文件](../../../../contracts/tests/test_task_catalog_contract.py) · 89 行 · SHA-256 `15b9f78a7dc1bbed2ad11c029ac2224e30a6a0a5acabd0ae56abb1b6cf7200b6`

导入模块：`json`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_catalog` — `load_catalog()` | function / [31](../../../../contracts/tests/test_task_catalog_contract.py#L31) | `CANONICAL_PATH.read_text`、`json.loads` |
| `test_canonical_task_catalog_exists_and_parses` — `test_canonical_task_catalog_exists_and_parses()` | function / [35](../../../../contracts/tests/test_task_catalog_contract.py#L35) | `CANONICAL_PATH.is_file`、`isinstance`、`load_catalog` |
| `test_task_family_ids_are_non_empty_and_unique` — `test_task_family_ids_are_non_empty_and_unique()` | function / [42](../../../../contracts/tests/test_task_catalog_contract.py#L42) | `all`、`isinstance`、`len`、`load_catalog`、`set` |
| `test_each_task_family_declares_required_metadata` — `test_each_task_family_declares_required_metadata()` | function / [48](../../../../contracts/tests/test_task_catalog_contract.py#L48) | `load_catalog`、`set`、`task.get` |
| `test_catalog_declares_its_canonical_repository_path` — `test_catalog_declares_its_canonical_repository_path()` | function / [56](../../../../contracts/tests/test_task_catalog_contract.py#L56) | `<dynamic>.as_posix`、`CANONICAL_PATH.relative_to`、`load_catalog` |
| `test_historical_heldout_set_is_retained_for_regression` — `test_historical_heldout_set_is_retained_for_regression()` | function / [62](../../../../contracts/tests/test_task_catalog_contract.py#L62) | `len`、`load_catalog`、`set` |
| `test_family_recipe_policy_is_explicitly_historical` — `test_family_recipe_policy_is_explicitly_historical()` | function / [79](../../../../contracts/tests/test_task_catalog_contract.py#L79) | `load_catalog` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`range`

## `contracts/tests/test_training_eligibility_schema.py`

[打开源文件](../../../../contracts/tests/test_training_eligibility_schema.py) · 82 行 · SHA-256 `f23ba070cecafe25096b60f0713df7dee474d74b82f3627b1d9fc7e06e1624a1`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_certificate` — `_certificate()` | function / [16](../../../../contracts/tests/test_training_eligibility_schema.py#L16) | 无直接调用 |
| `_errors` — `_errors(payload)` | function / [56](../../../../contracts/tests/test_training_eligibility_schema.py#L56) | `<dynamic>.iter_errors`、`Draft202012Validator`、`tuple` |
| `test_training_eligibility_schema_accepts_eligible_certificate` — `test_training_eligibility_schema_accepts_eligible_certificate()` | function / [60](../../../../contracts/tests/test_training_eligibility_schema.py#L60) | `_certificate`、`_errors` |
| `test_training_eligibility_schema_rejects_unknown_fields` — `test_training_eligibility_schema_rejects_unknown_fields()` | function / [64](../../../../contracts/tests/test_training_eligibility_schema.py#L64) | `_certificate`、`_errors`、`any` |
| `test_eligible_certificate_requires_every_check_true` — `test_eligible_certificate_requires_every_check_true()` | function / [71](../../../../contracts/tests/test_training_eligibility_schema.py#L71) | `_certificate`、`_errors` |
| `test_ineligible_certificate_requires_an_exclusion_reason` — `test_ineligible_certificate_requires_an_exclusion_reason()` | function / [78](../../../../contracts/tests/test_training_eligibility_schema.py#L78) | `_certificate`、`_errors`、`copy.deepcopy` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_training_pool_manifest_schema.py`

[打开源文件](../../../../contracts/tests/test_training_pool_manifest_schema.py) · 80 行 · SHA-256 `0e9f21676e93db7aa4296742d583585033e9e41eb6d43390394e994246513ab6`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_ref` — `_ref(treatment)` | function / [16](../../../../contracts/tests/test_training_pool_manifest_schema.py#L16) | 无直接调用 |
| `_manifest` — `_manifest()` | function / [30](../../../../contracts/tests/test_training_pool_manifest_schema.py#L30) | `_ref` |
| `_errors` — `_errors(payload)` | function / [59](../../../../contracts/tests/test_training_pool_manifest_schema.py#L59) | `<dynamic>.iter_errors`、`Draft202012Validator`、`tuple` |
| `test_training_pool_manifest_schema_accepts_canonical_shape` — `test_training_pool_manifest_schema_accepts_canonical_shape()` | function / [63](../../../../contracts/tests/test_training_pool_manifest_schema.py#L63) | `_errors`、`_manifest` |
| `test_training_pool_manifest_schema_is_closed` — `test_training_pool_manifest_schema_is_closed()` | function / [67](../../../../contracts/tests/test_training_pool_manifest_schema.py#L67) | `_errors`、`_manifest` |
| `test_training_pool_manifest_requires_transition_hash_only_for_traj_rows` — `test_training_pool_manifest_requires_transition_hash_only_for_traj_rows()` | function / [73](../../../../contracts/tests/test_training_pool_manifest_schema.py#L73) | `_errors`、`_manifest`、`copy.deepcopy` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_training_release_manifest_schema.py`

[打开源文件](../../../../contracts/tests/test_training_release_manifest_schema.py) · 92 行 · SHA-256 `1dd77434a437c3c6d24c6e26ca2d02049e8623ce23b38c3e068d9de5c0d468a8`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_manifest` — `_manifest(state)` | function / [16](../../../../contracts/tests/test_training_release_manifest_schema.py#L16) | `treatments.append` |
| `_errors` — `_errors(payload)` | function / [69](../../../../contracts/tests/test_training_release_manifest_schema.py#L69) | `<dynamic>.iter_errors`、`Draft202012Validator`、`tuple` |
| `test_training_release_schema_distinguishes_candidate_and_promoted` — `test_training_release_schema_distinguishes_candidate_and_promoted()` | function / [73](../../../../contracts/tests/test_training_release_manifest_schema.py#L73) | `_errors`、`_manifest` |
| `test_candidate_cannot_authorize_training_or_carry_authorization` — `test_candidate_cannot_authorize_training_or_carry_authorization()` | function / [78](../../../../contracts/tests/test_training_release_manifest_schema.py#L78) | `_errors`、`_manifest` |
| `test_training_release_schema_is_closed` — `test_training_release_schema_is_closed()` | function / [89](../../../../contracts/tests/test_training_release_manifest_schema.py#L89) | `_errors`、`_manifest`、`copy.deepcopy` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_training_view_eligibility_sidecar_schema.py`

[打开源文件](../../../../contracts/tests/test_training_view_eligibility_sidecar_schema.py) · 59 行 · SHA-256 `27cedcd4ad773432f6082dd77587cecb9296703925265cc750be3e1d69b7a557`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_sidecar` — `_sidecar(treatment)` | function / [17](../../../../contracts/tests/test_training_view_eligibility_sidecar_schema.py#L17) | 无直接调用 |
| `_errors` — `_errors(payload)` | function / [36](../../../../contracts/tests/test_training_view_eligibility_sidecar_schema.py#L36) | `<dynamic>.iter_errors`、`Draft202012Validator`、`tuple` |
| `test_sidecar_schema_accepts_project_and_transition_links` — `test_sidecar_schema_accepts_project_and_transition_links()` | function / [40](../../../../contracts/tests/test_training_view_eligibility_sidecar_schema.py#L40) | `_errors`、`_sidecar` |
| `test_sidecar_schema_is_closed_and_requires_m6t_transition_hash` — `test_sidecar_schema_is_closed_and_requires_m6t_transition_hash()` | function / [46](../../../../contracts/tests/test_training_view_eligibility_sidecar_schema.py#L46) | `_errors`、`_sidecar` |
| `test_non_transition_sidecar_forbids_transition_hash` — `test_non_transition_sidecar_forbids_transition_hash()` | function / [56](../../../../contracts/tests/test_training_view_eligibility_sidecar_schema.py#L56) | `_errors`、`_sidecar`、`copy.deepcopy` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_training_view_schema.py`

[打开源文件](../../../../contracts/tests/test_training_view_schema.py) · 52 行 · SHA-256 `5df9dae815f770a34e9ca6042e53448b786479a986bbc4fe13476ae75a6e58f3`

导入模块：`json`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_schema` — `load_schema()` | function / [24](../../../../contracts/tests/test_training_view_schema.py#L24) | `SCHEMA_PATH.read_text`、`json.loads` |
| `test_training_view_schema_declares_all_views` — `test_training_view_schema_declares_all_views()` | function / [28](../../../../contracts/tests/test_training_view_schema.py#L28) | `load_schema`、`set` |
| `test_requirement_to_file_is_a_derived_non_evaluation_view` — `test_requirement_to_file_is_a_derived_non_evaluation_view()` | function / [33](../../../../contracts/tests/test_training_view_schema.py#L33) | `<dynamic>.get`、`load_schema`、`next`、`set` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_training_view_v2_schema.py`

[打开源文件](../../../../contracts/tests/test_training_view_v2_schema.py) · 74 行 · SHA-256 `1ea3e6633b842b1b0a508aa3b730a7ab067cbe8007e92889b959cd4a176f1898`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_row` — `_row(treatment)` | function / [17](../../../../contracts/tests/test_training_view_v2_schema.py#L17) | 无直接调用 |
| `test_training_view_v2_schema_is_closed_and_accepts_project_treatment` — `test_training_view_v2_schema_is_closed_and_accepts_project_treatment()` | function / [49](../../../../contracts/tests/test_training_view_v2_schema.py#L49) | `<dynamic>.validate`、`Draft202012Validator`、`Draft202012Validator.check_schema`、`_row` |
| `test_training_view_v2_requires_transition_target_for_m6t` — `test_training_view_v2_requires_transition_target_for_m6t()` | function / [55](../../../../contracts/tests/test_training_view_v2_schema.py#L55) | `<dynamic>.validate`、`Draft202012Validator`、`_row`、`pytest.raises` |
| `test_training_view_v2_rejects_transition_target_for_m6u` — `test_training_view_v2_rejects_transition_target_for_m6u()` | function / [63](../../../../contracts/tests/test_training_view_v2_schema.py#L63) | `<dynamic>.validate`、`Draft202012Validator`、`_row`、`pytest.raises` |
| `test_training_view_v2_rejects_unknown_envelope_field` — `test_training_view_v2_rejects_unknown_envelope_field()` | function / [70](../../../../contracts/tests/test_training_view_v2_schema.py#L70) | `<dynamic>.validate`、`Draft202012Validator`、`_row`、`copy.deepcopy`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.read_text`、`<dynamic>.resolve`、`Path`、`json.loads`

## `contracts/tests/test_trajectory_schema.py`

[打开源文件](../../../../contracts/tests/test_trajectory_schema.py) · 151 行 · SHA-256 `195288d731bff92413f7681f98de5b3c4fe406d0ff065ecb16680eef76836e0c`

导入模块：`copy`、`json`、`jsonschema`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_schema` — `load_schema()` | function / [28](../../../../contracts/tests/test_trajectory_schema.py#L28) | `SCHEMA_PATH.read_text`、`json.loads` |
| `find_definition_enum` — `find_definition_enum(node, key)` | function / [32](../../../../contracts/tests/test_trajectory_schema.py#L32) | `find_definition_enum`、`isinstance`、`node.values` |
| `test_trajectory_schema_identity_and_required_fields` — `test_trajectory_schema_identity_and_required_fields()` | function / [48](../../../../contracts/tests/test_trajectory_schema.py#L48) | `load_schema`、`set` |
| `test_trajectory_schema_has_distinct_stage_statuses` — `test_trajectory_schema_has_distinct_stage_statuses()` | function / [60](../../../../contracts/tests/test_trajectory_schema.py#L60) | `find_definition_enum`、`load_schema` |
| `test_trajectory_schema_covers_l0_through_l5` — `test_trajectory_schema_covers_l0_through_l5()` | function / [66](../../../../contracts/tests/test_trajectory_schema.py#L66) | `load_schema`、`set` |
| `test_stage_skip_reason_is_conditional` — `test_stage_skip_reason_is_conditional()` | function / [73](../../../../contracts/tests/test_trajectory_schema.py#L73) | `load_schema`、`next`、`set` |
| `_trajectory_v2` — `_trajectory_v2()` | function / [91](../../../../contracts/tests/test_trajectory_schema.py#L91) | 无直接调用 |
| `test_trajectory_v2_requires_event_derived_cost_and_explicit_missing_lineage` — `test_trajectory_v2_requires_event_derived_cost_and_explicit_missing_lineage()` | function / [126](../../../../contracts/tests/test_trajectory_schema.py#L126) | `Draft202012Validator`、`Draft202012Validator.check_schema`、`SCHEMA_V2_PATH.read_text`、`_trajectory_v2`、`copy.deepcopy`、`json.loads`、`pytest.raises`、`validator.validate` |
| `test_trajectory_v2_hidden_reference_is_opaque_and_closed` — `test_trajectory_v2_hidden_reference_is_opaque_and_closed()` | function / [139](../../../../contracts/tests/test_trajectory_schema.py#L139) | `Draft202012Validator`、`SCHEMA_V2_PATH.read_text`、`_trajectory_v2`、`json.loads`、`pytest.raises`、`validator.validate` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `contracts/tests/test_verify_phase_a_backup.py`

[打开源文件](../../../../contracts/tests/test_verify_phase_a_backup.py) · 194 行 · SHA-256 `fdd714c658bf736bd494998b89da8ce8702906990570d4c129e0c7a296e1cb49`

导入模块：`contracts.tools.verify_phase_a_backup`、`hashlib`、`json`、`pathlib`、`pytest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_sha256` — `_sha256(data)` | function / [13](../../../../contracts/tests/test_verify_phase_a_backup.py#L13) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `_write_json` — `_write_json(path, payload)` | function / [17](../../../../contracts/tests/test_verify_phase_a_backup.py#L17) | `json.dumps`、`path.write_text` |
| `_build_repository_and_backup` — `_build_repository_and_backup(tmp_path)` | function / [24](../../../../contracts/tests/test_verify_phase_a_backup.py#L24) | `<dynamic>.join`、`<dynamic>.mkdir`、`<dynamic>.split`、`<dynamic>.write_bytes`、`<dynamic>.write_text`、`Path`、`_sha256`、`_write_json`、`files.items`、`len`、`records.append`、`relative.split`、`restore.mkdir`、`restore_path.parent.mkdir`、`restore_path.write_bytes`、`sorted`、`sum`、`workspace.mkdir`、`workspace_path.parent.mkdir`、`workspace_path.write_bytes` |
| `test_verified_external_backup_produces_pass_recheck` — `test_verified_external_backup_produces_pass_recheck(tmp_path)` | function / [90](../../../../contracts/tests/test_verify_phase_a_backup.py#L90) | `<dynamic>.read_bytes`、`_build_repository_and_backup`、`_sha256`、`backup.resolve`、`repository.resolve`、`str`、`verify_phase_a_backup` |
| `test_recheck_output_is_atomic_json` — `test_recheck_output_is_atomic_json(tmp_path)` | function / [118](../../../../contracts/tests/test_verify_phase_a_backup.py#L118) | `_build_repository_and_backup`、`json.loads`、`list`、`output.parent.glob`、`output.read_text`、`verify_phase_a_backup`、`write_recheck` |
| `test_backup_inside_repository_is_rejected` — `test_backup_inside_repository_is_rejected(tmp_path)` | function / [129](../../../../contracts/tests/test_verify_phase_a_backup.py#L129) | `_build_repository_and_backup`、`external.rename`、`pytest.raises`、`verify_phase_a_backup` |
| `test_workspace_hash_mismatch_is_rejected` — `test_workspace_hash_mismatch_is_rejected(tmp_path)` | function / [138](../../../../contracts/tests/test_verify_phase_a_backup.py#L138) | `<dynamic>.write_bytes`、`_build_repository_and_backup`、`pytest.raises`、`verify_phase_a_backup` |
| `test_extra_workspace_file_is_rejected` — `test_extra_workspace_file_is_rejected(tmp_path)` | function / [146](../../../../contracts/tests/test_verify_phase_a_backup.py#L146) | `<dynamic>.write_text`、`_build_repository_and_backup`、`pytest.raises`、`verify_phase_a_backup` |
| `test_checksum_ledger_mismatch_is_rejected` — `test_checksum_ledger_mismatch_is_rejected(tmp_path)` | function / [157](../../../../contracts/tests/test_verify_phase_a_backup.py#L157) | `<dynamic>.write_text`、`_build_repository_and_backup`、`pytest.raises`、`verify_phase_a_backup` |
| `test_unsafe_manifest_path_is_rejected` — `test_unsafe_manifest_path_is_rejected(tmp_path, unsafe_path)` | function / [172](../../../../contracts/tests/test_verify_phase_a_backup.py#L172) | `_build_repository_and_backup`、`_write_json`、`json.loads`、`manifest_path.read_text`、`pytest.raises`、`verify_phase_a_backup` |
| `test_invalid_verification_count_is_rejected` — `test_invalid_verification_count_is_rejected(tmp_path)` | function / [186](../../../../contracts/tests/test_verify_phase_a_backup.py#L186) | `_build_repository_and_backup`、`_write_json`、`json.loads`、`pytest.raises`、`verification_path.read_text`、`verify_phase_a_backup` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`pytest.mark.parametrize`
