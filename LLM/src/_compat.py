"""Shared helpers for deprecated SR2FPGA command entry points."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import runpy
import sys


def warn_replacement(old_command: str, new_command: str) -> None:
    print(
        f"DEPRECATED: {old_command} -> {new_command}",
        file=sys.stderr,
    )


def run_module(
    module_name: str,
    old_command: str,
    new_command: str,
) -> None:
    warn_replacement(old_command, new_command)
    package_name = module_name.split(".", 1)[0]
    if importlib.util.find_spec(package_name) is None:
        repository_root = Path(__file__).resolve().parents[2]
        for source_root in (
            repository_root / "agent" / "src",
            repository_root / "training" / "src",
        ):
            source_text = str(source_root)
            if source_text not in sys.path:
                sys.path.insert(0, source_text)
    runpy.run_module(module_name, run_name="__main__")
