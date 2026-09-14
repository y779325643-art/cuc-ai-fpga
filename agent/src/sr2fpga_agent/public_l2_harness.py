"""Evaluator-owned trusted public L2 harness loading and commitments."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from sr2fpga_agent.models import canonical_json_bytes as _canonical_json
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.path_safety import validate_project_relative_path


class PublicL2HarnessError(ValueError):
    pass


_HDL_TOKEN = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\\[^\s]+|'
    r'`[A-Za-z_][A-Za-z0-9_$]*|\$[A-Za-z0-9_$]*|[A-Za-z_][A-Za-z0-9_$]*|[^\s]',
    re.DOTALL,
)
_PURE_SYSTEM_FUNCTIONS = frozenset({
    "$signed", "$unsigned", "$clog2", "$bits", "$size", "$left", "$right",
    "$low", "$high", "$increment", "$dimensions", "$unpacked_dimensions",
    "$isunknown", "$onehot", "$onehot0", "$countones", "$countbits",
    "$rtoi", "$itor", "$realtobits", "$bitstoreal", "$time", "$realtime", "$stime",
})


def _hdl_tokens(content: str):
    return [
        token for token in _HDL_TOKEN.finditer(content)
        if not token.group().startswith(("//", "/*"))
    ]


def candidate_simulation_violations(
    files: Mapping[str, str], sources: Sequence[str], trusted_sources: Sequence[str],
) -> tuple[str, ...]:
    """Keep candidate HDL out of simulator control and testbench scope.

    Public L2 supports module connections through ports, local literal includes,
    and pure system functions. Hierarchical references and side-effecting system
    tasks require a separate evaluator policy; do not silently execute them.
    """
    trusted_names = set()
    for content in trusted_sources:
        tokens = _hdl_tokens(content)
        for index, token in enumerate(tokens[:-1]):
            if token.group() == "module":
                trusted_names.add(tokens[index + 1].group().removeprefix("\\"))
            elif token.group() in {"task", "function"}:
                # Unqualified task calls can resolve upwards into the testbench.
                declaration = []
                for item in tokens[index + 1:]:
                    if item.group() in {"(", ";"}:
                        break
                    declaration.append(item.group().removeprefix("\\"))
                if declaration:
                    trusted_names.add(declaration[-1])
    pending = list(sources)
    seen = set()
    violations = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        tokens = _hdl_tokens(files[path])
        for index, token in enumerate(tokens):
            value = token.group().removeprefix("\\")
            dpi = (
                value in {"import", "export"} and index + 1 < len(tokens)
                and tokens[index + 1].group().startswith('"DPI')
            )
            if (
                (value.startswith("$") and value not in _PURE_SYSTEM_FUNCTIONS)
                or value in trusted_names
                or value in {"bind", "disable", "force", "release", "defparam"}
                or dpi
            ):
                violations.add("candidate_simulator_control_or_testbench_access")
            if value == "." and index and re.fullmatch(
                r"\\?[A-Za-z_][A-Za-z0-9_$]*", tokens[index - 1].group()
            ):
                violations.add("candidate_hierarchical_reference")
            if value == "`include":
                include = tokens[index + 1].group() if index + 1 < len(tokens) else ""
                try:
                    if not (include.startswith('"') and include.endswith('"')):
                        raise ValueError("nonliteral include")
                    included_path = validate_project_relative_path(include[1:-1])
                    if included_path not in files:
                        raise ValueError("external include")
                    pending.append(included_path)
                except ValueError:
                    violations.add("candidate_external_or_nonliteral_include")
    return tuple(sorted(violations))


def instrument_trusted_completion(content: str, marker: str, paths: set[str]) -> str:
    """Instrument trusted exit sites, preserving the testbench's control flow."""
    edits = []
    tokens = _hdl_tokens(content)
    for index, token in enumerate(tokens):
        if token.group() == "`include":
            include = tokens[index + 1] if index + 1 < len(tokens) else None
            if include is None or include.group()[1:-1] not in paths:
                raise PublicL2HarnessError("trusted includes must name a bundled file literally")
            edits.append((include.start(), include.end(), '"__sr2fpga_trusted_public_l2/' + include.group()[1:-1] + '"'))
        if token.group() not in {"$finish", "$finish_and_return"}:
            continue
        end = next((item.end() for item in tokens[index + 1:] if item.group() == ";"), None)
        if end is None:
            raise PublicL2HarnessError("trusted completion call has no statement terminator")
        edits.append((token.start(), token.start(), f'begin $display("{marker}"); '))
        edits.append((end, end, " end"))
    for start, end, replacement in sorted(edits, reverse=True):
        content = content[:start] + replacement + content[end:]
    return content


