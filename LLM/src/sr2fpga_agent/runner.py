"""Deprecated runner command forwarding to the standalone Agent."""

from LLM.src._compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_agent.runner",
        "python -m LLM.src.sr2fpga_agent.runner",
        "python -m sr2fpga_agent.runner",
    )


if __name__ == "__main__":
    main()
