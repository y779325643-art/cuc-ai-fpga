import sys

from sr2fpga_agent.pc.development_tools import run_recorded


def test_recorded_timeout_preserves_partial_output(tmp_path):
    result = run_recorded([sys.executable, "-u", "-c", "import time; print('started'); time.sleep(10)"],
                          tmp_path, "bounded", timeout_seconds=1)
    assert result.status == "timeout"
    assert result.exit_code is None
    assert result.stdout == "started\n"
    assert (tmp_path / "bounded.stdout.log").read_text() == "started\n"
    assert result.duration_seconds < 8


def test_recorded_nonzero_exit_is_not_pass(tmp_path):
    result = run_recorded([sys.executable, "-c", "raise SystemExit(7)"], tmp_path, "failure", timeout_seconds=5)
    assert result.status == "failed" and result.exit_code == 7
