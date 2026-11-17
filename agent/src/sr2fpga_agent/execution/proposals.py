"""Strict model proposals and transactional model-owned file replacements."""
from __future__ import annotations

import copy
import json
from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.parsers import resolve_project_manifest
from sr2fpga_agent.path_safety import validate_project_relative_path
from sr2fpga_agent.pc.inputs import ParseLimits, PcParseError, _parse
from .isolation import candidate_sha256, validate_candidate_sources


def parse_proposal(text: str, contract_key: str) -> dict[str, Any]:
    try:
        value = _parse(text.encode("utf-8"), ParseLimits(8_000_000, 128))
    except PcParseError as error:
        if str(error) != "invalid PC JSON":
            raise
        contract = {
            "pc21_project_proposal": "pc21-project-proposal-v1",
            "pc21_behavior_bundle": "pc21-behavior-bundle-v1",
            "pc21_repair_proposal": "pc21-repair-proposal-v1",
        }.get(contract_key, "proposal")
        if text.lstrip().startswith("```"):
            raise PcParseError(f"invalid {contract} JSON: Markdown code fences are forbidden") from None
        cause = error.__cause__
        location = (f" at line {cause.lineno}, column {cause.colno}"
                    if isinstance(cause, json.JSONDecodeError) else "")
        raise PcParseError(f"invalid {contract} JSON{location}: return exactly one JSON object") from None
    errors = ContractRegistry().load_schema(contract_key).validate(value)
    if errors:
        raise ValueError("; ".join(errors))
    return value


def admit_project(files: dict[str, str]) -> dict[str, str]:
    """No intelligent merge, newline rewriting, source inference or wiring fix."""
    validate_candidate_sources(files)
    _parse(files["manifest.json"].encode("utf-8"), ParseLimits(8_000_000, 128))
    manifest = resolve_project_manifest(files)
    if manifest.is_legacy:
        raise ValueError("current methods require project-package-v1")
    return copy.deepcopy(files)


def apply_project_patch(parent: dict[str, str], proposal: dict[str, Any]) -> dict[str, str]:
    if proposal["base_candidate_sha256"] != candidate_sha256(parent):
        raise ValueError("project patch names a different parent candidate")
    replacements, removals = proposal["files"], proposal["remove_paths"]
    if set(replacements).intersection(removals) or len(removals) != len(set(removals)):
        raise ValueError("patch paths conflict or repeat")
    for path in [*replacements, *removals]:
        validate_project_relative_path(path)
        if path != "manifest.json" and path != "README.md" and not path.startswith("rtl/"):
            raise ValueError("patch touches a trusted or non-model-owned path")
    if any(path not in parent for path in removals):
        raise ValueError("cannot remove a file absent from the parent")
    result = {path: text for path, text in parent.items() if path not in removals}
    result.update(replacements)
    result = admit_project(result)
    if candidate_sha256(result) == candidate_sha256(parent):
        raise ValueError("patch makes no nonempty byte change")
    return result


JSON_ONLY_FORMAT = (
    'Return exactly one JSON object. Do not include Markdown fences, explanatory prose, '
    'or a second value. Escape embedded newlines, double quotes and backslashes inside '
    'JSON string values correctly; literal newlines inside a string are invalid JSON. '
)
MODEL_FILE_RULES = (
    'The manifest.json file must conform to project-package-v1 and declare the full '
    'source inventory and public top ABI. Only manifest.json, rtl/*.v or *.sv and optional README.md '
    'are writable. No testbench, scripts, macros, file/system tasks, strings, hierarchical access, '
    'bind/force/defparam or imports; named port bindings are allowed. System functions are limited '
    'to $signed/$unsigned/$clog2/$bits/$size. Implement all public arithmetic and transactions.'
)
BODY_OWNERSHIP_GUIDANCE = (
    'Each body contains only module-internal declarations, functions, assignments and procedural '
    'blocks inserted after the supplied protected header. The framework adds the module header '
    'and the final endmodule. Do not output module, endmodule, a module port header, or a complete '
    'module in a body. Keep protected ports and specialization parameters unchanged. '
)
BODY_HDL_RULES = (
    'Bodies cannot instantiate modules, access files/hierarchy, use macros/strings/delays/attributes, '
    'or declare initial blocks or specialization parameters. Only $signed/$unsigned/$clog2 '
    'system functions are supported in a body.'
)
PROJECT_FORMAT = (
    JSON_ONLY_FORMAT
    + 'Use {"contract_version":"pc21-project-proposal-v1","files":{"manifest.json":"...",'
    '"rtl/design.sv":"..."}}. '
    + MODEL_FILE_RULES
)
DESIGN_FORMAT = (
    JSON_ONLY_FORMAT
    + 'Use the direct design root conforming to the supplied PC2.1 DesignProposal schema. '
    'Do not wrap it in design or provide bindings/schema_version. Entry signature is requirement_boundary.'
)
BEHAVIOR_FORMAT = (
    JSON_ONLY_FORMAT
    + 'Use a pc21-behavior-bundle-v1 object with contract_version, the exact supplied '
    'build_plan_sha256 and units. Cover every required unit once with {"body":"..."}. '
    + BODY_OWNERSHIP_GUIDANCE
    + BODY_HDL_RULES
)
REPAIR_FORMAT = (
    JSON_ONLY_FORMAT
    + 'The single top-level object must use contract_version="pc21-repair-proposal-v1", '
    'the permitted action, and the fields required by that action in the supplied repair schema. '
    'Use one permitted action: replace_project with complete files; '
    'replace_project_files with base_candidate_sha256, files and remove_paths; replace_design with '
    'a design field; or replace_behavior_units with base_candidate_sha256, build_plan_sha256 and units '
    '(only known unit bodies). For replace_project and replace_project_files, put file contents '
    'directly in the repair object files field. '
    'Changing design invalidates all old bodies and needs a separate subsequent behavior call. '
    'Never modify requirements, profiles, assets, evaluator, scores or budgets. '
    'For files in replace_project or replace_project_files: '
    + MODEL_FILE_RULES
    + ' For units in replace_behavior_units: ' + BODY_OWNERSHIP_GUIDANCE + BODY_HDL_RULES
)
