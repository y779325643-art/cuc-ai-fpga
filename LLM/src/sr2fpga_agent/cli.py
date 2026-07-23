"""Deprecated Agent CLI forwarding to the standalone Agent."""

from LLM.src._compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_agent.cli",
        "python -m LLM.src.sr2fpga_agent.cli",
        "python -m sr2fpga_agent.cli",
    )


if __name__ == "__main__":
    main()
