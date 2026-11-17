"""PC 2.1 deterministic structure and parser-enforced behavior composition.

Only checked declarations drive construction. No family dispatch, arithmetic,
FIFO, conversion or algorithm is supplied by this module. Behavior bodies are
untrusted and must pass the bounded syntax policy and a real Yosys AST/frontend
check before a complete canonical FPGA Project Package is returned.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sr2fpga_agent.local_tools import executable_env, resolve_executable

from .abi import ABI_VERSION, type_layout


EMITTER_VERSION = "pc21-structure-emitter-v1"
BODY_POLICY_VERSION = "pc21-yosys-body-subset-v1"
BEHAVIOR_CONTRACT = "pc21-behavior-bundle-v1"
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_KEYWORDS = set("""always always_comb always_ff always_latch and assign automatic begin
buf case casex casez cell config deassign default defparam design disable edge else
end endcase endconfig endfunction endgenerate endmodule endprimitive endspecify
endtable endtask event for force forever fork function generate genvar if ifnone
initial inout input integer join localparam logic macromodule module nand negedge
nor not or output parameter posedge primitive program real realtime reg release
repeat signed specify specparam supply0 supply1 table task time tran tri unsigned
wait wand wire wor xnor xor interface package bind class import export return
""".split())


class PcBuildError(ValueError):
    """Construction or untrusted behavior cannot satisfy the build boundary."""

    def __init__(self, message: str, *, evidence_path: str | None = None) -> None:
        super().__init__(message)
        self.evidence_path = evidence_path


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StructureBuild:
    files: dict[str, str]
    units: dict[str, dict[str, Any]]
    abi_map: dict[str, Any]
    construction_origin_map: dict[str, Any]
    build_plan: dict[str, Any]
    build_plan_sha256: str
    manifest: dict[str, Any]


@dataclass(frozen=True)
class ComposedProject:
    files: dict[str, str]
    construction_origin_map: dict[str, Any]
    parser_evidence: dict[str, Any]
    build_plan_sha256: str


def _physical_identifier(name: str) -> str:
    if not _IDENTIFIER.fullmatch(name) or name in _KEYWORDS:
        raise PcBuildError(f"physical ABI name is not a supported HDL identifier: {name}")
    return name


def _ports(instance: Any, boundary: dict[str, Any], entry: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    abi: dict[str, Any] = {"domains": {}, "ports": {}}
    ports: list[dict[str, Any]] = []
    for name, domain in sorted(instance.signature["domains"].items()):
        mapping = boundary["abi"]["domains"][name] if entry else {
            "clock": f"d_{name}_clock" if domain["clock"] != "none" else None,
            "reset": f"d_{name}_reset" if domain["reset"]["kind"] != "none" else None,
        }
        abi["domains"][name] = dict(mapping)
        for role in ("clock", "reset"):
            if mapping[role] is not None:
                ports.append({"name": _physical_identifier(mapping[role]), "direction": "input",
                              "width": 1, "signed": False, "logical": name, "role": role})
    for name, port in sorted(instance.signature["ports"].items()):
        stream = port["kind"] == "stream"
        roles = ("payload", "valid", "ready") if stream else ("signal",)
        mapping = boundary["abi"]["ports"][name] if entry else {
            role: f"p_{name}_{role}" for role in roles
        }
        abi["ports"][name] = dict(mapping)
        abi["ports"][name]["layout"] = type_layout(instance.port_types[name])
        for role in roles:
            direction = port["direction"]
            if role == "ready":
                direction = "input" if direction == "output" else "output"
            scalar = instance.port_types[name]
            signed = role in {"signal", "payload"} and (
                scalar["kind"] == "sint" or
                (scalar["kind"] == "fixed" and scalar["signed"])
            )
            ports.append({"name": _physical_identifier(mapping[role]), "direction": direction,
                          "width": instance.port_widths[name] if role in {"signal", "payload"} else 1,
                          "signed": signed, "logical": name, "role": role})
    names = [port["name"].casefold() for port in ports]
    if len(set(names)) != len(names):
        raise PcBuildError("physical ABI names collide, including case-insensitive files/tool names")
    return ports, abi


def _declaration(port: dict[str, Any], *, wire: bool = False, name: str | None = None) -> str:
    prefix = "wire" if wire else port["direction"] + " logic"
    signed = " signed" if port["signed"] else ""
    width = f" [{port['width'] - 1}:0]" if port["width"] > 1 else ""
    return f"{prefix}{signed}{width} {name or port['name']}"


def _header(name: str, ports: list[dict[str, Any]], parameters: dict[str, int]) -> str:
    declarations = ",\n".join("    " + _declaration(port) for port in ports)
    header = f"module {name}(\n{declarations}\n);\n"
    for parameter, value in sorted(parameters.items()):
        header += f"localparam logic [63:0] k_{parameter} = 64'd{value};\n"
    return header


def build_structure(checked: Any, *, bindings: dict[str, Any],
                    toolchain_id: str = "generic-development") -> StructureBuild:
    """Specialize checked instances and emit only protected wiring.

    ``bindings`` must be the full three-source controller binding map. This API
    consumes the checker's result; it does not accept a candidate's own claim of
    being checked. The controller retains the returned object until composition.
    """
    if set(bindings) != {"requirements", "target_profile", "capability_profile"}:
        raise PcBuildError("all three controller source bindings are required")
    for ref in bindings.values():
        if (not isinstance(ref, dict) or set(ref) != {"id", "sha256"}
                or not isinstance(ref["id"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", str(ref["sha256"]))):
            raise PcBuildError("invalid controller source binding")
    if "self" not in checked.instances:
        raise PcBuildError("checked design lacks the root instance")
    boundary = checked.boundary
    top = _physical_identifier(boundary["rtl_top"])
    code_files = ("emitter.py", "abi.py", "checker.py", "expressions.py", "tensors.py", "semantics.py")
    code_hashes = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                   for name in code_files}
    identity = {"design": checked.design, "boundary": boundary, "capability": checked.capability,
                "bindings": bindings, "emitter": EMITTER_VERSION, "abi": ABI_VERSION,
                "body_policy": BODY_POLICY_VERSION, "checker_scope": checked.scope,
                "code_sha256": code_hashes, "toolchain_id": toolchain_id}
    dependency = _sha(identity)
    metadata: dict[str, dict[str, Any]] = {}
    specializations: dict[str, str] = {}
    for path, instance in sorted(checked.instances.items()):
        ports, abi = _ports(instance, boundary, path == "self")
        key = _sha({"dependency": dependency, "module": instance.module_id,
                    "parameters": instance.parameters, "signature": instance.signature,
                    "domains": instance.domains, "entry": path == "self"})
        name = top if path == "self" else "pc_" + key[:24]
        if name.casefold() == top.casefold() and path != "self":
            raise PcBuildError("internal module name collides with top")
        metadata[path] = {"key": key, "name": name, "ports": ports, "abi": abi,
                          "path": "rtl/" + ("top" if path == "self" else key[:24]) + ".sv"}
        specializations.setdefault(key, path)
    files: dict[str, str] = {}
    units: dict[str, dict[str, Any]] = {}
    origins: dict[str, Any] = {}
    for key, path in sorted(specializations.items()):
        instance = checked.instances[path]
        meta = metadata[path]
        header = _header(meta["name"], meta["ports"], instance.parameters)
        file_path = meta["path"]
        if instance.implementation["kind"] == "behavioral":
            unit_id = "unit_" + key[:24]
            units[unit_id] = {
                "module_id": instance.module_id, "module_name": meta["name"],
                "path": file_path, "ports": meta["ports"], "header": header,
                "parameters": instance.parameters,
                "parameter_names": {name: f"k_{name}" for name in instance.parameters},
                "signature": instance.signature, "implementation": instance.implementation,
                "instance_paths": sorted(p for p, m in metadata.items() if m["key"] == key),
            }
            origins[file_path] = {"signature": "trusted_structure", "body": "model_behavior",
                                  "module_id": instance.module_id, "unit_id": unit_id}
            continue
        lines: list[str] = []
        signals: dict[tuple[str, str, str], str] = {}
        for port, mapping in meta["abi"]["ports"].items():
            for role, name in mapping.items():
                if role != "layout":
                    signals[("self", port, role)] = name
        for child_id, child_path in sorted(instance.children.items()):
            child_meta = metadata[child_path]
            instance_name = "i_" + child_id
            bindings_list = []
            for physical in child_meta["ports"]:
                name = physical["name"]
                if physical["role"] in {"clock", "reset"}:
                    local_slot = physical["logical"]
                    parent_slot = instance.implementation["instances"][child_id]["domains"][local_slot]
                    actual = meta["abi"]["domains"][parent_slot][physical["role"]]
                    if actual is None:
                        raise PcBuildError("clock/reset domain binding loses a required physical pin")
                else:
                    actual = f"w_{child_id}__{name}"
                    lines.append(_declaration(physical, wire=True, name=actual) + ";")
                    signals[(child_id, physical["logical"], physical["role"])] = actual
                bindings_list.append(f".{name}({actual})")
            lines.append(f"{child_meta['name']} {instance_name} (" + ", ".join(bindings_list) + ");")
        for net_name, net in sorted(instance.implementation["nets"].items()):
            source = net["source"]
            for sink in net["sinks"]:
                sink_instance = instance if sink["instance"] == "self" else checked.instances[
                    instance.children[sink["instance"]]]
                stream = sink_instance.signature["ports"][sink["port"]]["kind"] == "stream"
                if source["kind"] == "constant":
                    width = sink_instance.port_widths[sink["port"]]
                    raw = source["raw_value"] & ((1 << width) - 1)
                    actual = f"{width}'h{raw:x}"
                    lines.append(f"assign {signals[(sink['instance'], sink['port'], 'signal')]} = {actual};")
                    continue
                endpoint = source["endpoint"]
                roles = ("payload", "valid", "ready") if stream else ("signal",)
                for role in roles:
                    left = signals[(sink["instance"], sink["port"], role)]
                    right = signals[(endpoint["instance"], endpoint["port"], role)]
                    if role == "ready":
                        left, right = right, left
                    lines.append(f"assign {left} = {right};")
        files[file_path] = header + "\n".join(lines) + "\nendmodule\n"
        origins[file_path] = {"signature": "trusted_structure", "body": "trusted_structure",
                              "module_id": instance.module_id}
    sources = sorted(set(files) | {unit["path"] for unit in units.values()})
    manifest = {"contract_version": "project-package-v1", "project_name": top,
                "top": {"module": top, "source": metadata["self"]["path"], "interface": {
                    "ports": [{key: p[key] for key in ("name", "direction", "width")}
                              for p in metadata["self"]["ports"]]}},
                "sources": [{"path": path, "role": "rtl_source", "language": "systemverilog"}
                            for path in sources], "artifacts": [],
                "build": {"toolchain_id": toolchain_id, "language_standard": "systemverilog-2012"}}
    abi_map = {"version": ABI_VERSION, "instances": metadata}
    plan = {"identity": identity, "dependency_sha256": dependency, "units": units,
            "abi_map": abi_map, "manifest": manifest,
            "structure_sha256": {path: hashlib.sha256(text.encode()).hexdigest()
                                 for path, text in files.items()}, "origins": origins}
    return StructureBuild(files, units, abi_map, origins, plan, _sha(plan), manifest)


def _body_tokens(body: str) -> list[str]:
    """Lex the restricted preprocessor-free source before invoking a compiler.

    This is a security prefilter, not the HDL parser or the edit-boundary proof.
    The real frontend AST and lowered port/cell checks run afterwards.
    """
    tokens = []
    index = 0
    while index < len(body):
        if body[index].isspace():
            index += 1
        elif body.startswith("//", index):
            end = body.find("\n", index)
            index = len(body) if end < 0 else end + 1
        elif body.startswith("/*", index):
            end = body.find("*/", index + 2)
            if end < 0:
                raise PcBuildError("unterminated behavior comment")
            index = end + 2
        elif body.startswith("(*", index) and (not tokens or tokens[-1] != "@"):
            raise PcBuildError("behavior attributes are outside the supported syntax policy")
        elif body[index] in '`\\".#':
            raise PcBuildError("behavior directives, strings, delays and hierarchical access are forbidden")
        elif body[index].isalpha() or body[index] in "_$":
            end = index + 1
            while end < len(body) and (body[end].isalnum() or body[end] in "_$"):
                end += 1
            token = body[index:end]
            if token.startswith("$") and token not in {"$signed", "$unsigned", "$clog2"}:
                raise PcBuildError("behavior system task/function is outside the supported syntax policy")
            tokens.append(token)
            index = end
        else:
            tokens.append(body[index])
            index += 1
    forbidden = {"module", "endmodule", "macromodule",
                 "parameter", "defparam", "interface", "package", "bind", "class", "import",
                 "export", "primitive", "program", "initial", "force", "release", "specify"}
    if forbidden.intersection(tokens):
        raise PcBuildError("behavior attempts a protected or unsupported HDL declaration")
    return tokens


def _inspect_ast(log: str, unit: dict[str, Any]) -> None:
    """Inspect actual frontend AST nodes; fail closed if the dump is unavailable."""
    nodes: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    for line in log.splitlines():
        match = re.match(r"^( +)(AST_[A-Z0-9_]+)\s", line)
        if match is None:
            continue
        name = re.search(r"str='\\([^']*)'", line)
        node = {"depth": len(match[1]), "kind": match[2],
                "name": name[1] if name else None, "children": []}
        while stack and stack[-1]["depth"] >= node["depth"]:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            nodes.append(node)
        stack.append(node)
    if len(nodes) != 1 or nodes[0]["kind"] != "AST_MODULE" or nodes[0]["name"] != unit["module_name"]:
        raise PcBuildError("real HDL parser did not expose exactly the protected behavior module AST")
    inputs = {p["name"] for p in unit["ports"] if p["direction"] == "input"}
    protected = inputs | set(unit["parameter_names"].values())
    pending = [nodes[0]]
    while pending:
        node = pending.pop()
        if node["kind"] in {"AST_CELL", "AST_BIND", "AST_INTERFACE", "AST_PACKAGE"}:
            raise PcBuildError("behavior contains an architectural instance or cross-unit declaration")
        if node["kind"] in {"AST_ASSIGN", "AST_ASSIGN_EQ", "AST_ASSIGN_LE"}:
            if not node["children"]:
                raise PcBuildError("malformed parser assignment AST")
            lvalues = [node["children"][0]]
            while lvalues:
                lhs = lvalues.pop()
                if lhs["kind"] == "AST_IDENTIFIER" and lhs["name"] in protected:
                    raise PcBuildError("behavior writes a protected input or specialization parameter")
                if lhs["kind"] != "AST_RANGE":
                    lvalues.extend(lhs["children"])
        pending.extend(node["children"])


def _frontend(files: dict[str, str], script: str, *, yosys: str,
              timeout_seconds: float, scratch_root: Path,
              frontend_runner: Callable[..., Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Preserve source and actual execution evidence even on parser failure."""
    executable = resolve_executable(yosys)
    if executable is None and frontend_runner is None:
        raise PcBuildError("Yosys frontend is unavailable; behavior boundary is unverified")
    scratch_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="parse-", dir=scratch_root))
    for path, source in files.items():
        target = work / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    command = [str(executable) if frontend_runner is None else yosys, "-Q", "-T", "-p", script]
    record: dict[str, Any] = {"command": command, "timeout_seconds": timeout_seconds,
                              "source_sha256": {p: hashlib.sha256(s.encode()).hexdigest()
                                                for p, s in files.items()},
                              "policy": BODY_POLICY_VERSION}
    evidence_path = work / "tool-run.json"
    try:
        if frontend_runner is None:
            result = subprocess.run(command, cwd=work, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=timeout_seconds,
                                    check=False, env=executable_env())
            returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
        else:
            result = frontend_runner(command, work, timeout_seconds)
            returncode, stdout, stderr = result.exit_code, result.stdout, result.stderr
            if result.status == "timeout":
                raise subprocess.TimeoutExpired(command, timeout_seconds, output=stdout, stderr=stderr)
            if result.status != "passed" and returncode is None:
                returncode = -1
    except subprocess.TimeoutExpired as error:
        record.update(returncode=None, status="timeout",
                      stdout=(error.stdout or b"").decode(errors="replace")
                      if isinstance(error.stdout, bytes) else error.stdout or "",
                      stderr=(error.stderr or b"").decode(errors="replace")
                      if isinstance(error.stderr, bytes) else error.stderr or "")
        evidence_path.write_text(_json(record) + "\n", encoding="utf-8")
        raise PcBuildError("behavior parser timeout", evidence_path=str(evidence_path)) from error
    record.update(returncode=returncode, status="completed", stdout=stdout, stderr=stderr)
    evidence_path.write_text(_json(record) + "\n", encoding="utf-8")
    if returncode != 0:
        raise PcBuildError("behavior real parser rejected source: " + stderr[-3000:],
                           evidence_path=str(evidence_path))
    parsed = json.loads((work / "parsed.json").read_text(encoding="utf-8"))
    record.update(parser_creator=parsed.get("creator"), evidence_path=str(evidence_path))
    return parsed, record


