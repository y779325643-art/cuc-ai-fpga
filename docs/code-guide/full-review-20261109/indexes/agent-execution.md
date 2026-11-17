# agent-execution：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/execution/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/__init__.py) · 1 行 · SHA-256 `09a706085e13078875a9f3933e019b63339b9f6ebdbb5ad02a2f142522e2c8c6`

> Current PC 2.1 generation infrastructure; execution requires explicit scope.

导入模块：无显式 import

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/execution/__main__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/__main__.py) · 41 行 · SHA-256 `7ed3402a61a4333c9f80b0159c6c989f74402460008a0c3fe05a01dfd1b0a35d`

> Current PC 2.1 preflight and explicitly scoped development/replay execution.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`sr2fpga_agent.execution.integration`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `main` — `main(argv)` | function / [11](../../../../agent/src/sr2fpga_agent/execution/__main__.py#L11) | `any`、`argparse.ArgumentParser`、`args.output.resolve`、`commands.add_parser`、`inspect.add_argument`、`int`、`json.dumps`、`load_json`、`parser.add_subparsers`、`parser.exit`、`parser.parse_args`、`preflight`、`print`、`run.add_argument`、`run_development`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`main`

## `agent/src/sr2fpga_agent/execution/budgets.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/budgets.py) · 494 行 · SHA-256 `d3c0ed6c53a0200d8f3dfed0ee58d8fdeb2e7b064c6cb8e1c4d705a157750712`

> Persistent PC 2.1 resource reservations and shared-method cost attribution.

导入模块：`__future__`、`contextlib`、`dataclasses`、`fcntl`、`hashlib`、`json`、`math`、`msvcrt`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.models`、`threading`、`types`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `BudgetError` — `BudgetError` | class / [48](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L48) | 无直接调用 |
| `BudgetExceeded` — `BudgetExceeded` | class / [52](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L52) | 无直接调用 |
| `BudgetBusy` — `BudgetBusy` | class / [56](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L56) | 无直接调用 |
| `_number` — `_number(value, axis)` | function / [60](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L60) | `ValueError`、`math.isfinite`、`type` |
| `BudgetLimits` — `BudgetLimits` | class / [70](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L70) | 无直接调用 |
| `BudgetLimits.__post_init__` — `__post_init__(self)` | function / [85](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L85) | `RESOURCE_LIMITS.items`、`ValueError`、`_number`、`fields`、`getattr`、`reverse.get` |
| `BudgetLimits.from_dict` — `from_dict(cls, payload)` | function / [94](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L94) | `ValueError`、`cls`、`dict`、`fields`、`set` |
| `BudgetLimits.for_method` — `for_method(cls, method, **limits)` | function / [100](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L100) | `ValueError`、`cls`、`limits.setdefault` |
| `BudgetLimits.to_dict` — `to_dict(self)` | function / [108](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L108) | `asdict` |
| `Reservation` — `Reservation` | class / [113](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L113) | 无直接调用 |
| `Reservation.to_dict` — `to_dict(self)` | function / [122](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L122) | `dict`、`list` |
| `BudgetLedger` — `BudgetLedger` | class / [129](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L129) | 无直接调用 |
| `BudgetLedger.__init__` — `__init__(self, store, stream_id, limits, budget_policy_id)` | function / [138](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L138) | `<dynamic>.hexdigest`、`BudgetError`、`MappingProxyType`、`Path`、`TypeError`、`ValueError`、`any`、`canonical_json_bytes`、`hashlib.sha256`、`isinstance`、`item.to_dict`、`limits.items`、`normalized.items`、`self._locked`、`self._replay`、`sorted`、`store.put_blob`、`store.read_verified`、`store.reference`、`stream_id.encode` |
| `BudgetLedger._locked` — `_locked(self)` | function / [177](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L177) | `<dynamic>.casefold`、`BudgetBusy`、`_THREAD_LOCKS.setdefault`、`__import__`、`fcntl.flock`、`handle.close`、`handle.fileno`、`handle.flush`、`handle.seek`、`handle.tell`、`handle.write`、`lock.acquire`、`lock.release`、`msvcrt.locking`、`self._lock_path.open`、`self._lock_path.parent.mkdir`、`self._lock_path.resolve`、`str`、`threading.Lock` |
| `BudgetLedger._replay` — `_replay(self)` | function / [216](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L216) | `<dynamic>.hexdigest`、`ArtifactIntegrityError`、`canonical_json_bytes`、`enumerate`、`event.get`、`event.items`、`hashlib.sha256`、`json.loads`、`payload.get`、`self._is_usage_refinement`、`self.store.event_refs`、`self.store.read_verified`、`self.store.reference` |
| `BudgetLedger._event` — `_event(self, kind, payload)` | function / [259](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L259) | `self.store.append_event` |
| `BudgetLedger._reservation_id` — `_reservation_id(self, operation_id)` | function / [262](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L262) | `<dynamic>.hexdigest`、`ValueError`、`canonical_json_bytes`、`hashlib.sha256`、`isinstance` |
| `BudgetLedger._view` — `_view(item)` | function / [268](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L268) | `MappingProxyType`、`Reservation`、`dict`、`tuple` |
| `BudgetLedger._is_usage_refinement` — `_is_usage_refinement(item, payload)` | function / [274](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L274) | `all`、`any`、`before.items`、`payload.get`、`set` |
| `BudgetLedger.reserve` — `reserve(self, operation_id, consumers, model_calls, input_tokens, output_tokens, context_tokens, public_tool_calls, public_cycles, final_public_tool_calls, hidden_tool_calls, active_seconds, eda_seconds, cpu_seconds, memory_bytes, token_reservation_kind, metadata)` | function / [284](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L284) | `<dynamic>.get`、`BudgetError`、`BudgetExceeded`、`ValueError`、`_number`、`any`、`canonical_json_bytes`、`dict`、`getattr`、`isinstance`、`json.dumps`、`json.loads`、`len`、`max`、`record.items`、`resources.items`、`resources.values`、`self._event`、`self._locked`、`self._replay`、`self._reservation_id`、`self._summarize`、`self._view`、`set`、`sorted`、`source.strip` |
| `BudgetLedger.dispatch` — `dispatch(self, reservation_id)` | function / [348](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L348) | `BudgetError`、`self._event`、`self._item`、`self._locked`、`self._replay`、`self._view` |
| `BudgetLedger.cancel` — `cancel(self, reservation_id, reason)` | function / [358](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L358) | `BudgetError`、`ValueError`、`isinstance`、`item.get`、`self._event`、`self._item`、`self._locked`、`self._replay`、`self._view` |
| `BudgetLedger.reconcile` — `reconcile(self, reservation_id, observed, outcome, unavailable_reasons)` | function / [371](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L371) | `<dynamic>.items`、`BudgetError`、`ValueError`、`_number`、`any`、`dict`、`isinstance`、`observed.items`、`reasons.pop`、`reasons.setdefault`、`reasons.values`、`self._event`、`self._is_usage_refinement`、`self._item`、`self._locked`、`self._replay`、`self._view`、`set` |
| `BudgetLedger._item` — `_item(items, reservation_id)` | function / [426](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L426) | `BudgetError` |
| `BudgetLedger._summarize` — `_summarize(self, items)` | function / [431](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L431) | `<dynamic>.append`、`<dynamic>.get`、`<dynamic>.items`、`<dynamic>.setdefault`、`RESOURCE_LIMITS.items`、`dict`、`empty`、`getattr`、`items.items`、`items.values`、`limit.to_dict`、`max`、`methods.items`、`methods.values` |
| `BudgetLedger._summarize.empty` — `empty()` | function / [432](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L432) | 无直接调用 |
| `BudgetLedger.snapshot` — `snapshot(self)` | function / [487](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L487) | `self._locked`、`self._replay`、`self._summarize` |
| `BudgetLedger.remaining` — `remaining(self, method, axis)` | function / [491](../../../../agent/src/sr2fpga_agent/execution/budgets.py#L491) | `ValueError`、`self.snapshot` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`frozenset`、`threading.Lock`

## `agent/src/sr2fpga_agent/execution/development.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/development.py) · 40 行 · SHA-256 `d2e6efb9cf10f651f1e4761d15a6d6644b4f4baba55db97ac6f3a9d27cd69f30`

