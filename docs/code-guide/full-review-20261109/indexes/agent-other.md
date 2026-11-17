# agent-other：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/scripts/analyze_phase_d_h2_failures.py`

[打开源文件](../../../../agent/scripts/analyze_phase_d_h2_failures.py) · 216 行 · SHA-256 `bf6bc604d21c5576b075ac6f18b5b7c246f28b257b063fcaa447b02b8689bd0b`

> Analyze frozen Phase D failures and replay generated HIS through current H2.

导入模块：`__future__`、`argparse`、`collections`、`json`、`os`、`pathlib`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.models`、`sys`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `analyze_dataset` — `analyze_dataset(dataset_root)` | function / [24](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L24) | `<dynamic>.get`、`Counter`、`_count_diagnostics`、`_counter_dict`、`_generation_failure_category`、`_nested_counter_dict`、`_read_json`、`_replay_h2`、`_set_count_dict`、`before_status.values`、`changed_to_pass.append`、`dataset_root.glob`、`dataset_root.resolve`、`defaultdict`、`diagnosis.get`、`dict`、`generation_categories.values`、`len`、`metadata.get`、`new_h2.get`、`old_h2.get`、`path.is_dir`、`record.update`、`records.append`、`replay_errors.items`、`sorted`、`str`、`sum`、`trajectory.get` |
| `_replay_h2` — `_replay_h2(sample, metadata)` | function / [114](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L114) | `<dynamic>.get`、`<dynamic>.read_text`、`<dynamic>.strip`、`GeneratedProject`、`ProjectRequest`、`ValueError`、`his_path.is_file`、`his_path.read_text`、`int`、`metadata.get`、`str`、`validate_system_his_h_stages` |
| `_generation_failure_category` — `_generation_failure_category(root_cause)` | function / [132](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L132) | `root_cause.lower` |
| `_diagnostic_category` — `_diagnostic_category(diagnostic)` | function / [147](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L147) | 无直接调用 |
| `_count_diagnostics` — `_count_diagnostics(sample_id, diagnostics, counts, affected)` | function / [161](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L161) | `<dynamic>.add`、`_diagnostic_category` |
| `_read_json` — `_read_json(path)` | function / [173](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L173) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_counter_dict` — `_counter_dict(counter)` | function / [180](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L180) | `sorted` |
| `_nested_counter_dict` — `_nested_counter_dict(values)` | function / [184](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L184) | `_counter_dict`、`sorted` |
| `_set_count_dict` — `_set_count_dict(values)` | function / [188](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L188) | `len`、`sorted` |
| `_parse_args` — `_parse_args()` | function / [192](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L192) | `argparse.ArgumentParser`、`parser.add_argument`、`parser.parse_args` |
| `main` — `main()` | function / [199](../../../../agent/scripts/analyze_phase_d_h2_failures.py#L199) | `SystemExit`、`_parse_args`、`analyze_dataset`、`args.dataset_root.resolve`、`args.output.resolve`、`json.dumps`、`output.parent.mkdir`、`output.write_text`、`sys.stdout.write` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.expanduser`、`<dynamic>.resolve`、`Path`、`SystemExit`、`main`、`os.environ.get`、`str`、`sys.path.insert`

## `agent/scripts/audit_phase_d_pilot.py`

[打开源文件](../../../../agent/scripts/audit_phase_d_pilot.py) · 433 行 · SHA-256 `ff28f27ae4d811de716323e0cf441217bffb10ab81a2eae0caa400fbc196a828`

> Independent integrity audit for the frozen SR2FPGA Phase D pilot.

导入模块：`__future__`、`argparse`、`hashlib`、`json`、`os`、`pathlib`、`re`、`sr2fpga_agent.measurement_freeze`、`sys`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `audit_run` — `audit_run(run_root)` | function / [44](../../../../agent/scripts/audit_phase_d_pilot.py#L44) | `<dynamic>.get`、`<dynamic>.hexdigest`、`<dynamic>.is_file`、`<dynamic>.resolve`、`<dynamic>.rstrip`、`Path`、`Path.cwd`、`_group_samples`、`_has_l0_l3_verdicts`、`_read_json`、`_read_sample`、`_record`、`_secret_findings`、`_trusted_artifact_violations`、`any`、`bool`、`config.get`、`dataset_root.is_absolute`、`enumerate`、`freeze.get`、`freeze_fingerprint`、`freeze_samples.get`、`frozen_identity_violations.append`、`frozen_sample.get`、`hashlib.sha256`、`int`、`isinstance`、`item.get`、`len`、`missing_l4_reports.append`、`paired.get`、`pairs.items`、`pairs.values`、`patch.get`、`requirement.encode`、`requirement_path.read_text`、`run_root.resolve`、`same_source_violations.append`、`set`、`sorted`、`state.get`、`str`、`sum`、`summary.get` |
| `main` — `main(argv)` | function / [299](../../../../agent/scripts/audit_phase_d_pilot.py#L299) | `argparse.ArgumentParser`、`args.output.parent.mkdir`、`args.output.write_text`、`audit_run`、`json.dumps`、`parser.add_argument`、`parser.parse_args`、`print` |
| `_read_sample` — `_read_sample(sample_dir, sample_id)` | function / [312](../../../../agent/scripts/audit_phase_d_pilot.py#L312) | `_read_json`、`isinstance`、`measurement.get`、`metadata.get`、`str`、`trajectory.get`、`verification.get` |
| `_read_json` — `_read_json(path)` | function / [340](../../../../agent/scripts/audit_phase_d_pilot.py#L340) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_group_samples` — `_group_samples(samples, key)` | function / [347](../../../../agent/scripts/audit_phase_d_pilot.py#L347) | `<dynamic>.append`、`groups.setdefault`、`sample.get`、`str` |
| `_has_l0_l3_verdicts` — `_has_l0_l3_verdicts(labels)` | function / [354](../../../../agent/scripts/audit_phase_d_pilot.py#L354) | `all`、`checks.get`、`isinstance`、`labels.get` |
| `_trusted_artifact_violations` — `_trusted_artifact_violations(samples)` | function / [366](../../../../agent/scripts/audit_phase_d_pilot.py#L366) | `<dynamic>.get`、`<dynamic>.lower`、`<dynamic>.replace`、`any`、`enumerate`、`isinstance`、`patch.get`、`str`、`violations.append` |
| `_secret_findings` — `_secret_findings(roots)` | function / [387](../../../../agent/scripts/audit_phase_d_pilot.py#L387) | `_file_contains_secret`、`findings.append`、`path.is_file`、`path.resolve`、`root.exists`、`root.rglob`、`seen.add`、`set`、`sorted`、`str` |
| `_file_contains_secret` — `_file_contains_secret(path)` | function / [409](../../../../agent/scripts/audit_phase_d_pilot.py#L409) | `any`、`handle.read`、`path.open`、`pattern.search` |
| `_record` — `_record(checks, blocking, name, passed, **details)` | function / [420](../../../../agent/scripts/audit_phase_d_pilot.py#L420) | `blocking.append`、`bool` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.expanduser`、`<dynamic>.resolve`、`Path`、`SystemExit`、`main`、`os.environ.get`、`re.compile`、`str`、`sys.path.insert`

## `agent/scripts/openxc7_pnr.sh`

[打开源文件](../../../../agent/scripts/openxc7_pnr.sh) · 228 行 · SHA-256 `e90f5b5ab88e427953e405a37fdc2593bc1786afbf99fc98ea993a460fa3a951`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。
