# app-tests：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `app/test_server.py`

[打开源文件](../../../../app/test_server.py) · 365 行 · SHA-256 `f738c10ffabda01c361f7d176435c318227df6493f5fe867764d6b53ea5ce67f`

导入模块：`__future__`、`http.client`、`http.server`、`json`、`pathlib`、`pytest`、`re`、`server`、`sr2fpga_agent.agent`、`sr2fpga_agent.models`、`sys`、`threading`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `demo_server` — `demo_server()` | function / [31](../../../../app/test_server.py#L31) | `ThreadingHTTPServer`、`server.server_close`、`server.shutdown`、`thread.join`、`thread.start`、`threading.Thread` |
| `_request` — `_request(server_address, method, path)` | function / [43](../../../../app/test_server.py#L43) | `HTTPConnection`、`connection.close`、`connection.getresponse`、`connection.request`、`response.read` |
| `_post_json` — `_post_json(server_address, path, payload)` | function / [53](../../../../app/test_server.py#L53) | `<dynamic>.encode`、`HTTPConnection`、`connection.close`、`connection.getresponse`、`connection.request`、`json.dumps`、`response.read` |
| `test_static_server_only_serves_public_ui_files` — `test_static_server_only_serves_public_ui_files(demo_server, method, path)` | function / [66](../../../../app/test_server.py#L66) | `_request` |
| `test_static_server_blocks_non_public_files` — `test_static_server_blocks_non_public_files(demo_server, method, path)` | function / [78](../../../../app/test_server.py#L78) | `_request` |
| `test_internal_error_does_not_expose_exception_details` — `test_internal_error_does_not_expose_exception_details(demo_server, monkeypatch)` | function / [85](../../../../app/test_server.py#L85) | `_post_json`、`body.decode`、`json.loads`、`monkeypatch.setattr` |
| `test_internal_error_does_not_expose_exception_details.fail_generation` — `fail_generation(*args, **kwargs)` | function / [88](../../../../app/test_server.py#L88) | `RuntimeError` |
| `test_validate_request_accepts_supported_demo_input` — `test_validate_request_accepts_supported_demo_input()` | function / [99](../../../../app/test_server.py#L99) | `_validate_request` |
| `test_validate_request_infers_task_type_from_requirement` — `test_validate_request_infers_task_type_from_requirement()` | function / [115](../../../../app/test_server.py#L115) | `_validate_request` |
| `test_infer_demo_task_type_returns_none_for_unknown_requirement` — `test_infer_demo_task_type_returns_none_for_unknown_requirement()` | function / [131](../../../../app/test_server.py#L131) | `infer_demo_task_type` |
| `test_infer_demo_task_type_uses_registry_task_names` — `test_infer_demo_task_type_uses_registry_task_names()` | function / [135](../../../../app/test_server.py#L135) | `infer_demo_task_type` |
| `test_task_registry_payload_comes_from_backend_supported_tasks` — `test_task_registry_payload_comes_from_backend_supported_tasks()` | function / [139](../../../../app/test_server.py#L139) | `<dynamic>.issubset`、`len`、`task_registry_payload` |
| `test_task_registry_uses_public_labels_without_internal_t_numbers` — `test_task_registry_uses_public_labels_without_internal_t_numbers()` | function / [149](../../../../app/test_server.py#L149) | `all`、`labels.values`、`re.search`、`task_registry_payload` |
| `test_audit_requirement_asks_for_task_family_when_auto_inference_fails` — `test_audit_requirement_asks_for_task_family_when_auto_inference_fails()` | function / [161](../../../../app/test_server.py#L161) | `audit_requirement` |
| `test_audit_requirement_returns_boundary_payload` — `test_audit_requirement_returns_boundary_payload()` | function / [176](../../../../app/test_server.py#L176) | `audit_requirement` |
| `test_audit_requirement_requires_ui_engineering_context_clock` — `test_audit_requirement_requires_ui_engineering_context_clock()` | function / [194](../../../../app/test_server.py#L194) | `audit_requirement` |
| `test_audit_request_accepts_free_mode_without_supported_task_family` — `test_audit_request_accepts_free_mode_without_supported_task_family()` | function / [219](../../../../app/test_server.py#L219) | `_validate_audit_request` |
| `test_audit_requirement_endpoint_returns_json` — `test_audit_requirement_endpoint_returns_json(demo_server)` | function / [236](../../../../app/test_server.py#L236) | `_post_json`、`json.loads` |
| `test_tasks_endpoint_returns_registry_tasks` — `test_tasks_endpoint_returns_registry_tasks(demo_server)` | function / [252](../../../../app/test_server.py#L252) | `_request`、`json.loads` |
| `test_validate_request_rejects_invalid_input` — `test_validate_request_rejects_invalid_input(field, value)` | function / [266](../../../../app/test_server.py#L266) | `_validate_request`、`pytest.raises` |
| `test_stage_statuses_preserve_not_run_reason` — `test_stage_statuses_preserve_not_run_reason()` | function / [278](../../../../app/test_server.py#L278) | `_stage_statuses` |
| `test_stage_statuses_do_not_turn_capability_gap_into_l0_failure` — `test_stage_statuses_do_not_turn_capability_gap_into_l0_failure()` | function / [298](../../../../app/test_server.py#L298) | `_stage_statuses` |
| `test_ui_preserves_agent_tool_status` — `test_ui_preserves_agent_tool_status(status, reason)` | function / [312](../../../../app/test_server.py#L312) | `<dynamic>.get`、`ToolResult`、`_stage_statuses`、`_tool_stage_outcome` |
| `_context_payload` — `_context_payload()` | function / [322](../../../../app/test_server.py#L322) | `_template_context` |
| `test_unsupported_context_stops_audit_and_generation` — `test_unsupported_context_stops_audit_and_generation(tmp_path, field, value)` | function / [327](../../../../app/test_server.py#L327) | `_context_payload`、`audit_requirement`、`generate_demo`、`list`、`tmp_path.iterdir` |
| `test_context_clock_must_be_finite_and_positive` — `test_context_clock_must_be_finite_and_positive(clock)` | function / [340](../../../../app/test_server.py#L340) | `_context_payload`、`audit_requirement` |
| `test_clock_context_reaches_recorded_project` — `test_clock_context_reaches_recorded_project(tmp_path)` | function / [346](../../../../app/test_server.py#L346) | `<dynamic>.read_text`、`_context_payload`、`audit_requirement`、`generate_demo`、`json.loads` |
| `test_conflicting_text_and_context_requires_clarification` — `test_conflicting_text_and_context_requires_clarification(requirement)` | function / [362](../../../../app/test_server.py#L362) | `_context_payload`、`audit_requirement` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`pytest.mark.parametrize`、`str`、`sys.path.insert`