@dataclass(frozen=True)
class TrustedPublicL2HarnessFile:
    path: str
    content: str
    sha256: str


@dataclass(frozen=True)
class DevelopmentTrustedPublicL2Harness:
    harness_id: str
    testbench_top: str
    language_standard: str
    files: tuple[TrustedPublicL2HarnessFile, ...]
    timeout_seconds: int
    manifest_sha256: str
    bundle_sha256: str

    def public_evidence(self) -> dict[str, str | None]:
        return {
            "status": "available",
            "harness_id": self.harness_id,
            "manifest_sha256": self.manifest_sha256,
            "bundle_sha256": self.bundle_sha256,
            "reason": None,
        }


def load_development_public_l2_harness(
    manifest_path: Path,
    *,
    registry: ContractRegistry | None = None,
) -> DevelopmentTrustedPublicL2Harness:
    """Load and hash-check one development/excluded evaluator-owned harness."""

    path = Path(manifest_path).resolve()
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise PublicL2HarnessError("public L2 harness manifest is unavailable") from exc
    try:
        payload = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise PublicL2HarnessError("public L2 harness manifest is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise PublicL2HarnessError("public L2 harness manifest must be an object")
    errors = (registry or ContractRegistry()).load_schema(
        "development_public_l2_harness"
    ).validate(payload)
    if errors:
        raise PublicL2HarnessError(
            "invalid public L2 harness manifest: " + "; ".join(errors)
        )

    root = path.parent.resolve()
    files: list[TrustedPublicL2HarnessFile] = []
    seen: set[str] = set()
    for item in payload["files"]:
        relative = validate_project_relative_path(str(item["path"]))
        if relative in seen:
            raise PublicL2HarnessError("duplicate public L2 harness file path")
        seen.add(relative)
        source = (root / Path(*relative.split("/"))).resolve()
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise PublicL2HarnessError("public L2 harness file escapes manifest root") from exc
        try:
            content_bytes = source.read_bytes()
        except OSError as exc:
            raise PublicL2HarnessError("public L2 harness file is unavailable") from exc
        digest = hashlib.sha256(content_bytes).hexdigest()
        if digest != item["sha256"]:
            raise PublicL2HarnessError("public L2 harness file hash mismatch")
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublicL2HarnessError("public L2 harness file must be UTF-8 text") from exc
        files.append(TrustedPublicL2HarnessFile(relative, content, digest))

    manifest_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    bundle_sha256 = hashlib.sha256(
        _canonical_json(
            {
                "harness_id": payload["harness_id"],
                "testbench_top": payload["testbench_top"],
                "language_standard": payload["language_standard"],
                "timeout_seconds": payload["timeout_seconds"],
                "pass_rule": payload["pass_rule"],
                "files": [
                    {"path": item.path, "sha256": item.sha256} for item in files
                ],
            }
        )
    ).hexdigest()
    return DevelopmentTrustedPublicL2Harness(
        harness_id=payload["harness_id"],
        testbench_top=payload["testbench_top"],
        language_standard=payload["language_standard"],
        files=tuple(files),
        timeout_seconds=payload["timeout_seconds"],
        manifest_sha256=manifest_sha256,
        bundle_sha256=bundle_sha256,
    )


def unavailable_public_l2_harness_evidence() -> dict[str, str | None]:
    return {
        "status": "unavailable",
        "harness_id": None,
        "manifest_sha256": None,
        "bundle_sha256": None,
        "reason": "needs_oracle",
    }


