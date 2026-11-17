# compatibility_tests-tests：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `compatibility_tests/test_active_documentation_paths.py`

[打开源文件](../../../../compatibility_tests/test_active_documentation_paths.py) · 93 行 · SHA-256 `24bb5ed4475edf6f51e683f03bb21c4a5cf573f33a5e64207027f478b9d4713f`

导入模块：`pathlib`、`re`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_read` — `_read(path)` | function / [34](../../../../compatibility_tests/test_active_documentation_paths.py#L34) | `<dynamic>.read_text` |
| `test_core_active_docs_define_canonical_project_ownership` — `test_core_active_docs_define_canonical_project_ownership()` | function / [38](../../../../compatibility_tests/test_active_documentation_paths.py#L38) | `_read` |
| `test_active_docs_do_not_present_legacy_paths_as_primary_commands` — `test_active_docs_do_not_present_legacy_paths_as_primary_commands()` | function / [49](../../../../compatibility_tests/test_active_documentation_paths.py#L49) | `_read`、`pattern.search` |
| `test_active_docs_state_cross_project_and_verdict_rules` — `test_active_docs_state_cross_project_and_verdict_rules()` | function / [58](../../../../compatibility_tests/test_active_documentation_paths.py#L58) | `<dynamic>.join`、`_read`、`re.sub` |
| `test_retired_compatibility_surfaces_are_absent` — `test_retired_compatibility_surfaces_are_absent()` | function / [65](../../../../compatibility_tests/test_active_documentation_paths.py#L65) | `<dynamic>.exists` |
| `test_agents_is_the_only_repository_agent_guidance` — `test_agents_is_the_only_repository_agent_guidance()` | function / [70](../../../../compatibility_tests/test_active_documentation_paths.py#L70) | `<dynamic>.exists`、`Path`、`_read` |
| `test_markdown_links_in_core_active_docs_resolve` — `test_markdown_links_in_core_active_docs_resolve()` | function / [81](../../../../compatibility_tests/test_active_documentation_paths.py#L81) | `<dynamic>.resolve`、`_read`、`link_pattern.findall`、`re.compile`、`resolved.exists`、`target.split`、`target.startswith` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`re.compile`

## `compatibility_tests/test_project_terminology.py`

[打开源文件](../../../../compatibility_tests/test_project_terminology.py) · 76 行 · SHA-256 `b65db6a779b8c1703ca423d10e23c3d4c90b2654844c615d7fd5ef30378ea447`

> Current PC2.1 registration and historical serialization stay distinct.

导入模块：`json`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `test_terminology_ledger_preserves_object_and_compatibility_boundaries` — `test_terminology_ledger_preserves_object_and_compatibility_boundaries()` | function / [9](../../../../compatibility_tests/test_project_terminology.py#L9) | `LEDGER.read_text` |
| `test_current_and_historical_contracts_are_registered_separately` — `test_current_and_historical_contracts_are_registered_separately()` | function / [21](../../../../compatibility_tests/test_project_terminology.py#L21) | `<dynamic>.read_text`、`json.loads` |
| `test_ui_uses_pc_and_fpp_without_legacy_paper_label` — `test_ui_uses_pc_and_fpp_without_legacy_paper_label()` | function / [31](../../../../compatibility_tests/test_project_terminology.py#L31) | `<dynamic>.read_text` |
| `test_active_naming_entries_link_to_the_ledger` — `test_active_naming_entries_link_to_the_ledger()` | function / [43](../../../../compatibility_tests/test_project_terminology.py#L43) | `<dynamic>.read_text` |
| `test_old_specifications_have_an_explicit_archive_entry` — `test_old_specifications_have_an_explicit_archive_entry()` | function / [56](../../../../compatibility_tests/test_project_terminology.py#L56) | `<dynamic>.exists`、`<dynamic>.is_file`、`<dynamic>.read_text` |
| `test_persistent_writing_state_cannot_resume_an_old_research_plan` — `test_persistent_writing_state_cannot_resume_an_old_research_plan()` | function / [69](../../../../compatibility_tests/test_project_terminology.py#L69) | `<dynamic>.is_file`、`<dynamic>.read_text`、`json.loads` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `compatibility_tests/test_promoted_training_release_reader.py`

[打开源文件](../../../../compatibility_tests/test_promoted_training_release_reader.py) · 245 行 · SHA-256 `db6c44f9f92d124884e773ca45c29a1f3445e15d5de13ad79585d81cc5400576`

导入模块：`hashlib`、`json`、`pytest`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.training_pool`、`sr2fpga_agent.training_release`、`sr2fpga_training.contracts`、`sr2fpga_training.release_bundle`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_sha256` — `_sha256(value)` | function / [21](../../../../compatibility_tests/test_promoted_training_release_reader.py#L21) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |
| `_certificate` — `_certificate()` | function / [26](../../../../compatibility_tests/test_promoted_training_release_reader.py#L26) | `_sha256` |
| `_row_and_sidecar` — `_row_and_sidecar(treatment, certificate)` | function / [66](../../../../compatibility_tests/test_promoted_training_release_reader.py#L66) | `_sha256`、`treatment.lower` |
| `_candidate` — `_candidate(tmp_path)` | function / [109](../../../../compatibility_tests/test_promoted_training_release_reader.py#L109) | `PromotionAuthorizationExpectation`、`ReleaseLeakagePolicy.create`、`RepositoryPaths`、`TrainingLeakagePolicyExpectation.create`、`_certificate`、`_row_and_sidecar`、`build_candidate_training_release`、`build_training_pool_manifest` |
| `_promote` — `_promote(release, authorization)` | function / [144](../../../../compatibility_tests/test_promoted_training_release_reader.py#L144) | `_sha256`、`json.dumps`、`json.loads`、`manifest.items`、`manifest_path.read_text`、`manifest_path.write_text` |
| `test_training_rejects_candidate_and_inspects_bound_promoted_release` — `test_training_rejects_candidate_and_inspects_bound_promoted_release(tmp_path)` | function / [164](../../../../compatibility_tests/test_promoted_training_release_reader.py#L164) | `<dynamic>.read_bytes`、`_candidate`、`_promote`、`inspect_promoted_release`、`inspected.treatment_path`、`pytest.raises` |
| `test_training_rejects_authorization_leakage_and_pool_binding_mismatch` — `test_training_rejects_authorization_leakage_and_pool_binding_mismatch(tmp_path)` | function / [185](../../../../compatibility_tests/test_promoted_training_release_reader.py#L185) | `PromotionAuthorizationExpectation`、`TrainingLeakagePolicyExpectation.create`、`_candidate`、`_promote`、`_sha256`、`inspect_promoted_release`、`json.dumps`、`json.loads`、`manifest.items`、`manifest_path.read_text`、`manifest_path.write_text`、`pytest.raises` |
| `test_training_rejects_release_checksum_and_inventory_tampering` — `test_training_rejects_release_checksum_and_inventory_tampering(tmp_path)` | function / [227](../../../../compatibility_tests/test_promoted_training_release_reader.py#L227) | `<dynamic>.write_text`、`_candidate`、`_promote`、`inspect_promoted_release`、`pytest.raises`、`view.read_bytes`、`view.write_bytes` |

## `compatibility_tests/test_tmp_retirement.py`

[打开源文件](../../../../compatibility_tests/test_tmp_retirement.py) · 96 行 · SHA-256 `152e457307d61783bf663c11cf3ac7b1b614328ab1b6873be7617f03efa823c1`

导入模块：`json`、`pathlib`、`re`、`subprocess`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `test_no_tmp_content_remains_tracked` — `test_no_tmp_content_remains_tracked()` | function / [29](../../../../compatibility_tests/test_tmp_retirement.py#L29) | `completed.stdout.splitlines`、`subprocess.run` |
| `test_tmp_is_ignored_and_canonical_configs_do_not_write_there` — `test_tmp_is_ignored_and_canonical_configs_do_not_write_there()` | function / [41](../../../../compatibility_tests/test_tmp_retirement.py#L41) | `<dynamic>.glob`、`<dynamic>.read_text`、`<dynamic>.splitlines`、`list`、`path.read_text`、`str` |
| `test_active_evidence_does_not_reference_live_tmp_paths` — `test_active_evidence_does_not_reference_live_tmp_paths()` | function / [56](../../../../compatibility_tests/test_tmp_retirement.py#L56) | `live_tmp_pattern.search`、`path.read_text`、`re.compile`、`str` |
| `test_inventory_accounts_for_every_pre_cleanup_path` — `test_inventory_accounts_for_every_pre_cleanup_path()` | function / [64](../../../../compatibility_tests/test_tmp_retirement.py#L64) | `<dynamic>.startswith`、`INVENTORY_PATH.read_text`、`destination.exists`、`json.loads`、`len`、`sorted`、`sum` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`
