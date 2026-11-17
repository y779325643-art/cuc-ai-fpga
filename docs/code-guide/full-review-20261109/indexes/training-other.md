# training-other：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `training/scripts/merge_lora.sh`

[打开源文件](../../../../training/scripts/merge_lora.sh) · 20 行 · SHA-256 `5d28d70c4e67d6d96e581f32c2e869cd524b1c061c05abff26acc0e27787c901`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `training/scripts/serve_qwen_vllm.sh`

[打开源文件](../../../../training/scripts/serve_qwen_vllm.sh) · 46 行 · SHA-256 `5a3ef22867cd8bfa79436bb352de9fc1cabbcd9425ccda7d40839b07ef5057ff`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `training/scripts/serve_vllm.sh`

[打开源文件](../../../../training/scripts/serve_vllm.sh) · 45 行 · SHA-256 `06a558b6f8ff500c16137d8aa3f9f79b200e8b435d7a11de0988969866c9eff3`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `training/scripts/setup_server.sh`

[打开源文件](../../../../training/scripts/setup_server.sh) · 17 行 · SHA-256 `2766c7e3bd7f151ad442ed5b039156b3ae37abaef57af5812fec8bb988c92ba5`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `training/scripts/test_api.sh`

[打开源文件](../../../../training/scripts/test_api.sh) · 19 行 · SHA-256 `07f042c92075b4cd66552c5fff5654c5d773cfa96a4f8b97aaa27b9a51597569`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `training/scripts/test_gemma_transformers.py`

[打开源文件](../../../../training/scripts/test_gemma_transformers.py) · 54 行 · SHA-256 `96c579a5ad49aa748e20a206dc15a9a472e99eb42105e0ad443dd3c1d35a3b1e`

> Smoke-test Gemma 4 12B through Transformers chat generation.

导入模块：`os`、`torch`、`transformers`

