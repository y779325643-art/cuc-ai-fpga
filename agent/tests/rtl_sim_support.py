"""Shared Icarus and Verilator drivers for generated-project test fixtures.

Not collected by pytest: the module name does not start with ``test_``.

Several test modules used to shell out to ``iverilog``/``vvp`` with a bare
``subprocess.run`` and the inherited environment. That skips
:func:`sr2fpga_agent.local_tools.executable_env`, which is what puts an
oss-cad-suite ``lib/`` directory on PATH; without it the Icarus driver cannot
start its own backend on Windows. Routing every simulation through one helper
keeps the tool-environment rule in the one place the runtime already owns it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from sr2fpga_agent.local_tools import executable_env, resolve_executable

ICARUS_LANGUAGE_FLAG = "-g2012"


def tool_available(*names: str) -> bool:
    """Return whether every named executable resolves through the project rules."""

    return all(resolve_executable(name) is not None for name in names)


def write_project(project_dir: Path, project: Any) -> None:
    """Materialize a GeneratedProject under ``project_dir``."""

    for path, source in project.files.items():
        destination = project_dir / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")


def run_tool(command: list[str], cwd: Path, *, timeout: int | None = None):
    """Run one RTL tool with the project's resolved executable and environment."""

    resolved = resolve_executable(command[0])
    argv = list(command)
    if resolved is not None:
        argv[0] = str(resolved)
    return subprocess.run(
        argv,
        cwd=cwd,
        env=executable_env(),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def compile_and_run(
    project: Any,
    *,
    testbench_source: str | None = None,
    timeout: int = 3,
) -> str:
    """Compile a generated project under Icarus and return the simulation stdout.

    ``testbench_source`` overwrites the manifest testbench before compiling,
    which is how the width-9 and in-last fixtures inject their own stimulus.
    """

    manifest = json.loads(project.files["manifest.json"])
    testbench = manifest["simulation"]["testbench"]
    with _project_workspace(project) as project_dir:
        if testbench_source is not None:
            (project_dir / testbench).write_text(testbench_source, encoding="utf-8")
        compile_result = run_tool(
            ["iverilog", ICARUS_LANGUAGE_FLAG, "-o", "sim.out", *manifest["sources"], testbench],
            project_dir,
        )
        if compile_result.returncode != 0:
            raise AssertionError(compile_result.stdout + compile_result.stderr)
        run_result = run_tool(["vvp", "sim.out"], project_dir, timeout=timeout)
    if run_result.returncode != 0:
        raise AssertionError(run_result.stdout + run_result.stderr)
    return run_result.stdout


def lint_with_verilator(project: Any) -> None:
    """Lint every manifest source with Verilator, raising on any diagnostic."""

    manifest = json.loads(project.files["manifest.json"])
    with _project_workspace(project) as project_dir:
        result = run_tool(
            ["verilator", "--lint-only", "-Wall", *manifest["sources"]],
            project_dir,
        )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)


def _project_workspace(project: Any):
    # Imported here so a module-level tempfile patch in the importing test
    # module is the one this helper observes.
    import tempfile

    class _Workspace:
        def __enter__(self) -> Path:
            self._tmp = tempfile.TemporaryDirectory()
            project_dir = Path(self._tmp.__enter__())
            write_project(project_dir, project)
            return project_dir

        def __exit__(self, *exc_info) -> None:
            self._tmp.__exit__(*exc_info)

    return _Workspace()
