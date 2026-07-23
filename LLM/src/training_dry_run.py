"""Deprecated dry-run command forwarding to standalone Training."""

try:
    from LLM.src._compat import run_module
except ModuleNotFoundError:
    from _compat import run_module


def main() -> None:
    run_module(
        "sr2fpga_training.training_dry_run",
        "python LLM/src/training_dry_run.py",
        "python -m sr2fpga_training.training_dry_run",
    )


if __name__ == "__main__":
    main()
