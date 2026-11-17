"""Small development adapter using the existing write-once artifact/event store.

The transport is external: a candidate receives a public prompt and returns
text. Reservations precede dispatch; submission never spends another call.
No official method, hidden outcome, provider token count or seed is asserted.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactStore, BudgetReservationError
from sr2fpga_agent.models import canonical_json_bytes
from sr2fpga_agent.path_safety import validate_sample_id
from sr2fpga_agent.repository_paths import RepositoryPaths

from .context import PublicTask, check_task_design, load_public_task
from .inputs import ParseLimits, TrustedContext, TrustedSource, assemble_project_contract


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def prepare_dw_pw(root: Path, *, max_model_calls: int = 6) -> "DevelopmentSession":
    """Materialize only public inputs; no HDL or model execution."""
    from sr2fpga_agent.tasks.ai_dw_pw import build_development_task
    if type(max_model_calls) is not int or not 0 <= max_model_calls <= 6:
        raise ValueError("development model-call ceiling must be in 0..6")
    root = Path(root).resolve()
    if root.exists():
        raise ValueError("development run directory must be fresh")
    task = build_development_task()
    assets = []
    for index, (name, content) in enumerate(sorted(task["public_assets"].items())):
        relative = f"assets/asset-{index:03d}.json"
        assets.append({"id": name, "path": relative, "size_bytes": len(content),
                       "sha256": hashlib.sha256(content).hexdigest()})
    requirements = {
        "contract_version": "development-public-context-v2", "analysis_population": "development",
        "requirement_id": task["task_id"], "revision_id": "development-v1",
        "public_text": task["public_text"], "boundary": task["boundary"]["boundary"],
        "fact_records": [{"fact_id": key, **value, "provenance": "system_assumption",
                          "source_ids": ["paper1-v2.2-section-6.2", task["task_id"]]}
                         for key, value in sorted(task["facts"].items())],
        "public_assets": assets,
    }
    target = {"contract_version": "pc21-development-target-v1", "target_id": "generic-yosys-development-v1",
              "language": "systemverilog", "synthesis_scope": "generic_yosys", "clock_period_ns": 10,
              "tool_timeout_seconds": 60, "max_simulation_cycles": 12000}
    capability = {"contract_version": "pc21-development-capability-v1", "limits": {
        "max_instances": 64, "max_hierarchy_depth": 16, "max_width": 4096,
        "max_tensor_elements": 4096, "supported_reset_kinds": ["none", "sync"], "max_clock_domains": 1}}
    for name, value in (("requirements", requirements), ("target-profile", target),
                        ("capability-profile", capability)):
        _write(root / "public" / (name + ".json"), canonical_json_bytes(value))
    for asset in assets:
        _write(root / "public" / asset["path"], task["public_assets"][asset["id"]])
    session = DevelopmentSession(root)
    public = session.load_task()
    for name, source in (("requirements", public.sources.requirements),
                         ("target-profile", public.sources.target_profile),
                         ("capability-profile", public.sources.capability_profile)):
        session.store.put_blob("public/" + name, source.content, media_type="application/json")
    session.store.put_blob("configuration", canonical_json_bytes({
        "analysis_population": "development", "max_model_calls": max_model_calls,
        "max_output_tokens": None, "provider_token_usage": "unavailable",
        "candidate_transport": "external_public_prompt_response", "official": False,
        "candidate_filesystem_isolation": "not_enforced_by_collaboration_api",
        "formal_method_conformant": False, "hidden_evaluation": "not_run",
    }), media_type="application/json")
    session.capture_sources("preparation")
    session.store.append_event("dw-pw", "development_prepared", {
        "bindings": public.sources.bindings(), "max_model_calls": max_model_calls,
        "token_ceiling": None, "formal_method_conformant": False,
    })
    return session


class DevelopmentSession:
    def __init__(self, root: Path):
        self.root = Path(root).resolve(strict=True)
        self.store = ArtifactStore(self.root / "store")

    def load_task(self) -> PublicTask:
        sources = {}
        for field, name in (("requirements", "requirements"), ("target_profile", "target-profile"),
                            ("capability_profile", "capability-profile")):
            content = (self.root / "public" / (name + ".json")).read_bytes()
            reference = self.store.reference("public/" + name)
            if reference is not None:
                if content != self.store.read_verified(reference):
                    raise ValueError("frozen public source bytes changed: " + name)
            elif self.store.reference("configuration") is not None:
                raise ValueError("incomplete frozen public sources")
            sources[field] = TrustedSource(name, content)
        context = TrustedContext(**sources)
        return load_public_task(context, asset_root=self.root / "public",
                                limits=ParseLimits(8_000_000, 128))

    def capture_sources(self, label: str) -> None:
        repository = RepositoryPaths.discover().root
        records = []
        for relative in ("agent/src/sr2fpga_agent", "contracts"):
            for path in sorted((repository / relative).rglob("*")):
                if path.is_file() and path.suffix in {".py", ".json"}:
                    key = path.relative_to(repository).as_posix()
                    ref = self.store.put_blob(f"source/{label}/file-{len(records):04d}", path.read_bytes())
                    records.append({"path": key, "ref": ref.to_dict()})
        self.store.put_blob(f"source/{label}/manifest", canonical_json_bytes(records), media_type="application/json")
        git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, capture_output=True, text=True, check=False)
        self.store.append_event("dw-pw", "source_snapshot", {"label": label, "sources": records,
                                "git_head": git.stdout.strip() if git.returncode == 0 else None,
                                "working_tree_bytes_included": True})

    def verify_sources(self) -> None:
        repository = RepositoryPaths.discover().root
        records = json.loads(self.store.read_verified("source/preparation/manifest"))
        for record in records:
            path = repository / record["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["ref"]["sha256"]:
                raise ValueError("trusted source drift after preparation: " + record["path"])

    def reserve_call(self, stage: str, prompt: str) -> int:
        self.verify_sources()
        self.load_task()
        lock = self.root / "dispatch.lock"
        try:
            with lock.open("xb") as handle:
                handle.write(b"Exclusive model call reservation; interrupted reservations require inspection.\n")
        except FileExistsError as error:
            raise ValueError("concurrent or interrupted candidate dispatch reservation") from error
        try:
            return self._reserve_call(stage, prompt)
        finally:
            lock.unlink()

    def _reserve_call(self, stage: str, prompt: str) -> int:
        if stage not in {"design", "behavior", "repair_design", "repair_behavior"}:
            raise ValueError("unknown candidate call stage")
        config = json.loads(self.store.read_verified("configuration"))
        events = [json.loads(self.store.read_verified(ref)) for ref in self.store.event_refs("dw-pw")]
        call_id = 1 + sum(event["event_type"] == "candidate_call_reserved" for event in events)
        if call_id > config["max_model_calls"]:
            raise BudgetReservationError("candidate model-call budget exhausted")
        prompt_bytes = prompt.encode("utf-8")
        self.store.consume_once(f"candidate-call-{call_id}", hashlib.sha256(prompt_bytes).hexdigest())
        ref = self.store.put_blob(f"calls/{call_id}/prompt", prompt_bytes, media_type="text/plain")
        self.store.append_event("dw-pw", "candidate_call_reserved", {
            "call_id": call_id, "stage": stage, "prompt_ref": ref.to_dict(),
            "max_model_calls": config["max_model_calls"], "provider_token_usage": "unavailable"})
        return call_id

    def record_response(self, call_id: int, response: str, *, transport_identity: str) -> None:
        if self.store.reference(f"calls/{call_id}/prompt") is None:
            raise ValueError("candidate call must be reserved before dispatch")
        ref = self.store.put_blob(f"calls/{call_id}/response", response.encode("utf-8"), media_type="text/plain")
        self.store.append_event("dw-pw", "candidate_response_received", {
            "call_id": call_id, "response_ref": ref.to_dict(), "transport_identity": transport_identity,
            "provider_token_usage": "unavailable"})

    def build(self, raw_design: bytes, *, attempt: str):
        from .emitter import build_structure
        validate_sample_id(attempt)
        self.verify_sources()
        task = self.load_task()
        self.store.put_blob(f"attempts/{attempt}/raw-design", raw_design, media_type="application/json")
        pc = assemble_project_contract(raw_design, task.sources, limits=ParseLimits(8_000_000, 128))
        checked = check_task_design(pc["design"], task)
        build = build_structure(checked, bindings=pc["bindings"], toolchain_id=task.target["target_id"])
        self.store.put_validated_json(f"attempts/{attempt}/pc", pc, contract_key="project_contract_2_1")
        self.store.put_blob(f"attempts/{attempt}/build", canonical_json_bytes(asdict(build)), media_type="application/json")
        return build

    def compose(self, build, bundle: dict[str, Any], *, attempt: str, origin: str):
        from .emitter import compose_behavior, write_project
        validate_sample_id(attempt)
        self.verify_sources()
        if origin not in {"hand_authored_reference", "candidate_model"}:
            raise ValueError("behavior origin must be explicit")
        self.store.put_validated_json(f"attempts/{attempt}/behavior", bundle, contract_key="pc21_behavior_bundle")
        try:
            project = compose_behavior(build, bundle, timeout_seconds=self.load_task().target["tool_timeout_seconds"],
                                       scratch_root=self.root / "attempts" / attempt / "parser",
                                       behavior_origin="hand_authored_development_control" if origin == "hand_authored_reference" else "model_behavior")
        except ValueError as error:
            self.store.append_event("dw-pw", "composition_rejected", {
                "attempt": attempt, "reason": str(error), "origin": origin,
                "parser_evidence_path": str(getattr(error, "evidence_path", ""))})
            raise
        self.store.put_blob(f"attempts/{attempt}/parser-evidence", canonical_json_bytes(project.parser_evidence),
                            media_type="application/json")
        origins = {"behavior_origin": origin, "files": project.construction_origin_map}
        self.store.put_blob(f"attempts/{attempt}/construction-origin-map", canonical_json_bytes(origins),
                            media_type="application/json")
        output = self.root / "attempts" / attempt / "project"
        write_project(project, output)
        files = {path: hashlib.sha256(content.encode("utf-8")).hexdigest() for path, content in project.files.items()}
        self.store.append_event("dw-pw", "candidate_composed", {
            "attempt": attempt, "origin": origin, "build_plan_sha256": build.build_plan_sha256,
            "files": files, "public_semantics": "not_evaluated", "official": False})
        return project, output

    def evaluate_public(self, project, project_root: Path, *, attempt: str, terminal: bool = False):
        """Trusted development suite, with complete raw tool and trace records.

        Terminal replay uses the identical sealed candidate and a different,
        exposed development input seed. It is not an official hidden submission.
        """
        import random
        from sr2fpga_agent.parsers import resolve_project_manifest
        from .development_tools import run_recorded
        from sr2fpga_agent.tasks.ai_dw_pw.harness import check_trace, render_testbench
        validate_sample_id(attempt)
        self.verify_sources()
        task = self.load_task()
        root = Path(project_root).resolve(strict=True)
        for path, expected in project.files.items():
            if (root / path).read_bytes() != expected.encode("utf-8"):
                raise ValueError("candidate bytes changed before public evaluation")
        stage_root = self.root / "attempts" / attempt / ("terminal-evaluation" if terminal else "public-evaluation")
        stage_root.mkdir(parents=True, exist_ok=False)
        if terminal:
            rng = random.Random(91271)
            frames = tuple(tuple(rng.randrange(-128, 128) for _ in range(60)) for _ in range(3))
        else:
            frames = None
        harness = stage_root / "trusted_dw_pw_tb.sv"
        harness.write_text(render_testbench(frames), encoding="utf-8")
        manifest = resolve_project_manifest(project.files)
        source_paths = [str((root / source).resolve()) for source in manifest.sources]
        timeout = task.target["tool_timeout_seconds"]
        records = {}

        def run(name, command):
            result = run_recorded(command, stage_root, name, timeout_seconds=timeout)
            data = asdict(result)
            for field in ("stdout", "stderr"):
                if isinstance(data[field], bytes):
                    data[field] = data[field].decode("utf-8", errors="replace")
            _write(stage_root / (name + ".json"), canonical_json_bytes(data))
            records[name] = data
            self.store.put_blob(f"attempts/{attempt}/{'terminal' if terminal else 'public'}/{name}",
                                canonical_json_bytes(data), media_type="application/json")
            return result

        for tool in ("iverilog", "vvp", "yosys"):
            run("version_" + tool, [tool, "-V"])
        compiled = run("compile", ["iverilog", "-v", "-g2012", "-s", "trusted_dw_pw_tb",
                                    "-o", "simulation.vvp", *source_paths, str(harness)])
        result = {"compile": compiled.status, "simulation": "not_run", "semantic": "not_run",
                  "synthesis": "not_run", "official": False, "hidden_evaluation": "not_run"}
        if compiled.status == "passed":
            simulated = run("simulation", ["vvp", "simulation.vvp"])
            result["simulation"] = simulated.status
            if simulated.status == "passed":
                try:
                    result["trace"] = asdict(check_trace(simulated.stdout))
                    result["semantic"] = "pass"
                except ValueError as error:
                    result["semantic"] = "fail"
                    result["diagnostic"] = str(error)
        if result["semantic"] == "pass":
            # Source filenames are host-selected and quoted in a script; only
            # the manifest's fixed top is interpreted as an HDL identifier.
            top = manifest.top_module
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", top) or any('"' in path for path in source_paths):
                raise ValueError("unsafe trusted synthesis input")
            quoted = " ".join('"' + path.replace("\\", "/") + '"' for path in source_paths)
            script = f"read_verilog -sv {quoted}\nsynth -top {top}\nstat\n"
            _write(stage_root / "synthesis.ys", script.encode())
            synthesized = run("synthesis", ["yosys", "-s", "synthesis.ys"])
            result["synthesis"] = synthesized.status
        _write(stage_root / "result.json", canonical_json_bytes(result))
        self.store.append_event("dw-pw", "terminal_development_evaluated" if terminal else "public_development_evaluated",
                                {"attempt": attempt, **result})
        return result