def _parse_unit(source: str, unit: dict[str, Any], *, yosys: str,
                timeout_seconds: float, scratch_root: Path,
                frontend_runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    parsed, record = _frontend({"unit.sv": source},
                               "read_verilog -sv -noautowire -dump_ast1 unit.sv; proc; write_json parsed.json",
                               yosys=yosys, timeout_seconds=timeout_seconds, scratch_root=scratch_root,
                               frontend_runner=frontend_runner)
    try:
        _inspect_ast(record["stdout"], unit)
        modules = parsed.get("modules", {})
        if set(modules) != {unit["module_name"]}:
            raise PcBuildError("behavior changes the protected module set")
        module = modules[unit["module_name"]]
        actual = module.get("ports", {})
        expected = {p["name"]: p for p in unit["ports"]}
        if set(actual) != set(expected):
            raise PcBuildError("behavior changes the protected port set")
        for name, port in expected.items():
            observed = actual[name]
            if (observed.get("direction") != port["direction"]
                    or len(observed.get("bits", [])) != port["width"]
                    or bool(observed.get("signed", 0)) != port["signed"]):
                raise PcBuildError("behavior changes a protected port type")
        if any(not cell.get("type", "").startswith("$")
               for cell in module.get("cells", {}).values()):
            raise PcBuildError("behavior introduces an undeclared module dependency")
    except PcBuildError as error:
        error.evidence_path = record["evidence_path"]
        raise
    return record


def compose_behavior(build: StructureBuild, bundle: dict[str, Any], *,
                     yosys: str = "yosys", timeout_seconds: float = 30,
                     scratch_root: str | Path | None = None,
                     behavior_origin: str = "model_behavior",
                     frontend_runner: Callable[..., Any] | None = None) -> ComposedProject:
    """Compose every required unit exactly once, then inspect the real HDL AST."""
    if timeout_seconds <= 0:
        raise ValueError("parser timeout must be positive")
    if behavior_origin not in {"model_behavior", "hand_authored_development_control"}:
        raise ValueError("unknown controller-selected behavior origin")
    if _sha(build.build_plan) != build.build_plan_sha256:
        raise PcBuildError("protected build plan changed after construction")
    for name, expected in build.build_plan["identity"]["code_sha256"].items():
        if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != expected:
            raise PcBuildError("checker or construction implementation changed after the build plan")
    if (build.units != build.build_plan["units"] or build.manifest != build.build_plan["manifest"]
            or build.abi_map != build.build_plan["abi_map"]):
        raise PcBuildError("protected construction metadata changed")
    hashes = {path: hashlib.sha256(text.encode()).hexdigest() for path, text in build.files.items()}
    if hashes != build.build_plan["structure_sha256"]:
        raise PcBuildError("protected structural source changed")
    if (not isinstance(bundle, dict)
            or set(bundle) != {"contract_version", "build_plan_sha256", "units"}
            or bundle["contract_version"] != BEHAVIOR_CONTRACT
            or bundle["build_plan_sha256"] != build.build_plan_sha256
            or not isinstance(bundle["units"], dict)
            or set(bundle["units"]) != set(build.units)):
        raise PcBuildError("behavior bundle must bind the plan and cover every unit exactly once")
    root = Path(scratch_root) if scratch_root is not None else (
        Path(__file__).resolve().parents[4] / "artifacts" / "pc21-parser")
    files = dict(build.files)
    origins = copy.deepcopy(build.construction_origin_map)
    evidence = {}
    for unit_id, unit in sorted(build.units.items()):
        entry = bundle["units"][unit_id]
        if (not isinstance(entry, dict) or set(entry) != {"body"}
                or not isinstance(entry["body"], str) or not entry["body"].strip()):
            raise PcBuildError("each behavior unit requires one non-empty body")
        body = entry["body"]
        if len(body.encode("utf-8")) > 1_000_000:
            raise PcBuildError("behavior body exceeds the local parser resource bound")
        _body_tokens(body)
        source = unit["header"] + body + "\nendmodule\n"
        evidence[unit_id] = _parse_unit(source, unit, yosys=yosys,
                                      timeout_seconds=timeout_seconds, scratch_root=root,
                                      frontend_runner=frontend_runner)
        files[unit["path"]] = source
        header_lines = len(unit["header"].splitlines())
        origins[unit["path"]].update({
            "body": behavior_origin,
            "signature_lines": [1, header_lines],
            "body_lines": [header_lines + 1, header_lines + len(body.splitlines())],
            "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "file_sha256": hashlib.sha256(source.encode()).hexdigest(),
        })
    project_script = ("read_verilog -sv -noautowire " + " ".join(sorted(files)) + "; hierarchy -check -top " +
                      build.manifest["top"]["module"] + "; proc; write_json parsed.json")
    parsed, project_record = _frontend(files, project_script, yosys=yosys,
                                       timeout_seconds=timeout_seconds, scratch_root=root,
                                       frontend_runner=frontend_runner)
    expected_modules = {item["name"] for item in build.abi_map["instances"].values()}
    if set(parsed["modules"]) != expected_modules:
        raise PcBuildError("composed project module set differs from protected construction",
                           evidence_path=project_record["evidence_path"])
    evidence["__project__"] = project_record
    files["manifest.json"] = _json(build.manifest) + "\n"
    from sr2fpga_agent.parsers import resolve_project_manifest
    resolve_project_manifest(files)
    return ComposedProject(files, origins, evidence, build.build_plan_sha256)


def write_project(project: ComposedProject, output_root: str | Path) -> Path:
    """Write a complete composed FPP to a fresh directory, without replacement."""
    from sr2fpga_agent.path_safety import validate_project_relative_path
    root = Path(output_root)
    for path in project.files:
        validate_project_relative_path(path)
    root.mkdir(parents=True, exist_ok=False)
    resolved = root.resolve()
    for path, text in sorted(project.files.items()):
        target = root / path
        if not target.resolve().is_relative_to(resolved):
            raise PcBuildError("project output escapes its root")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    return resolved
