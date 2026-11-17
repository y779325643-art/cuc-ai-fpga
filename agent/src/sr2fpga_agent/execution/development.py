"""Explicitly synthetic terminal suites for integration tests, never formal hidden.

This trusted factory is imported only after generation closes. It returns no
model context or reference behavior, and it never dispatches a model.
"""
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import random

from sr2fpga_agent.models import canonical_json_bytes
from sr2fpga_agent.tasks.llm import CASE_MODULES
from .evaluation import TrustedSuite


def terminal_suites(public_tasks):
    suites = {}
    for case in public_tasks:
        harness = import_module(CASE_MODULES[case] + ".harness")
        task = import_module(CASE_MODULES[case] + ".task")
        rng = random.Random(20261028 + {"qkv": 17, "attention": 31, "ffn": 53}[case])
        if case == "attention":
            from sr2fpga_agent.tasks.llm_attention.oracle import DecodeInput
            commands = tuple(DecodeInput(
                tuple(rng.randrange(-128, 128) for _ in range(task.QUERY_HEADS * task.HEAD_DIM)),
                tuple(rng.randrange(-128, 128) for _ in range(task.KV_HEADS * task.HEAD_DIM)),
                tuple(rng.randrange(-128, 128) for _ in range(task.KV_HEADS * task.HEAD_DIM))) for _ in range(6))
            def render(module=harness, values=commands):
                return module.render_testbench(values)
        else:
            size = task.TOKENS * (task.INPUT_DIM if case == "qkv" else task.DIN)
            frames = tuple(tuple(rng.randrange(-128, 128) for _ in range(size)) for _ in range(3))
            def render(module=harness, values=frames):
                return module.render_testbench(values)
        source_files = [*Path(harness.__file__).parent.glob("*.py"), Path(__file__)]
        sources = {str(path.resolve()): sha256(path.read_bytes()).hexdigest() for path in source_files}
        identity = sha256(canonical_json_bytes({"case": case, "scope": "synthetic_terminal_development_v1"})).hexdigest()
        suites[case] = TrustedSuite(case + "-synthetic-terminal-v1", harness.TESTBENCH_TOP,
            render, harness.check_trace, identity, source_sha256=tuple(sorted(sources.items())))
    return suites
