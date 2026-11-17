# agent-pc：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/pc/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/__init__.py) · 34 行 · SHA-256 `e8a5ae5d9182bd6e26d0578b1b9c11ab152862ec998b1d5fadc9266e35ea29f4`

> PC 2.1 input boundary; schema acceptance is not semantic correctness.

导入模块：`sr2fpga_agent.pc.inputs`、`sr2fpga_agent.pc.semantics`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/pc/__main__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/__main__.py) · 128 行 · SHA-256 `057aa3a3b9758d7399ba44f2c4fdd07265597f9eccfa96329060efcb938041e4`

> PC2.1 input, typed semantic checking and deterministic RTL development CLI.

导入模块：`__future__`、`argparse`、`dataclasses`、`json`、`pathlib`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.pc.context`、`sr2fpga_agent.pc.emitter`、`sr2fpga_agent.pc.inputs`、`sr2fpga_agent.repository_paths`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `main` — `main(argv)` | function / [15](../../../../agent/src/sr2fpga_agent/pc/__main__.py#L15) | `<dynamic>.encode`、`<dynamic>.read_bytes`、`<dynamic>.resolve`、`<dynamic>.write_text`、`ContractRegistry`、`ParseLimits`、`RepositoryPaths.discover`、`TrustedContext`、`TrustedSource`、`ValueError`、`_parse`、`_validate`、`argparse.ArgumentParser`、`args.behavior_bundle.open`、`args.input.open`、`args.output.open`、`args.output.resolve`、`asdict`、`assemble_project_contract`、`build.files.items`、`build_structure`、`check_task_design`、`compose_behavior`、`getattr`、`handle.read`、`handle.write`、`json.dumps`、`load_public_task`、`output.exists`、`output.is_relative_to`、`output.mkdir`、`parse_project_contract`、`parser.add_argument`、`parser.error`、`parser.exit`、`parser.parse_args`、`print`、`target.parent.mkdir`、`target.write_text`、`write_project` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`main`

## `agent/src/sr2fpga_agent/pc/abi.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/abi.py) · 97 行 · SHA-256 `740a63c8af4bd8ef096ae2a79f22e2063c31c49024e1930f56ca57d9da7d3040`

> Deterministic physical views of already checked PC 2.1 types.

