"""Deprecated evidence command forwarding to the standalone Agent."""

from LLM.src._compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_agent.task_evidence",
        "python -m LLM.src.sr2fpga_agent.task_evidence",
        "python -m sr2fpga_agent.task_evidence",
    )


if __name__ == "__main__":
    main()
