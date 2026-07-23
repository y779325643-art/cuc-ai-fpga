"""Deprecated REQ2FILE command forwarding to the standalone Agent."""

from LLM.src._compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_agent.req2file_eval",
        "python -m LLM.src.req2file_eval",
        "python -m sr2fpga_agent.req2file_eval",
    )


if __name__ == "__main__":
    main()
