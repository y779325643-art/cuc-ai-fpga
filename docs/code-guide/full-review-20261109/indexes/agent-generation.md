# agent-generation：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/generation/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/__init__.py) · 35 行 · SHA-256 `16f047628c54c6adf2040c6c99b01a822afe4bdc75f2d5e8fb9a8c36824242e0`

> SR2FPGA provider-neutral model-backed project generators.

导入模块：`sr2fpga_agent.generation.context_direct`、`sr2fpga_agent.generation.context_his`、`sr2fpga_agent.generation.context_plan`、`sr2fpga_agent.generation.direct_project`、`sr2fpga_agent.generation.his2project`、`sr2fpga_agent.generation.req2his`、`sr2fpga_agent.generation.skeleton_fill`、`sr2fpga_agent.generation.two_stage`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/generation/context_direct.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/context_direct.py) · 64 行 · SHA-256 `b814c3ca71ea00c898a921f7406637d650d4e1e13d02e6db218c9020ba6c6a4d`

> Direct generation facades that consume only frozen public context.

导入模块：`__future__`、`re`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.prompts`、`sr2fpga_agent.repair`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `FrozenContextDirectProjectFacade` — `FrozenContextDirectProjectFacade` | class / [15](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L15) | 无直接调用 |
| `FrozenContextDirectProjectFacade.__init__` — `__init__(self, client)` | function / [18](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L18) | 无直接调用 |
| `FrozenContextDirectProjectFacade.emit_project` — `emit_project(self, context)` | function / [21](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L21) | `GeneratedProject`、`_frozen_direct_project_messages`、`_project_name`、`parse_project_files`、`self._client.chat` |
| `FrozenContextDirectProjectGenerator` — `FrozenContextDirectProjectGenerator` | class / [34](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L34) | 无直接调用 |
| `FrozenContextDirectProjectGenerator.__init__` — `__init__(self, client, context)` | function / [37](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L37) | `FrozenContextDirectProjectFacade` |
| `FrozenContextDirectProjectGenerator.generate` — `generate(self, request, platform)` | function / [41](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L41) | `self._facade.emit_project` |
| `FrozenContextProjectRepairFacade` — `FrozenContextProjectRepairFacade` | class / [46](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L46) | 无直接调用 |
| `FrozenContextProjectRepairFacade.__init__` — `__init__(self, client)` | function / [49](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L49) | `ProjectRepairer` |
| `FrozenContextProjectRepairFacade.repair_project` — `repair_project(self, context, project, diagnosis)` | function / [52](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L52) | `dict`、`self._repairer.repair` |
| `_project_name` — `_project_name(requirement_id)` | function / [62](../../../../agent/src/sr2fpga_agent/generation/context_direct.py#L62) | `<dynamic>.strip`、`re.sub` |

## `agent/src/sr2fpga_agent/generation/context_his.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/context_his.py) · 693 行 · SHA-256 `ffbcd901bfa442544af42ef6ff5da5401a7d800aff238a43e917eeb8e9dadd51`

> System-HIS generation and lowering from frozen public context.

