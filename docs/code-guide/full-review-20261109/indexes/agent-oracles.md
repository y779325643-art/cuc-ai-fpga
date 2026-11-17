# agent-oracles：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/oracles/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/__init__.py) · 84 行 · SHA-256 `6f7937b1657b0e8d84ae65a679c145f869168abe52c86033e6ac737e7b6b6145`

> Public API and family registry for independent Python-reference oracles.

导入模块：`__future__`、`pathlib`、`sr2fpga_agent.models`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.oracles.image`、`sr2fpga_agent.oracles.numeric`、`sr2fpga_agent.oracles.rl`、`sr2fpga_agent.oracles.signal`、`sr2fpga_agent.oracles.types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `build_oracle_bundle_for_request` — `build_oracle_bundle_for_request(family_id, request, output_root)` | function / [54](../../../../agent/src/sr2fpga_agent/oracles/__init__.py#L54) | `REFERENCE_BUILDERS.get`、`builder` |

## `agent/src/sr2fpga_agent/oracles/bundle.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/bundle.py) · 548 行 · SHA-256 `90d3107a09310123ff01569b0863c529d0e0a7f437629140bb5c183e9eff3458`

> Serialization and strict validation for independent oracle bundles.

导入模块：`__future__`、`hashlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.oracles.types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_canonical_json` — `_canonical_json(value)` | function / [60](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L60) | `ValueError`、`json.dumps`、`text.encode` |
| `_sha256` — `_sha256(data)` | function / [76](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L76) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `_bundle_hash` — `_bundle_hash(manifest)` | function / [80](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L80) | `_canonical_json`、`_sha256`、`dict`、`payload.pop` |
| `_memh_text` — `_memh_text(records, width)` | function / [86](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L86) | `<dynamic>.join`、`_validate_records` |
| `_validate_records` — `_validate_records(records, width)` | function / [92](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L92) | `ValueError`、`_is_int`、`any`、`isinstance` |
| `_safe_bundle_path` — `_safe_bundle_path(root, relative_path)` | function / [102](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L102) | `<dynamic>.resolve`、`Path`、`PurePosixPath`、`PureWindowsPath`、`ValueError`、`any`、`candidate.relative_to`、`isinstance`、`posix_path.as_posix`、`posix_path.is_absolute`、`relative_path.split`、`root.resolve`、`windows_path.is_absolute` |
| `_is_int` — `_is_int(value)` | function / [126](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L126) | `isinstance` |
| `_require_string` — `_require_string(value, label)` | function / [130](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L130) | `ValueError`、`isinstance`、`value.strip` |
| `_validate_scenario_id` — `_validate_scenario_id(value)` | function / [136](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L136) | `<dynamic>.upper`、`ValueError`、`_SCENARIO_ID_RE.fullmatch`、`isinstance`、`scenario_id.endswith`、`scenario_id.split`、`value.strip` |
| `_validate_scenario_class` — `_validate_scenario_class(value)` | function / [150](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L150) | `ValueError`、`str` |
| `_validate_width` — `_validate_width(value, label)` | function / [156](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L156) | `ValueError`、`_is_int`、`int` |
| `_validate_seed` — `_validate_seed(value)` | function / [162](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L162) | `ValueError`、`_is_int`、`int` |
| `_validate_fields` — `_validate_fields(fields, record_width_bits, label)` | function / [168](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L168) | `ValueError`、`_is_int`、`_require_string`、`isinstance`、`names.add`、`set`、`sorted`、`zip` |
| `_field_dict` — `_field_dict(field)` | function / [195](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L195) | 无直接调用 |
| `_field_from_dict` — `_field_from_dict(value, label)` | function / [204](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L204) | `OracleField`、`ValueError`、`isinstance`、`set` |
| `_validate_spec` — `_validate_spec(scenario)` | function / [215](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L215) | `ValueError`、`_validate_fields`、`_validate_records`、`_validate_scenario_class`、`_validate_scenario_id`、`_validate_seed`、`_validate_width`、`isinstance`、`len` |
| `write_oracle_bundle` — `write_oracle_bundle(root, family_id, reference_model, reference_version, task_parameters, scenarios)` | function / [239](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L239) | `<dynamic>.write_bytes`、`<dynamic>.write_text`、`Path`、`ValueError`、`_bundle_hash`、`_canonical_json`、`_field_dict`、`_memh_text`、`_require_string`、`_sha256`、`_validate_spec`、`expected_text.encode`、`input_text.encode`、`isinstance`、`json.dumps`、`len`、`load_oracle_bundle`、`root.mkdir`、`scenario.scenario_id.casefold`、`scenario_entries.append`、`scenario_ids.add`、`scenario_root.mkdir`、`set` |
| `_reject_duplicate_keys` — `_reject_duplicate_keys(pairs)` | function / [330](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L330) | `ValueError` |
| `_reject_nonfinite_number` — `_reject_nonfinite_number(value)` | function / [339](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L339) | `ValueError` |
| `_read_manifest` — `_read_manifest(root)` | function / [343](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L343) | `<dynamic>.read_text`、`ValueError`、`isinstance`、`json.loads`、`set` |
| `_read_record_file` — `_read_record_file(root, relative_path, expected_sha256, transaction_count, record_width_bits)` | function / [363](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L363) | `<dynamic>.splitlines`、`ValueError`、`_safe_bundle_path`、`_sha256`、`any`、`data.decode`、`int`、`len`、`path.is_file`、`path.read_bytes`、`re.compile`、`record_re.fullmatch` |
| `_scenario_from_dict` — `_scenario_from_dict(root, value, validate_record_files)` | function / [392](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L392) | `OracleScenarioManifest`、`ValueError`、`_SHA256_RE.fullmatch`、`_field_from_dict`、`_is_int`、`_read_record_file`、`_safe_bundle_path`、`_validate_fields`、`_validate_scenario_class`、`_validate_scenario_id`、`_validate_seed`、`_validate_width`、`isinstance`、`set`、`tuple` |
| `_load_oracle_bundle` — `_load_oracle_bundle(root, validate_record_files)` | function / [457](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L457) | `OracleBundle`、`Path`、`ValueError`、`_SHA256_RE.fullmatch`、`_bundle_hash`、`_canonical_json`、`_read_manifest`、`_require_string`、`_scenario_from_dict`、`dict`、`isinstance`、`len`、`scenario.scenario_id.casefold`、`set`、`tuple` |
| `load_oracle_bundle` — `load_oracle_bundle(root)` | function / [500](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L500) | `Path`、`_load_oracle_bundle` |
| `load_oracle_manifest_commitment` — `load_oracle_manifest_commitment(root)` | function / [506](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L506) | `Path`、`_load_oracle_bundle` |
| `sanitize_oracle_profile` — `sanitize_oracle_profile(bundle)` | function / [512](../../../../agent/src/sr2fpga_agent/oracles/bundle.py#L512) | `<dynamic>.encode`、`_field_dict`、`_sha256`、`scenario_profile.update`、`scenarios.append`、`sorted` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`frozenset`、`range`、`re.compile`

## `agent/src/sr2fpga_agent/oracles/image.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/image.py) · 397 行 · SHA-256 `a3f66122ba72daca3507e333a5e8f1b3d5603daa3cb4302bc77446692a403afa`

> Independent 5x5 image references and evaluator-local oracle bundles.

导入模块：`__future__`、`dataclasses`、`pathlib`、`random`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.oracles.types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `SobelResult` — `SobelResult` | class / [32](../../../../agent/src/sr2fpga_agent/oracles/image.py#L32) | 无直接调用 |
| `VisionDefectResult` — `VisionDefectResult` | class / [38](../../../../agent/src/sr2fpga_agent/oracles/image.py#L38) | 无直接调用 |
| `_ImageOperation` — `_ImageOperation` | class / [47](../../../../agent/src/sr2fpga_agent/oracles/image.py#L47) | 无直接调用 |
| `sobel_frame` — `sobel_frame(frame, threshold)` | function / [55](../../../../agent/src/sr2fpga_agent/oracles/image.py#L55) | `SobelResult`、`ValueError`、`_validate_5x5_u8`、`abs`、`int`、`isinstance`、`range`、`sum`、`tuple` |
| `vision_defect_frame` — `vision_defect_frame(frame, threshold)` | function / [81](../../../../agent/src/sr2fpga_agent/oracles/image.py#L81) | `VisionDefectResult`、`enumerate`、`next`、`sobel_frame` |
| `build_sobel_threshold_bundle` — `build_sobel_threshold_bundle(width, root)` | function / [97](../../../../agent/src/sr2fpga_agent/oracles/image.py#L97) | `_ImageOperation`、`_flat_frame`、`_horizontal_step_frame`、`_random_frames`、`_scenario`、`_shifted_vertical_step_frame`、`_validate_pixel_width`、`_write_bundle`、`enumerate`、`tuple` |
| `build_vision_defect_bundle` — `build_vision_defect_bundle(width, root)` | function / [150](../../../../agent/src/sr2fpga_agent/oracles/image.py#L150) | `_ImageOperation`、`_flat_frame`、`_horizontal_step_frame`、`_random_frames`、`_scenario`、`_shifted_vertical_step_frame`、`_validate_pixel_width`、`_write_bundle`、`enumerate`、`tuple` |
| `_write_bundle` — `_write_bundle(root, family_id, scenarios)` | function / [203](../../../../agent/src/sr2fpga_agent/oracles/image.py#L203) | `Path`、`write_oracle_bundle` |
| `_scenario` — `_scenario(scenario_id, scenario_class, seed, operations, vision)` | function / [228](../../../../agent/src/sr2fpga_agent/oracles/image.py#L228) | `OracleField`、`OracleScenarioSpec`、`ValueError`、`_operation_output_count`、`_validate_5x5_u8`、`_validate_operation`、`_validate_stall`、`dict`、`enumerate`、`expected_outputs.append`、`inputs.append`、`int`、`len`、`range`、`stalls.get`、`tuple`、`vision_defect_frame` |
| `_validate_5x5_u8` — `_validate_5x5_u8(frame)` | function / [310](../../../../agent/src/sr2fpga_agent/oracles/image.py#L310) | `ValueError`、`isinstance`、`len`、`normalized.append`、`rows.append`、`tuple` |
| `_flat_frame` — `_flat_frame(level)` | function / [326](../../../../agent/src/sr2fpga_agent/oracles/image.py#L326) | `range`、`tuple` |
| `_vertical_step_frame` — `_vertical_step_frame(level)` | function / [330](../../../../agent/src/sr2fpga_agent/oracles/image.py#L330) | `range`、`tuple` |
| `_horizontal_step_frame` — `_horizontal_step_frame(level)` | function / [334](../../../../agent/src/sr2fpga_agent/oracles/image.py#L334) | `range`、`tuple` |
| `_shifted_vertical_step_frame` — `_shifted_vertical_step_frame(level)` | function / [338](../../../../agent/src/sr2fpga_agent/oracles/image.py#L338) | `range`、`tuple` |
| `_random_frames` — `_random_frames(seed, count)` | function / [342](../../../../agent/src/sr2fpga_agent/oracles/image.py#L342) | `random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_validate_pixel_width` — `_validate_pixel_width(width)` | function / [353](../../../../agent/src/sr2fpga_agent/oracles/image.py#L353) | `ValueError` |
| `_validate_stall` — `_validate_stall(stall_cycles)` | function / [358](../../../../agent/src/sr2fpga_agent/oracles/image.py#L358) | `ValueError`、`isinstance` |
| `_validate_operation` — `_validate_operation(operation)` | function / [363](../../../../agent/src/sr2fpga_agent/oracles/image.py#L363) | `ValueError`、`_validate_stall`、`len`、`set` |
| `_operation_output_count` — `_operation_output_count(operation)` | function / [379](../../../../agent/src/sr2fpga_agent/oracles/image.py#L379) | 无直接调用 |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/oracles/numeric.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/numeric.py) · 326 行 · SHA-256 `913f4410bf5ff0d471c74ca1f817e2094a8c31e6aeb95921979fe958e77de52b`

> Independent numeric reference models and evaluator-local scenario bundles.

导入模块：`__future__`、`pathlib`、`random`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.oracles.types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `signed` — `signed(value, width)` | function / [26](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L26) | `ValueError`、`isinstance` |
| `fir_outputs` — `fir_outputs(samples, width)` | function / [37](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L37) | `outputs.append`、`signed` |
| `matrix_vector_outputs` — `matrix_vector_outputs(samples, width)` | function / [49](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L49) | `ValueError`、`len`、`range`、`signed`、`sum`、`zip` |
| `build_fir_filter_bundle` — `build_fir_filter_bundle(width, root)` | function / [63](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L63) | `Path`、`_fir_scenario`、`_random_fir_events`、`list`、`write_oracle_bundle` |
| `build_matrix_vector_mac_bundle` — `build_matrix_vector_mac_bundle(width, root)` | function / [121](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L121) | `Path`、`_matrix_scenario`、`_random_matrix_events`、`list`、`write_oracle_bundle` |
| `_input_fields` — `_input_fields(width)` | function / [195](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L195) | `OracleField` |
| `_expected_fields` — `_expected_fields(result_width)` | function / [203](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L203) | `OracleField` |
| `_pack_input` — `_pack_input(sample, reset_before, stall_cycles, width)` | function / [210](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L210) | `ValueError`、`int` |
| `_pack_expected` — `_pack_expected(result, expect_output, result_width)` | function / [220](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L220) | `int` |
| `_fir_scenario` — `_fir_scenario(scenario_id, scenario_class, seed, events, width, result_width)` | function / [224](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L224) | `OracleScenarioSpec`、`_expected_fields`、`_input_fields`、`_pack_expected`、`_pack_input`、`expected_records.append`、`input_records.append`、`signed`、`tuple` |
| `_matrix_scenario` — `_matrix_scenario(scenario_id, scenario_class, seed, events, width, result_width)` | function / [256](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L256) | `OracleScenarioSpec`、`_expected_fields`、`_input_fields`、`_pack_expected`、`_pack_input`、`expected_records.append`、`group.append`、`group.clear`、`input_records.append`、`len`、`matrix_vector_outputs`、`signed`、`tuple` |
| `_random_fir_events` — `_random_fir_events(width, seed)` | function / [290](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L290) | `random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_random_matrix_events` — `_random_matrix_events(width, seed)` | function / [304](../../../../agent/src/sr2fpga_agent/oracles/numeric.py#L304) | `random.Random`、`randomizer.randint`、`range`、`tuple` |

## `agent/src/sr2fpga_agent/oracles/rl.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/rl.py) · 546 行 · SHA-256 `a72559fab6420b31b4908e89693d5cdc52af33cedae057401b9dea99f0e8fb79`

> Independent fixed-point RL references and evaluator-local oracle bundles.

导入模块：`__future__`、`dataclasses`、`pathlib`、`random`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.oracles.types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RLConfig` — `RLConfig` | class / [31](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L31) | 无直接调用 |
| `RLConfig.write` — `write(self, address, data, width)` | function / [39](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L39) | `ValueError`、`_validate_unsigned`、`_validate_width`、`bool`、`isinstance`、`replace` |
| `_RLOperation` — `_RLOperation` | class / [51](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L51) | 无直接调用 |
| `saturate_signed` — `saturate_signed(value, width)` | function / [63](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L63) | `ValueError`、`_validate_width`、`isinstance`、`max`、`min` |
| `td_update` — `td_update(reward, value, next_value, gamma, alpha, width)` | function / [72](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L72) | `_validate_signed`、`_validate_unsigned`、`_validate_width`、`saturate_signed` |
| `argmax_first` — `argmax_first(values)` | function / [93](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L93) | `ValueError`、`isinstance`、`len`、`max`、`range` |
| `rl_accelerator_step` — `rl_accelerator_step(config, obs0, obs1, reward, next_value, done, width)` | function / [99](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L99) | `ValueError`、`_validate_unsigned`、`_validate_width`、`argmax_first`、`getattr`、`isinstance`、`max`、`min` |
| `build_qtable_update_bundle` — `build_qtable_update_bundle(width, root)` | function / [139](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L139) | `Path`、`_random_td_records`、`_signed_bounds`、`_td_scenario`、`_validate_width`、`write_oracle_bundle` |
| `build_rl_accelerator_bundle` — `build_rl_accelerator_bundle(width, root)` | function / [197](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L197) | `Path`、`_cfg`、`_config_writes`、`_random_rl_operations`、`_reset`、`_rl_scenario`、`_sample`、`_validate_width`、`write_oracle_bundle` |
| `_td_scenario` — `_td_scenario(scenario_id, scenario_class, seed, width, records)` | function / [275](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L275) | `OracleField`、`OracleScenarioSpec`、`_pack_signed`、`_validate_stall`、`expected.append`、`inputs.append`、`int`、`td_update`、`tuple` |
| `_rl_scenario` — `_rl_scenario(scenario_id, scenario_class, seed, width, operations)` | function / [324](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L324) | `OracleField`、`OracleScenarioSpec`、`RLConfig`、`_validate_operation`、`config.write`、`expected.append`、`inputs.append`、`int`、`rl_accelerator_step`、`tuple` |
| `_random_td_records` — `_random_td_records(width, seed, count)` | function / [422](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L422) | `_signed_bounds`、`min`、`random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_random_rl_operations` — `_random_rl_operations(width, seed)` | function / [444](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L444) | `_config_writes`、`_reset`、`_sample`、`min`、`random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_reset` — `_reset()` | function / [462](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L462) | `_RLOperation` |
| `_cfg` — `_cfg(address, data)` | function / [466](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L466) | `_RLOperation` |
| `_config_writes` — `_config_writes(values)` | function / [470](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L470) | `ValueError`、`_cfg`、`enumerate`、`len`、`tuple` |
| `_sample` — `_sample(obs0, obs1, reward, next_value, done, stall_cycles)` | function / [476](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L476) | `_RLOperation` |
| `_validate_operation` — `_validate_operation(operation, width)` | function / [496](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L496) | `ValueError`、`_validate_stall`、`_validate_unsigned`、`getattr`、`isinstance` |
| `_validate_width` — `_validate_width(width)` | function / [508](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L508) | `ValueError`、`isinstance` |
| `_signed_bounds` — `_signed_bounds(width)` | function / [513](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L513) | 无直接调用 |
| `_validate_signed` — `_validate_signed(name, value, width)` | function / [517](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L517) | `ValueError`、`_signed_bounds`、`isinstance` |
| `_validate_unsigned` — `_validate_unsigned(name, value, width)` | function / [523](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L523) | `ValueError`、`isinstance` |
| `_validate_stall` — `_validate_stall(stall_cycles)` | function / [528](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L528) | `ValueError`、`isinstance` |
| `_pack_signed` — `_pack_signed(value, width)` | function / [533](../../../../agent/src/sr2fpga_agent/oracles/rl.py#L533) | 无直接调用 |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/oracles/signal.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/signal.py) · 449 行 · SHA-256 `47f63fbce9cb912697b6a362529aac0c0e79637562525d7d6f29659483c08e7f`

> Independent signal-processing references and evaluator-local bundles.

导入模块：`__future__`、`pathlib`、`random`、`sr2fpga_agent.oracles.bundle`、`sr2fpga_agent.oracles.numeric`、`sr2fpga_agent.oracles.types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `matched_filter_outputs` — `matched_filter_outputs(samples, width)` | function / [30](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L30) | `outputs.append`、`signed`、`sum`、`zip` |
| `detect_peak` — `detect_peak(values, threshold)` | function / [41](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L41) | `enumerate` |
| `pulse_radar` — `pulse_radar(samples, width, threshold)` | function / [53](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L53) | `detect_peak`、`matched_filter_outputs` |
| `build_matched_filter_bundle` — `build_matched_filter_bundle(width, root)` | function / [59](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L59) | `Path`、`_matched_scenario`、`_random_matched_events`、`list`、`write_oracle_bundle` |
| `build_peak_detector_bundle` — `build_peak_detector_bundle(width, root)` | function / [119](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L119) | `Path`、`_peak_scenario`、`_random_peak_events`、`write_oracle_bundle` |
| `build_pulse_radar_bundle` — `build_pulse_radar_bundle(width, root)` | function / [177](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L177) | `Path`、`_radar_scenario`、`_random_radar_events`、`list`、`write_oracle_bundle` |
| `_matched_input_fields` — `_matched_input_fields(width)` | function / [247](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L247) | `OracleField` |
| `_framed_input_fields` — `_framed_input_fields(width)` | function / [255](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L255) | `OracleField` |
| `_peak_expected_fields` — `_peak_expected_fields(value_width)` | function / [264](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L264) | `OracleField` |
| `_pack_matched_input` — `_pack_matched_input(sample, reset_before, stall_cycles, width)` | function / [273](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L273) | `_validate_stall`、`int` |
| `_pack_framed_input` — `_pack_framed_input(sample, in_last, reset_before, stall_cycles, width)` | function / [278](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L278) | `_validate_stall`、`int` |
| `_pack_peak_expected` — `_pack_peak_expected(result, expect_output, value_width)` | function / [288](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L288) | `int` |
| `_matched_scenario` — `_matched_scenario(scenario_id, scenario_class, seed, events, width, acc_width)` | function / [299](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L299) | `OracleField`、`OracleScenarioSpec`、`_matched_input_fields`、`_pack_matched_input`、`expected.append`、`inputs.append`、`signed`、`sum`、`tuple`、`zip` |
| `_peak_scenario` — `_peak_scenario(scenario_id, scenario_class, seed, events, width)` | function / [330](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L330) | `OracleScenarioSpec`、`_framed_input_fields`、`_pack_framed_input`、`_pack_peak_expected`、`_peak_expected_fields`、`detect_peak`、`expected.append`、`frame.append`、`frame.clear`、`inputs.append`、`signed`、`tuple` |
| `_radar_scenario` — `_radar_scenario(scenario_id, scenario_class, seed, events, width, acc_width)` | function / [362](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L362) | `OracleScenarioSpec`、`_framed_input_fields`、`_pack_framed_input`、`_pack_peak_expected`、`_peak_expected_fields`、`correlations.append`、`correlations.clear`、`detect_peak`、`expected.append`、`inputs.append`、`signed`、`sum`、`tuple`、`zip` |
| `_random_matched_events` — `_random_matched_events(width, seed)` | function / [405](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L405) | `random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_random_peak_events` — `_random_peak_events(width, seed)` | function / [415](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L415) | `random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_random_radar_events` — `_random_radar_events(width, seed)` | function / [425](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L425) | `random.Random`、`randomizer.randint`、`range`、`tuple` |
| `_validate_stall` — `_validate_stall(stall_cycles)` | function / [435](../../../../agent/src/sr2fpga_agent/oracles/signal.py#L435) | `ValueError`、`isinstance` |

## `agent/src/sr2fpga_agent/oracles/types.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/oracles/types.py) · 254 行 · SHA-256 `372f7f44937ce06b4a0d5624e42ff158c6525e97cde2510b64e54b57609efc2d`

> Immutable data types for evaluator-local oracle bundles.

导入模块：`__future__`、`dataclasses`、`pathlib`、`sr2fpga_agent.models`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_validate_execution_outcome` — `_validate_execution_outcome(status, failure_origin, failure_type)` | function / [27](../../../../agent/src/sr2fpga_agent/oracles/types.py#L27) | `ValueError`、`failure_type.strip`、`isinstance` |
| `OracleField` — `OracleField` | class / [49](../../../../agent/src/sr2fpga_agent/oracles/types.py#L49) | 无直接调用 |
| `OracleScenarioSpec` — `OracleScenarioSpec` | class / [57](../../../../agent/src/sr2fpga_agent/oracles/types.py#L57) | 无直接调用 |
| `OracleScenarioManifest` — `OracleScenarioManifest` | class / [70](../../../../agent/src/sr2fpga_agent/oracles/types.py#L70) | 无直接调用 |
| `OracleBundle` — `OracleBundle` | class / [86](../../../../agent/src/sr2fpga_agent/oracles/types.py#L86) | 无直接调用 |
| `OracleScenarioResult` — `OracleScenarioResult` | class / [98](../../../../agent/src/sr2fpga_agent/oracles/types.py#L98) | 无直接调用 |
| `OracleScenarioResult.__post_init__` — `__post_init__(self)` | function / [111](../../../../agent/src/sr2fpga_agent/oracles/types.py#L111) | `_validate_execution_outcome` |
| `OracleScenarioResult.from_tool_result` — `from_tool_result(cls, scenario, result, failure_origin, failure_type, mismatch_detail)` | function / [119](../../../../agent/src/sr2fpga_agent/oracles/types.py#L119) | `cls`、`tuple` |
| `OracleScenarioResult.to_dict` — `to_dict(self)` | function / [142](../../../../agent/src/sr2fpga_agent/oracles/types.py#L142) | `dict`、`list` |
| `OracleRunEvidence` — `OracleRunEvidence` | class / [159](../../../../agent/src/sr2fpga_agent/oracles/types.py#L159) | 无直接调用 |
| `OracleRunEvidence.__post_init__` — `__post_init__(self)` | function / [168](../../../../agent/src/sr2fpga_agent/oracles/types.py#L168) | `_validate_execution_outcome` |
| `OracleRunEvidence.from_results` — `from_results(cls, bundle, results)` | function / [176](../../../../agent/src/sr2fpga_agent/oracles/types.py#L176) | `<dynamic>.join`、`_primary_failure`、`cls`、`sorted`、`tuple` |
| `OracleRunEvidence.scenario_counts` — `scenario_counts(self)` | function / [207](../../../../agent/src/sr2fpga_agent/oracles/types.py#L207) | `counts.get` |
| `OracleRunEvidence.class_status` — `class_status(self, scenario_class)` | function / [213](../../../../agent/src/sr2fpga_agent/oracles/types.py#L213) | `all`、`tuple` |
| `OracleRunEvidence.to_dict` — `to_dict(self)` | function / [221](../../../../agent/src/sr2fpga_agent/oracles/types.py#L221) | `list`、`result.to_dict`、`self.class_status`、`self.scenario_counts`、`sorted` |
| `_primary_failure` — `_primary_failure(results)` | function / [242](../../../../agent/src/sr2fpga_agent/oracles/types.py#L242) | `min`、`precedence.get` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`
