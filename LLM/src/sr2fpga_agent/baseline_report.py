"""Deprecated report command forwarding to the standalone Agent."""

from LLM.src._compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_agent.baseline_report",
        "python -m LLM.src.sr2fpga_agent.baseline_report",
        "python -m sr2fpga_agent.baseline_report",
    )


if __name__ == "__main__":
    main()
