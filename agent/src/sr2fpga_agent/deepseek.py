"""Compatibility exports for the former monolithic DeepSeek integration."""

from __future__ import annotations

import select
import time
import urllib.error
import urllib.request

from sr2fpga_agent.generation import (
    DirectProjectGenerator,
    HisProjectGenerator,
    OracleHisProjectGenerator,
    SystemHisGenerator,
    TwoStageProjectGenerator,
)
from sr2fpga_agent.generation.his2project import _project_rtl_sources
from sr2fpga_agent.parsers import (
    MULTIMODULE_RTL_EXAMPLES,
    REQUIRED_PROJECT_FILES,
    _canonical_json,
    _diagnosis_mentions_path,
    _ensure_trailing_newline,
    _files_from_list,
    _manifest_is_valid_for_project,
    _minimize_repaired_project,
    _project_system_his_schema,
    _project_task_type,
    _strip_markdown_fence,
    _validate_expected_rtl_structure,
    _validate_manifest,
    _validate_repair_preserves_l0_when_not_repairing_l0,
    _validate_system_his_contract_unchanged,
    diff_projects,
    parse_behavior_files,
    parse_project_files,
    parse_system_his_v12,
)
from sr2fpga_agent.prompts import (
    _additional_file_entries,
    _additional_project_file_entries,
    _additional_repair_file_entries,
    _artifact_sources_example,
    _functional_mismatch_repair_rules,
    _his_project_messages,
    _icarus_testbench_rules,
    _manifest_sources_example,
    _project_messages,
    _repair_messages,
    _repair_rtl_contract,
    _repair_sources_example,
    _repair_system_his_prompt,
    _rtl_contract_for_task,
    _system_his_contract,
    _system_his_v12_messages,
    _system_his_v12_retry_guidance,
    _system_his_v12_task_guidance,
    _unused_parameter_repair_rules,
    _with_his_project_retry_feedback,
    _with_system_his_retry_feedback,
)
from sr2fpga_agent.providers import (
    TRANSIENT_HTTP_STATUS_CODES,
    AnthropicCompatibleClient,
    AnthropicCompatibleConfig,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
    _TransientOpenAICompatibleError,
    _anthropic_messages_payload,
    _default_ssl_context,
    _messages_for_model,
    _model_supports_json_response_format,
    _read_anthropic_message_text,
    _read_chat_completion_json,
    _read_response_body,
    _read_streaming_chat_content,
    _read_streaming_line,
    _response_fileno,
    _response_read_deadline,
)
from sr2fpga_agent.repair import ProjectRepairer, SystemHisRepairer

# Former provider-specific public names remain aliases for one compatibility cycle.
DeepSeekProjectGenerator = DirectProjectGenerator
DeepSeekHisProjectGenerator = HisProjectGenerator
DeepSeekOracleHisProjectGenerator = OracleHisProjectGenerator
DeepSeekSystemHisGenerator = SystemHisGenerator
DeepSeekTwoStageProjectGenerator = TwoStageProjectGenerator
DeepSeekRepairer = ProjectRepairer

__all__ = [
    "AnthropicCompatibleClient",
    "AnthropicCompatibleConfig",
    "DirectProjectGenerator",
    "HisProjectGenerator",
    "OracleHisProjectGenerator",
    "ProjectRepairer",
    "SystemHisGenerator",
    "SystemHisRepairer",
    "TwoStageProjectGenerator",
    "DeepSeekHisProjectGenerator",
    "DeepSeekOracleHisProjectGenerator",
    "DeepSeekProjectGenerator",
    "DeepSeekRepairer",
    "DeepSeekSystemHisGenerator",
    "DeepSeekTwoStageProjectGenerator",
    "OpenAICompatibleClient",
    "OpenAICompatibleConfig",
    "diff_projects",
    "parse_behavior_files",
    "parse_project_files",
    "parse_system_his_v12",
]
