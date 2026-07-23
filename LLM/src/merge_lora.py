"""Deprecated merge command forwarding to standalone Training."""

try:
    from LLM.src._compat import run_module
except ModuleNotFoundError:
    from _compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_training.merge_lora",
        "python LLM/src/merge_lora.py",
        "python -m sr2fpga_training.merge_lora",
    )


if __name__ == "__main__":
    main()