导入模块：`__future__`、`itertools`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `type_layout` — `type_layout(value, offset)` | function / [16](../../../../agent/src/sr2fpga_agent/pc/abi.py#L16) | `fields.append`、`range`、`result.update`、`type_layout` |
| `tensor_beats` — `tensor_beats(descriptor)` | function / [46](../../../../agent/src/sr2fpga_agent/pc/abi.py#L46) | `coordinates.append`、`coords.append`、`dict`、`len`、`product`、`range`、`sequence.get`、`zip` |
| `pack_tensor_beat` — `pack_tensor_beat(descriptor, raw_lanes)` | function / [76](../../../../agent/src/sr2fpga_agent/pc/abi.py#L76) | `ValueError`、`enumerate`、`int`、`len`、`type` |

## `agent/src/sr2fpga_agent/pc/checker.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/checker.py) · 418 行 · SHA-256 `249c1e4c4f8220a9ba4d6da3b66df7ec9ba8d7d4ceeb51709f07599dbda54e7f`

> Pure PC 2.1 configuration elaboration and listed static checks.

导入模块：`__future__`、`collections.abc`、`copy`、`dataclasses`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.pc.expressions`、`sr2fpga_agent.pc.semantics`、`sr2fpga_agent.pc.tensors`、`sr2fpga_agent.public_boundary`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `CheckedInstance` — `CheckedInstance` | class / [46](../../../../agent/src/sr2fpga_agent/pc/checker.py#L46) | `field` |
| `CheckedDesign` — `CheckedDesign` | class / [61](../../../../agent/src/sr2fpga_agent/pc/checker.py#L61) | 无直接调用 |
| `_require` — `_require(condition, path, message)` | function / [77](../../../../agent/src/sr2fpga_agent/pc/checker.py#L77) | `PcSemanticError` |
| `_capability` — `_capability(payload)` | function / [82](../../../../agent/src/sr2fpga_agent/pc/checker.py#L82) | `<dynamic>.join`、`_require`、`all`、`deepcopy`、`dict`、`isinstance`、`len`、`natural`、`result.update`、`set`、`sorted`、`type` |
| `resolve_type` — `resolve_type(data_type, parameters, tensors, used_tensors, path, max_width, depth)` | function / [105](../../../../agent/src/sr2fpga_agent/pc/checker.py#L105) | `_require`、`deepcopy`、`dict`、`enumerate`、`evaluate`、`fields.append`、`names.add`、`resolve_type`、`set`、`sum`、`used_tensors.add` |
| `_raw_range` — `_raw_range(data_type)` | function / [141](../../../../agent/src/sr2fpga_agent/pc/checker.py#L141) | `storage_range` |
| `check_design` — `check_design(design, boundary, capability, facts, public_assets)` | function / [147](../../../../agent/src/sr2fpga_agent/pc/checker.py#L147) | `<dynamic>.join`、`<dynamic>.validate`、`<dynamic>.values`、`CheckedDesign`、`ContractRegistry`、`_capability`、`_check_requirement_map`、`_require`、`all`、`check`、`check_public_boundary_domains`、`check_public_boundary_ports`、`deepcopy`、`dict`、`elaborate`、`facts.items`、`isinstance`、`len`、`mapping.values`、`physical.extend`、`record.get`、`registry.load_schema`、`set`、`sum`、`top_domains.values`、`tuple` |
| `check_design.fact` — `fact(name, role, path)` | function / [180](../../../../agent/src/sr2fpga_agent/pc/checker.py#L180) | `_require` |
| `check_design.elaborate` — `elaborate(module_id, path, values, parent_parameters, root_domains, depth)` | function / [199](../../../../agent/src/sr2fpga_agent/pc/checker.py#L199) | `<dynamic>.items`、`<dynamic>.join`、`CheckedInstance`、`_check_nets`、`_check_timing`、`_raw_range`、`_require`、`all`、`any`、`bind_parameters`、`bound_ports.values`、`bound_states.values`、`check_tensor_rules`、`deepcopy`、`domains.items`、`domains.values`、`elaborate`、`evaluate`、`fact`、`implementation.get`、`len`、`natural`、`obligations.append`、`obligations.extend`、`port_types.items`、`resolve_tensor`、`resolve_type`、`set`、`signature.get`、`signature.pop`、`sorted` |
| `_check_nets` — `_check_nets(instance, instances, max_width)` | function / [311](../../../../agent/src/sr2fpga_agent/pc/checker.py#L311) | `<dynamic>.add`、`<dynamic>.items`、`_raw_range`、`_require`、`body.get`、`endpoint`、`enumerate`、`instance.children.items`、`len`、`receivers.add`、`repr`、`resolve_type`、`set`、`sorted`、`sources.add`、`stream_sources.add`、`unused.add` |
| `_check_nets.endpoint` — `endpoint(value, source, p)` | function / [319](../../../../agent/src/sr2fpga_agent/pc/checker.py#L319) | `_require` |
| `_check_timing` — `_check_timing(body, ports, domains, domain_bindings, parameters, fact, path)` | function / [366](../../../../agent/src/sr2fpga_agent/pc/checker.py#L366) | `<dynamic>.items`、`_require`、`body.get`、`evaluate`、`fact`、`len`、`natural`、`ports.get`、`set` |
| `_check_requirement_map` — `_check_requirement_map(design, instances, facts)` | function / [392](../../../../agent/src/sr2fpga_agent/pc/checker.py#L392) | `<dynamic>.join`、`_require`、`enumerate`、`expanded.implementation.get`、`facts.items`、`instances.values`、`mapped.add`、`next`、`seen.add`、`set`、`sorted`、`target.get`、`value.get` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/pc/context.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/context.py) · 95 行 · SHA-256 `f552ba450366ba6f48b1272c5c1409a246f6535dc29a0252edbf1a210aec1486`

> Load the registered, byte-bound PC2.1 development public projection.

导入模块：`__future__`、`dataclasses`、`hashlib`、`pathlib`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.pc.checker`、`sr2fpga_agent.pc.inputs`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PublicTask` — `PublicTask` | class / [21](../../../../agent/src/sr2fpga_agent/pc/context.py#L21) | 无直接调用 |
| `PublicTask.boundary` — `boundary(self)` | function / [29](../../../../agent/src/sr2fpga_agent/pc/context.py#L29) | 无直接调用 |
| `PublicTask.facts` — `facts(self)` | function / [33](../../../../agent/src/sr2fpga_agent/pc/context.py#L33) | 无直接调用 |
| `load_public_task` — `load_public_task(context, asset_root, limits, registry)` | function / [37](../../../../agent/src/sr2fpga_agent/pc/context.py#L37) | `<dynamic>.casefold`、`<dynamic>.hexdigest`、`<dynamic>.resolve`、`ContractRegistry`、`Path`、`PublicTask`、`ValueError`、`_parse`、`_validate`、`getattr`、`hashlib.sha256`、`len`、`path.is_file`、`path.is_relative_to`、`path.read_bytes`、`path.stat`、`validate_project_relative_path` |
| `check_task_design` — `check_task_design(design, task)` | function / [80](../../../../agent/src/sr2fpga_agent/pc/context.py#L80) | `<dynamic>.hexdigest`、`ParseLimits`、`ValueError`、`_parse`、`check_design`、`hashlib.sha256`、`len`、`max`、`set` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/pc/development.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/development.py) · 285 行 · SHA-256 `206ca5bcc8aadfaec4bb0e515d57c9095f8bae2a70aad3948b6169f69931166c`

> Small development adapter using the existing write-once artifact/event store.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`pathlib`、`random`、`re`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.pc.context`、`sr2fpga_agent.pc.development_tools`、`sr2fpga_agent.pc.emitter`、`sr2fpga_agent.pc.inputs`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.tasks.ai_dw_pw`、`sr2fpga_agent.tasks.ai_dw_pw.harness`、`subprocess`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_write` — `_write(path, content)` | function / [27](../../../../agent/src/sr2fpga_agent/pc/development.py#L27) | `handle.write`、`path.open`、`path.parent.mkdir` |
| `prepare_dw_pw` — `prepare_dw_pw(root, max_model_calls)` | function / [33](../../../../agent/src/sr2fpga_agent/pc/development.py#L33) | `<dynamic>.hexdigest`、`<dynamic>.items`、`<dynamic>.resolve`、`DevelopmentSession`、`Path`、`ValueError`、`_write`、`assets.append`、`build_development_task`、`canonical_json_bytes`、`enumerate`、`hashlib.sha256`、`len`、`public.sources.bindings`、`root.exists`、`session.capture_sources`、`session.load_task`、`session.store.append_event`、`session.store.put_blob`、`sorted`、`type` |
| `DevelopmentSession` — `DevelopmentSession` | class / [88](../../../../agent/src/sr2fpga_agent/pc/development.py#L88) | 无直接调用 |
| `DevelopmentSession.__init__` — `__init__(self, root)` | function / [89](../../../../agent/src/sr2fpga_agent/pc/development.py#L89) | `<dynamic>.resolve`、`ArtifactStore`、`Path` |
| `DevelopmentSession.load_task` — `load_task(self)` | function / [93](../../../../agent/src/sr2fpga_agent/pc/development.py#L93) | `<dynamic>.read_bytes`、`ParseLimits`、`TrustedContext`、`TrustedSource`、`ValueError`、`load_public_task`、`self.store.read_verified`、`self.store.reference` |
| `DevelopmentSession.capture_sources` — `capture_sources(self, label)` | function / [109](../../../../agent/src/sr2fpga_agent/pc/development.py#L109) | `<dynamic>.as_posix`、`<dynamic>.rglob`、`RepositoryPaths.discover`、`canonical_json_bytes`、`git.stdout.strip`、`len`、`path.is_file`、`path.read_bytes`、`path.relative_to`、`records.append`、`ref.to_dict`、`self.store.append_event`、`self.store.put_blob`、`sorted`、`subprocess.run` |
| `DevelopmentSession.verify_sources` — `verify_sources(self)` | function / [124](../../../../agent/src/sr2fpga_agent/pc/development.py#L124) | `<dynamic>.hexdigest`、`RepositoryPaths.discover`、`ValueError`、`hashlib.sha256`、`json.loads`、`path.is_file`、`path.read_bytes`、`self.store.read_verified` |
| `DevelopmentSession.reserve_call` — `reserve_call(self, stage, prompt)` | function / [132](../../../../agent/src/sr2fpga_agent/pc/development.py#L132) | `ValueError`、`handle.write`、`lock.open`、`lock.unlink`、`self._reserve_call`、`self.load_task`、`self.verify_sources` |
| `DevelopmentSession._reserve_call` — `_reserve_call(self, stage, prompt)` | function / [146](../../../../agent/src/sr2fpga_agent/pc/development.py#L146) | `<dynamic>.hexdigest`、`BudgetReservationError`、`ValueError`、`hashlib.sha256`、`json.loads`、`prompt.encode`、`ref.to_dict`、`self.store.append_event`、`self.store.consume_once`、`self.store.event_refs`、`self.store.put_blob`、`self.store.read_verified`、`sum` |
| `DevelopmentSession.record_response` — `record_response(self, call_id, response, transport_identity)` | function / [162](../../../../agent/src/sr2fpga_agent/pc/development.py#L162) | `ValueError`、`ref.to_dict`、`response.encode`、`self.store.append_event`、`self.store.put_blob`、`self.store.reference` |
| `DevelopmentSession.build` — `build(self, raw_design, attempt)` | function / [170](../../../../agent/src/sr2fpga_agent/pc/development.py#L170) | `ParseLimits`、`asdict`、`assemble_project_contract`、`build_structure`、`canonical_json_bytes`、`check_task_design`、`self.load_task`、`self.store.put_blob`、`self.store.put_validated_json`、`self.verify_sources`、`validate_sample_id` |
| `DevelopmentSession.compose` — `compose(self, build, bundle, attempt, origin)` | function / [183](../../../../agent/src/sr2fpga_agent/pc/development.py#L183) | `<dynamic>.hexdigest`、`ValueError`、`canonical_json_bytes`、`compose_behavior`、`content.encode`、`getattr`、`hashlib.sha256`、`project.files.items`、`self.load_task`、`self.store.append_event`、`self.store.put_blob`、`self.store.put_validated_json`、`self.verify_sources`、`str`、`validate_sample_id`、`write_project` |
| `DevelopmentSession.evaluate_public` — `evaluate_public(self, project, project_root, attempt, terminal)` | function / [212](../../../../agent/src/sr2fpga_agent/pc/development.py#L212) | `<dynamic>.join`、`<dynamic>.read_bytes`、`<dynamic>.resolve`、`Path`、`ValueError`、`_write`、`any`、`asdict`、`canonical_json_bytes`、`check_trace`、`expected.encode`、`harness.write_text`、`path.replace`、`project.files.items`、`random.Random`、`range`、`re.fullmatch`、`render_testbench`、`resolve_project_manifest`、`rng.randrange`、`run`、`script.encode`、`self.load_task`、`self.store.append_event`、`self.verify_sources`、`stage_root.mkdir`、`str`、`tuple`、`validate_sample_id` |
| `DevelopmentSession.evaluate_public.run` — `run(name, command)` | function / [243](../../../../agent/src/sr2fpga_agent/pc/development.py#L243) | `<dynamic>.decode`、`_write`、`asdict`、`canonical_json_bytes`、`isinstance`、`run_recorded`、`self.store.put_blob` |

## `agent/src/sr2fpga_agent/pc/development_tools.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/development_tools.py) · 57 行 · SHA-256 `f73fc7f3eef7cb59c63fb90ebf2be9306bd478d5581899e77e3ea173e028adb9`

> Persist tool output while running bounded development subprocess trees.

导入模块：`__future__`、`os`、`pathlib`、`signal`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.models`、`subprocess`、`time`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `run_recorded` — `run_recorded(command, cwd, stage, timeout_seconds)` | function / [15](../../../../agent/src/sr2fpga_agent/pc/development_tools.py#L15) | `<dynamic>.isalnum`、`ToolResult`、`ValueError`、`executable_env`、`list`、`os.killpg`、`process.kill`、`process.wait`、`resolve_executable`、`stage.replace`、`stderr_path.open`、`stderr_path.read_text`、`stdout_path.open`、`stdout_path.read_text`、`str`、`subprocess.Popen`、`subprocess.run`、`time.monotonic` |

## `agent/src/sr2fpga_agent/pc/emitter.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/emitter.py) · 511 行 · SHA-256 `92b66d8faf07a102a7b9898094ca766193dd616d6586442c3a7ea04952de11b6`

> PC 2.1 deterministic structure and parser-enforced behavior composition.

导入模块：`__future__`、`copy`、`dataclasses`、`hashlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.pc.abi`、`subprocess`、`tempfile`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PcBuildError` — `PcBuildError` | class / [41](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L41) | 无直接调用 |
| `PcBuildError.__init__` — `__init__(self, message, evidence_path)` | function / [44](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L44) | `<dynamic>.__init__`、`super` |
| `_json` — `_json(value)` | function / [49](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L49) | `json.dumps` |
| `_sha` — `_sha(value)` | function / [53](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L53) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`_json`、`hashlib.sha256` |
| `StructureBuild` — `StructureBuild` | class / [58](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L58) | 无直接调用 |
| `ComposedProject` — `ComposedProject` | class / [69](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L69) | 无直接调用 |
| `_physical_identifier` — `_physical_identifier(name)` | function / [76](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L76) | `PcBuildError`、`_IDENTIFIER.fullmatch` |
| `_ports` — `_ports(instance, boundary, entry)` | function / [82](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L82) | `<dynamic>.casefold`、`<dynamic>.items`、`PcBuildError`、`_physical_identifier`、`dict`、`len`、`ports.append`、`set`、`sorted`、`type_layout` |
| `_declaration` — `_declaration(port, wire, name)` | function / [121](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L121) | 无直接调用 |
| `_header` — `_header(name, ports, parameters)` | function / [128](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L128) | `<dynamic>.join`、`_declaration`、`parameters.items`、`sorted` |
| `build_structure` — `build_structure(checked, bindings, toolchain_id)` | function / [136](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L136) | `<dynamic>.hexdigest`、`<dynamic>.items`、`<dynamic>.join`、`<dynamic>.read_bytes`、`<dynamic>.with_name`、`Path`、`PcBuildError`、`StructureBuild`、`_declaration`、`_header`、`_physical_identifier`、`_ports`、`_sha`、`bindings.values`、`bindings_list.append`、`checked.instances.items`、`files.items`、`hashlib.sha256`、`instance.children.items`、`isinstance`、`lines.append`、`mapping.items`、`metadata.items`、`name.casefold`、`re.fullmatch`、`set`、`sorted`、`specializations.items`、`specializations.setdefault`、`str`、`text.encode`、`top.casefold`、`units.values` |
| `_body_tokens` — `_body_tokens(body)` | function / [260](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L260) | `<dynamic>.isalnum`、`<dynamic>.isalpha`、`<dynamic>.isspace`、`PcBuildError`、`body.find`、`body.startswith`、`forbidden.intersection`、`len`、`token.startswith`、`tokens.append` |
| `_inspect_ast` — `_inspect_ast(log, unit)` | function / [303](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L303) | `<dynamic>.append`、`<dynamic>.values`、`PcBuildError`、`len`、`log.splitlines`、`lvalues.extend`、`lvalues.pop`、`nodes.append`、`pending.extend`、`pending.pop`、`re.match`、`re.search`、`set`、`stack.append`、`stack.pop` |
| `_frontend` — `_frontend(files, script, yosys, timeout_seconds, scratch_root, frontend_runner)` | function / [343](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L343) | `<dynamic>.decode`、`<dynamic>.hexdigest`、`<dynamic>.read_text`、`Path`、`PcBuildError`、`_json`、`evidence_path.write_text`、`executable_env`、`files.items`、`frontend_runner`、`hashlib.sha256`、`isinstance`、`json.loads`、`parsed.get`、`record.update`、`resolve_executable`、`s.encode`、`scratch_root.mkdir`、`str`、`subprocess.TimeoutExpired`、`subprocess.run`、`target.parent.mkdir`、`target.write_text`、`tempfile.mkdtemp` |
| `_parse_unit` — `_parse_unit(source, unit, yosys, timeout_seconds, scratch_root, frontend_runner)` | function / [393](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L393) | `<dynamic>.startswith`、`<dynamic>.values`、`PcBuildError`、`_frontend`、`_inspect_ast`、`any`、`bool`、`cell.get`、`expected.items`、`len`、`module.get`、`observed.get`、`parsed.get`、`set` |
| `compose_behavior` — `compose_behavior(build, bundle, yosys, timeout_seconds, scratch_root, behavior_origin, frontend_runner)` | function / [425](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L425) | `<dynamic>.hexdigest`、`<dynamic>.items`、`<dynamic>.join`、`<dynamic>.read_bytes`、`<dynamic>.resolve`、`<dynamic>.splitlines`、`<dynamic>.strip`、`<dynamic>.update`、`<dynamic>.values`、`<dynamic>.with_name`、`ComposedProject`、`Path`、`PcBuildError`、`ValueError`、`_body_tokens`、`_frontend`、`_json`、`_parse_unit`、`_sha`、`body.encode`、`body.splitlines`、`build.files.items`、`build.units.items`、`copy.deepcopy`、`dict`、`hashlib.sha256`、`isinstance`、`len`、`resolve_project_manifest`、`set`、`sorted`、`source.encode`、`text.encode` |
| `write_project` — `write_project(project, output_root)` | function / [496](../../../../agent/src/sr2fpga_agent/pc/emitter.py#L496) | `<dynamic>.is_relative_to`、`Path`、`PcBuildError`、`project.files.items`、`root.mkdir`、`root.resolve`、`sorted`、`stream.write`、`target.open`、`target.parent.mkdir`、`target.resolve`、`validate_project_relative_path` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.split`、`dataclass`、`re.compile`、`set`

## `agent/src/sr2fpga_agent/pc/expressions.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/expressions.py) · 77 行 · SHA-256 `40b7b541e53abef5f2040e0c9f5d222ab15c9f4deb641bc0c3729c6a0c55211d`

> Bounded natural-number AST evaluation; never interprets HDL or Python.

导入模块：`__future__`、`collections.abc`、`sr2fpga_agent.pc.semantics`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `natural` — `natural(value, path, positive)` | function / [13](../../../../agent/src/sr2fpga_agent/pc/expressions.py#L13) | `PcSemanticError`、`int`、`type` |
| `evaluate` — `evaluate(expression, parameters, path, max_depth)` | function / [20](../../../../agent/src/sr2fpga_agent/pc/expressions.py#L20) | `<dynamic>.bit_length`、`PcSemanticError`、`enumerate`、`evaluate`、`expression.get`、`isinstance`、`len`、`max`、`min`、`natural`、`set`、`type` |
| `bind_parameters` — `bind_parameters(declarations, values, parent, path)` | function / [63](../../../../agent/src/sr2fpga_agent/pc/expressions.py#L63) | `PcSemanticError`、`declarations.items`、`evaluate`、`natural`、`set` |

## `agent/src/sr2fpga_agent/pc/inputs.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/inputs.py) · 216 行 · SHA-256 `3700d06f0d1243e60b9ac38ccd8622a8eaf95ddc0611f19ae69e9144fd77d7d8`

> Strict input and trusted byte binding (plan v2.2 §4.1; architecture §6).

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.pc.semantics`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PcInputError` — `PcInputError` | class / [28](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L28) | 无直接调用 |
| `PcParseError` — `PcParseError` | class / [32](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L32) | 无直接调用 |
| `PcSchemaError` — `PcSchemaError` | class / [36](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L36) | 无直接调用 |
| `BindingError` — `BindingError` | class / [40](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L40) | 无直接调用 |
| `ParseLimits` — `ParseLimits` | class / [45](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L45) | 无直接调用 |
| `ParseLimits.__post_init__` — `__post_init__(self)` | function / [54](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L54) | `ValueError`、`type` |
| `TrustedSource` — `TrustedSource` | class / [61](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L61) | 无直接调用 |
| `TrustedSource.__post_init__` — `__post_init__(self)` | function / [67](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L67) | `TypeError`、`ValueError`、`isinstance`、`len`、`type` |
| `TrustedSource.reference` — `reference(self)` | function / [73](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L73) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `TrustedContext` — `TrustedContext` | class / [78](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L78) | 无直接调用 |
| `TrustedContext.__post_init__` — `__post_init__(self)` | function / [83](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L83) | `TypeError`、`all`、`isinstance` |
| `TrustedContext.bindings` — `bindings(self)` | function / [89](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L89) | `<dynamic>.reference`、`getattr` |
| `_reject_number` — `_reject_number(value)` | function / [95](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L95) | `PcParseError` |
| `_object` — `_object(pairs)` | function / [99](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L99) | `PcParseError` |
| `_parse` — `_parse(raw, limits)` | function / [108](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L108) | `PcParseError`、`TypeError`、`any`、`isinstance`、`json.loads`、`len`、`ord`、`pending.extend`、`pending.pop`、`raw.decode`、`type`、`value.keys`、`value.values` |
| `_validate` — `_validate(payload, key, registry)` | function / [159](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L159) | `<dynamic>.join`、`<dynamic>.validate`、`PcSchemaError`、`registry.load_schema` |
| `_validate_semantics` — `_validate_semantics(design)` | function / [165](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L165) | `validate_acyclic_modules`、`validate_entry_module`、`validate_instance_modules`、`validate_instance_parameter_names`、`validate_reachable_modules`、`validate_signature_sources` |
| `parse_design_proposal` — `parse_design_proposal(raw, limits, registry)` | function / [176](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L176) | `ContractRegistry`、`_parse`、`_validate` |
| `_validate_bound` — `_validate_bound(pc, context, registry)` | function / [184](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L184) | `BindingError`、`_validate`、`context.bindings`、`expected.items` |
| `assemble_project_contract` — `assemble_project_contract(raw_design, context, limits, registry)` | function / [193](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L193) | `ContractRegistry`、`_validate_bound`、`_validate_semantics`、`context.bindings`、`parse_design_proposal` |
| `parse_project_contract` — `parse_project_contract(raw, context, limits, registry)` | function / [209](../../../../agent/src/sr2fpga_agent/pc/inputs.py#L209) | `ContractRegistry`、`_parse`、`_validate_bound`、`_validate_semantics` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/pc/semantics.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/semantics.py) · 173 行 · SHA-256 `5065a0039411ad0c9d9c4b3985afe5bd519c8a4471234c89c3b196cc4462c663`

> Incremental PC 2.1 semantic checks after schema validation.

导入模块：`__future__`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `PcSemanticError` — `PcSemanticError` | class / [8](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L8) | 无直接调用 |
| `validate_entry_module` — `validate_entry_module(design)` | function / [12](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L12) | `PcSemanticError` |
| `validate_instance_modules` — `validate_instance_modules(design)` | function / [26](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L26) | `<dynamic>.items`、`PcSemanticError`、`modules.items` |
| `_child_module_names` — `_child_module_names(module)` | function / [47](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L47) | `<dynamic>.values`、`tuple` |
| `validate_acyclic_modules` — `validate_acyclic_modules(design)` | function / [58](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L58) | `<dynamic>.join`、`PcSemanticError`、`_child_module_names`、`active_positions.get`、`active_positions.pop`、`child_iterators.append`、`child_iterators.pop`、`completed.add`、`iter`、`len`、`next`、`path.append`、`path.pop`、`set` |
| `validate_reachable_modules` — `validate_reachable_modules(design)` | function / [100](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L100) | `<dynamic>.join`、`PcSemanticError`、`_child_module_names`、`pending.extend`、`pending.pop`、`reachable.add`、`set`、`sorted` |
| `validate_signature_sources` — `validate_signature_sources(design)` | function / [128](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L128) | `<dynamic>.items`、`PcSemanticError` |
| `validate_instance_parameter_names` — `validate_instance_parameter_names(design)` | function / [144](../../../../agent/src/sr2fpga_agent/pc/semantics.py#L144) | `<dynamic>.items`、`<dynamic>.join`、`PcSemanticError`、`modules.items`、`set`、`sorted` |

## `agent/src/sr2fpga_agent/pc/tensors.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/pc/tensors.py) · 208 行 · SHA-256 `0f26a71283ed704699aa9698fcae9205835fc6ad41e33d565388b4beb87276bb`

> Configuration-local tensor descriptors and finite declared relationships.

导入模块：`__future__`、`copy`、`math`、`sr2fpga_agent.pc.expressions`、`sr2fpga_agent.pc.semantics`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_require` — `_require(condition, path, message)` | function / [16](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L16) | `PcSemanticError` |
| `storage_range` — `storage_range(element)` | function / [21](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L21) | 无直接调用 |
| `resolve_tensor` — `resolve_tensor(contract, parameters, path, fact, max_elements, max_width)` | function / [28](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L28) | `_require`、`all`、`deepcopy`、`dict`、`enumerate`、`evaluate`、`fact`、`gcd`、`len`、`natural`、`set`、`sorted`、`storage_range`、`type` |
| `_equivalent` — `_equivalent(a, b, omit)` | function / [100](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L100) | `a.items`、`b.items` |
| `_zero_points` — `_zero_points(tensor)` | function / [105](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L105) | 无直接调用 |
| `check_tensor_rules` — `check_tensor_rules(implementation, ports, port_types, states, path, fact)` | function / [112](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L112) | `<dynamic>.items`、`<dynamic>.join`、`PcSemanticError`、`_equivalent`、`_require`、`_zero_points`、`all`、`bound_states.add`、`deepcopy`、`fact`、`implementation.get`、`len`、`obligations.append`、`port_types.items`、`qa.pop`、`qb.pop`、`rule.get`、`set`、`sorted`、`states.items`、`storage_range`、`tensor`、`tuple`、`used.intersection`、`used.update` |
| `check_tensor_rules.tensor` — `tensor(name, direction, rule_path)` | function / [119](../../../../agent/src/sr2fpga_agent/pc/tensors.py#L119) | `_require` |
