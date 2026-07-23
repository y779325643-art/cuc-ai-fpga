"""Deprecated dataset command forwarding to standalone Training."""

try:
    from LLM.src._compat import run_module
except ModuleNotFoundError:
    from _compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_training.prepare_dataset",
        "python LLM/src/prepare_dataset.py",
        "python -m sr2fpga_training.prepare_dataset",
    )


if __name__ == "__main__":
    main()
