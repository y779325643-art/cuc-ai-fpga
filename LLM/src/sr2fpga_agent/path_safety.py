"""Path and tool-script input validation for generated project artifacts."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re

from LLM.src.sr2fpga_agent.contract_skeleton import BEHAVIOR_REGION_BEGIN, BEHAVIOR_REGION_END
from LLM.src.sr2fpga_agent.models import GeneratedProject, PatchMetadata


_SAFE_SAMPLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SAFE_PATH_PART = re.compile(r"^[A-Za-z0-9_.-]+$")
_SAFE_VERILOG_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def validate_sample_id(sample_id: str) -> str:
    """Return a safe sample id suitable for use as one path component."""

    if not _SAFE_SAMPLE_ID.fullmatch(sample_id):
        raise ValueError(f"unsafe sample_id: {sample_id}")
    return sample_id


def validate_project_relative_path(path: str) -> str:
    """Return a normalized POSIX relative project path or raise ValueError."""

    if "\\" in path or ":" in path:
        raise ValueError(f"unsafe project file path: {path}")
    relative = PurePosixPath(path)
    if relative.is_absolute() or not relative.parts:
        raise ValueError(f"unsafe project file path: {path}")
    for part in relative.parts:
        if part in {"", ".", ".."} or not _SAFE_PATH_PART.fullmatch(part):
            raise ValueError(f"unsafe project file path: {path}")
    return relative.as_posix()


def project_file_target(project_dir: Path, relative_path: str) -> Path:
    """Resolve a validated project file path and ensure it stays inside project_dir."""

    safe_path = validate_project_relative_path(relative_path)
    root = project_dir.resolve(strict=False)
    target = (root / safe_path).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"unsafe project file path: {relative_path}") from exc
    return target


def build_yosys_script(sources: list[str], top_module: str) -> str:
    """Build a Yosys command script from validated manifest fields."""

    safe_sources = [validate_project_relative_path(source) for source in sources]
    if not safe_sources:
        raise ValueError("unsafe Yosys manifest: no Verilog sources")
    for source in safe_sources:
        if not source.endswith(".v"):
            raise ValueError(f"unsafe Yosys manifest source: {source}")
    if not _SAFE_VERILOG_IDENTIFIER.fullmatch(top_module):
        raise ValueError(f"unsafe Yosys top_module: {top_module}")
    return f"read_verilog {' '.join(safe_sources)}; synth -top {top_module}; stat"


def build_patch_metadata(
    old: GeneratedProject,
    new: GeneratedProject,
    diagnosis: dict[str, object],
    patch_id: str = "p001",
) -> PatchMetadata:
    """Classify a repair diff against the model-editable project surface."""

    files_touched = sorted(
        path for path in set(old.files) | set(new.files) if old.files.get(path) != new.files.get(path)
    )
    trusted = [path for path in files_touched if _is_trusted_artifact(path)]
    target_failure = str(diagnosis.get("stage", diagnosis.get("failure_type", "")))
    allowed = (
        bool(files_touched)
        and not trusted
        and all(_is_model_editable(path) for path in files_touched)
        and _rtl_edit_surface_respected(
            old,
            new,
            files_touched,
            allow_legacy_interface_change=target_failure == "l0_consistency",
        )
    )
    before = _status_map(diagnosis.get("tool_result_before"))
    return PatchMetadata(
        patch_id=patch_id,
        format="unified_diff",
        diagnosis_id=str(diagnosis.get("diagnosis_id", "d001")),
        files_touched=files_touched,
        allowed_edit_regions_respected=allowed,
        expected_effect=str(diagnosis.get("expected_effect", diagnosis.get("root_cause", ""))),
        tool_result_before=before,
        tool_result_after={},
        regressions=[],
        touched_trusted_artifacts=bool(trusted),
        status="valid" if allowed else "invalid_edit_surface",
        automatic_pass_credit=False,
        repair_regression={
            "target_failure": target_failure,
            "fixed_target": False,
            "regressed_levels": [],
            "regressed_scenarios": [],
            "hidden_tests_preserved": False,
        },
    )


def finalize_patch_metadata(metadata: PatchMetadata, tool_result_after: dict[str, str]) -> PatchMetadata:
    """Attach the next attempt's verdicts and regression summary to a patch."""

    regressions = sorted(
        stage
        for stage, status in metadata.tool_result_before.items()
        if status == "passed" and stage in tool_result_after and tool_result_after[stage] != "passed"
    )
    target = str(metadata.repair_regression.get("target_failure", ""))
    hidden_stages = [stage for stage in tool_result_after if "hidden" in stage.lower()]
    fixed_target = bool(target) and tool_result_after.get(target) == "passed"
    repair_regression = {
        "target_failure": target,
        "fixed_target": fixed_target,
        "regressed_levels": regressions,
        "regressed_scenarios": [stage for stage in regressions if "scenario" in stage.lower()],
        "hidden_tests_preserved": bool(hidden_stages) and all(
            tool_result_after[stage] == "passed" for stage in hidden_stages
        ),
    }
    return PatchMetadata(
        **{
            **metadata.to_dict(),
            "tool_result_after": dict(tool_result_after),
            "regressions": regressions,
            "automatic_pass_credit": metadata.status == "valid" and fixed_target and not regressions,
            "repair_regression": repair_regression,
        }
    )