导入模块：`__future__`、`copy`、`dataclasses`、`json`、`re`、`sr2fpga_agent.contract_skeleton`、`sr2fpga_agent.episode_executor`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.method_adapters`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.path_safety`、`sr2fpga_agent.project_contract`、`sr2fpga_agent.prompts`、`sr2fpga_agent.providers`、`sr2fpga_agent.rtl_identifier_checker`、`sr2fpga_agent.system_his_checker`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `FrozenContextSystemHisFacade` — `FrozenContextSystemHisFacade` | class / [59](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L59) | 无直接调用 |
| `FrozenContextSystemHisFacade.__init__` — `__init__(self, req2his_client, project_client, platform, project_output_repair_client)` | function / [62](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L62) | 无直接调用 |
| `FrozenContextSystemHisFacade.emit_his` — `emit_his(self, context)` | function / [76](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L76) | `RuntimeError`、`_frozen_system_his_messages`、`_normalize_his_project_identity`、`_unparsed_his_output`、`parse_system_his_payload`、`self._check_platform`、`self._req2his_client.stream_chat`、`str` |
| `FrozenContextSystemHisFacade.emit_free_project` — `emit_free_project(self, context, system_his)` | function / [90](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L90) | `GeneratedProject`、`RuntimeError`、`_attach_frozen_system_his`、`_frozen_his_free_project_messages`、`_validate_his_project`、`dict`、`frozen_public_project_request`、`parse_project_files`、`self._check_platform`、`self._project_client.stream_chat` |
| `FrozenContextSystemHisFacade.emit_skeleton_project` — `emit_skeleton_project(self, context, system_his)` | function / [116](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L116) | `self.emit_skeleton_project_output`、`self.lower_skeleton_project_output` |
| `FrozenContextSystemHisFacade.emit_skeleton_project_output` — `emit_skeleton_project_output(self, context, system_his)` | function / [124](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L124) | `RuntimeError`、`SkeletonProjectOutput`、`_frozen_his_skeleton_messages`、`_validate_static_his_skeleton`、`dict`、`project_package_sha256`、`self._build_skeleton`、`self._project_client.stream_chat` |
| `FrozenContextSystemHisFacade.lower_skeleton_project_output` — `lower_skeleton_project_output(self, context, system_his, output)` | function / [142](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L142) | `ValueError`、`_validate_his_project`、`dict`、`merge_behavior_files`、`parse_behavior_files`、`project_package_sha256`、`self._build_skeleton` |
| `FrozenContextSystemHisFacade.repair_skeleton_project_output` — `repair_skeleton_project_output(self, context, system_his, previous_output, error)` | function / [159](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L159) | `RuntimeError`、`SkeletonProjectOutput`、`ValueError`、`_frozen_his_skeleton_messages`、`_validate_static_his_skeleton`、`_with_his_project_retry_feedback`、`dict`、`project_package_sha256`、`self._build_skeleton`、`self._project_output_repair_client.stream_chat` |
| `FrozenContextSystemHisFacade._build_skeleton` — `_build_skeleton(self, context, system_his)` | function / [187](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L187) | `_canonicalize_skeleton`、`build_contract_skeleton_project`、`frozen_public_project_request`、`self._check_platform` |
| `FrozenContextSystemHisFacade._check_platform` — `_check_platform(self, context)` | function / [202](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L202) | `ValueError`、`platform_profile_sha256` |
| `FrozenContextSystemHisValidationFacade` — `FrozenContextSystemHisValidationFacade` | class / [207](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L207) | 无直接调用 |
| `FrozenContextSystemHisValidationFacade.__init__` — `__init__(self, platform)` | function / [208](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L208) | 无直接调用 |
| `FrozenContextSystemHisValidationFacade.validate_his` — `validate_his(self, context, system_his)` | function / [211](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L211) | `dict`、`validate_frozen_system_his_payload_h_stages` |
| `FrozenContextHisGeneratorBridge` — `FrozenContextHisGeneratorBridge` | class / [223](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L223) | 无直接调用 |
| `FrozenContextHisGeneratorBridge.__init__` — `__init__(self, method_condition, context, services, system_his, coordinator, pairing, prepared_shared_artifacts, prepared_trusted_skeleton, max_his_corrections, max_project_output_repairs, max_shared_pre_candidate_repairs)` | function / [228](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L228) | `<dynamic>.create`、`MethodAdapterRegistry`、`ValueError` |
| `FrozenContextHisGeneratorBridge.generate` — `generate(self, _request, _platform)` | function / [261](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L261) | `<dynamic>.emit_candidate`、`EpisodeExecutor`、`RuntimeError`、`SharedArtifactRefs`、`SystemHisValidationError`、`_merge_shared_system_his`、`dict`、`isinstance`、`json.dumps`、`self._coordinator.materialize_system_his`、`self._services.artifacts.event_refs`、`self._services.artifacts.put_project`、`self._services.artifacts.read_planning`、`self._services.artifacts.read_project`、`self._system_his.emit_his`、`self._validate_prepared_artifacts` |
| `FrozenContextHisGeneratorBridge._validate_prepared_artifacts` — `_validate_prepared_artifacts(self, shared)` | function / [337](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L337) | `ValueError`、`any`、`self._pairing.digest`、`self._services.artifacts.read_project` |
| `_merge_shared_system_his` — `_merge_shared_system_his(shared, system_his)` | function / [386](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L386) | `replace` |
| `FrozenContextSystemHisCorrectionFacade` — `FrozenContextSystemHisCorrectionFacade` | class / [393](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L393) | 无直接调用 |
| `FrozenContextSystemHisCorrectionFacade.__init__` — `__init__(self, client, platform, project_client, project_envelope, event_ref_resolver)` | function / [396](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L396) | `copy.deepcopy`、`dict` |
| `FrozenContextSystemHisCorrectionFacade.correct_his` — `correct_his(self, context, system_his, diagnosis)` | function / [413](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L413) | `ValueError`、`_frozen_system_his_correction_messages`、`_normalize_his_project_identity`、`_unparsed_his_output`、`all`、`diagnosis.get`、`dict`、`isinstance`、`list`、`parse_system_his_payload`、`platform_profile_sha256`、`self._client.stream_chat`、`str` |
| `FrozenContextSystemHisCorrectionFacade.repair_project` — `repair_project(self, context, project, diagnosis)` | function / [444](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L444) | `<dynamic>.join`、`GeneratedProject`、`RuntimeError`、`ValueError`、`_frozen_project_repair_messages`、`_parse_rtl_repair_files`、`_public_project_diagnosis`、`_validate_his_project`、`any`、`build_patch_metadata`、`diagnosis.get`、`dict`、`files.update`、`isinstance`、`platform_profile_sha256`、`project_package_sha256`、`record.get`、`region.get`、`resolve_project_manifest`、`self._project_client.chat`、`self._project_envelope.get`、`set`、`sorted`、`str`、`verify_project_envelope` |
| `_canonicalize_skeleton` — `_canonicalize_skeleton(project, system_his, platform)` | function / [515](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L515) | `GeneratedProject`、`artifact_roles.items`、`artifacts.get`、`dict`、`isinstance`、`json.dumps`、`port.get`、`ports.append`、`re.sub`、`str`、`system_his.get`、`top.get`、`width.get` |
| `_rtl_sources` — `_rtl_sources(project)` | function / [578](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L578) | `json.loads` |
| `_attach_frozen_system_his` — `_attach_frozen_system_his(project, system_his)` | function / [583](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L583) | `GeneratedProject`、`ValueError`、`any`、`artifacts.append`、`dict`、`entry.get`、`files.get`、`isinstance`、`json.dumps`、`json.loads`、`manifest.get` |
| `_validate_his_project` — `_validate_his_project(project)` | function / [621](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L621) | `<dynamic>.join`、`ValueError`、`_rtl_sources`、`check_his_project_consistency`、`check_rtl_identifiers` |
| `_validate_static_his_skeleton` — `_validate_static_his_skeleton(skeleton)` | function / [632](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L632) | `<dynamic>.join`、`ValueError`、`check_his_project_consistency` |
| `_unparsed_his_output` — `_unparsed_his_output(content, error)` | function / [641](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L641) | 无直接调用 |
| `_normalize_his_project_identity` — `_normalize_his_project_identity(context, payload)` | function / [649](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L649) | `copy.deepcopy`、`dict`、`frozen_public_project_request`、`isinstance`、`normalized.get` |
| `_public_project_diagnosis` — `_public_project_diagnosis(diagnosis)` | function / [666](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L666) | `<dynamic>.strip`、`ValueError`、`all`、`diagnosis.get`、`isinstance`、`item.strip`、`list`、`str` |
| `_parse_rtl_repair_files` — `_parse_rtl_repair_files(content, allowed)` | function / [680](../../../../agent/src/sr2fpga_agent/generation/context_his.py#L680) | `ValueError`、`isinstance`、`json.loads`、`paths.issubset`、`raw.items`、`set`、`str` |

## `agent/src/sr2fpga_agent/generation/context_plan.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/context_plan.py) · 59 行 · SHA-256 `8a8cfa8029f2ced7da716c3f4fd2ce44bcacf056270711ca44778d763f67a257`

> M2 untyped planning and project emission from frozen public context.

导入模块：`__future__`、`sr2fpga_agent.frozen_context`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.prompts`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `FrozenContextUntypedPlanFacade` — `FrozenContextUntypedPlanFacade` | class / [19](../../../../agent/src/sr2fpga_agent/generation/context_plan.py#L19) | 无直接调用 |
| `FrozenContextUntypedPlanFacade.__init__` — `__init__(self, plan_client, project_client)` | function / [22](../../../../agent/src/sr2fpga_agent/generation/context_plan.py#L22) | 无直接调用 |
| `FrozenContextUntypedPlanFacade.emit_plan` — `emit_plan(self, context)` | function / [26](../../../../agent/src/sr2fpga_agent/generation/context_plan.py#L26) | `<dynamic>.strip`、`ValueError`、`_frozen_untyped_plan_messages`、`callable`、`client.stream_chat`、`factory`、`getattr` |
| `FrozenContextUntypedPlanFacade.emit_project` — `emit_project(self, context, plan)` | function / [36](../../../../agent/src/sr2fpga_agent/generation/context_plan.py#L36) | `<dynamic>.strip`、`GeneratedProject`、`ValueError`、`_frozen_project_from_untyped_plan_messages`、`frozen_public_project_request`、`isinstance`、`parse_project_files`、`self._project_client.stream_chat`、`set` |

## `agent/src/sr2fpga_agent/generation/direct_project.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/direct_project.py) · 36 行 · SHA-256 `8e4c0847d412589628a5793a7c875e75fd6acf70bacbe5258b3cfeb60a7b84d7`

