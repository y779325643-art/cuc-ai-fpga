"""Load the registered, byte-bound PC2.1 development public projection.

Only operator-selected sources and an explicitly supplied public asset root are
read. Candidate bindings and asset identities never select arbitrary files.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.path_safety import validate_project_relative_path

from .inputs import ParseLimits, TrustedContext, _parse, _validate


@dataclass(frozen=True)
class PublicTask:
    sources: TrustedContext
    requirements: dict[str, Any]
    target: dict[str, Any]
    capability: dict[str, Any]
    asset_bytes: dict[str, bytes]

    @property
    def boundary(self) -> dict[str, Any]:
        return self.requirements["boundary"]

    @property
    def facts(self) -> dict[str, dict[str, Any]]:
        return {item["fact_id"]: item for item in self.requirements["fact_records"]}


def load_public_task(context: TrustedContext, *, asset_root: Path | None,
                     limits: ParseLimits, registry: ContractRegistry | None = None) -> PublicTask:
    registry = registry or ContractRegistry()
    documents = {}
    for field, key in (("requirements", "development_public_context_v2"),
                       ("target_profile", "pc21_development_target"),
                       ("capability_profile", "pc21_development_capability")):
        document = _parse(getattr(context, field).content, limits)
        _validate(document, key, registry)
        documents[field] = document
    requirements = documents["requirements"]
    facts = requirements["fact_records"]
    if len({fact["fact_id"] for fact in facts}) != len(facts):
        raise ValueError("duplicate public fact identity")
    assets = requirements["public_assets"]
    if len({asset["id"] for asset in assets}) != len(assets):
        raise ValueError("duplicate public asset identity")
    if len({asset["path"].casefold() for asset in assets}) != len(assets):
        raise ValueError("duplicate public asset path")
    if assets and asset_root is None:
        raise ValueError("public assets require an operator-selected asset root")
    root = Path(asset_root).resolve(strict=True) if asset_root is not None else None
    asset_bytes = {}
    for asset in assets:
        relative = asset["path"]
        validate_project_relative_path(relative)
        if "\\" in relative or ":" in relative:
            raise ValueError("public asset path must be a portable relative path")
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("public asset escapes the selected asset root")
        # Limit before allocation; declared size is not permission to read an
        # unbounded file. Assets share the operator's source byte ceiling.
        if asset["size_bytes"] > limits.max_bytes or path.stat().st_size != asset["size_bytes"]:
            raise ValueError("public asset size mismatch or resource limit")
        content = path.read_bytes()
        if len(content) != asset["size_bytes"] or hashlib.sha256(content).hexdigest() != asset["sha256"]:
            raise ValueError("public asset byte binding mismatch")
        asset_bytes[asset["id"]] = content
    return PublicTask(context, requirements, documents["target_profile"],
                      documents["capability_profile"], asset_bytes)


def check_task_design(design: dict[str, Any], task: PublicTask):
    from .checker import check_design
    for source, projection in ((task.sources.requirements, task.requirements),
                               (task.sources.target_profile, task.target),
                               (task.sources.capability_profile, task.capability)):
        if _parse(source.content, ParseLimits(max(len(source.content), 1), 128)) != projection:
            raise ValueError("public projection differs from bound source bytes")
    assets = task.requirements["public_assets"]
    if set(task.asset_bytes) != {asset["id"] for asset in assets}:
        raise ValueError("public asset projection identity mismatch")
    for asset in assets:
        data = task.asset_bytes[asset["id"]]
        if len(data) != asset["size_bytes"] or hashlib.sha256(data).hexdigest() != asset["sha256"]:
            raise ValueError("public asset projection differs from bound source bytes")
    return check_design(design, task.boundary, task.capability["limits"],
                        facts=task.facts, public_assets=task.asset_bytes)