def _status_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(stage): str(status) for stage, status in value.items()}


def _is_model_editable(path: str) -> bool:
    return path.startswith("rtl/")


def _rtl_edit_surface_respected(
    old: GeneratedProject,
    new: GeneratedProject,
    files_touched: list[str],
    *,
    allow_legacy_interface_change: bool,
) -> bool:
    if any(path not in old.files or path not in new.files for path in files_touched):
        return False

    skeleton_project = any(
        BEHAVIOR_REGION_BEGIN in content or BEHAVIOR_REGION_END in content
        for path, content in old.files.items()
        if path.startswith("rtl/")
    )
    for path in files_touched:
        old_content = old.files[path]
        new_content = new.files[path]
        if skeleton_project:
            if BEHAVIOR_REGION_BEGIN not in old_content and BEHAVIOR_REGION_END not in old_content:
                return False
            if not _behavior_regions_respected(old_content, new_content):
                return False
        else:
            old_signature = _rtl_interface_signature(old_content)
            new_signature = _rtl_interface_signature(new_content)
            if not old_signature or not new_signature:
                return False
            if old_signature != new_signature and not allow_legacy_interface_change:
                return False
    return True


def _behavior_regions_respected(old: str, new: str) -> bool:
    old_masked, old_regions = _masked_behavior_regions(old)
    new_masked, new_regions = _masked_behavior_regions(new)
    if old_masked is None or new_masked is None or len(old_regions) != len(new_regions):
        return False
    if old_masked != new_masked:
        return False
    return all(not re.search(r"(?m)^\s*module\b|\bendmodule\b", region) for region in new_regions)


def _masked_behavior_regions(content: str) -> tuple[str | None, list[str]]:
    pattern = re.compile(
        rf"{re.escape(BEHAVIOR_REGION_BEGIN)}(.*?){re.escape(BEHAVIOR_REGION_END)}",
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    begin_count = content.count(BEHAVIOR_REGION_BEGIN)
    end_count = content.count(BEHAVIOR_REGION_END)
    if not matches or len(matches) != begin_count or len(matches) != end_count:
        return None, []
    regions = [match.group(1) for match in matches]
    masked = pattern.sub(
        f"{BEHAVIOR_REGION_BEGIN}\n<SR2FPGA_EDITABLE_REGION>\n{BEHAVIOR_REGION_END}",
        content,
    )
    return masked, regions


def _rtl_interface_signature(content: str) -> tuple[tuple[str, ...], ...]:
    without_comments = re.sub(r"/\*.*?\*/|//[^\n]*", "", content, flags=re.DOTALL)
    signatures: list[tuple[str, ...]] = []
    for match in re.finditer(r"(?m)^\s*module\s+[A-Za-z_][A-Za-z0-9_$]*\b", without_comments):
        end = without_comments.find(";", match.end())
        if end < 0:
            return ()
        header = without_comments[match.start() : end + 1]
        signatures.append(tuple(re.findall(r"[A-Za-z_][A-Za-z0-9_$]*|\d+|\S", header)))
    return tuple(signatures)


def _is_trusted_artifact(path: str) -> bool:
    normalized = path.replace("\\", "/").lower().lstrip("./")
    padded = f"/{normalized.strip('/')}/"
    return (
        normalized == "sim/tb_top.v"
        or normalized == "oracle"
        or normalized.startswith("oracle/")
        or "/eval/oracle/" in padded
        or normalized.startswith("llm/src/sr2fpga_agent/oracles/")
        or normalized.startswith("models/")
        or normalized.startswith("hidden/")
        or normalized.startswith("tests/hidden/")
        or "scoreboard" in normalized
        or "checker" in normalized
        or "uvm" in normalized
        or normalized.startswith("board/")
        or normalized.startswith("constraints/")
        or normalized.startswith("data_release/")
    )