> Direct requirement-to-project generation.

导入模块：`__future__`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.prompts`、`sr2fpga_agent.providers`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `DirectProjectGenerator` — `DirectProjectGenerator` | class / [11](../../../../agent/src/sr2fpga_agent/generation/direct_project.py#L11) | 无直接调用 |
| `DirectProjectGenerator.__init__` — `__init__(self, client, max_attempts)` | function / [14](../../../../agent/src/sr2fpga_agent/generation/direct_project.py#L14) | 无直接调用 |
| `DirectProjectGenerator.generate` — `generate(self, request, platform)` | function / [18](../../../../agent/src/sr2fpga_agent/generation/direct_project.py#L18) | `GeneratedProject`、`RuntimeError`、`_project_messages`、`parse_project_files`、`range`、`record_parser_schema_retry`、`self.client.chat` |

## `agent/src/sr2fpga_agent/generation/his2project.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/his2project.py) · 72 行 · SHA-256 `8050d6a3e4e01d8bb7eb067be9aed6b7e4aac9f038a04e82e918405614374248`

> System-HIS-to-project skeleton fill generation.

导入模块：`__future__`、`json`、`sr2fpga_agent.contract_skeleton`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.prompts`、`sr2fpga_agent.providers`、`sr2fpga_agent.rtl_identifier_checker`、`sr2fpga_agent.system_his_v12_checker`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `HisProjectGenerator` — `HisProjectGenerator` | class / [17](../../../../agent/src/sr2fpga_agent/generation/his2project.py#L17) | 无直接调用 |
| `HisProjectGenerator.__init__` — `__init__(self, client, max_attempts)` | function / [20](../../../../agent/src/sr2fpga_agent/generation/his2project.py#L20) | 无直接调用 |
| `HisProjectGenerator.generate` — `generate(self, request, platform, system_his)` | function / [24](../../../../agent/src/sr2fpga_agent/generation/his2project.py#L24) | `<dynamic>.join`、`RuntimeError`、`ValueError`、`_his_project_messages`、`_project_rtl_sources`、`_with_his_project_retry_feedback`、`build_contract_skeleton_project`、`check_rtl_identifiers`、`check_system_his_v12_against_rtl`、`merge_behavior_files`、`parse_behavior_files`、`range`、`record_parser_schema_retry`、`self.client.stream_chat`、`str` |
| `_project_rtl_sources` — `_project_rtl_sources(project)` | function / [64](../../../../agent/src/sr2fpga_agent/generation/his2project.py#L64) | `isinstance`、`json.loads`、`manifest.get`、`path.endswith`、`project.files.get`、`sorted`、`source.endswith` |

## `agent/src/sr2fpga_agent/generation/req2his.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/req2his.py) · 167 行 · SHA-256 `6b73b24a1d508a5e646ec38979f32cfcca0497b3397565cb1b759f79080f9dc6`