> Explicitly synthetic terminal suites for integration tests, never formal hidden.

导入模块：`hashlib`、`importlib`、`pathlib`、`random`、`sr2fpga_agent.execution.evaluation`、`sr2fpga_agent.models`、`sr2fpga_agent.tasks.llm`、`sr2fpga_agent.tasks.llm_attention.oracle`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `terminal_suites` — `terminal_suites(public_tasks)` | function / [16](../../../../agent/src/sr2fpga_agent/execution/development.py#L16) | `<dynamic>.hexdigest`、`<dynamic>.parent.glob`、`DecodeInput`、`Path`、`TrustedSuite`、`canonical_json_bytes`、`import_module`、`path.read_bytes`、`path.resolve`、`random.Random`、`range`、`rng.randrange`、`sha256`、`sorted`、`sources.items`、`str`、`tuple` |
| `terminal_suites.render` — `render(module, values)` | function / [28](../../../../agent/src/sr2fpga_agent/execution/development.py#L28) | `module.render_testbench` |
| `terminal_suites.render` — `render(module, values)` | function / [33](../../../../agent/src/sr2fpga_agent/execution/development.py#L33) | `module.render_testbench` |

## `agent/src/sr2fpga_agent/execution/evaluation.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/evaluation.py) · 669 行 · SHA-256 `9320f9053cfbbb31525086ac21e71372785d499b2aac389c5a0afece169d88d2`

> PC-neutral public evaluation and durable, evaluator-private terminal slots.

导入模块：`__future__`、`contextlib`、`dataclasses`、`hashlib`、`importlib`、`json`、`pathlib`、`re`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.execution.isolation`、`sr2fpga_agent.execution.locking`、`sr2fpga_agent.execution.public_feedback`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.pc.expressions`、`sr2fpga_agent.pc.inputs`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_sha` — `_sha(value)` | function / [42](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L42) | `<dynamic>.hexdigest`、`canonical_json_bytes`、`hashlib.sha256` |
| `task_identity` — `task_identity(task)` | function / [46](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L46) | `_sha`、`task.sources.bindings` |
| `EvaluationIntegrityError` — `EvaluationIntegrityError` | class / [50](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L50) | 无直接调用 |
| `_verify_public_task` — `_verify_public_task(task)` | function / [54](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L54) | `<dynamic>.hexdigest`、`EvaluationIntegrityError`、`ParseLimits`、`_parse`、`getattr`、`hashlib.sha256`、`len`、`max`、`set` |
| `assert_supported_case` — `assert_supported_case(case, task)` | function / [69](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L69) | `<dynamic>.build_development_task`、`ValueError`、`_verify_public_task`、`import_module` |
| `TrustedSuite` — `TrustedSuite` | class / [94](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L94) | `field` |
| `TrustedSuite.__post_init__` — `__post_init__(self)` | function / [104](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L104) | `<dynamic>.hexdigest`、`EvaluationIntegrityError`、`Path`、`ValueError`、`_sha`、`hashlib.sha256`、`isinstance`、`object.__setattr__`、`re.fullmatch`、`rendered.encode`、`self.render`、`self.verify` |
| `TrustedSuite.verify` — `verify(self)` | function / [123](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L123) | `<dynamic>.hexdigest`、`<dynamic>.read_bytes`、`EvaluationIntegrityError`、`Path`、`hashlib.sha256`、`isinstance`、`rendered.encode`、`self.render` |
| `TrustedSuite.for_development_case` — `for_development_case(cls, case)` | function / [136](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L136) | `<dynamic>.hexdigest`、`Path`、`ValueError`、`_sha`、`case_root.glob`、`cls`、`hashlib.sha256`、`import_module`、`path.read_bytes`、`path.resolve`、`sorted`、`str`、`tuple` |
| `EvaluationResult` — `EvaluationResult` | class / [150](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L150) | `field` |
| `EvaluationResult.__post_init__` — `__post_init__(self)` | function / [164](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L164) | `ValueError`、`any`、`object.__setattr__`、`self.stages.values`、`set`、`validate_diagnostics` |
| `EvaluationResult.accepted` — `accepted(self)` | function / [183](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L183) | 无直接调用 |
| `EvaluationResult.public_feedback` — `public_feedback(self)` | function / [186](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L186) | `<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`PermissionError`、`ValueError`、`dict`、`list`、`validate_diagnostics` |
| `EvaluationResult.to_dict` — `to_dict(self, include_private)` | function / [200](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L200) | `asdict`、`value.pop` |
| `_type_width` — `_type_width(value, parameters, tensors)` | function / [211](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L211) | `_type_width`、`evaluate`、`sum` |
| `expected_public_abi` — `expected_public_abi(task)` | function / [222](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L222) | `<dynamic>.items`、`<dynamic>.values`、`ValueError`、`_type_width`、`mapping.items`、`mapping.values`、`re.fullmatch`、`signature.get` |
| `Pc21Evaluator` — `Pc21Evaluator` | class / [250](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L250) | 无直接调用 |
| `Pc21Evaluator.__init__` — `__init__(self, case, public_task, evaluator_root, backend, tool_budget, synthesize, suite, limits)` | function / [253](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L253) | `<dynamic>.resolve`、`ArtifactStore`、`LocalDevelopmentBackend`、`Path`、`ToolLimits`、`TrustedSuite.for_development_case`、`ValueError`、`_verify_public_task`、`assert_supported_case`、`self._tool_policy_identity`、`self.root.mkdir`、`task_identity` |
| `Pc21Evaluator._tool_policy_identity` — `_tool_policy_identity(self)` | function / [272](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L272) | `_sha`、`asdict`、`self.backend.policy` |
| `Pc21Evaluator._run` — `_run(self, command, work, stage, visibility, candidate_files)` | function / [277](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L277) | `EvaluationIntegrityError`、`_verify_public_task`、`execute`、`self._tool_policy_identity`、`self.suite.verify`、`self.tool_budget`、`task_identity`、`verify_candidate` |
| `Pc21Evaluator._run.execute` — `execute()` | function / [283](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L283) | `self.backend.run` |
| `Pc21Evaluator._run.verify_candidate` — `verify_candidate()` | function / [285](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L285) | `EvaluationIntegrityError`、`candidate_files.items`、`expected.encode`、`target.is_file`、`target.is_symlink`、`target.read_bytes` |
| `Pc21Evaluator.evaluate` — `evaluate(self, files, evaluation_id, visibility)` | function / [296](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L296) | `<dynamic>.append`、`<dynamic>.hexdigest`、`<dynamic>.join`、`<dynamic>.read_text`、`<dynamic>.write_text`、`CandidateBoundaryError`、`EvaluationIntegrityError`、`EvaluationResult`、`GeneratedProject`、`ValueError`、`_ToolInfrastructureError`、`_verify_public_task`、`any`、`asdict`、`bool`、`candidate_sha256`、`canonical_json_bytes`、`check_project_package_l0`、`diagnostics.append`、`dict.fromkeys`、`evaluation_id.encode`、`expected_public_abi`、`files.items`、`functional_diagnostics`、`hasattr`、`hashlib.sha256`、`json.loads`、`len`、`list`、`manifest.source_languages.values`、`physical_ports.items`、`ports.items`、`private.update`、`public_diagnostics.extend`、`re.fullmatch`、`ref.to_dict`、`resolve_project_manifest`、`self._require_tool`、`self._run`、`self._tool_policy_identity`、`self.store.append_event`、`self.store.put_blob`、`self.suite.check`、`self.suite.verify`、`set`、`source_diagnostics`、`str`、`stream.write`、`target.open`、`target.parent.mkdir`、`task_identity`、`tuple`、`type`、`validate_candidate_sources`、`validate_project_relative_path`、`work.mkdir` |
| `Pc21Evaluator._require_tool` — `_require_tool(result, diagnostics, failure_code)` | function / [430](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L430) | `CandidateBoundaryError`、`_ToolInfrastructureError`、`diagnostics.append` |
| `_ToolInfrastructureError` — `_ToolInfrastructureError` | class / [443](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L443) | 无直接调用 |
| `TerminalEvaluationAuthority` — `TerminalEvaluationAuthority` | class / [447](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L447) | 无直接调用 |
| `TerminalEvaluationAuthority.__init__` — `__init__(self, private_root, planned_slots, max_infrastructure_retries)` | function / [454](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L454) | `<dynamic>.resolve`、`ArtifactStore`、`Path`、`ValueError`、`canonical_json_bytes`、`len`、`self._identity`、`self._key`、`self.root.mkdir`、`self.store.put_blob`、`type` |
| `TerminalEvaluationAuthority._identity` — `_identity(slot)` | function / [469](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L469) | `ValueError`、`any`、`identity.values`、`isinstance`、`range`、`str` |
| `TerminalEvaluationAuthority._key` — `_key(cls, slot)` | function / [477](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L477) | `_sha`、`cls._identity` |
| `TerminalEvaluationAuthority._lock` — `_lock(self)` | function / [481](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L481) | `file_lock` |
| `TerminalEvaluationAuthority.seal_terminal` — `seal_terminal(self, slot, files, task_sha256, suite_sha256, tool_policy_sha256, reason)` | function / [486](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L486) | `ValueError`、`candidate_sha256`、`canonical_json_bytes`、`re.fullmatch`、`self._key`、`self._lock`、`self.store.put_blob`、`self.store.reference` |
| `TerminalEvaluationAuthority.close_barrier` — `close_barrier(self)` | function / [507](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L507) | `ValueError`、`any`、`canonical_json_bytes`、`len`、`refs.items`、`refs.values`、`self._lock`、`self.store.put_blob`、`self.store.reference` |
| `TerminalEvaluationAuthority.close_without_execution` — `close_without_execution(self, slot, reason)` | function / [517](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L517) | `IsolationUnavailable`、`PermissionError`、`ValueError`、`candidate_sha256`、`canonical_json_bytes`、`isinstance`、`json.loads`、`len`、`previous.get`、`self._key`、`self._lock`、`self._receipt`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference` |
| `TerminalEvaluationAuthority.evaluate_once` — `evaluate_once(self, slot, evaluator)` | function / [543](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L543) | `EvaluationResult`、`IsolationUnavailable`、`PermissionError`、`ValueError`、`candidate_sha256`、`canonical_json_bytes`、`evaluator`、`history.append`、`int`、`json.loads`、`len`、`range`、`result.to_dict`、`self._key`、`self._lock`、`self._receipt`、`self.store.consume_once`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference` |
| `TerminalEvaluationAuthority._receipt` — `_receipt(self, key)` | function / [605](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L605) | `self.analysis_result`、`self.store.reference` |
| `TerminalEvaluationAuthority.analysis_result` — `analysis_result(self, slot)` | function / [611](../../../../agent/src/sr2fpga_agent/execution/evaluation.py#L611) | `EvaluationResult`、`PermissionError`、`ValueError`、`any`、`candidate_sha256`、`executions.append`、`expected_seals.items`、`int`、`json.loads`、`range`、`self._key`、`self.store.read_verified`、`self.store.reference`、`set`、`type` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/execution/gateway.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/gateway.py) · 379 行 · SHA-256 `c3f638b1bc60417bfb2809a220dce197e835cd0b44ba1d2af0831f22eb271ff1`

> Text-only model gateway with durable, per-operation budget transactions.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`os`、`pathlib`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.execution.budgets`、`sr2fpga_agent.execution.integration`、`sr2fpga_agent.execution.prompt_guidance`、`sr2fpga_agent.execution.public_interfaces`、`sr2fpga_agent.models`、`sr2fpga_agent.providers`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ModelResponse` — `ModelResponse` | class / [24](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L24) | 无直接调用 |
| `TextTransport` — `TextTransport` | class / [34](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L34) | 无直接调用 |
| `TextTransport.count_input_tokens` — `count_input_tokens(self, messages)` | function / [39](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L39) | 无直接调用 |
| `TextTransport.generate` — `generate(self, messages, stage, max_output_tokens, timeout_seconds)` | function / [40](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L40) | 无直接调用 |
| `ModelStageFailure` — `ModelStageFailure` | class / [44](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L44) | 无直接调用 |
| `ModelStageFailure.__init__` — `__init__(self, reason, response)` | function / [45](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L45) | `<dynamic>.__init__`、`super` |
| `ReplayTransport` — `ReplayTransport` | class / [50](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L50) | 无直接调用 |
| `ReplayTransport.__init__` — `__init__(self, responses)` | function / [60](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L60) | `list`、`responses.items` |
| `ReplayTransport.prime_consumed` — `prime_consumed(self, counts)` | function / [65](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L65) | `ValueError`、`counts.items`、`len`、`self.responses.get`、`type` |
| `ReplayTransport.count_input_tokens` — `count_input_tokens(self, messages)` | function / [76](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L76) | `canonical_json_bytes`、`len` |
| `ReplayTransport.generate` — `generate(self, messages, stage, max_output_tokens, timeout_seconds)` | function / [79](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L79) | `<dynamic>.pop`、`ModelResponse`、`entry.encode`、`entry.get`、`isinstance`、`json.dumps`、`json.loads`、`len`、`self.count_input_tokens`、`self.requests.append`、`self.responses.get`、`str` |
| `ClientTransport` — `ClientTransport` | class / [96](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L96) | 无直接调用 |
| `ClientTransport.__init__` — `__init__(self, client, input_counter, tokenizer_id)` | function / [106](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L106) | `ValueError`、`callable` |
| `ClientTransport.count_input_tokens` — `count_input_tokens(self, messages)` | function / [112](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L112) | `ValueError`、`self.input_counter`、`type` |
| `ClientTransport.public_identity` — `public_identity(self)` | function / [118](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L118) | `<dynamic>.encode`、`<dynamic>.hexdigest`、`getattr`、`hasattr`、`hashlib.sha256`、`str` |
| `ClientTransport.generate` — `generate(self, messages, stage, max_output_tokens, timeout_seconds)` | function / [125](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L125) | `<dynamic>`、`ModelResponse`、`client.chat`、`client.consume_response_provenance`、`client.consume_token_usage`、`client.consume_transport_attempt_count`、`getattr`、`replace`、`type`、`usage.get` |
| `ProviderCapacityTransport` — `ProviderCapacityTransport` | class / [146](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L146) | 无直接调用 |
| `ProviderCapacityTransport.__init__` — `__init__(self, client, input_token_bound, context_capacity, output_capacity, capacity_source)` | function / [154](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L154) | `ValueError`、`any`、`capacity_source.strip`、`isinstance`、`type` |
| `ProviderCapacityTransport.count_input_tokens` — `count_input_tokens(self, messages)` | function / [168](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L168) | 无直接调用 |
| `ProviderCapacityTransport.input_accounting` — `input_accounting(self)` | function / [173](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L173) | 无直接调用 |
| `ProviderCapacityTransport.public_identity` — `public_identity(self)` | function / [179](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L179) | `<dynamic>.public_identity`、`self.input_accounting`、`super` |
| `ProviderCapacityTransport.usage_exceeds_capacity` — `usage_exceeds_capacity(self, response, output_bound)` | function / [182](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L182) | 无直接调用 |
| `_provider_client` — `_provider_client(settings)` | function / [189](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L189) | `OpenAICompatibleClient`、`OpenAICompatibleConfig`、`ValueError`、`os.environ.get`、`settings.get` |
| `create_provider_transport` — `create_provider_transport(settings)` | function / [201](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L201) | `<dynamic>`、`ClientTransport`、`ValueError`、`_provider_client`、`load_callable`、`set` |
| `create_provider_capacity_transport` — `create_provider_capacity_transport(settings)` | function / [218](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L218) | `ProviderCapacityTransport`、`ValueError`、`_provider_client`、`set` |
| `ModelGateway` — `ModelGateway` | class / [229](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L229) | 无直接调用 |
| `ModelGateway.__init__` — `__init__(self, store, ledger, transport, allow_model_calls, max_call_seconds)` | function / [230](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L230) | `Path`、`ValueError`、`counts.get`、`directory.glob`、`isinstance`、`json.loads`、`store.read_verified`、`transport.prime_consumed` |
| `ModelGateway.call` — `call(self, operation_id, stage, consumers, public_payload, output_format)` | function / [247](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L247) | `<dynamic>.decode`、`<dynamic>.hexdigest`、`<dynamic>.values`、`ModelResponse`、`ModelStageFailure`、`PermissionError`、`any`、`canonical_json_bytes`、`dict`、`float`、`hashlib.sha256`、`indexed_public_payload`、`int`、`isinstance`、`json.loads`、`list`、`metadata.update`、`min`、`next`、`operation_id.encode`、`payload.get`、`replace`、`self._reconcile_record`、`self._restore`、`self.ledger.dispatch`、`self.ledger.reconcile`、`self.ledger.remaining`、`self.ledger.reserve`、`self.ledger.snapshot`、`self.store.append_event`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference`、`self.transport.count_input_tokens`、`self.transport.generate`、`self.transport.input_accounting`、`self.transport.public_identity`、`self.transport.usage_exceeds_capacity`、`time.monotonic`、`type`、`values.items` |
| `ModelGateway._reconcile_record` — `_reconcile_record(self, payload)` | function / [367](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L367) | `self.ledger.reconcile` |
| `ModelGateway._restore` — `_restore(payload)` | function / [373](../../../../agent/src/sr2fpga_agent/execution/gateway.py#L373) | `ModelResponse`、`ModelStageFailure`、`payload.get`、`response.text.strip` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/execution/integration.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/integration.py) · 270 行 · SHA-256 `9b90559e0251413dc72f88a70b5e3a42d6bde280b7cf5c184e56100abc0eea76`

> Operator-selected public inputs, development preflight and verified analysis views.

导入模块：`__future__`、`dataclasses`、`importlib`、`json`、`pathlib`、`sr2fpga_agent.analysis`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.execution.budgets`、`sr2fpga_agent.execution.evaluation`、`sr2fpga_agent.execution.gateway`、`sr2fpga_agent.execution.isolation`、`sr2fpga_agent.execution.runtime`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.models`、`sr2fpga_agent.pc.context`、`sr2fpga_agent.pc.inputs`、`sr2fpga_agent.repository_paths`、`sr2fpga_agent.tasks.llm`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `load_json` — `load_json(path)` | function / [28](../../../../agent/src/sr2fpga_agent/execution/integration.py#L28) | `<dynamic>.open`、`Path`、`ValueError`、`json.loads`、`len`、`stream.read` |
| `load_json.pairs` — `pairs(items)` | function / [29](../../../../agent/src/sr2fpga_agent/execution/integration.py#L29) | `ValueError` |
| `load_json.nonfinite` — `nonfinite(value)` | function / [36](../../../../agent/src/sr2fpga_agent/execution/integration.py#L36) | `ValueError` |
| `validate_document` — `validate_document(key, value)` | function / [45](../../../../agent/src/sr2fpga_agent/execution/integration.py#L45) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.validate`、`ContractRegistry`、`ValueError` |
| `load_public_directory` — `load_public_directory(directory)` | function / [51](../../../../agent/src/sr2fpga_agent/execution/integration.py#L51) | `<dynamic>.read_bytes`、`<dynamic>.resolve`、`ParseLimits`、`Path`、`TrustedContext`、`TrustedSource`、`load_public_task` |
| `configured_limits` — `configured_limits(values, final)` | function / [60](../../../../agent/src/sr2fpga_agent/execution/integration.py#L60) | `BudgetLimits.for_method` |
| `load_callable` — `load_callable(spec)` | function / [65](../../../../agent/src/sr2fpga_agent/execution/integration.py#L65) | `ValueError`、`all`、`callable`、`getattr`、`importlib.import_module`、`module.split`、`name.isidentifier`、`part.isidentifier`、`spec.partition` |
| `backend_from_config` — `backend_from_config(config)` | function / [75](../../../../agent/src/sr2fpga_agent/execution/integration.py#L75) | `DockerBackend`、`LocalDevelopmentBackend`、`config.get` |
| `preflight` — `preflight(config, formal)` | function / [81](../../../../agent/src/sr2fpga_agent/execution/integration.py#L81) | `Path`、`ToolLimits`、`ValueError`、`any`、`assert_supported_case`、`backend.available`、`backend.policy`、`backend_from_config`、`configured_limits`、`isinstance`、`load_json`、`load_public_directory`、`public.sources.bindings`、`reasons.append`、`reasons.extend`、`reject_literal_credentials`、`resolve_executable`、`validate_document` |
| `preflight.reject_literal_credentials` — `reject_literal_credentials(value)` | function / [83](../../../../agent/src/sr2fpga_agent/execution/integration.py#L83) | `<dynamic>.lower`、`ValueError`、`any`、`isinstance`、`reject_literal_credentials`、`str`、`value.values` |
| `_write_new` — `_write_new(path, value, contract_key)` | function / [120](../../../../agent/src/sr2fpga_agent/execution/integration.py#L120) | `ValueError`、`canonical_json_bytes`、`path.exists`、`path.open`、`path.parent.mkdir`、`path.read_bytes`、`stream.write`、`validate_document` |
| `run_development` — `run_development(configs, output, allow_model_calls, terminal_suite_factory)` | function / [133](../../../../agent/src/sr2fpga_agent/execution/integration.py#L133) | `<dynamic>`、`<dynamic>.get`、`<dynamic>.items`、`<dynamic>.join`、`<dynamic>.resolve`、`ArtifactStore`、`PairedBlockRuntime`、`Path`、`ReplayTransport`、`RepositoryPaths.discover`、`RuntimeIdentity`、`ToolLimits`、`ValueError`、`_write_new`、`backend.qualify`、`backend_from_config`、`binding_records.append`、`block.generate`、`blocks.append`、`bool`、`canonical_json_bytes`、`canonical_sha256`、`configured_limits`、`dict`、`enumerate`、`export_analysis_views`、`finalize_batch`、`isinstance`、`json.loads`、`len`、`load_callable`、`load_json`、`load_public_directory`、`preflight`、`root.is_relative_to`、`root.mkdir`、`run_store.put_blob`、`run_store.read_verified`、`run_store.reference`、`runtime_source_snapshot`、`sorted`、`sum`、`validate_document`、`zip` |
| `export_analysis_views` — `export_analysis_views(blocks, final, output)` | function / [215](../../../../agent/src/sr2fpga_agent/execution/integration.py#L215) | `<dynamic>.read_verified`、`<dynamic>.reference`、`<dynamic>.snapshot`、`ArtifactStore`、`BudgetLedger`、`EvaluationResult`、`RuntimeIntegrityError`、`TerminalEvaluationAuthority`、`ValueError`、`_runtime_hash`、`_write_new`、`asdict`、`authority._key`、`authority.analysis_result`、`authority.store.read_verified`、`authority.store.reference`、`block.generate`、`block.identity.slot`、`block.store.read_verified`、`candidate_sha256`、`canonical_sha256`、`evidence.public_feedback`、`evidence.to_dict`、`final.get`、`json.loads`、`raw.get`、`results.append`、`slots.append`、`task_identity`、`terminal_value` |

## `agent/src/sr2fpga_agent/execution/isolation.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/isolation.py) · 281 行 · SHA-256 `a991625151fdbcc6c61c1c077ce12fc5bfa21fceb916d1a9ef447a0296de0b91`

> Explicit public projection, candidate admission and bounded tool isolation.

导入模块：`__future__`、`dataclasses`、`hashlib`、`json`、`math`、`os`、`pathlib`、`re`、`shlex`、`shutil`、`signal`、`sr2fpga_agent.local_tools`、`sr2fpga_agent.models`、`sr2fpga_agent.path_safety`、`subprocess`、`time`、`typing`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `IsolationUnavailable` — `IsolationUnavailable` | class / [30](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L30) | 无直接调用 |
| `CandidateBoundaryError` — `CandidateBoundaryError` | class / [34](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L34) | 无直接调用 |
| `ToolLimits` — `ToolLimits` | class / [39](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L39) | 无直接调用 |
| `ToolLimits.__post_init__` — `__post_init__(self)` | function / [47](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L47) | `ValueError`、`getattr`、`isinstance`、`math.isfinite`、`type` |
| `public_task_projection` — `public_task_projection(task)` | function / [57](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L57) | `<dynamic>.decode`、`canonical_json_bytes`、`json.loads` |
| `candidate_sha256` — `candidate_sha256(files)` | function / [74](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L74) | `<dynamic>.hexdigest`、`canonical_json_bytes`、`hashlib.sha256` |
| `_hdl_tokens` — `_hdl_tokens(text)` | function / [78](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L78) | `<dynamic>.isalnum`、`<dynamic>.isalpha`、`<dynamic>.isspace`、`CandidateBoundaryError`、`len`、`text.find`、`text.startswith`、`tokens.append` |
| `validate_candidate_sources` — `validate_candidate_sources(files)` | function / [107](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L107) | `<dynamic>.suffix.lower`、`CandidateBoundaryError`、`Path`、`_hdl_tokens`、`any`、`enumerate`、`files.items`、`folded.add`、`isinstance`、`path.casefold`、`path.startswith`、`set`、`token.startswith`、`validate_project_relative_path` |
| `_safe_environment` — `_safe_environment()` | function / [135](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L135) | `executable_env`、`host.items`、`key.upper` |
| `_run_process` — `_run_process(command, cwd, stage, limits, env)` | function / [141](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L141) | `ToolResult`、`ValueError`、`_safe_environment`、`bounded`、`os.killpg`、`process.kill`、`process.wait`、`re.fullmatch`、`stderr_path.open`、`stderr_path.stat`、`stdout_path.open`、`stdout_path.stat`、`str`、`subprocess.Popen`、`subprocess.run`、`time.monotonic` |
| `_run_process.bounded` — `bounded(path)` | function / [170](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L170) | `<dynamic>.decode`、`path.open`、`stream.read` |
| `LocalDevelopmentBackend` — `LocalDevelopmentBackend` | class / [179](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L179) | 无直接调用 |
| `LocalDevelopmentBackend.policy` — `policy(self)` | function / [183](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L183) | 无直接调用 |
| `LocalDevelopmentBackend.run` — `run(self, command, cwd, stage, limits)` | function / [187](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L187) | `_run_process`、`resolve_executable`、`str` |
| `DockerBackend` — `DockerBackend` | class / [193](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L193) | 无直接调用 |
| `DockerBackend.__init__` — `__init__(self, image, user, docker, endpoint)` | function / [201](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L201) | `ValueError`、`any`、`char.isspace`、`endpoint.startswith`、`re.fullmatch` |
| `DockerBackend._client` — `_client(self)` | function / [214](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L214) | 无直接调用 |
| `DockerBackend.policy` — `policy(self)` | function / [217](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L217) | 无直接调用 |
| `DockerBackend.available` — `available(self)` | function / [222](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L222) | `self._client`、`shutil.which`、`subprocess.run`、`system.stdout.strip` |
| `DockerBackend.command` — `command(self, command, cwd, limits, name)` | function / [234](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L234) | `<dynamic>.exists`、`CandidateBoundaryError`、`any`、`cwd.resolve`、`path.is_symlink`、`self._client`、`str`、`work.rglob` |
| `DockerBackend.qualify` — `qualify(self, workspace)` | function / [249](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L249) | `<dynamic>.is_file`、`<dynamic>.lstrip`、`<dynamic>.read_text`、`IsolationUnavailable`、`ToolLimits`、`_run_process`、`outside.as_posix`、`outside.open`、`self.available`、`self.command`、`shlex.quote`、`stream.write`、`uuid.uuid4`、`workspace.mkdir` |
| `DockerBackend.run` — `run(self, command, cwd, stage, limits)` | function / [271](../../../../agent/src/sr2fpga_agent/execution/isolation.py#L271) | `CandidateBoundaryError`、`IsolationUnavailable`、`_run_process`、`self._client`、`self.command`、`subprocess.run`、`uuid.uuid4` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`

## `agent/src/sr2fpga_agent/execution/locking.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/locking.py) · 57 行 · SHA-256 `3bbd23f857e0888207732967ee7256fda6d30108533fc300346f36eae3292c0a`

> Nonblocking thread/process locks released by the OS on process termination.

导入模块：`contextlib`、`fcntl`、`msvcrt`、`os`、`pathlib`、`threading`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RuntimeLockBusy` — `RuntimeLockBusy` | class / [8](../../../../agent/src/sr2fpga_agent/execution/locking.py#L8) | 无直接调用 |
| `file_lock` — `file_lock(path)` | function / [17](../../../../agent/src/sr2fpga_agent/execution/locking.py#L17) | `<dynamic>.resolve`、`Path`、`RuntimeLockBusy`、`_LOCKS.setdefault`、`fcntl.flock`、`handle.close`、`handle.fileno`、`handle.flush`、`handle.seek`、`handle.write`、`lock.acquire`、`lock.release`、`msvcrt.locking`、`path.open`、`path.parent.mkdir`、`path.stat`、`str`、`threading.Lock` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`threading.Lock`

## `agent/src/sr2fpga_agent/execution/prompt_guidance.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/prompt_guidance.py) · 62 行 · SHA-256 `77e35ebee8061dd04a0d91ffaa806eb1781c1fd1ef8a787ebc03cffb85696cb5`

> Versioned, task-independent tool guidance shared by every model stage.

导入模块：无显式 import

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/execution/proposals.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/proposals.py) · 123 行 · SHA-256 `598f01baaf01bdabffb43d0b8e903542dc44bd9ef34bf0dd33f230b619060bc5`

> Strict model proposals and transactional model-owned file replacements.

导入模块：`__future__`、`copy`、`json`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.execution.isolation`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.pc.inputs`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `parse_proposal` — `parse_proposal(text, contract_key)` | function / [15](../../../../agent/src/sr2fpga_agent/execution/proposals.py#L15) | `<dynamic>.get`、`<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.startswith`、`<dynamic>.validate`、`ContractRegistry`、`ParseLimits`、`PcParseError`、`ValueError`、`_parse`、`isinstance`、`str`、`text.encode`、`text.lstrip` |
| `admit_project` — `admit_project(files)` | function / [38](../../../../agent/src/sr2fpga_agent/execution/proposals.py#L38) | `<dynamic>.encode`、`ParseLimits`、`ValueError`、`_parse`、`copy.deepcopy`、`resolve_project_manifest`、`validate_candidate_sources` |
| `apply_project_patch` — `apply_project_patch(parent, proposal)` | function / [48](../../../../agent/src/sr2fpga_agent/execution/proposals.py#L48) | `<dynamic>.intersection`、`ValueError`、`admit_project`、`any`、`candidate_sha256`、`len`、`parent.items`、`path.startswith`、`result.update`、`set`、`validate_project_relative_path` |

## `agent/src/sr2fpga_agent/execution/public_feedback.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py) · 184 行 · SHA-256 `431592f3e3c4ae77c29c32c3bb419cc53f7867eb936fd038ec289f4684f8a442`

> Bounded public diagnostics; raw tool and checker text stays evaluator-owned.

导入模块：`__future__`、`copy`、`pathlib`、`re`、`sr2fpga_agent.models`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_diagnostic` — `_diagnostic(stage, category, **location)` | function / [44](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py#L44) | 无直接调用 |
| `_safe_source_path` — `_safe_source_path(value)` | function / [48](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py#L48) | `_SOURCE_PATH.fullmatch`、`all`、`isinstance`、`len`、`value.split` |
| `validate_diagnostics` — `validate_diagnostics(values)` | function / [53](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py#L53) | `ValueError`、`_safe_source_path`、`copy.deepcopy`、`isinstance`、`item.get`、`len`、`result.append`、`set`、`tuple`、`type` |
| `_source_category` — `_source_category(message, source_line)` | function / [80](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py#L80) | `any`、`message.lower`、`re.search`、`source_line.split` |
| `source_diagnostics` — `source_diagnostics(result, candidate_files, declared_sources, work)` | function / [97](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py#L97) | `<dynamic>.replace`、`<dynamic>.splitlines`、`PurePosixPath`、`_LOCATION.fullmatch`、`_diagnostic`、`_safe_source_path`、`_source_category`、`alias.replace`、`aliases.get`、`diagnostics.append`、`int`、`len`、`min`、`str`、`type`、`validate_diagnostics` |
| `functional_diagnostics` — `functional_diagnostics(error)` | function / [167](../../../../agent/src/sr2fpga_agent/execution/public_feedback.py#L167) | `_FUNCTIONAL_MESSAGES.get`、`_diagnostic`、`len`、`message.startswith`、`str` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`re.compile`

## `agent/src/sr2fpga_agent/execution/public_interfaces.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/public_interfaces.py) · 67 行 · SHA-256 `defc9081c1aae990270b4753f41804ad68c82e4a7165db056777dcc4849f50bb`

> Read-only name index derived solely from the public entry boundary.

导入模块：`__future__`、`json`、`sr2fpga_agent.models`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `public_interface_index` — `public_interface_index(boundary)` | function / [17](../../../../agent/src/sr2fpga_agent/execution/public_interfaces.py#L17) | `<dynamic>.items`、`canonical_json_bytes`、`dict`、`json.loads`、`port.get`、`ports.append`、`sorted` |
| `indexed_public_payload` — `indexed_public_payload(payload)` | function / [56](../../../../agent/src/sr2fpga_agent/execution/public_interfaces.py#L56) | `ValueError`、`dict`、`public_interface_index` |

## `agent/src/sr2fpga_agent/execution/runtime.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/execution/runtime.py) · 711 行 · SHA-256 `55040b75517111ceb6dcb10b3e351dfe68688cbc5520c731df520c8a2f9ea339`

> PC 2.1 M0-M5 shared initial DAG, bounded repair and immutable terminals.

导入模块：`__future__`、`copy`、`dataclasses`、`hashlib`、`io`、`json`、`pathlib`、`random`、`sr2fpga_agent.artifact_store`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.execution.budgets`、`sr2fpga_agent.execution.evaluation`、`sr2fpga_agent.execution.gateway`、`sr2fpga_agent.execution.isolation`、`sr2fpga_agent.execution.locking`、`sr2fpga_agent.execution.proposals`、`sr2fpga_agent.models`、`sr2fpga_agent.pc.context`、`sr2fpga_agent.pc.emitter`、`sr2fpga_agent.pc.inputs`、`sr2fpga_agent.tasks.llm`、`subprocess`、`time`、`typing`、`zipfile`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RuntimeIntegrityError` — `RuntimeIntegrityError` | class / [42](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L42) | 无直接调用 |
| `CompositionInfrastructureError` — `CompositionInfrastructureError` | class / [46](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L46) | 无直接调用 |
| `_sha` — `_sha(value)` | function / [50](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L50) | `<dynamic>.hexdigest`、`canonical_json_bytes`、`hashlib.sha256` |
| `runtime_source_snapshot` — `runtime_source_snapshot()` | function / [54](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L54) | `<dynamic>.hexdigest`、`<dynamic>.rglob`、`Path`、`hashlib.sha256`、`package.rglob`、`path.read_bytes`、`path.relative_to`、`sorted`、`str` |
| `terminal_value` — `terminal_value(terminal, public, hidden)` | function / [60](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L60) | `<dynamic>.get`、`RuntimeIntegrityError`、`public.get` |
| `RuntimeIdentity` — `RuntimeIdentity` | class / [72](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L72) | 无直接调用 |
| `RuntimeIdentity.slot` — `slot(self, method)` | function / [81](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L81) | 无直接调用 |
| `PairedBlockRuntime` — `PairedBlockRuntime` | class / [87](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L87) | 无直接调用 |
| `PairedBlockRuntime.__init__` — `__init__(self, public_task, case, identity, output_root, evaluator_root, transport, limits, tool_limits, backend, schedule_seed, allow_model_calls, max_model_call_seconds, public_suite, final_limits, evaluator_factory)` | function / [95](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L95) | `<dynamic>.items`、`<dynamic>.resolve`、`ArtifactStore`、`BudgetLedger`、`LocalDevelopmentBackend`、`ModelGateway`、`Path`、`TrustedSuite.for_development_case`、`ValueError`、`_sha`、`asdict`、`assert_supported_case`、`canonical_json_bytes`、`hasattr`、`isinstance`、`public_task.sources.bindings`、`public_task_projection`、`self._source_guard`、`self.backend.policy`、`self.private_root.is_relative_to`、`self.private_root.mkdir`、`self.root.is_relative_to`、`self.root.mkdir`、`self.store.put_blob`、`set`、`transport.public_identity`、`type`、`value.strip` |
| `PairedBlockRuntime._source_guard` — `_source_guard(self)` | function / [150](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L150) | `<dynamic>.as_posix`、`<dynamic>.hexdigest`、`<dynamic>.read_bytes`、`Path`、`RuntimeIntegrityError`、`ValueError`、`_sha`、`archive.writestr`、`archive_bytes.getvalue`、`archive_ref.to_dict`、`canonical_json_bytes`、`current.items`、`hashlib.sha256`、`io.BytesIO`、`revision.stdout.strip`、`runtime_source_snapshot`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference`、`subprocess.run`、`zipfile.ZipFile` |
| `PairedBlockRuntime._event` — `_event(self, kind, **payload)` | function / [177](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L177) | `self.events.append`、`self.store.append_event` |
| `PairedBlockRuntime._cached` — `_cached(self, operation, consumers, action)` | function / [181](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L181) | `_sha`、`action`、`canonical_json_bytes`、`json.loads`、`self._diagnostic`、`self._source_guard`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference`、`str`、`tuple` |
| `PairedBlockRuntime._meter_pure` — `_meter_pure(self, stage, operation)` | function / [198](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L198) | `BudgetExceeded`、`StructureBuild`、`ValueError`、`_sha`、`asdict`、`canonical_json_bytes`、`float`、`isinstance`、`json.loads`、`min`、`operation`、`self.ledger.dispatch`、`self.ledger.reconcile`、`self.ledger.remaining`、`self.ledger.reserve`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference`、`str`、`time.monotonic`、`time.process_time` |
| `PairedBlockRuntime._tool_budget` — `_tool_budget(self, stage, limits, execute)` | function / [240](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L240) | `execute`、`self.ledger.dispatch`、`self.ledger.reconcile`、`self.ledger.reserve` |
| `PairedBlockRuntime._frontend_runner` — `_frontend_runner(self, command, cwd, timeout)` | function / [260](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L260) | `CompositionInfrastructureError`、`min`、`replace`、`self._tool_budget`、`self.backend.run` |
| `PairedBlockRuntime._call` — `_call(self, operation, stage, consumers, payload, fmt)` | function / [268](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L268) | `PermissionError`、`RuntimeIntegrityError`、`isinstance`、`self._event`、`self._source_guard`、`self.gateway.call`、`self.store.reference`、`str` |
| `PairedBlockRuntime._check_pc` — `_check_pc(self, text)` | function / [286](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L286) | `self._diagnostic`、`self._meter_pure` |
| `PairedBlockRuntime._check_pc.check` — `check()` | function / [287](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L287) | `ParseLimits`、`assemble_project_contract`、`check_task_design`、`text.encode` |
| `PairedBlockRuntime._diagnostic` — `_diagnostic(self, error)` | function / [296](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L296) | `<dynamic>.replace`、`str` |
| `PairedBlockRuntime._build` — `_build(self, pc)` | function / [299](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L299) | `self._meter_pure` |
| `PairedBlockRuntime._build.build` — `build()` | function / [300](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L300) | `build_structure`、`check_task_design` |
| `PairedBlockRuntime._compose` — `_compose(self, build, bundle)` | function / [305](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L305) | `_sha`、`compose_behavior` |
| `PairedBlockRuntime._admit` — `_admit(self, files, pc, build, bundle, construction_origin_map, parent)` | function / [312](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L312) | `_sha`、`admit_project`、`asdict`、`candidate_sha256`、`canonical_json_bytes`、`reference.to_dict`、`self._event`、`self.store.put_blob`、`self.store.reference` |
| `PairedBlockRuntime._evaluate` — `_evaluate(self, candidate, consumers, operation)` | function / [328](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L328) | `self._cached`、`str` |
| `PairedBlockRuntime._evaluate.run` — `run()` | function / [329](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L329) | `RuntimeIntegrityError`、`_sha`、`canonical_json_bytes`、`copy.deepcopy`、`evaluator.evaluate`、`result.public_feedback`、`result.to_dict`、`self.evaluator_factory`、`self.ledger.dispatch`、`self.ledger.reconcile`、`self.ledger.reserve`、`self.store.put_blob` |
| `PairedBlockRuntime._project_node` — `_project_node(self, operation, stage, consumers, payload)` | function / [351](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L351) | `self._cached` |
| `PairedBlockRuntime._project_node.execute` — `execute()` | function / [352](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L352) | `<dynamic>.load_schema`、`ContractRegistry`、`parse_proposal`、`payload.get`、`self._admit`、`self._call`、`self._diagnostic`、`self._meter_pure` |
| `PairedBlockRuntime._body_node` — `_body_node(self, operation, consumers, pc, previous_build, feedback)` | function / [366](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L366) | `self._cached` |
| `PairedBlockRuntime._body_node.execute` — `execute()` | function / [369](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L369) | `<dynamic>.load_schema`、`ContractRegistry`、`StructureBuild`、`asdict`、`locals`、`parse_proposal`、`self._admit`、`self._build`、`self._call`、`self._compose`、`self._diagnostic`、`self._event` |
| `PairedBlockRuntime._state` — `_state(initial)` | function / [395](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L395) | `initial.get`、`initial.items` |
| `PairedBlockRuntime._repair` — `_repair(self, method, state)` | function / [402](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L402) | `<dynamic>.append`、`<dynamic>.encode`、`<dynamic>.get`、`<dynamic>.hexdigest`、`_sha`、`any`、`hashlib.sha256`、`json.loads`、`operation.encode`、`self._cached`、`self._evaluate`、`self._event`、`self.ledger.remaining`、`self.store.append_event`、`self.store.event_refs`、`self.store.read_verified`、`self.store.reference`、`sorted`、`state.clear`、`state.get`、`state.update`、`str`、`update.get`、`update.items` |
| `PairedBlockRuntime._repair.execute` — `execute()` | function / [422](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L422) | `<dynamic>.decode`、`<dynamic>.load_schema`、`<dynamic>.update`、`ContractRegistry`、`StructureBuild`、`ValueError`、`apply_project_patch`、`asdict`、`candidate_sha256`、`canonical_json_bytes`、`copy.deepcopy`、`parse_proposal`、`self._admit`、`self._body_node`、`self._build`、`self._call`、`self._check_pc`、`self._compose`、`self._diagnostic`、`set` |
| `PairedBlockRuntime.generate` — `generate(self)` | function / [507](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L507) | `file_lock`、`self._generate_locked` |
| `PairedBlockRuntime._generate_locked` — `_generate_locked(self)` | function / [511](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L511) | `<dynamic>.get`、`asdict`、`canonical_json_bytes`、`copy.deepcopy`、`evaluated.get`、`initial.get`、`json.loads`、`random.Random`、`rng.shuffle`、`self._body_node`、`self._cached`、`self._call`、`self._evaluate`、`self._project_node`、`self._repair`、`self._source_guard`、`self._state`、`self.ledger.snapshot`、`self.store.put_blob`、`self.store.read_verified`、`self.store.reference` |
| `PairedBlockRuntime._generate_locked.plan_pc` — `plan_pc()` | function / [540](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L540) | `<dynamic>.load_schema`、`ContractRegistry`、`self._call`、`self._check_pc` |
| `finalize_batch` — `finalize_batch(blocks, private_root, private_suites)` | function / [580](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L580) | `<dynamic>.get`、`<dynamic>.resolve`、`<dynamic>.snapshot`、`ArtifactStore`、`BudgetLedger`、`EvaluationResult`、`Path`、`RuntimeIntegrityError`、`TerminalEvaluationAuthority`、`ValueError`、`_sha`、`asdict`、`authority._key`、`authority.analysis_result`、`authority.close_barrier`、`authority.close_without_execution`、`authority.evaluate_once`、`authority.seal_terminal`、`block.evaluator_factory`、`block.generate`、`block.identity.slot`、`block.private_root.is_relative_to`、`block.root.is_relative_to`、`canonical_json_bytes`、`copy.deepcopy`、`enumerate`、`final_public.public_feedback`、`final_public.to_dict`、`final_public_store.put_blob`、`final_public_store.read_verified`、`final_public_store.reference`、`hidden.get`、`id`、`json.loads`、`len`、`other.root.is_relative_to`、`private_root.is_relative_to`、`public.get`、`public_worker.evaluate`、`records.append`、`set`、`str`、`task_identity`、`terminal_value`、`zip` |
| `finalize_batch.final_tool_budget` — `final_tool_budget(stage, limits, execute, consumer, budget, index, block_key)` | function / [615](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L615) | `budget.dispatch`、`budget.reconcile`、`budget.reserve`、`execute`、`stage.startswith` |
| `finalize_batch.execute_hidden` — `execute_hidden(files, worker, key, owner)` | function / [686](../../../../agent/src/sr2fpga_agent/execution/runtime.py#L686) | `EvaluationResult`、`candidate_sha256`、`task_identity`、`worker.evaluate` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`tuple`
