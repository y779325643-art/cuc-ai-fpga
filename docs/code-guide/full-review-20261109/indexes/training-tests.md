# training-tests：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `training/tests/test_prepare_dataset.py`

[打开源文件](../../../../training/tests/test_prepare_dataset.py) · 389 行 · SHA-256 `1afd4cc9fe3e5259c9d6ea0c46c71af2ae535f7581927d3391e3fa9d805c759e`

导入模块：`json`、`os`、`pathlib`、`sr2fpga_training.prepare_dataset`、`subprocess`、`sys`、`tempfile`、`unittest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PrepareDatasetTest` — `PrepareDatasetTest` | class / [12](../../../../training/tests/test_prepare_dataset.py#L12) | 无直接调用 |
| `PrepareDatasetTest.test_convert_prompt_completion_rows_to_messages_jsonl` — `test_convert_prompt_completion_rows_to_messages_jsonl(self)` | function / [13](../../../../training/tests/test_prepare_dataset.py#L13) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_accepts_existing_messages_rows` — `test_accepts_existing_messages_rows(self)` | function / [47](../../../../training/tests/test_prepare_dataset.py#L47) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_requirement_to_his_training_view_rows` — `test_converts_requirement_to_his_training_view_rows(self)` | function / [62](../../../../training/tests/test_prepare_dataset.py#L62) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_his_to_project_training_view_rows` — `test_converts_his_to_project_training_view_rows(self)` | function / [86](../../../../training/tests/test_prepare_dataset.py#L86) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_requirement_to_project_training_view_rows` — `test_converts_requirement_to_project_training_view_rows(self)` | function / [110](../../../../training/tests/test_prepare_dataset.py#L110) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_requirement_to_file_training_view_rows` — `test_converts_requirement_to_file_training_view_rows(self)` | function / [134](../../../../training/tests/test_prepare_dataset.py#L134) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_filters_rows_by_sample_prefix_and_excluded_file_path` — `test_filters_rows_by_sample_prefix_and_excluded_file_path(self)` | function / [160](../../../../training/tests/test_prepare_dataset.py#L160) | `<dynamic>.join`、`<dynamic>.splitlines`、`Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`len`、`self.assertEqual`、`self.assertIn`、`self.assertNotIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_cli_filters_rows_by_sample_prefix_and_excluded_file_path` — `test_cli_filters_rows_by_sample_prefix_and_excluded_file_path(self)` | function / [206](../../../../training/tests/test_prepare_dataset.py#L206) | `<dynamic>.join`、`<dynamic>.resolve`、`<dynamic>.splitlines`、`Path`、`json.dumps`、`json.loads`、`len`、`os.environ.get`、`os.pathsep.join`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`str`、`subprocess.run`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_project_to_predicted_qor_training_view_rows` — `test_converts_project_to_predicted_qor_training_view_rows(self)` | function / [272](../../../../training/tests/test_prepare_dataset.py#L272) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_project_to_measured_qor_training_view_rows` — `test_converts_project_to_measured_qor_training_view_rows(self)` | function / [296](../../../../training/tests/test_prepare_dataset.py#L296) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_failure_to_diagnosis_training_view_rows` — `test_converts_failure_to_diagnosis_training_view_rows(self)` | function / [320](../../../../training/tests/test_prepare_dataset.py#L320) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_converts_failure_to_patch_training_view_rows` — `test_converts_failure_to_patch_training_view_rows(self)` | function / [344](../../../../training/tests/test_prepare_dataset.py#L344) | `Path`、`convert_jsonl`、`json.dumps`、`json.loads`、`self.assertEqual`、`self.assertIn`、`source.write_text`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_rejects_rows_missing_answer` — `test_rejects_rows_missing_answer(self)` | function / [369](../../../../training/tests/test_prepare_dataset.py#L369) | `Path`、`convert_jsonl`、`json.dumps`、`self.assertRaisesRegex`、`source.write_text`、`tempfile.TemporaryDirectory` |
| `PrepareDatasetTest.test_rejects_invalid_json_with_line_number` — `test_rejects_invalid_json_with_line_number(self)` | function / [378](../../../../training/tests/test_prepare_dataset.py#L378) | `Path`、`convert_jsonl`、`self.assertRaisesRegex`、`source.write_text`、`tempfile.TemporaryDirectory` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`unittest.main`

## `training/tests/test_serving_entrypoints.py`

[打开源文件](../../../../training/tests/test_serving_entrypoints.py) · 242 行 · SHA-256 `0747f8125040a7e514161c8a8fc327ac5750cbe83187119a421dbcfd3d9f2e3e`

导入模块：`collections.abc`、`os`、`pathlib`、`shutil`、`subprocess`、`tempfile`、`unittest`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ServingEntrypointsTest` — `ServingEntrypointsTest` | class / [13](../../../../training/tests/test_serving_entrypoints.py#L13) | 无直接调用 |
| `ServingEntrypointsTest.test_shell_scripts_are_forced_to_lf_by_git` — `test_shell_scripts_are_forced_to_lf_by_git(self)` | function / [14](../../../../training/tests/test_serving_entrypoints.py#L14) | `<dynamic>.read_text`、`self.assertIn` |
| `ServingEntrypointsTest.test_runtime_scripts_use_training_local_venv_by_default` — `test_runtime_scripts_use_training_local_venv_by_default(self)` | function / [19](../../../../training/tests/test_serving_entrypoints.py#L19) | `<dynamic>.read_text`、`self.assertIn`、`self.assertNotIn`、`self.subTest` |
| `ServingEntrypointsTest._capture_vllm_args` — `_capture_vllm_args(self, script, extra_env)` | function / [37](../../../../training/tests/test_serving_entrypoints.py#L37) | `<dynamic>.splitlines`、`Path`、`_add_wslenv_entries`、`_bash_command`、`_bash_executable`、`_env_for_bash`、`_is_windows_wsl_bash`、`_path_for_bash`、`capture_file.read_text`、`env.update`、`extra_env.keys`、`fake_vllm.chmod`、`fake_vllm.write_text`、`os.environ.copy`、`subprocess.run`、`tempfile.TemporaryDirectory` |
| `ServingEntrypointsTest.test_gemma_vllm_uses_public_default_and_text_only_flags` — `test_gemma_vllm_uses_public_default_and_text_only_flags(self)` | function / [70](../../../../training/tests/test_serving_entrypoints.py#L70) | `self._capture_vllm_args`、`self.assertEqual`、`self.assertIn`、`self.assertNotIn` |
| `ServingEntrypointsTest.test_qwen_vllm_has_stable_coder_defaults` — `test_qwen_vllm_has_stable_coder_defaults(self)` | function / [82](../../../../training/tests/test_serving_entrypoints.py#L82) | `_bash_executable`、`_path_for_bash`、`args.index`、`self._capture_vllm_args`、`self.assertEqual`、`self.assertIn`、`tempfile.TemporaryDirectory` |
| `ServingEntrypointsTest.test_qwen_vllm_defaults_to_public_model_identifier` — `test_qwen_vllm_defaults_to_public_model_identifier(self)` | function / [96](../../../../training/tests/test_serving_entrypoints.py#L96) | `<dynamic>.read_text`、`self.assertIn` |
| `ServingEntrypointsTest.test_qwen_vllm_explains_how_to_download_a_missing_local_model` — `test_qwen_vllm_explains_how_to_download_a_missing_local_model(self)` | function / [106](../../../../training/tests/test_serving_entrypoints.py#L106) | `_bash_command`、`_bash_executable`、`_env_for_bash`、`os.environ.copy`、`self.assertIn`、`self.assertNotEqual`、`subprocess.run` |
| `ServingEntrypointsTest.test_qwen_vllm_disables_flashinfer_sampler_without_nvcc` — `test_qwen_vllm_disables_flashinfer_sampler_without_nvcc(self)` | function / [128](../../../../training/tests/test_serving_entrypoints.py#L128) | `<dynamic>.read_text`、`self.assertIn` |
| `ServingEntrypointsTest.test_transformers_smoke_test_uses_chat_template` — `test_transformers_smoke_test_uses_chat_template(self)` | function / [135](../../../../training/tests/test_serving_entrypoints.py#L135) | `<dynamic>.read_text`、`self.assertIn` |
| `_bash_executable` — `_bash_executable()` | function / [151](../../../../training/tests/test_serving_entrypoints.py#L151) | `shutil.which` |
| `_bash_command` — `_bash_command(script, bash)` | function / [155](../../../../training/tests/test_serving_entrypoints.py#L155) | `_path_for_bash` |
| `_env_for_bash` — `_env_for_bash(base_env, bash, prepend_path)` | function / [159](../../../../training/tests/test_serving_entrypoints.py#L159) | `<dynamic>.join`、`_add_wslenv_entries`、`_is_windows_wsl_bash`、`_path_for_bash`、`dict`、`env.get`、`os.pathsep.join`、`path_entries.append`、`path_entries.extend`、`str` |
| `_path_for_bash` — `_path_for_bash(path, bash)` | function / [203](../../../../training/tests/test_serving_entrypoints.py#L203) | `_is_windows_wsl_bash`、`_windows_path_to_wsl`、`str` |
| `_is_windows_wsl_bash` — `_is_windows_wsl_bash(bash)` | function / [210](../../../../training/tests/test_serving_entrypoints.py#L210) | `<dynamic>.lower`、`bash.replace` |
| `_windows_path_to_wsl` — `_windows_path_to_wsl(path)` | function / [217](../../../../training/tests/test_serving_entrypoints.py#L217) | `<dynamic>.lower`、`<dynamic>.lstrip`、`<dynamic>.resolve`、`Path`、`os.path.splitdrive`、`path.replace`、`path.startswith`、`str`、`tail.replace` |
| `_add_wslenv_entries` — `_add_wslenv_entries(env, names)` | function / [228](../../../../training/tests/test_serving_entrypoints.py#L228) | `<dynamic>.join`、`<dynamic>.split`、`entry.split`、`env.get`、`existing.append`、`seen.add`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`unittest.main`

## `training/tests/test_training_cli_smoke.py`

[打开源文件](../../../../training/tests/test_training_cli_smoke.py) · 94 行 · SHA-256 `00a91aae93dd9c2181c28bbc614d4b043e4853cb5937b8c0f988a7cd049a09df`

导入模块：`json`、`os`、`pathlib`、`pytest`、`subprocess`、`sys`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_installed_environment` — `_installed_environment()` | function / [16](../../../../training/tests/test_training_cli_smoke.py#L16) | `environment.pop`、`os.environ.copy` |
| `test_training_cli_help_works_from_lightweight_install` — `test_training_cli_help_works_from_lightweight_install(tmp_path, module, usage_token)` | function / [31](../../../../training/tests/test_training_cli_smoke.py#L31) | `_installed_environment`、`subprocess.run` |
| `test_lightweight_install_converts_and_dry_runs_without_model` — `test_lightweight_install_converts_and_dry_runs_without_model(tmp_path)` | function / [50](../../../../training/tests/test_training_cli_smoke.py#L50) | `_installed_environment`、`json.loads`、`str`、`subprocess.run` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`

## `training/tests/test_training_config_policy.py`

[打开源文件](../../../../training/tests/test_training_config_policy.py) · 127 行 · SHA-256 `76f4d01118be5dc01f86702b0745b9c7ebbd8f660b4805b682f2f32b9102e9e6`

导入模块：`ast`、`pathlib`、`re`、`yaml`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_all_strings` — `_all_strings(value)` | function / [36](../../../../training/tests/test_training_config_policy.py#L36) | `_all_strings`、`isinstance`、`value.values` |
| `test_expected_training_configs_and_scripts_are_canonical` — `test_expected_training_configs_and_scripts_are_canonical()` | function / [47](../../../../training/tests/test_training_config_policy.py#L47) | `CONFIG_ROOT.iterdir`、`SCRIPT_ROOT.iterdir`、`path.is_file` |
| `test_committed_training_assets_contain_no_private_paths_or_keys` — `test_committed_training_assets_contain_no_private_paths_or_keys()` | function / [56](../../../../training/tests/test_training_config_policy.py#L56) | `CONFIG_ROOT.rglob`、`SCRIPT_ROOT.rglob`、`path.is_file`、`path.read_text`、`path.relative_to`、`pattern.search`、`str`、`violations.append` |
| `test_training_config_outputs_are_ignored_artifacts` — `test_training_config_outputs_are_ignored_artifacts()` | function / [74](../../../../training/tests/test_training_config_policy.py#L74) | `<dynamic>.startswith`、`CONFIG_ROOT.glob`、`any`、`isinstance`、`path.read_text`、`pattern.search`、`str`、`yaml.safe_load` |
| `test_local_training_config_overrides_are_ignored` — `test_local_training_config_overrides_are_ignored()` | function / [88](../../../../training/tests/test_training_config_policy.py#L88) | `<dynamic>.read_text` |
| `test_shell_scripts_use_training_owned_overrides_and_modules` — `test_shell_scripts_use_training_owned_overrides_and_modules()` | function / [93](../../../../training/tests/test_training_config_policy.py#L93) | `<dynamic>.join`、`SCRIPT_ROOT.glob`、`path.read_text`、`runtime_scripts.values` |
| `test_training_fixture_tests_do_not_write_to_tracked_tmp` — `test_training_fixture_tests_do_not_write_to_tracked_tmp()` | function / [115](../../../../training/tests/test_training_config_policy.py#L115) | `<dynamic>.startswith`、`any`、`ast.parse`、`ast.walk`、`isinstance`、`node.value.replace`、`str`、`test_path.read_text` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`re.compile`

## `training/tests/test_training_dry_run.py`

[打开源文件](../../../../training/tests/test_training_dry_run.py) · 161 行 · SHA-256 `5e90e283e6617458db61479f11e8c8b718e65e27072afead27ecb3dde6f7d6de`

导入模块：`io`、`json`、`pathlib`、`sr2fpga_training.training_dry_run`、`tempfile`、`unittest`、`unittest.mock`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TrainingDryRunTest` — `TrainingDryRunTest` | class / [16](../../../../training/tests/test_training_dry_run.py#L16) | 无直接调用 |
| `TrainingDryRunTest.test_reports_length_stats_and_truncation_risk` — `test_reports_length_stats_and_truncation_risk(self)` | function / [17](../../../../training/tests/test_training_dry_run.py#L17) | `<dynamic>.join`、`Path`、`dry_run_chat_jsonl`、`json.dumps`、`self.assertEqual`、`self.assertFalse`、`self.assertGreaterEqual`、`tempfile.TemporaryDirectory`、`train_file.write_text` |
| `TrainingDryRunTest.test_dry_run_from_config_uses_train_file_and_max_seq_length` — `test_dry_run_from_config_uses_train_file_and_max_seq_length(self)` | function / [54](../../../../training/tests/test_training_dry_run.py#L54) | `<dynamic>.join`、`Path`、`config_path.write_text`、`dry_run_from_config`、`json.dumps`、`self.assertEqual`、`str`、`tempfile.TemporaryDirectory`、`train_file.write_text` |
| `TrainingDryRunTest.test_cli_can_fail_on_truncation_risk` — `test_cli_can_fail_on_truncation_risk(self)` | function / [89](../../../../training/tests/test_training_dry_run.py#L89) | `<dynamic>.join`、`Path`、`io.StringIO`、`json.dumps`、`main`、`patch`、`self.assertEqual`、`self.assertRaises`、`str`、`tempfile.TemporaryDirectory`、`train_file.write_text` |
| `TrainingDryRunTest.test_cli_accepts_train_file_compatibility_alias` — `test_cli_accepts_train_file_compatibility_alias(self)` | function / [121](../../../../training/tests/test_training_dry_run.py#L121) | `Path`、`io.StringIO`、`json.dumps`、`json.loads`、`main`、`patch`、`self.assertEqual`、`stdout.getvalue`、`str`、`tempfile.TemporaryDirectory`、`train_file.write_text` |
| `TrainingDryRunTest.test_rejects_chat_rows_without_assistant_turn` — `test_rejects_chat_rows_without_assistant_turn(self)` | function / [148](../../../../training/tests/test_training_dry_run.py#L148) | `Path`、`dry_run_chat_jsonl`、`json.dumps`、`self.assertRaisesRegex`、`tempfile.TemporaryDirectory`、`train_file.write_text` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`unittest.main`

## `training/tests/test_training_package_boundary.py`

[打开源文件](../../../../training/tests/test_training_package_boundary.py) · 124 行 · SHA-256 `225dda98cab59dfd9fe29439992220a783254c14922f05cd0412988f82dcc7e9`

导入模块：`ast`、`json`、`os`、`pathlib`、`subprocess`、`sys`、`tomllib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_requirement_name` — `_requirement_name(requirement)` | function / [16](../../../../training/tests/test_training_package_boundary.py#L16) | `<dynamic>.lower`、`requirement.split`、`requirement.strip` |
| `_import_roots` — `_import_roots(path)` | function / [22](../../../../training/tests/test_training_package_boundary.py#L22) | `alias.name.split`、`ast.parse`、`ast.walk`、`isinstance`、`node.module.split`、`path.read_text`、`roots.add`、`roots.update`、`set`、`str` |
| `test_training_project_metadata_and_entry_points` — `test_training_project_metadata_and_entry_points()` | function / [33](../../../../training/tests/test_training_package_boundary.py#L33) | `PYPROJECT.read_text`、`_requirement_name`、`tomllib.loads` |
| `test_training_source_has_no_agent_or_legacy_imports` — `test_training_source_has_no_agent_or_legacy_imports()` | function / [70](../../../../training/tests/test_training_package_boundary.py#L70) | `SOURCE_ROOT.rglob`、`_import_roots`、`path.relative_to`、`sorted`、`str` |
| `test_lightweight_modules_do_not_eagerly_import_heavy_backends` — `test_lightweight_modules_do_not_eagerly_import_heavy_backends()` | function / [82](../../../../training/tests/test_training_package_boundary.py#L82) | `json.loads`、`os.environ.get`、`os.pathsep.join`、`str`、`subprocess.run` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `training/tests/test_training_smoke_assets.py`

[打开源文件](../../../../training/tests/test_training_smoke_assets.py) · 174 行 · SHA-256 `0217bcf8c805642f92b8a6a36aedcac50dedf423aecaf1d9e7f07def83a6f4c8`

导入模块：`json`、`pathlib`、`sr2fpga_training.prepare_dataset`、`sr2fpga_training.training_dry_run`、`tempfile`、`unittest`、`yaml`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_release_exports_path` — `_release_exports_path(release_id)` | function / [15](../../../../training/tests/test_training_smoke_assets.py#L15) | `<dynamic>.read_text`、`json.loads`、`next` |
| `TrainingSmokeAssetsTest` — `TrainingSmokeAssetsTest` | class / [25](../../../../training/tests/test_training_smoke_assets.py#L25) | 无直接调用 |
| `TrainingSmokeAssetsTest.test_smoke_dataset_can_be_converted_to_chat_jsonl` — `test_smoke_dataset_can_be_converted_to_chat_jsonl(self)` | function / [26](../../../../training/tests/test_training_smoke_assets.py#L26) | `<dynamic>.splitlines`、`Path`、`all`、`convert_jsonl`、`json.loads`、`len`、`line.strip`、`self.assertEqual`、`self.assertGreaterEqual`、`self.assertTrue`、`target.read_text`、`tempfile.TemporaryDirectory` |
| `TrainingSmokeAssetsTest.test_t0_t4_export_views_can_be_converted_to_chat_jsonl` — `test_t0_t4_export_views_can_be_converted_to_chat_jsonl(self)` | function / [42](../../../../training/tests/test_training_smoke_assets.py#L42) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.splitlines`、`<dynamic>.startswith`、`Path`、`_release_exports_path`、`all`、`any`、`convert_jsonl`、`dry_run_chat_jsonl`、`filtered.write_text`、`json.dumps`、`json.loads`、`len`、`line.strip`、`self.assertEqual`、`self.assertGreater`、`self.assertTrue`、`source.read_text`、`target.read_text`、`tempfile.TemporaryDirectory`、`view.replace` |
| `TrainingSmokeAssetsTest.test_t0_t4_requirement_to_file_non_his_rows_fit_short_context` — `test_t0_t4_requirement_to_file_non_his_rows_fit_short_context(self)` | function / [96](../../../../training/tests/test_training_smoke_assets.py#L96) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.splitlines`、`<dynamic>.startswith`、`Path`、`_release_exports_path`、`convert_jsonl`、`dry_run_chat_jsonl`、`filtered.write_text`、`json.dumps`、`json.loads`、`len`、`line.strip`、`self.assertEqual`、`self.assertGreater`、`self.assertTrue`、`source.read_text`、`tempfile.TemporaryDirectory` |
| `TrainingSmokeAssetsTest.test_qwen_smoke_training_config_uses_public_model_and_small_run` — `test_qwen_smoke_training_config_uses_public_model_and_small_run(self)` | function / [127](../../../../training/tests/test_training_smoke_assets.py#L127) | `config_path.read_text`、`self.assertEqual`、`self.assertLessEqual`、`self.assertTrue`、`yaml.safe_load` |
| `TrainingSmokeAssetsTest.test_qwen_req2file_short_training_config_uses_short_context_dataset` — `test_qwen_req2file_short_training_config_uses_short_context_dataset(self)` | function / [149](../../../../training/tests/test_training_smoke_assets.py#L149) | `config_path.read_text`、`self.assertEqual`、`self.assertLessEqual`、`self.assertTrue`、`yaml.safe_load` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`unittest.main`

## `training/tests/test_training_view_provenance.py`

[打开源文件](../../../../training/tests/test_training_view_provenance.py) · 127 行 · SHA-256 `e2e1bf3a793d413d79b463f1158257858d8a13d59c9014f1730cd045ab82251e`

导入模块：`json`、`os`、`pathlib`、`pytest`、`sr2fpga_training.prepare_dataset`、`subprocess`、`sys`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_canonical_req2file_row` — `_canonical_req2file_row()` | function / [16](../../../../training/tests/test_training_view_provenance.py#L16) | 无直接调用 |
| `_convert_one` — `_convert_one(tmp_path, row)` | function / [30](../../../../training/tests/test_training_view_provenance.py#L30) | `convert_jsonl`、`json.dumps`、`json.loads`、`source.write_text`、`target.read_text` |
| `test_valid_requirement_to_file_provenance_converts` — `test_valid_requirement_to_file_provenance_converts(tmp_path)` | function / [38](../../../../training/tests/test_training_view_provenance.py#L38) | `_canonical_req2file_row`、`_convert_one` |
| `test_requirement_to_file_requires_source_episode_id` — `test_requirement_to_file_requires_source_episode_id(tmp_path)` | function / [45](../../../../training/tests/test_training_view_provenance.py#L45) | `_canonical_req2file_row`、`_convert_one`、`pytest.raises` |
| `test_requirement_to_file_cannot_be_official_eval_unit` — `test_requirement_to_file_cannot_be_official_eval_unit(tmp_path)` | function / [53](../../../../training/tests/test_training_view_provenance.py#L53) | `_canonical_req2file_row`、`_convert_one`、`pytest.raises` |
| `test_requirement_to_file_cannot_receive_standalone_credit` — `test_requirement_to_file_cannot_receive_standalone_credit(tmp_path)` | function / [61](../../../../training/tests/test_training_view_provenance.py#L61) | `_canonical_req2file_row`、`_convert_one`、`pytest.raises` |
| `test_legacy_project_level_view_still_converts` — `test_legacy_project_level_view_still_converts(tmp_path)` | function / [71](../../../../training/tests/test_training_view_provenance.py#L71) | `_convert_one` |
| `test_historical_req2file_without_view_type_still_converts` — `test_historical_req2file_without_view_type_still_converts(tmp_path)` | function / [89](../../../../training/tests/test_training_view_provenance.py#L89) | `_convert_one` |
| `test_training_contract_reader_does_not_import_agent` — `test_training_contract_reader_does_not_import_agent()` | function / [105](../../../../training/tests/test_training_view_provenance.py#L105) | `json.loads`、`os.environ.get`、`os.pathsep.join`、`str`、`subprocess.run` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`

## `training/tests/test_training_view_v2_reader.py`

[打开源文件](../../../../training/tests/test_training_view_v2_reader.py) · 135 行 · SHA-256 `ee267bb8a8b31161bdb019727b4a3e2125c53e91112945274b2db0649708d298`

导入模块：`copy`、`hashlib`、`json`、`pathlib`、`pytest`、`sr2fpga_training.contracts`、`sr2fpga_training.prepare_dataset`、`sr2fpga_training.release_reader`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_sha256` — `_sha256(value)` | function / [17](../../../../training/tests/test_training_view_v2_reader.py#L17) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |
| `_row` — `_row(row_id, treatment, prompt)` | function / [22](../../../../training/tests/test_training_view_v2_reader.py#L22) | `_sha256` |
| `_write_rows` — `_write_rows(path, rows)` | function / [54](../../../../training/tests/test_training_view_v2_reader.py#L54) | `<dynamic>.join`、`json.dumps`、`path.write_text` |
| `test_reader_validates_hash_and_renderer_uses_only_payload` — `test_reader_validates_hash_and_renderer_uses_only_payload(tmp_path)` | function / [61](../../../../training/tests/test_training_view_v2_reader.py#L61) | `_row`、`_write_rows`、`json.loads`、`load_training_view_rows_v2`、`render_training_view_row_v2`、`str` |
| `test_prepare_dataset_consumes_canonical_v2_row` — `test_prepare_dataset_consumes_canonical_v2_row(tmp_path)` | function / [75](../../../../training/tests/test_training_view_v2_reader.py#L75) | `_row`、`_write_rows`、`convert_jsonl`、`json.loads`、`target.read_text` |
| `test_converter_rejects_duplicate_rows_before_filtering_or_overwrite` — `test_converter_rejects_duplicate_rows_before_filtering_or_overwrite(tmp_path, prefix)` | function / [86](../../../../training/tests/test_training_view_v2_reader.py#L86) | `_row`、`_write_rows`、`convert_jsonl`、`pytest.raises`、`target.read_text`、`target.write_text` |
| `test_reader_rejects_hash_mismatch` — `test_reader_rejects_hash_mismatch()` | function / [95](../../../../training/tests/test_training_view_v2_reader.py#L95) | `_row`、`pytest.raises`、`validate_training_view_row_v2` |
| `test_m6u_rejects_serialized_feedback_fields` — `test_m6u_rejects_serialized_feedback_fields(field)` | function / [106](../../../../training/tests/test_training_view_v2_reader.py#L106) | `_row`、`pytest.raises`、`validate_training_view_row_v2` |
| `test_reader_rejects_hidden_marker_and_private_canary` — `test_reader_rejects_hidden_marker_and_private_canary()` | function / [112](../../../../training/tests/test_training_view_v2_reader.py#L112) | `_row`、`pytest.raises`、`validate_training_view_row_v2` |
| `test_reader_rejects_entire_jsonl_on_duplicate_or_invalid_row` — `test_reader_rejects_entire_jsonl_on_duplicate_or_invalid_row(tmp_path)` | function / [124](../../../../training/tests/test_training_view_v2_reader.py#L124) | `_row`、`_write_rows`、`copy.deepcopy`、`load_training_view_rows_v2`、`pytest.raises` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`pytest.mark.parametrize`
