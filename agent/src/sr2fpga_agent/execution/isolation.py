"""Explicit public projection, candidate admission and bounded tool isolation.

The local backend is development-only. Docker qualification requires an actual
probe against an operator-selected, locally present image pinned by digest;
configuration or separate directories alone never establish OS isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import subprocess
import time
from typing import Any
import uuid

from sr2fpga_agent.local_tools import executable_env, resolve_executable
from sr2fpga_agent.models import ToolResult, canonical_json_bytes
from sr2fpga_agent.path_safety import validate_project_relative_path


class IsolationUnavailable(RuntimeError):
    """The requested OS boundary has not been qualified on this host."""


class CandidateBoundaryError(ValueError):
    """Candidate files attempt to cross the declared editable/executable surface."""


@dataclass(frozen=True)
class ToolLimits:
    timeout_seconds: float = 60
    memory_bytes: int = 2_147_483_648
    cpu_seconds: int = 60
    cpu_count: float = 1
    pids_limit: int = 64
    max_output_bytes: int = 32_000_000

    def __post_init__(self) -> None:
        for name in ("timeout_seconds", "cpu_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("memory_bytes", "cpu_seconds", "pids_limit", "max_output_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")


def public_task_projection(task: Any) -> dict[str, Any]:
    """Create a model-facing value without source paths, stores or evaluator refs."""
    requirements = task.requirements
    allowed = ("contract_version", "analysis_population", "requirement_id", "revision_id",
               "public_text", "boundary", "fact_records")
    projection = {name: requirements[name] for name in allowed}
    projection["target_profile"] = task.target
    projection["capability_profile"] = task.capability
    projection["public_assets"] = [
        {"id": asset["id"], "sha256": asset["sha256"], "size_bytes": asset["size_bytes"],
         "content_utf8": task.asset_bytes[asset["id"]].decode("utf-8")}
        for asset in requirements["public_assets"]
    ]
    # Detach every nested mutable value; the returned object is not authority.
    return json.loads(canonical_json_bytes(projection))


def candidate_sha256(files: dict[str, str]) -> str:
    return hashlib.sha256(canonical_json_bytes(files)).hexdigest()


def _hdl_tokens(text: str) -> list[str]:
    """Lex enough to reject unsafe syntax; real frontend checks remain mandatory."""
    tokens: list[str] = []
    index = 0
    while index < len(text):
        if text[index].isspace():
            index += 1
        elif text.startswith("//", index):
            end = text.find("\n", index)
            index = len(text) if end < 0 else end + 1
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise CandidateBoundaryError("unterminated candidate comment")
            index = end + 2
        elif text[index] in '`\\"':
            raise CandidateBoundaryError("candidate macros, strings and escaped identifiers are forbidden")
        elif text[index].isalpha() or text[index] in "_$":
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] in "_$"):
                end += 1
            tokens.append(text[index:end])
            index = end
        else:
            tokens.append(text[index])
            index += 1
    return tokens


def validate_candidate_sources(files: dict[str, str]) -> None:
    """Admit declared model-owned RTL only, never candidate tools or testbenches."""
    if not isinstance(files, dict) or "manifest.json" not in files:
        raise CandidateBoundaryError("canonical manifest is required")
    folded: set[str] = set()
    for path, content in files.items():
        validate_project_relative_path(path)
        if path.casefold() in folded:
            raise CandidateBoundaryError("case-insensitive candidate path collision")
        folded.add(path.casefold())
        if not isinstance(content, str):
            raise CandidateBoundaryError("candidate files must contain text")
        if path in {"manifest.json", "README.md"}:
            continue
        if not path.startswith("rtl/") or Path(path).suffix.lower() not in {".v", ".sv"}:
            raise CandidateBoundaryError("candidate file is outside model-owned RTL")
        tokens = _hdl_tokens(content)
        if any(token.startswith("$") and token not in {"$signed", "$unsigned", "$clog2", "$bits", "$size"}
               for token in tokens):
            raise CandidateBoundaryError("candidate system task/function is outside the allowed subset")
        if any(token in {"bind", "defparam", "force", "release", "import", "export", "program"} for token in tokens):
            raise CandidateBoundaryError("candidate attempts a cross-unit or procedural override")
        # Named port bindings '.port(expr)' remain legal; hierarchy 'a.b' does not.
        for index, token in enumerate(tokens):
            if token == "." and (index == 0 or tokens[index - 1] not in {"(", ","}):
                raise CandidateBoundaryError("candidate hierarchical access is forbidden")


def _safe_environment() -> dict[str, str]:
    host = executable_env()
    allowed = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TMP", "TEMP", "YOSYSHQ_ROOT"}
    return {key: value for key, value in host.items() if key.upper() in allowed}


def _run_process(command: list[str], cwd: Path, stage: str, limits: ToolLimits,
                 *, env: dict[str, str] | None = None) -> ToolResult:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", stage):
        raise ValueError("invalid tool stage")
    start = time.monotonic()
    stdout_path, stderr_path = cwd / f"{stage}.stdout.log", cwd / f"{stage}.stderr.log"
    status, exit_code = "failed", None
    options: dict[str, Any] = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env or _safe_environment(),
                                       stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, **options)
        except FileNotFoundError:
            status = "missing_tool"
        else:
            try:
                exit_code = process.wait(timeout=limits.timeout_seconds)
                status = "passed" if exit_code == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timeout"
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, timeout=10, check=False)
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    def bounded(path: Path) -> str:
        with path.open("rb") as stream:
            return stream.read(limits.max_output_bytes).decode("utf-8", errors="replace")
    if stdout_path.stat().st_size > limits.max_output_bytes or stderr_path.stat().st_size > limits.max_output_bytes:
        status = "output_limit_exceeded"
    return ToolResult(stage, command, status, exit_code, bounded(stdout_path), bounded(stderr_path),
                      time.monotonic() - start)


class LocalDevelopmentBackend:
    isolation_qualified = False
    backend_id = "local-development-unqualified-v1"

    def policy(self) -> dict[str, Any]:
        return {"backend": self.backend_id, "isolation_qualified": False,
                "cpu_memory_enforced": False, "environment": "minimal_allowlist"}

    def run(self, command: list[str], cwd: Path, stage: str, limits: ToolLimits) -> ToolResult:
        resolved = resolve_executable(command[0])
        args = [str(resolved) if resolved is not None else command[0], *command[1:]]
        return _run_process(args, cwd, stage, limits)


class DockerBackend:
    """Linux container boundary; no implicit image pull or network entitlement.

    Flags follow https://docs.docker.com/reference/cli/docker/container/run/.
    Actual qualification is separate from availability and constructor success.
    """
    backend_id = "docker-linux-restricted-v1"

    def __init__(self, image: str, *, user: str = "1000:1000", docker: str = "docker", endpoint: str | None = None):
        if not re.fullmatch(r"[A-Za-z0-9._:/-]+@sha256:[0-9a-f]{64}", image):
            raise ValueError("Docker image must be pinned by SHA256 digest")
        if not re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", user):
            raise ValueError("Docker user and group must be explicit non-root numeric IDs")
        endpoint = endpoint or ("npipe:////./pipe/docker_engine" if os.name == "nt" else "unix:///var/run/docker.sock")
        if not (endpoint.startswith("unix:///") or endpoint.startswith("npipe:////./pipe/")):
            raise ValueError("candidate workers require an explicit local Docker socket/pipe")
        if any(char.isspace() for char in endpoint) or any(char in endpoint for char in "\r\n"):
            raise ValueError("invalid local Docker endpoint")
        self.image, self.user, self.docker, self.endpoint = image, user, docker, endpoint
        self.isolation_qualified = False

    def _client(self) -> list[str]:
        return [self.docker, "--host", self.endpoint]

    def policy(self) -> dict[str, Any]:
        return {"backend": self.backend_id, "image": self.image, "user": self.user, "endpoint": self.endpoint,
                "network": "none", "rootfs": "read_only", "capabilities": "none",
                "no_new_privileges": True, "isolation_qualified": self.isolation_qualified}

    def available(self) -> bool:
        if shutil.which(self.docker) is None:
            return False
        try:
            system = subprocess.run([*self._client(), "info", "--format", "{{.OSType}}"],
                                    capture_output=True, text=True, timeout=10, check=False)
            image = subprocess.run([*self._client(), "image", "inspect", self.image],
                                   capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return system.returncode == 0 and system.stdout.strip() == "linux" and image.returncode == 0

    def command(self, command: list[str], cwd: Path, limits: ToolLimits, *, name: str) -> list[str]:
        work = cwd.resolve(strict=True)
        if work.parent == work or (work / ".git").exists() or (work / "AGENTS.md").exists():
            raise CandidateBoundaryError("host roots and repository roots cannot become tool work mounts")
        if "," in str(work) or any(path.is_symlink() for path in work.rglob("*")):
            raise CandidateBoundaryError("container work mount contains unsupported paths or symlinks")
        return [*self._client(), "run", "--rm", "--pull", "never", "--name", name,
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges=true", "--user", self.user,
                "--memory", str(limits.memory_bytes), "--memory-swap", str(limits.memory_bytes),
                "--cpus", str(limits.cpu_count), "--pids-limit", str(limits.pids_limit),
                "--ulimit", f"cpu={limits.cpu_seconds}:{limits.cpu_seconds}",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--workdir", "/work",
                "--mount", f"type=bind,src={work},dst=/work", self.image, *command]

    def qualify(self, workspace: Path) -> bool:
        """Run a local, synthetic confinement probe; never pull/install images."""
        if not self.available():
            raise IsolationUnavailable("pinned Linux Docker toolchain is unavailable")
        workspace.mkdir(parents=True, exist_ok=False)
        marker = uuid.uuid4().hex
        outside = workspace.parent / ("private-canary-" + marker)
        with outside.open("x", encoding="utf-8") as stream:
            stream.write(marker)
        outside_path = "/" + outside.as_posix().lstrip("/")
        probe = ("test $(id -u) -ne 0 && test ! -w / && "
                 f"test ! -e {shlex.quote(outside_path)} && "
                 "grep -q '^CapEff:[[:space:]]*0000000000000000$' /proc/self/status && "
                 "grep -q '^Seccomp:[[:space:]]*2$' /proc/self/status && "
                 "test -z \"$SR2FPGA_PRIVATE_CANARY\" && printf qualified > /work/probe.txt")
        name = "sr2fpga-probe-" + marker
        result = _run_process(self.command(["/bin/sh", "-c", probe], workspace, ToolLimits(timeout_seconds=10), name=name),
                              workspace, "qualification", ToolLimits(timeout_seconds=15))
        self.isolation_qualified = (result.status == "passed" and (workspace / "probe.txt").is_file()
                                    and (workspace / "probe.txt").read_text() == "qualified")
        return self.isolation_qualified

    def run(self, command: list[str], cwd: Path, stage: str, limits: ToolLimits) -> ToolResult:
        if not self.isolation_qualified:
            raise IsolationUnavailable("Docker isolation must pass qualification before candidate tools")
        if not command or command[0] not in {"yosys", "iverilog", "vvp"}:
            raise CandidateBoundaryError("container candidate tool is outside the fixed allowlist")
        name = "sr2fpga-tool-" + uuid.uuid4().hex
        try:
            return _run_process(self.command(command, cwd, limits, name=name), cwd, stage, limits)
        finally:
            # An interrupted Docker CLI must not leave its container running.
            subprocess.run([*self._client(), "rm", "-f", name], capture_output=True, timeout=10, check=False)
