"""Local executable discovery helpers for cross-platform developer machines."""

from __future__ import annotations

import os
from pathlib import Path
import shutil


TOOL_FALLBACK_DIRS_ENV = "SR2FPGA_TOOL_FALLBACK_DIRS"
OSS_CAD_SUITE_ROOT_ENV = "SR2FPGA_OSS_CAD_SUITE_ROOT"


def resolve_executable(
    name: str,
    *,
    path_env: str | None = None,
    fallback_dirs: list[Path] | tuple[Path, ...] | None = None,
) -> Path | None:
    """Resolve an executable from PATH, then known local fallback directories."""

    search_path = os.environ.get("PATH", "") if path_env is None else path_env
    resolved = shutil.which(name, path=search_path)
    if resolved:
        return Path(resolved)

    fallback_path = os.pathsep.join(str(path) for path in _existing_fallback_dirs(fallback_dirs))
    if not fallback_path:
        return None
    resolved = shutil.which(name, path=fallback_path)
    return Path(resolved) if resolved else None


def executable_env(
    base_env: dict[str, str] | None = None,
    *,
    fallback_dirs: list[Path] | tuple[Path, ...] | None = None,
) -> dict[str, str]:
    """Return an environment with known local tool bins prepended to PATH."""

    env = dict(os.environ if base_env is None else base_env)
    existing_path = env.get("PATH", "")
    fallback_paths = _existing_fallback_dirs(fallback_dirs)
    prepend_paths = _path_entries_for_fallbacks(fallback_paths)
    prepend = [str(path) for path in prepend_paths]
    env["PATH"] = os.pathsep.join([*prepend, existing_path]) if existing_path else os.pathsep.join(prepend)
    _set_oss_cad_suite_env(env, fallback_paths)
    return env


def discover_tool_statuses(
    tools: tuple[str, ...],
    *,
    path_env: str | None = None,
    fallback_dirs: list[Path] | tuple[Path, ...] | None = None,
) -> dict[str, str]:
    """Return found/missing status for tool names using PATH plus local fallbacks."""

    return {
        tool: "found" if resolve_executable(tool, path_env=path_env, fallback_dirs=fallback_dirs) else "missing"
        for tool in tools
    }


def _existing_fallback_dirs(fallback_dirs: list[Path] | tuple[Path, ...] | None = None) -> list[Path]:
    dirs = _default_fallback_bin_dirs() if fallback_dirs is None else tuple(fallback_dirs)
    return [path for path in dirs if path.exists()]


def _default_fallback_bin_dirs() -> tuple[Path, ...]:
    paths: list[Path] = []

    configured = os.environ.get(TOOL_FALLBACK_DIRS_ENV, "")
    paths.extend(
        Path(entry).expanduser()
        for entry in configured.split(os.pathsep)
        if entry.strip()
    )

    suite_root = os.environ.get(OSS_CAD_SUITE_ROOT_ENV, "").strip()
    if suite_root:
        root = Path(suite_root).expanduser()
        paths.append(root if root.name.lower() == "bin" else root / "bin")

    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        program_files = os.environ.get(variable, "").strip()
        if program_files:
            paths.append(Path(program_files) / "Git" / "bin")

    return tuple(_dedupe_paths(paths))


def _path_entries_for_fallbacks(fallback_dirs: list[Path]) -> list[Path]:
    entries: list[Path] = []
    for path in fallback_dirs:
        entries.append(path)
        suite_root = _oss_cad_suite_root(path)
        if suite_root is not None:
            lib_dir = suite_root / "lib"
            if lib_dir.exists():
                entries.append(lib_dir)
    return _dedupe_paths(entries)


def _set_oss_cad_suite_env(env: dict[str, str], fallback_dirs: list[Path]) -> None:
    for path in fallback_dirs:
        suite_root = _oss_cad_suite_root(path)
        if suite_root is None:
            continue
        root_text = str(suite_root)
        if not root_text.endswith(os.sep):
            root_text += os.sep
        env.setdefault("YOSYSHQ_ROOT", root_text)
        verilator_root = suite_root / "share" / "verilator"
        if verilator_root.exists():
            env.setdefault("VERILATOR_ROOT", str(verilator_root))
        cert_file = suite_root / "etc" / "cacert.pem"
        if cert_file.exists():
            env.setdefault("SSL_CERT_FILE", str(cert_file))
        return


def _oss_cad_suite_root(path: Path) -> Path | None:
    normalized = Path(path)
    if normalized.name.lower() != "bin":
        return None
    root = normalized.parent
    return root if root.name.lower() == "oss-cad-suite" else None


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path).lower() if os.name == "nt" else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique
