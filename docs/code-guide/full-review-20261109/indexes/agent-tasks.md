# agent-tasks：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/tasks/ai_dw_pw/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/__init__.py) · 6 行 · SHA-256 `3952d3b89cd02b4ccd602ed970a5e0feed17e35ed1005c195234bca2d8244f2b`

> A fixed, exposed DW/PW development task; no official task qualification.

导入模块：`sr2fpga_agent.tasks.ai_dw_pw.oracle`、`sr2fpga_agent.tasks.ai_dw_pw.task`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/tasks/ai_dw_pw/harness.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/harness.py) · 202 行 · SHA-256 `df7efa631f2d23bc28af774a59892b6cc7d71b1e8810f3e71c31a2baa3d6ef0e`

> Evaluator-owned development simulation driver and complete-transaction checker.

导入模块：`__future__`、`dataclasses`、`random`、`sr2fpga_agent.tasks.ai_dw_pw.oracle`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `development_frames` — `development_frames()` | function / [15](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/harness.py#L15) | `random.Random`、`range`、`rng.choice`、`tuple` |
| `TraceResult` — `TraceResult` | class / [24](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/harness.py#L24) | 无直接调用 |
| `check_trace` — `check_trace(stdout, expected_completed)` | function / [33](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/harness.py#L33) | `TraceResult`、`ValueError`、`any`、`bool`、`evaluate`、`incoming.append`、`incoming.clear`、`int`、`len`、`line.split`、`line.startswith`、`list`、`map`、`pack_tensor`、`pending.clear`、`pending.pop`、`stdout.splitlines`、`unpack_tensor` |
| `render_testbench` — `render_testbench(frames)` | function / [132](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/harness.py#L132) | `<dynamic>.join`、`ValueError`、`any`、`development_frames`、`enumerate`、`len`、`pack_tensor` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py) · 71 行 · SHA-256 `438f80ae407b8150d9b4dfa29f3d61db37d36daa8a375d509fcd6c1a4250f812`

> Evaluator-owned, exact integer reference. Never imported by generated RTL.

导入模块：`__future__`、`fractions`、`sr2fpga_agent.tasks.ai_dw_pw.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `nearest_even` — `nearest_even(numerator, denominator)` | function / [11](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py#L11) | `Fraction`、`ValueError`、`round` |
| `saturate` — `saturate(value)` | function / [18](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py#L18) | `max`、`min` |
| `evaluate` — `evaluate(values)` | function / [22](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py#L22) | `ValueError`、`any`、`intermediate.append`、`len`、`max`、`nearest_even`、`range`、`result.append`、`saturate`、`sum`、`tuple`、`type` |
| `pack_tensor` — `pack_tensor(values, channels)` | function / [44](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py#L44) | `ValueError`、`any`、`beats.append`、`len`、`min`、`range`、`tuple`、`type` |
| `unpack_tensor` — `unpack_tensor(beats, channels)` | function / [57](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/oracle.py#L57) | `ValueError`、`enumerate`、`len`、`min`、`range`、`result.append`、`tuple`、`type` |

## `agent/src/sr2fpga_agent/tasks/ai_dw_pw/reference.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/reference.py) · 195 行 · SHA-256 `50aed68b463638e9bef7f9817d3f5d8c03c7f5bf01006fb52f8866f3b177d1ec`

> Hand-authored RTL control implementation, separate from evaluator oracle.

导入模块：`sr2fpga_agent.tasks.ai_dw_pw.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_lookup` — `_lookup(name, values)` | function / [10](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/reference.py#L10) | `<dynamic>.join`、`enumerate` |
| `reference_behavior_bodies` — `reference_behavior_bodies()` | function / [44](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/reference.py#L44) | `_lookup`、`tuple` |
| `render_reference_project` — `render_reference_project()` | function / [176](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/reference.py#L176) | `<dynamic>.items`、`reference_behavior_bodies` |

## `agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py) · 144 行 · SHA-256 `cbc4bf83d4308d42cb3c53d025d1344709e5cbb131d89a1646b4235a1f3266af`

> Public meaning and assets, separate from evaluator inputs and expected values.

导入模块：`__future__`、`copy`、`hashlib`、`json`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_tensor` — `_tensor(channels, quantization)` | function / [23](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L23) | 无直接调用 |
| `_quant` — `_quant(zero, denominator)` | function / [35](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L35) | 无直接调用 |
| `signatures` — `signatures()` | function / [41](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L41) | `_quant`、`_tensor`、`list`、`signature` |
| `signatures.signature` — `signature(rx, tx)` | function / [49](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L49) | `copy.deepcopy`、`dict.fromkeys` |
| `build_development_task` — `build_development_task()` | function / [61](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L61) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`assets.items`、`facts.items`、`facts_values.items`、`hashlib.sha256`、`json.dumps`、`len`、`list`、`signatures` |
| `reference_design` — `reference_design()` | function / [122](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L122) | `build_development_task`、`ep`、`net`、`signatures` |
| `reference_design.ep` — `ep(instance, port)` | function / [125](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L125) | 无直接调用 |
| `reference_design.net` — `net(source, sink)` | function / [127](../../../../agent/src/sr2fpga_agent/tasks/ai_dw_pw/task.py#L127) | 无直接调用 |

## `agent/src/sr2fpga_agent/tasks/llm.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm.py) · 252 行 · SHA-256 `39668c13ad969b279fae81b74ec5f47372b2e31e3e9f92438774fae86bf29a7a`

> Prepare public LLM cases or validate their hand-authored development controls.

导入模块：`__future__`、`argparse`、`dataclasses`、`hashlib`、`importlib`、`json`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.models`、`sr2fpga_agent.pc.context`、`sr2fpga_agent.pc.development_tools`、`sr2fpga_agent.pc.emitter`、`sr2fpga_agent.pc.inputs`、`sr2fpga_agent.repository_paths`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_write_json` — `_write_json(path, value)` | function / [42](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L42) | `canonical_json_bytes`、`path.open`、`path.parent.mkdir`、`stream.write` |
| `_case_module` — `_case_module(case)` | function / [48](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L48) | `ValueError`、`import_module` |
| `_source_files` — `_source_files(case)` | function / [54](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L54) | `<dynamic>.rglob`、`Path`、`RepositoryPaths.discover`、`_case_module`、`package.rglob`、`sorted` |
| `prepare_case` — `prepare_case(case, output)` | function / [61](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L61) | `<dynamic>.as_posix`、`<dynamic>.hexdigest`、`<dynamic>.items`、`<dynamic>.read_bytes`、`<dynamic>.resolve`、`ArtifactStore`、`FileExistsError`、`Path`、`RepositoryPaths.discover`、`ValueError`、`_case_module`、`_load_prepared`、`_source_files`、`_write_json`、`assets.append`、`canonical_json_bytes`、`enumerate`、`hashlib.sha256`、`isinstance`、`len`、`module.build_development_task`、`path.open`、`path.parent.mkdir`、`public.sources.bindings`、`ref.to_dict`、`relative.encode`、`root.exists`、`root.is_relative_to`、`root.mkdir`、`sorted`、`source.read_bytes`、`source.relative_to`、`store.append_event`、`store.put_blob`、`stream.write` |
| `_load_prepared` — `_load_prepared(root, case)` | function / [123](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L123) | `<dynamic>.items`、`<dynamic>.read_bytes`、`ArtifactStore`、`ParseLimits`、`RepositoryPaths.discover`、`TrustedContext`、`TrustedSource`、`ValueError`、`json.loads`、`load_public_task`、`store.read_verified`、`store.reference` |
| `check_reference` — `check_reference(case, output, synthesize)` | function / [147](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L147) | `<dynamic>.append_event`、`<dynamic>.join`、`<dynamic>.write_text`、`ArtifactStore`、`ParseLimits`、`ValueError`、`_case_module`、`_load_prepared`、`_write_json`、`asdict`、`assemble_project_contract`、`build.units.items`、`build_structure`、`canonical_json_bytes`、`check_task_design`、`compose_behavior`、`harness.check_trace`、`harness.render_testbench`、`import_module`、`is_dataclass`、`json.loads`、`list`、`module.reference_design`、`prepare_case`、`receipt.update`、`reference.reference_behavior_bodies`、`run_recorded`、`str`、`write_project` |
| `main` — `main(argv)` | function / [224](../../../../agent/src/sr2fpga_agent/tasks/llm.py#L224) | `any`、`argparse.ArgumentParser`、`args.output.exists`、`check_reference`、`int`、`json.dumps`、`parser.add_argument`、`parser.error`、`parser.exit`、`parser.parse_args`、`prepare_case`、`print`、`receipts.append`、`str`、`tuple` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`main`

## `agent/src/sr2fpga_agent/tasks/llm_attention/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/__init__.py) · 5 行 · SHA-256 `4e1a1f092d059089c021ea493489b77830f6312e589bf45a80ef8ffb76be80f5`

> Fixed, stateful quantized GQA decode-attention development case.

导入模块：`sr2fpga_agent.tasks.llm_attention.task`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/tasks/llm_attention/harness.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py) · 250 行 · SHA-256 `09095edffa1babc008041aa37175653b16050adaea358da1aae15cbfdcac913b`

> Evaluator-owned multi-stream schedule and persistent-cache transaction checker.

导入模块：`__future__`、`dataclasses`、`random`、`sr2fpga_agent.tasks.llm_attention.oracle`、`sr2fpga_agent.tasks.llm_attention.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `development_commands` — `development_commands()` | function / [17](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py#L17) | `DecodeInput`、`random.Random`、`range`、`rng.randrange`、`tuple` |
| `TraceResult` — `TraceResult` | class / [34](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py#L34) | 无直接调用 |
| `check_trace` — `check_trace(stdout, expected_completed)` | function / [47](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py#L47) | `<dynamic>.append`、`<dynamic>.clear`、`DecodeInput`、`DecodeOracle`、`INPUT_BEATS.items`、`TraceResult`、`ValueError`、`all`、`any`、`beats.clear`、`bool`、`incoming.values`、`int`、`len`、`line.split`、`line.startswith`、`list`、`map`、`max`、`oracle.decode`、`oracle.reset`、`pack_vectors`、`pending.clear`、`pending.pop`、`previous_input.values`、`stdout.splitlines`、`str`、`streams.items`、`streams.values`、`unpack_vectors` |
| `render_testbench` — `render_testbench(commands)` | function / [156](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/harness.py#L156) | `<dynamic>.join`、`ValueError`、`assignments.append`、`development_commands`、`enumerate`、`len`、`pack_vectors`、`send_tasks.append`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py) · 100 行 · SHA-256 `ed8754c44f6454c3ed11b0f77ae07a397bca6e7a51dc9c6929b5bacfe0669436`

> Evaluator-owned integer/Fraction model; no RTL implementation is imported.

导入模块：`__future__`、`dataclasses`、`fractions`、`sr2fpga_agent.tasks.llm_attention.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `nearest_even` — `nearest_even(numerator, denominator)` | function / [12](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L12) | `Fraction`、`ValueError`、`round`、`type` |
| `_raw` — `_raw(values, size)` | function / [18](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L18) | `ValueError`、`any`、`len`、`tuple`、`type` |
| `DecodeInput` — `DecodeInput` | class / [26](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L26) | 无直接调用 |
| `DecodeInput.__post_init__` — `__post_init__(self)` | function / [31](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L31) | `_raw` |
| `DecodeOracle` — `DecodeOracle` | class / [37](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L37) | 无直接调用 |
| `DecodeOracle.__init__` — `__init__(self)` | function / [40](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L40) | 无直接调用 |
| `DecodeOracle.reset` — `reset(self)` | function / [44](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L44) | `self.keys.clear`、`self.values.clear` |
| `DecodeOracle.valid_length` — `valid_length(self)` | function / [49](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L49) | `len` |
| `DecodeOracle.decode` — `decode(self, command)` | function / [52](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L52) | `ValueError`、`_raw`、`max`、`min`、`nearest_even`、`range`、`result.append`、`self.keys.append`、`self.values.append`、`sum`、`tuple`、`zip` |
| `pack_vectors` — `pack_vectors(values, heads)` | function / [78](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L78) | `_raw`、`range`、`result.extend`、`tuple` |
| `unpack_vectors` — `unpack_vectors(beats, heads)` | function / [88](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/oracle.py#L88) | `ValueError`、`enumerate`、`len`、`result.extend`、`tuple`、`type` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/tasks/llm_attention/reference.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/reference.py) · 193 行 · SHA-256 `9be3a3100077720dc22ce72b580e0d95b0c02d71f2738437b31fb28503b98e59`

> Hand-authored stateful RTL control; the generic emitter never inserts it.

导入模块：`sr2fpga_agent.tasks.llm_attention.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `reference_behavior_bodies` — `reference_behavior_bodies()` | function / [6](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/reference.py#L6) | `<dynamic>.join`、`enumerate` |
| `render_reference_project` — `render_reference_project()` | function / [176](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/reference.py#L176) | `<dynamic>.join`、`bindings.extend`、`ports.extend`、`reference_behavior_bodies`、`top_ports.extend` |

## `agent/src/sr2fpga_agent/tasks/llm_attention/task.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py) · 128 行 · SHA-256 `aa6b09f1336afcda8ac43d4f8f79307e3b8a2537e446dfc9e8701e18d63ca1db`

> Public fixed-profile GQA semantics; evaluator inputs and answers stay separate.

导入模块：`__future__`、`copy`、`hashlib`、`json`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_tensor` — `_tensor(heads, denominator)` | function / [16](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L16) | 无直接调用 |
| `signature` — `signature()` | function / [29](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L29) | `_tensor` |
| `build_development_task` — `build_development_task()` | function / [42](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L42) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`assets.items`、`facts.items`、`hashlib.sha256`、`json.dumps`、`len`、`signature`、`values.items` |
| `reference_design` — `reference_design()` | function / [106](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L106) | `build_development_task`、`copy.deepcopy`、`net`、`signature` |
| `reference_design.endpoint` — `endpoint(owner, port)` | function / [108](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L108) | 无直接调用 |
| `reference_design.net` — `net(source, sink, port)` | function / [110](../../../../agent/src/sr2fpga_agent/tasks/llm_attention/task.py#L110) | `endpoint` |

## `agent/src/sr2fpga_agent/tasks/llm_ffn/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/__init__.py) · 5 行 · SHA-256 `70cac0d452f6d91658b919ba7477b1ae36bbbab1286040e96f12425038febdc8`

> Fixed quantized LLM gated-FFN development task, not a qualified benchmark.

导入模块：`sr2fpga_agent.tasks.llm_ffn.task`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/tasks/llm_ffn/harness.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/harness.py) · 191 行 · SHA-256 `9031e59c42c321bb4213bfb2aa92411f93e1eb04021a0e1a4e67572d032bb5d9`

> Evaluator-owned FFN development inputs, reset/stall driver and scoreboard.

导入模块：`__future__`、`dataclasses`、`random`、`sr2fpga_agent.tasks.llm_ffn.oracle`、`sr2fpga_agent.tasks.llm_ffn.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `development_frames` — `development_frames()` | function / [14](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/harness.py#L14) | `random.Random`、`range`、`rng.randrange`、`tuple` |
| `TraceResult` — `TraceResult` | class / [21](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/harness.py#L21) | 无直接调用 |
| `check_trace` — `check_trace(stdout, expected_completed)` | function / [30](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/harness.py#L30) | `TraceResult`、`ValueError`、`any`、`bool`、`evaluate_token`、`incoming.append`、`incoming.clear`、`int`、`len`、`line.split`、`line.startswith`、`map`、`pack_tensor`、`pending.clear`、`pending.extend`、`pending.pop`、`stdout.splitlines`、`str`、`unpack_tensor` |
| `render_testbench` — `render_testbench(frames)` | function / [118](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/harness.py#L118) | `<dynamic>.join`、`ValueError`、`any`、`development_frames`、`enumerate`、`len`、`pack_tensor` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py) · 69 行 · SHA-256 `a919fb263ba47175e3db05bfda64e3a56c05efbc330b611e5608d20ef711d7ea`

> Evaluator-owned integer FFN oracle, separate from RTL state machines.

导入模块：`__future__`、`fractions`、`sr2fpga_agent.tasks.llm_ffn.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `nearest_even` — `nearest_even(value, divisor)` | function / [11](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L11) | `Fraction`、`ValueError`、`round`、`type` |
| `saturate` — `saturate(value)` | function / [17](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L17) | `max`、`min` |
| `evaluate_token` — `evaluate_token(values)` | function / [21](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L21) | `ValueError`、`any`、`enumerate`、`len`、`nearest_even`、`saturate`、`sum`、`tuple`、`type`、`zip` |
| `evaluate` — `evaluate(values)` | function / [34](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L34) | `ValueError`、`evaluate_token`、`len`、`range`、`tuple` |
| `pack_tensor` — `pack_tensor(values, channels)` | function / [41](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L41) | `ValueError`、`any`、`len`、`min`、`range`、`result.append`、`tuple`、`type` |
| `unpack_tensor` — `unpack_tensor(beats, channels)` | function / [55](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/oracle.py#L55) | `ValueError`、`enumerate`、`len`、`min`、`range`、`result.append`、`tuple`、`type` |

## `agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py) · 222 行 · SHA-256 `9db05bc90e2895494ad6ff99341dd17b6baf6efe8036416c9fc525a3c679540d`

> Explicit hand-authored RTL control, never inserted by the generic emitter.

导入模块：`__future__`、`sr2fpga_agent.tasks.llm_ffn.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_lookup` — `_lookup(name, values)` | function / [9](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py#L9) | `<dynamic>.join`、`enumerate` |
| `reference_behavior_bodies` — `reference_behavior_bodies()` | function / [35](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py#L35) | `_lookup`、`tuple` |
| `_manual_header` — `_manual_header(module, signature)` | function / [186](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py#L186) | `<dynamic>.items`、`<dynamic>.join` |
| `render_reference_project` — `render_reference_project()` | function / [197](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/reference.py#L197) | `<dynamic>.items`、`_manual_header`、`reference_behavior_bodies`、`signatures` |

## `agent/src/sr2fpga_agent/tasks/llm_ffn/task.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py) · 161 行 · SHA-256 `2a5c2cc003d192d82e7955bc7c17d69969f9c939f4d1ef42f040c7e8c3281799`

> Candidate-visible synthetic gated-FFN meaning and immutable public assets.

导入模块：`__future__`、`copy`、`hashlib`、`json`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_tensor` — `_tensor(channels)` | function / [31](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L31) | 无直接调用 |
| `_signature` — `_signature(ports)` | function / [42](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L42) | `_tensor`、`copy.deepcopy`、`dict.fromkeys` |
| `signatures` — `signatures()` | function / [53](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L53) | `_signature` |
| `build_development_task` — `build_development_task()` | function / [65](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L65) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`facts.items`、`hashlib.sha256`、`json.dumps`、`len`、`signatures`、`values.items` |
| `reference_design` — `reference_design()` | function / [133](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L133) | `build_development_task`、`net`、`signatures` |
| `reference_design.net` — `net(source, source_port, sink, sink_port)` | function / [136](../../../../agent/src/sr2fpga_agent/tasks/llm_ffn/task.py#L136) | 无直接调用 |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`range`、`tuple`

## `agent/src/sr2fpga_agent/tasks/llm_qkv/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/__init__.py) · 5 行 · SHA-256 `b23643407923c799a00eb7be57ed4d7bee19f9fad8bb58ba6b0d38a23d7af333`

> Fixed quantized LLM Q/K/V projection development case.

导入模块：`sr2fpga_agent.tasks.llm_qkv.task`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py) · 213 行 · SHA-256 `f92de43fc8c6a2220d063559318f5e05b5a7b1d15e957e5c9421786f6a6f8a19`

> Evaluator-owned QKV driver and exact multi-stream transaction checker.

导入模块：`__future__`、`dataclasses`、`random`、`sr2fpga_agent.tasks.llm_qkv.oracle`、`sr2fpga_agent.tasks.llm_qkv.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `development_frames` — `development_frames()` | function / [14](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py#L14) | `random.Random`、`range`、`rng.choice`、`tuple` |
| `TraceResult` — `TraceResult` | class / [21](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py#L21) | 无直接调用 |
| `check_trace` — `check_trace(stdout, expected_completed)` | function / [30](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py#L30) | `<dynamic>.clear`、`<dynamic>.extend`、`<dynamic>.items`、`<dynamic>.pop`、`TraceResult`、`ValueError`、`any`、`evaluate_token`、`incoming.append`、`incoming.clear`、`int`、`len`、`line.split`、`line.startswith`、`map`、`outputs.items`、`outputs.values`、`pack_tensor`、`pending.values`、`previous.values`、`stdout.splitlines`、`str`、`unpack_tensor`、`zip` |
| `render_testbench` — `render_testbench(frames)` | function / [131](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/harness.py#L131) | `<dynamic>.join`、`ValueError`、`any`、`development_frames`、`enumerate`、`len`、`pack_tensor` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py) · 58 行 · SHA-256 `0bfc92a7b8ac3a6c6c5ae9bcec6de31e367de55c3af959462fa8952a137df290`

> Evaluator-owned exact integer Q/K/V oracle, independent of the RTL machine.

导入模块：`__future__`、`fractions`、`sr2fpga_agent.tasks.llm_qkv.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `evaluate_token` — `evaluate_token(values)` | function / [11](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py#L11) | `Fraction`、`ValueError`、`WEIGHTS.items`、`any`、`len`、`max`、`min`、`round`、`sum`、`tuple`、`type`、`zip` |
| `evaluate` — `evaluate(values)` | function / [20](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py#L20) | `ValueError`、`evaluate_token`、`len`、`range`、`tuple` |
| `pack_tensor` — `pack_tensor(values, row_width)` | function / [27](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py#L27) | `ValueError`、`any`、`beats.append`、`len`、`min`、`range`、`tuple`、`type` |
| `unpack_tensor` — `unpack_tensor(beats, row_width)` | function / [41](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py#L41) | `ValueError`、`enumerate`、`len`、`min`、`range`、`result.append`、`tuple`、`type` |
| `packed_outputs` — `packed_outputs(values)` | function / [57](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/oracle.py#L57) | `<dynamic>.items`、`evaluate`、`pack_tensor` |

## `agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py) · 158 行 · SHA-256 `0e1a0314899d3010590604d9a1457f0b1ec50c6299aac9daf6ae618716afc40b`

> Explicit hand-authored QKV control bodies; never inserted by the emitter.

导入模块：`__future__`、`sr2fpga_agent.tasks.llm_qkv.task`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_lookup` — `_lookup(name, values)` | function / [8](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py#L8) | `<dynamic>.join`、`enumerate` |
| `_projection` — `_projection(branch, tokens_per_batch)` | function / [60](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py#L60) | `ValueError`、`_lookup`、`body.replace`、`len`、`replacements.items`、`str`、`tuple`、`type` |
| `reference_behavior_bodies` — `reference_behavior_bodies()` | function / [120](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py#L120) | `MODULES.items`、`_projection` |
| `_header` — `_header(name, outputs)` | function / [124](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py#L124) | `<dynamic>.join` |
| `render_reference_project` — `render_reference_project(tokens_per_batch)` | function / [133](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/reference.py#L133) | `<dynamic>.join`、`_header`、`_projection`、`branch.upper`、`lines.append`、`tuple` |

## `agent/src/sr2fpga_agent/tasks/llm_qkv/task.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py) · 153 行 · SHA-256 `cce44a05835b7e44645271e82b8bb3088ac2fc61b59db4c0c3c96040d4c91616`

> Candidate-visible QKV projection facts and synthetic public assets.

导入模块：`__future__`、`copy`、`hashlib`、`json`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_tensor` — `_tensor(shape, zero, scale_denominator)` | function / [34](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L34) | 无直接调用 |
| `_signature` — `_signature(port_contracts, tensors)` | function / [47](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L47) | `copy.deepcopy`、`dict.fromkeys`、`port_contracts.items`、`port_contracts.values` |
| `signatures` — `signatures()` | function / [57](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L57) | `_signature`、`_tensor`、`b.upper`、`branch.upper` |
| `build_development_task` — `build_development_task()` | function / [70](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L70) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`facts.items`、`hashlib.sha256`、`json.dumps`、`len`、`signatures`、`values.items` |
| `reference_design` — `reference_design()` | function / [128](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L128) | `MODULES.items`、`build_development_task`、`endpoint`、`list`、`net`、`signatures` |
| `reference_design.endpoint` — `endpoint(instance, port)` | function / [131](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L131) | 无直接调用 |
| `reference_design.net` — `net(source, sink)` | function / [134](../../../../agent/src/sr2fpga_agent/tasks/llm_qkv/task.py#L134) | 无直接调用 |