无命名类/函数定义；检查模块级代码和导出符号。

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.to`、`AutoModelForCausalLM.from_pretrained`、`AutoTokenizer.from_pretrained`、`model.eval`、`model.generate`、`os.environ.get`、`print`、`tokenizer`、`tokenizer.apply_chat_template`、`tokenizer.decode`、`torch.no_grad`

## `training/scripts/train_lora.sh`

[打开源文件](../../../../training/scripts/train_lora.sh) · 14 行 · SHA-256 `aa36b2d34a5df7ccb22480a96243bb4c1c6a9d70f469d5ad7fc85f2d97005390`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `training/src/sr2fpga_training/__init__.py`

[打开源文件](../../../../training/src/sr2fpga_training/__init__.py) · 5 行 · SHA-256 `e7d2eb0b6652c6650399b9012cbdcc976415bb026c8f4f7327e09de2ab1f5ec9`

> SR2FPGA dataset preparation and model training workflows.

导入模块：无显式 import

无命名类/函数定义；检查模块级代码和导出符号。

## `training/src/sr2fpga_training/contracts.py`

[打开源文件](../../../../training/src/sr2fpga_training/contracts.py) · 112 行 · SHA-256 `5a621823925493f4000c81e7828b34fa50fc59b75d1d243ec8a005c9419c3544`

> Training-owned readers for repository contract metadata.

导入模块：`__future__`、`functools`、`json`、`jsonschema`、`os`、`pathlib`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TrainingContractError` — `TrainingContractError` | class / [14](../../../../training/src/sr2fpga_training/contracts.py#L14) | 无直接调用 |
| `discover_repository_root` — `discover_repository_root(start)` | function / [18](../../../../training/src/sr2fpga_training/contracts.py#L18) | `<dynamic>.is_file`、`<dynamic>.resolve`、`<dynamic>.strip`、`Path`、`TrainingContractError`、`_require_repository_root`、`candidate.is_file`、`os.environ.get` |
| `validate_training_view_provenance` — `validate_training_view_provenance(row)` | function / [35](../../../../training/src/sr2fpga_training/contracts.py#L35) | `TrainingContractError`、`_training_view_schema`、`isinstance`、`row.get`、`source_episode_id.strip` |
| `_require_repository_root` — `_require_repository_root(candidate)` | function / [65](../../../../training/src/sr2fpga_training/contracts.py#L65) | `<dynamic>.is_file`、`<dynamic>.resolve`、`TrainingContractError`、`candidate.expanduser` |
| `_training_view_schema` — `_training_view_schema()` | function / [76](../../../../training/src/sr2fpga_training/contracts.py#L76) | `load_registered_schema` |
| `load_registered_schema` — `load_registered_schema(key)` | function / [81](../../../../training/src/sr2fpga_training/contracts.py#L81) | `<dynamic>.get`、`<dynamic>.resolve`、`Draft202012Validator.check_schema`、`Path`、`PurePosixPath`、`TrainingContractError`、`contracts.get`、`discover_repository_root`、`isinstance`、`json.loads`、`manifest.get`、`manifest_path.read_text`、`registry_entry.get`、`relative.is_absolute`、`schema.get`、`schema_path.read_text` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`lru_cache`

## `training/src/sr2fpga_training/merge_lora.py`

[打开源文件](../../../../training/src/sr2fpga_training/merge_lora.py) · 37 行 · SHA-256 `8de510aab8b97c044ed58aa60a4f5d99817911c5e6f1108cb88bbf5fa94d33d9`

> Merge a LoRA adapter into its base model for serving.

导入模块：`__future__`、`argparse`、`pathlib`、`peft`、`transformers`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `main` — `main()` | function / [9](../../../../training/src/sr2fpga_training/merge_lora.py#L9) | `AutoModelForCausalLM.from_pretrained`、`AutoTokenizer.from_pretrained`、`PeftModel.from_pretrained`、`argparse.ArgumentParser`、`args.output.mkdir`、`merged_model.save_pretrained`、`model.merge_and_unload`、`parser.add_argument`、`parser.parse_args`、`print`、`tokenizer.save_pretrained` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `training/src/sr2fpga_training/prepare_dataset.py`

[打开源文件](../../../../training/src/sr2fpga_training/prepare_dataset.py) · 329 行 · SHA-256 `e6759cd5bb21b358b2cf21d90951155bae5b9d368e60215cf7ddd436aa26618c`

> Prepare JSONL chat fine-tuning data.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`sr2fpga_training.contracts`、`sr2fpga_training.release_reader`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `DatasetFormatError` — `DatasetFormatError` | class / [26](../../../../training/src/sr2fpga_training/prepare_dataset.py#L26) | 无直接调用 |
| `convert_jsonl` — `convert_jsonl(source, target, sample_id_prefix, exclude_file_paths)` | function / [30](../../../../training/src/sr2fpga_training/prepare_dataset.py#L30) | `<dynamic>.startswith`、`DatasetFormatError`、`_row_to_messages`、`canonical_row_ids.add`、`enumerate`、`isinstance`、`json.dumps`、`json.loads`、`len`、`line.strip`、`output_file.write`、`row.get`、`rows.append`、`set`、`source.open`、`str`、`target.open`、`target.parent.mkdir` |
| `_row_to_messages` — `_row_to_messages(row, line_number)` | function / [73](../../../../training/src/sr2fpga_training/prepare_dataset.py#L73) | `<dynamic>.strip`、`DatasetFormatError`、`_canonical_requirement_to_file_messages`、`_compact_json`、`_pretty_json`、`_validate_messages`、`render_training_view_row_v2`、`row.get`、`str`、`validate_training_view_provenance` |
| `_canonical_requirement_to_file_messages` — `_canonical_requirement_to_file_messages(row, line_number)` | function / [227](../../../../training/src/sr2fpga_training/prepare_dataset.py#L227) | `DatasetFormatError`、`_validate_messages`、`content.strip`、`input_payload.get`、`isinstance`、`output_payload.get`、`path.strip`、`requirement.strip`、`row.get` |
| `_compact_json` — `_compact_json(value)` | function / [273](../../../../training/src/sr2fpga_training/prepare_dataset.py#L273) | `json.dumps` |
| `_pretty_json` — `_pretty_json(value)` | function / [277](../../../../training/src/sr2fpga_training/prepare_dataset.py#L277) | `json.dumps` |
| `_validate_messages` — `_validate_messages(messages, line_number)` | function / [281](../../../../training/src/sr2fpga_training/prepare_dataset.py#L281) | `<dynamic>.strip`、`DatasetFormatError`、`isinstance`、`len`、`message.get`、`normalized.append`、`str` |
| `main` — `main()` | function / [306](../../../../training/src/sr2fpga_training/prepare_dataset.py#L306) | `argparse.ArgumentParser`、`convert_jsonl`、`parser.add_argument`、`parser.parse_args`、`print`、`set` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `training/src/sr2fpga_training/release_bundle.py`

[打开源文件](../../../../training/src/sr2fpga_training/release_bundle.py) · 522 行 · SHA-256 `cb7ec4a48c8a6061e1ca681a7aa73e5d33d33c1201049390200302809cc6a407`

> Read-only inspection of promoted SR2FPGA training release bundles.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`jsonschema`、`pathlib`、`sr2fpga_training.contracts`、`sr2fpga_training.release_reader`、`types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PromotionAuthorizationExpectation` — `PromotionAuthorizationExpectation` | class / [25](../../../../training/src/sr2fpga_training/release_bundle.py#L25) | 无直接调用 |
| `TrainingLeakagePolicyExpectation` — `TrainingLeakagePolicyExpectation` | class / [32](../../../../training/src/sr2fpga_training/release_bundle.py#L32) | 无直接调用 |
| `TrainingLeakagePolicyExpectation.create` — `create(cls, policy_id, forbidden_canaries)` | function / [39](../../../../training/src/sr2fpga_training/release_bundle.py#L39) | `TrainingContractError`、`_sha256_json`、`any`、`cls`、`isinstance`、`set`、`sorted`、`tuple` |
| `InspectedTrainingRelease` — `InspectedTrainingRelease` | class / [59](../../../../training/src/sr2fpga_training/release_bundle.py#L59) | 无直接调用 |
| `InspectedTrainingRelease.treatment_path` — `treatment_path(self, treatment)` | function / [64](../../../../training/src/sr2fpga_training/release_bundle.py#L64) | `TrainingContractError` |
| `inspect_promoted_release` — `inspect_promoted_release(release_root, authorization, leakage_policy)` | function / [73](../../../../training/src/sr2fpga_training/release_bundle.py#L73) | `<dynamic>.as_posix`、`<dynamic>.read_bytes`、`<dynamic>.resolve`、`InspectedTrainingRelease`、`MappingProxyType`、`Path`、`TrainingContractError`、`_inspect_treatments`、`_load_object`、`_release_path`、`_sha256_bytes`、`_validate_authorization_expectation`、`_validate_file_semantics`、`_validate_leakage_policy_expectation`、`_validate_pool_manifest`、`_validate_release_manifest`、`inventory.items`、`len`、`path.is_file`、`path.relative_to`、`root.rglob`、`set` |
| `_inspect_treatments` — `_inspect_treatments(root, manifest, pool, forbidden_canaries)` | function / [152](../../../../training/src/sr2fpga_training/release_bundle.py#L152) | `TrainingContractError`、`_load_object`、`_load_rows`、`_release_path`、`_sha256_json`、`_validate_linked_artifacts`、`len`、`mixture.get`、`referenced.add`、`referenced.update`、`seen_certificates.setdefault`、`set`、`sorted` |
| `_validate_linked_artifacts` — `_validate_linked_artifacts(row, sidecar, certificate, ref, pool)` | function / [240](../../../../training/src/sr2fpga_training/release_bundle.py#L240) | `TrainingContractError`、`_row_ref`、`_validate_registered`、`_validate_self_hash` |
| `_validate_release_manifest` — `_validate_release_manifest(manifest)` | function / [297](../../../../training/src/sr2fpga_training/release_bundle.py#L297) | `TrainingContractError`、`_sha256_json`、`_validate_registered`、`_validate_self_hash`、`len`、`list`、`set`、`sorted` |
| `_validate_pool_manifest` — `_validate_pool_manifest(pool)` | function / [317](../../../../training/src/sr2fpga_training/release_bundle.py#L317) | `<dynamic>.issubset`、`TrainingContractError`、`_sha256_json`、`_validate_registered`、`_validate_self_hash`、`any`、`covered.extend`、`keys.append`、`len`、`ref.get`、`seen_rows.add`、`set`、`sorted` |
| `_load_rows` — `_load_rows(path, forbidden_canaries)` | function / [399](../../../../training/src/sr2fpga_training/release_bundle.py#L399) | `<dynamic>.splitlines`、`TrainingContractError`、`enumerate`、`isinstance`、`json.loads`、`line.strip`、`path.read_text`、`row_ids.add`、`rows.append`、`set`、`validate_training_view_row_v2` |
| `_row_ref` — `_row_ref(row, sidecar, certificate)` | function / [427](../../../../training/src/sr2fpga_training/release_bundle.py#L427) | 无直接调用 |
| `_validate_registered` — `_validate_registered(key, artifact)` | function / [443](../../../../training/src/sr2fpga_training/release_bundle.py#L443) | `<dynamic>.iter_errors`、`<dynamic>.join`、`Draft202012Validator`、`TrainingContractError`、`load_registered_schema`、`sorted`、`str`、`tuple` |
| `_validate_self_hash` — `_validate_self_hash(artifact, field, label)` | function / [454](../../../../training/src/sr2fpga_training/release_bundle.py#L454) | `TrainingContractError`、`_sha256_json`、`artifact.items` |
| `_validate_authorization_expectation` — `_validate_authorization_expectation(authorization)` | function / [460](../../../../training/src/sr2fpga_training/release_bundle.py#L460) | `TrainingContractError`、`any`、`len` |
| `_validate_leakage_policy_expectation` — `_validate_leakage_policy_expectation(policy)` | function / [472](../../../../training/src/sr2fpga_training/release_bundle.py#L472) | `TrainingContractError`、`TrainingLeakagePolicyExpectation.create` |
| `_validate_file_semantics` — `_validate_file_semantics(record)` | function / [483](../../../../training/src/sr2fpga_training/release_bundle.py#L483) | `TrainingContractError`、`path.startswith` |
| `_release_path` — `_release_path(root, relative_path)` | function / [499](../../../../training/src/sr2fpga_training/release_bundle.py#L499) | `<dynamic>.resolve`、`Path`、`TrainingContractError`、`relative_path.split` |
| `_load_object` — `_load_object(path)` | function / [506](../../../../training/src/sr2fpga_training/release_bundle.py#L506) | `TrainingContractError`、`isinstance`、`json.loads`、`path.read_text` |
| `_sha256_json` — `_sha256_json(value)` | function / [516](../../../../training/src/sr2fpga_training/release_bundle.py#L516) | `_sha256_bytes`、`json.dumps`、`raw.encode` |
| `_sha256_bytes` — `_sha256_bytes(value)` | function / [521](../../../../training/src/sr2fpga_training/release_bundle.py#L521) | `<dynamic>.hexdigest`、`hashlib.sha256` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `training/src/sr2fpga_training/release_reader.py`

[打开源文件](../../../../training/src/sr2fpga_training/release_reader.py) · 199 行 · SHA-256 `b1e18c6744dc51fcddef613106fc087c613cefdc2f8452a40d18b06d5bb8763a`

> Fail-closed reader and renderer for canonical training-view-row-v2 artifacts.

导入模块：`__future__`、`hashlib`、`json`、`jsonschema`、`pathlib`、`re`、`sr2fpga_training.contracts`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_training_view_rows_v2` — `load_training_view_rows_v2(path, forbidden_canaries)` | function / [62](../../../../training/src/sr2fpga_training/release_reader.py#L62) | `Path`、`TrainingContractError`、`enumerate`、`isinstance`、`json.loads`、`line.strip`、`row_ids.add`、`rows.append`、`set`、`source.open`、`validate_training_view_row_v2` |
| `validate_training_view_row_v2` — `validate_training_view_row_v2(row, forbidden_canaries)` | function / [97](../../../../training/src/sr2fpga_training/release_reader.py#L97) | `<dynamic>.iter_errors`、`<dynamic>.join`、`Draft202012Validator`、`TrainingContractError`、`_assert_model_visible_payload`、`_json_path`、`_sha256`、`load_registered_schema`、`row.items`、`sorted`、`str`、`tuple` |
| `render_training_view_row_v2` — `render_training_view_row_v2(row)` | function / [122](../../../../training/src/sr2fpga_training/release_reader.py#L122) | `dict`、`json.dumps`、`messages.append`、`validate_training_view_row_v2` |
| `_assert_model_visible_payload` — `_assert_model_visible_payload(payload, treatment, forbidden_canaries)` | function / [142](../../../../training/src/sr2fpga_training/release_reader.py#L142) | `<dynamic>.lower`、`<dynamic>.replace`、`TrainingContractError`、`_M6U_JSON_FIELD_PATTERN.search`、`_json_path`、`_walk`、`any`、`forbidden_keys.update`、`isinstance`、`key.strip`、`normalized.startswith`、`set`、`value.lower` |
| `_walk` — `_walk(value, path)` | function / [180](../../../../training/src/sr2fpga_training/release_reader.py#L180) | `_walk`、`enumerate`、`isinstance`、`value.items` |
| `_json_path` — `_json_path(parts)` | function / [190](../../../../training/src/sr2fpga_training/release_reader.py#L190) | `isinstance` |
| `_sha256` — `_sha256(value)` | function / [197](../../../../training/src/sr2fpga_training/release_reader.py#L197) | `<dynamic>.hexdigest`、`hashlib.sha256`、`json.dumps`、`raw.encode` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`frozenset`、`re.compile`

## `training/src/sr2fpga_training/train_lora.py`

[打开源文件](../../../../training/src/sr2fpga_training/train_lora.py) · 103 行 · SHA-256 `a4b1ce53dfee600d54398028e105015e923db2b56cd4e51aebd643408e775fff`

> Train a LoRA/QLoRA adapter for chat fine-tuning.

导入模块：`__future__`、`argparse`、`datasets`、`pathlib`、`peft`、`torch`、`transformers`、`trl`、`typing`、`yaml`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_config` — `load_config(path)` | function / [12](../../../../training/src/sr2fpga_training/train_lora.py#L12) | `ValueError`、`isinstance`、`path.open`、`yaml.safe_load` |
| `main` — `main()` | function / [20](../../../../training/src/sr2fpga_training/train_lora.py#L20) | `AutoModelForCausalLM.from_pretrained`、`AutoTokenizer.from_pretrained`、`BitsAndBytesConfig`、`LoraConfig`、`SFTTrainer`、`TrainingArguments`、`argparse.ArgumentParser`、`bool`、`config.get`、`float`、`int`、`list`、`load_config`、`load_dataset`、`parser.add_argument`、`parser.parse_args`、`tokenizer.save_pretrained`、`trainer.save_model`、`trainer.train` |
| `main.format_example` — `format_example(example)` | function / [62](../../../../training/src/sr2fpga_training/train_lora.py#L62) | `tokenizer.apply_chat_template` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`

## `training/src/sr2fpga_training/training_dry_run.py`

[打开源文件](../../../../training/src/sr2fpga_training/training_dry_run.py) · 124 行 · SHA-256 `2e692e6e4ff7c14783bc2b780a6ceee6690faaa0831bd0489a390ad2269b0891`

> Dry-run checks for chat fine-tuning JSONL files.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`re`、`typing`、`yaml`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `DryRunError` — `DryRunError` | class / [18](../../../../training/src/sr2fpga_training/training_dry_run.py#L18) | 无直接调用 |
| `dry_run_from_config` — `dry_run_from_config(config_path)` | function / [22](../../../../training/src/sr2fpga_training/training_dry_run.py#L22) | `Path`、`_load_config`、`config.get`、`dry_run_chat_jsonl`、`int`、`str` |
| `dry_run_chat_jsonl` — `dry_run_chat_jsonl(train_file, max_seq_length)` | function / [29](../../../../training/src/sr2fpga_training/training_dry_run.py#L29) | `DryRunError`、`_estimate_tokens`、`_render_messages`、`_validate_messages`、`enumerate`、`json.loads`、`len`、`lengths.append`、`line.strip`、`max`、`min`、`round`、`row.get`、`str`、`sum`、`train_file.open` |
| `_load_config` — `_load_config(path)` | function / [59](../../../../training/src/sr2fpga_training/training_dry_run.py#L59) | `DryRunError`、`isinstance`、`path.read_text`、`yaml.safe_load` |
| `_validate_messages` — `_validate_messages(messages, line_number)` | function / [68](../../../../training/src/sr2fpga_training/training_dry_run.py#L68) | `<dynamic>.strip`、`DryRunError`、`isinstance`、`len`、`message.get`、`normalized.append`、`str` |
| `_render_messages` — `_render_messages(messages)` | function / [91](../../../../training/src/sr2fpga_training/training_dry_run.py#L91) | `<dynamic>.join` |
| `_estimate_tokens` — `_estimate_tokens(text)` | function / [95](../../../../training/src/sr2fpga_training/training_dry_run.py#L95) | `len`、`re.findall` |
| `main` — `main()` | function / [99](../../../../training/src/sr2fpga_training/training_dry_run.py#L99) | `SystemExit`、`argparse.ArgumentParser`、`dry_run_chat_jsonl`、`dry_run_from_config`、`group.add_argument`、`json.dumps`、`parser.add_argument`、`parser.add_mutually_exclusive_group`、`parser.parse_args`、`print` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`main`
