"""Compatibility shim for the canonical :mod:`sr2fpga_agent` package."""

from __future__ import annotations

import importlib
from pathlib import Path
import pkgutil
import sys
import warnings


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_CANONICAL_SOURCE_ROOT = _REPOSITORY_ROOT / "agent" / "src"
_CANONICAL_PACKAGE_ROOT = _CANONICAL_SOURCE_ROOT / "sr2fpga_agent"

if not _CANONICAL_PACKAGE_ROOT.is_dir():
    raise ImportError(
        f"canonical sr2fpga_agent package is missing: {_CANONICAL_PACKAGE_ROOT}"
    )

canonical_source = str(_CANONICAL_SOURCE_ROOT)
if canonical_source not in sys.path:
    sys.path.insert(0, canonical_source)

__path__ = [str(_CANONICAL_PACKAGE_ROOT)]

warnings.warn(
    "LLM.src.sr2fpga_agent is deprecated; the canonical import is sr2fpga_agent",
    DeprecationWarning,
    stacklevel=2,
)

from sr2fpga_agent import *  # noqa: E402,F401,F403
from sr2fpga_agent import __all__  # noqa: E402,F401


def _legacy_module_requested_for_execution() -> str:
    arguments = tuple(getattr(sys, "orig_argv", ()))
    try:
        module_index = arguments.index("-m") + 1
    except ValueError:
        return ""
    return arguments[module_index] if module_index < len(arguments) else ""


_executed_legacy_module = _legacy_module_requested_for_execution()
_canonical_package = importlib.import_module("sr2fpga_agent")
for _module_info in pkgutil.walk_packages(
    _canonical_package.__path__,
    prefix="sr2fpga_agent.",
):
    _canonical_name = _module_info.name
    _suffix = _canonical_name.removeprefix("sr2fpga_agent")
    _legacy_name = f"{__name__}{_suffix}"
    if _legacy_name == _executed_legacy_module:
        continue
    _canonical_module = importlib.import_module(_canonical_name)
    sys.modules[_legacy_name] = _canonical_module
    if _suffix.count(".") == 1:
        setattr(sys.modules[__name__], _suffix[1:], _canonical_module)