> Requirement-to-System-HIS generation.

导入模块：`__future__`、`sr2fpga_agent.family_recipe`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.prompts`、`sr2fpga_agent.providers`、`sr2fpga_agent.repair`、`sr2fpga_agent.requirement_boundary`、`sr2fpga_agent.requirement_envelope`、`sr2fpga_agent.system_his_capabilities`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `RequirementClarificationRequired` — `RequirementClarificationRequired` | class / [27](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L27) | 无直接调用 |
| `RequirementClarificationRequired.__init__` — `__init__(self, envelope, ambiguity_keys)` | function / [30](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L30) | `<dynamic>.__init__`、`<dynamic>.join`、`enumerate`、`super`、`tuple` |
| `RequirementCapabilityGapError` — `RequirementCapabilityGapError` | class / [50](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L50) | 无直接调用 |
| `RequirementCapabilityGapError.__init__` — `__init__(self, requirement_id, gaps)` | function / [53](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L53) | `<dynamic>.__init__`、`<dynamic>.join`、`super` |
| `SystemHisGenerator` — `SystemHisGenerator` | class / [62](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L62) | 无直接调用 |
| `SystemHisGenerator.__init__` — `__init__(self, client, max_attempts, event_sink)` | function / [65](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L65) | `SystemHisRepairer`、`client_for_stage` |
| `SystemHisGenerator.generate` — `generate(self, request, platform)` | function / [79](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L79) | `RuntimeError`、`_prepare_requirement`、`_system_his_v12_messages`、`range`、`record_parser_schema_retry`、`self._emit_retry_event`、`self.client.stream_chat`、`self.repairer.repair`、`validate_system_his_candidate` |
| `SystemHisGenerator._emit_retry_event` — `_emit_retry_event(self, request, attempt_id, exc)` | function / [116](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L116) | `self.event_sink`、`str`、`type` |
| `_prepare_requirement` — `_prepare_requirement(request, platform)` | function / [142](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L142) | `RequirementCapabilityGapError`、`RequirementClarificationRequired`、`evaluate_requirement_boundary`、`select_family_recipe` |
| `_requirement_capability_gaps` — `_requirement_capability_gaps(envelope, backend)` | function / [163](../../../../agent/src/sr2fpga_agent/generation/req2his.py#L163) | `requirement_capability_gaps` |

## `agent/src/sr2fpga_agent/generation/skeleton_fill.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py) · 85 行 · SHA-256 `69dee471a3f6e8b4e0498c99f1953f28f63dcbfde27ad118ade74afa39fcf8a2`

> Oracle System-HIS skeleton-fill generation.

导入模块：`__future__`、`sr2fpga_agent.generation.his2project`、`sr2fpga_agent.models`、`sr2fpga_agent.parsers`、`sr2fpga_agent.project_generator`、`sr2fpga_agent.providers`、`sr2fpga_agent.system_his_fidelity`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `OracleHisProjectGenerator` — `OracleHisProjectGenerator` | class / [15](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L15) | 无直接调用 |
| `OracleHisProjectGenerator.__init__` — `__init__(self, client, max_attempts, event_sink)` | function / [20](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L20) | `HisProjectGenerator`、`ProjectGenerator` |
| `OracleHisProjectGenerator.generate` — `generate(self, request, platform)` | function / [30](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L30) | `self._oracle_system_his`、`self._run_stage`、`self.his_project_generator.generate` |
| `OracleHisProjectGenerator._oracle_system_his` — `_oracle_system_his(self, request, platform)` | function / [42](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L42) | `<dynamic>.join`、`ValueError`、`check_system_his_req_fidelity`、`parse_system_his_v12`、`self.oracle_generator.generate` |
| `OracleHisProjectGenerator._run_stage` — `_run_stage(self, stage, request, action)` | function / [50](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L50) | `action`、`self._emit_stage_event`、`str`、`time.monotonic`、`type` |
| `OracleHisProjectGenerator._emit_stage_event` — `_emit_stage_event(self, event, stage, request, **extra)` | function / [73](../../../../agent/src/sr2fpga_agent/generation/skeleton_fill.py#L73) | `self.event_sink` |

## `agent/src/sr2fpga_agent/generation/two_stage.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/generation/two_stage.py) · 108 行 · SHA-256 `0e7bb1fea6121e712ec63734ed8e5a68c0c242232aaa24bf16d59f0ed6b0d7ba`

> Two-stage REQ2HIS then HIS2PROJECT generation.

导入模块：`__future__`、`json`、`sr2fpga_agent.generation.his2project`、`sr2fpga_agent.generation.req2his`、`sr2fpga_agent.his_validation`、`sr2fpga_agent.model_budget`、`sr2fpga_agent.models`、`sr2fpga_agent.providers`、`time`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `TwoStageProjectGenerator` — `TwoStageProjectGenerator` | class / [19](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L19) | 无直接调用 |
| `TwoStageProjectGenerator.__init__` — `__init__(self, client, max_attempts, event_sink)` | function / [22](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L22) | `HisProjectGenerator`、`SystemHisGenerator`、`client_for_stage` |
| `TwoStageProjectGenerator.generate` — `generate(self, request, platform)` | function / [39](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L39) | `self.generate_from_system_his`、`self.generate_system_his` |
| `TwoStageProjectGenerator.generate_system_his` — `generate_system_his(self, request, platform)` | function / [43](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L43) | `self._run_stage`、`self.system_his_generator.generate` |
| `TwoStageProjectGenerator.generate_from_system_his` — `generate_from_system_his(self, request, platform, system_his)` | function / [51](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L51) | `SystemHisValidationError`、`json.dumps`、`self._run_stage`、`self.his_project_generator.generate`、`validate_system_his_payload_h_stages` |
| `TwoStageProjectGenerator._run_stage` — `_run_stage(self, stage, request, action)` | function / [73](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L73) | `action`、`self._emit_stage_event`、`str`、`time.monotonic`、`type` |
| `TwoStageProjectGenerator._emit_stage_event` — `_emit_stage_event(self, event, stage, request, **extra)` | function / [96](../../../../agent/src/sr2fpga_agent/generation/two_stage.py#L96) | `self.event_sink` |
