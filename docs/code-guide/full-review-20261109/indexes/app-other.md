# app-other：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `app/app.js`

[打开源文件](../../../../app/app.js) · 498 行 · SHA-256 `1e0dc3bd1ea1551cac29bba42e2173c986b179d8b74031da9798ff611e7253e0`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `app/index.html`

[打开源文件](../../../../app/index.html) · 188 行 · SHA-256 `1f2665c544b4a75bfe43c1a4467a03aba635980792e227f39e1a0a9ebf6acc8b`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。

## `app/server.py`

[打开源文件](../../../../app/server.py) · 679 行 · SHA-256 `733815fe14cb99c0e3d25dbb78fc0180e0293e901d055a191f6932ebf4392283`

> Local HTTP bridge between the SR2FPGA demo UI and the Agent runtime.

导入模块：`__future__`、`argparse`、`http`、`http.server`、`json`、`logging`、`math`、`pathlib`、`re`、`sr2fpga_agent.agent`、`sr2fpga_agent.models`、`sr2fpga_agent.project_generator`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.rtl_introspect`、`sr2fpga_agent.task_families`、`sys`、`threading`、`typing`、`urllib.parse`、`uuid`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_read_json` — `_read_json(path)` | function / [69](../../../../app/server.py#L69) | `TypeError`、`isinstance`、`json.loads`、`path.read_text` |
| `_validate_identity_fields` — `_validate_identity_fields(payload)` | function / [76](../../../../app/server.py#L76) | `<dynamic>.strip`、`PROJECT_NAME_PATTERN.fullmatch`、`TypeError`、`ValueError`、`isinstance`、`len`、`payload.get`、`str` |
| `_validate_width` — `_validate_width(payload)` | function / [99](../../../../app/server.py#L99) | `ValueError`、`isinstance`、`payload.get` |
| `_validate_request` — `_validate_request(payload)` | function / [106](../../../../app/server.py#L106) | `<dynamic>.join`、`ValueError`、`_missing_engineering_context`、`_resolve_task_type`、`_validate_identity_fields`、`_validate_width` |
| `_validate_audit_request` — `_validate_audit_request(payload)` | function / [122](../../../../app/server.py#L122) | `<dynamic>.strip`、`ValueError`、`_resolve_task_type`、`_validate_identity_fields`、`_validate_width`、`payload.get`、`str` |
| `infer_demo_task_type` — `infer_demo_task_type(requirement)` | function / [141](../../../../app/server.py#L141) | `_normalize_for_task_match`、`_task_type_matches_requirement`、`pattern.search`、`sorted` |
| `_normalize_for_task_match` — `_normalize_for_task_match(value)` | function / [154](../../../../app/server.py#L154) | `<dynamic>.join`、`<dynamic>.split`、`re.sub`、`value.lower` |
| `_task_type_matches_requirement` — `_task_type_matches_requirement(task_type, normalized_requirement)` | function / [158](../../../../app/server.py#L158) | `TASK_FAMILY_IDS.get`、`_normalize_for_task_match`、`any`、`candidates.add`、`family_id.replace`、`task_type.replace` |
| `task_registry_payload` — `task_registry_payload()` | function / [167](../../../../app/server.py#L167) | `_catalog_display_names`、`_task_label`、`_template_context`、`len`、`sorted` |
| `_catalog_display_names` — `_catalog_display_names()` | function / [187](../../../../app/server.py#L187) | `_read_json`、`catalog.get`、`family.get`、`isinstance` |
| `_task_label` — `_task_label(task_type, display_names)` | function / [198](../../../../app/server.py#L198) | `display_names.get`、`task_type.replace` |
| `_missing_engineering_context` — `_missing_engineering_context(payload)` | function / [204](../../../../app/server.py#L204) | `<dynamic>.strip`、`all`、`context.get`、`float`、`isinstance`、`math.isfinite`、`missing.append`、`payload.get`、`str` |
| `_template_context` — `_template_context(task_type, width)` | function / [236](../../../../app/server.py#L236) | `<dynamic>.generate`、`<dynamic>.join`、`PlatformProfile`、`ProjectGenerator`、`ProjectRequest`、`any`、`declared_module_ports`、`isinstance`、`json.loads`、`name.endswith`、`port_labels.append`、`ports.items`、`ports.keys`、`str`、`task_type.startswith` |
| `_demo_inputs` — `_demo_inputs(payload, task_type, width, project_name, requirement)` | function / [265](../../../../app/server.py#L265) | `PlatformProfile`、`ProjectRequest`、`context.get`、`float`、`payload.get`、`round`、`str` |
| `_context_gaps` — `_context_gaps(payload, task_type, width)` | function / [279](../../../../app/server.py#L279) | `<dynamic>.split`、`_template_context`、`context.get`、`expected.split`、`gaps.append`、`isinstance`、`payload.get`、`re.sub`、`sorted`、`str` |
| `_DemoProjectGenerator` — `_DemoProjectGenerator` | class / [298](../../../../app/server.py#L298) | 无直接调用 |
| `_DemoProjectGenerator.generate` — `generate(self, request, platform)` | function / [299](../../../../app/server.py#L299) | `<dynamic>.generate`、`GeneratedProject`、`_template_context`、`json.dumps`、`super` |
| `_engineering_context_clarification` — `_engineering_context_clarification(project_name, task_type, missing_context)` | function / [307](../../../../app/server.py#L307) | 无直接调用 |
| `_resolve_task_type` — `_resolve_task_type(payload, requirement, allow_unclassified)` | function / [329](../../../../app/server.py#L329) | `<dynamic>.strip`、`ValueError`、`infer_demo_task_type`、`payload.get`、`str` |
| `_file_role` — `_file_role(path)` | function / [346](../../../../app/server.py#L346) | `path.endswith`、`path.startswith` |
| `_project_files` — `_project_files(project_dir)` | function / [360](../../../../app/server.py#L360) | `<dynamic>.as_posix`、`_file_role`、`files.append`、`item.is_file`、`path.read_text`、`path.relative_to`、`project_dir.is_dir`、`project_dir.rglob`、`sorted` |
| `_stage_statuses` — `_stage_statuses(labels)` | function / [374](../../../../app/server.py#L374) | `checks.get`、`isinstance`、`labels.get`、`str` |
| `generate_demo` — `generate_demo(payload, output_root)` | function / [450](../../../../app/server.py#L450) | `<dynamic>.as_posix`、`<dynamic>.run_one`、`DataGenerationAgent`、`_DemoProjectGenerator`、`_demo_inputs`、`_project_files`、`_read_json`、`_stage_statuses`、`_validate_request`、`audit_requirement`、`boundary.to_dict`、`evaluate_requirement_boundary`、`payload.get`、`role_counts.get`、`sample_dir.is_relative_to`、`sample_dir.relative_to`、`uuid.uuid4` |
| `audit_requirement` — `audit_requirement(payload)` | function / [509](../../../../app/server.py#L509) | `<dynamic>.to_dict`、`_context_gaps`、`_demo_inputs`、`_engineering_context_clarification`、`_missing_engineering_context`、`_template_context`、`_validate_audit_request`、`conflicts.append`、`dict`、`evaluate_requirement_boundary`、`explicit.get`、`isinstance`、`missing_context.insert` |
| `DemoRequestHandler` — `DemoRequestHandler` | class / [581](../../../../app/server.py#L581) | `threading.Lock` |
| `DemoRequestHandler.__init__` — `__init__(self, *args, **kwargs)` | function / [593](../../../../app/server.py#L593) | `<dynamic>.__init__`、`str`、`super` |
| `DemoRequestHandler.do_GET` — `do_GET(self)` | function / [596](../../../../app/server.py#L596) | `<dynamic>.do_GET`、`TASK_FAMILY_IDS.values`、`len`、`self._send_json`、`self.public_files.get`、`self.send_error`、`set`、`super`、`task_registry_payload`、`urlsplit` |
| `DemoRequestHandler.do_HEAD` — `do_HEAD(self)` | function / [618](../../../../app/server.py#L618) | `<dynamic>.do_HEAD`、`self.public_files.get`、`self.send_error`、`super`、`urlsplit` |
| `DemoRequestHandler.do_POST` — `do_POST(self)` | function / [627](../../../../app/server.py#L627) | `<dynamic>.decode`、`LOGGER.exception`、`ValueError`、`audit_requirement`、`generate_demo`、`int`、`isinstance`、`json.loads`、`self._send_json`、`self.headers.get`、`self.rfile.read`、`self.send_error`、`str` |
| `DemoRequestHandler._send_json` — `_send_json(self, payload, status)` | function / [651](../../../../app/server.py#L651) | `<dynamic>.encode`、`json.dumps`、`len`、`self.end_headers`、`self.send_header`、`self.send_response`、`self.wfile.write`、`str` |
| `main` — `main(argv)` | function / [662](../../../../app/server.py#L662) | `ThreadingHTTPServer`、`argparse.ArgumentParser`、`parser.add_argument`、`parser.parse_args`、`print`、`server.serve_forever`、`server.server_close` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`logging.getLogger`、`main`、`re.compile`、`str`、`sys.path.insert`

## `app/styles.css`

[打开源文件](../../../../app/styles.css) · 1298 行 · SHA-256 `f73d0d97239f96af5774102bb9dff4cf4c73b05e504011d31386fc8d3130c22c`

非 Python 代码：此项完成文件库存；语言行为、事件调用或脚本入口见外围说明。HTML/CSS 为页面结构/样式，不强行解释成 Python 函数。
