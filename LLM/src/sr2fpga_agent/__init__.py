"""Compatibility shim for the canonical :mod:`sr2fpga_agent` package."""

from __future__ import annotations

from pathlib import Path
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
