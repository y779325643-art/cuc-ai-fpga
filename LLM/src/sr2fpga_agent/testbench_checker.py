"""Static checks for generated self-checking Verilog testbenches."""

from __future__ import annotations

from dataclasses import dataclass
import re

from LLM.src.sr2fpga_agent.models import ToolResult


@dataclass(frozen=True)
class TestbenchObservationIssue:
    line: int
    failure_type: str
    message: str


def check_testbench_observation_races(testbench: str) -> list[TestbenchObservationIssue]:
    """Find waits that can skip the current valid output transaction."""
    issues: list[TestbenchObservationIssue] = []
    lines = testbench.splitlines()
    for index, line in enumerate(lines):
        normalized = _normalize(line)
        if "wait(out_valid)" not in normalized:
            continue
        for lookahead_index in range(index + 1, min(index + 8, len(lines))):
            lookahead = _normalize(lines[lookahead_index])
            if not lookahead:
                continue
            if "out_data" in lookahead or "expected" in lookahead:
                break
            if "@(posedge clk)" in lookahead:
                issues.append(
                    TestbenchObservationIssue(
                        line=index + 1,
                        failure_type="testbench_observation_race",
                        message=(
                            f"line {index + 1}: wait(out_valid) is followed by @(posedge clk) "
                            "before checking out_data, which can skip the current output transaction"
                        ),
                    )
                )
                break
    return issues


def check_testbench_static_issues(testbench: str) -> list[TestbenchObservationIssue]:
    """Run all static checks for generated self-checking testbenches."""
    return [
        *check_testbench_missing_functional_oracle(testbench),
        *check_testbench_observation_races(testbench),
        *check_testbench_stimulus_reaccept_risks(testbench),
    ]


def check_testbench_missing_functional_oracle(testbench: str) -> list[TestbenchObservationIssue]:
    """Find testbenches that can print TEST_PASS without any conditional oracle."""
    pass_match = re.search(r'TEST_PASS', testbench)
    if not pass_match:
        return []
    before_pass = testbench[: pass_match.start()]
    has_conditional_failure = re.search(r"\bif\s*\([^)]*\).*TEST_FAIL", before_pass, re.DOTALL) is not None
    if has_conditional_failure:
        return []
    line = testbench[: pass_match.start()].count("\n") + 1
    return [
        TestbenchObservationIssue(
            line=line,
            failure_type="testbench_missing_functional_oracle",
            message=(
                f"line {line}: TEST_PASS appears without a prior conditional TEST_FAIL oracle; "
                "the testbench can pass without comparing expected top-level behavior"
            ),
        )
    ]


def check_testbench_stimulus_reaccept_risks(testbench: str) -> list[TestbenchObservationIssue]:
    """Find valid-ready stimulus that can re-accept the same packet repeatedly."""
    issues: list[TestbenchObservationIssue] = []
    lines = testbench.splitlines()
    for index, line in enumerate(lines):
        normalized = _normalize(line)
        asserted_valids = _valid_signals_assigned(normalized, "1")
        if not asserted_valids:
            continue
        if index > 0 and _valid_signals_assigned(_normalize(lines[index - 1]), "1"):
            continue
        live_valids = set(asserted_valids)
        for lookahead_index in range(index + 1, min(index + 40, len(lines))):
            lookahead = _normalize(lines[lookahead_index])
            live_valids.update(_valid_signals_assigned(lookahead, "1"))
            for signal in list(live_valids):
                if _assigns_valid_signal(lookahead, signal, "0"):
                    live_valids.remove(signal)
            if not live_valids:
                break
            if "wait(out_valid)" in lookahead:
                signal_text = ", ".join(sorted(live_valids))
                issues.append(
                    TestbenchObservationIssue(
                        line=index + 1,
                        failure_type="testbench_stimulus_reaccept_risk",
                        message=(
                            f"line {index + 1}: {signal_text} is asserted before wait(out_valid) "
                            "and is not withdrawn on input ready, so the same packet can be accepted repeatedly"
                        ),
                    )
                )
                break
    return issues


def testbench_observation_tool_result(issues: list[TestbenchObservationIssue]) -> ToolResult:
    """Represent testbench observation issues as a pipeline ToolResult."""
    if not issues:
        return ToolResult(
            stage="testbench_static_check",
            command=["testbench_static_checker"],
            status="passed",
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.0,
        )
    return ToolResult(
        stage="testbench_static_check",
        command=["testbench_static_checker"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr="\n".join(
            f"{issue.failure_type}: {issue.message}" for issue in issues
        )
        + "\n",
        duration_seconds=0.0,
    )


def _normalize(line: str) -> str:
    return " ".join(line.strip().split())


def _valid_signals_assigned(line: str, value: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*valid)\s*(?:<=|=)\s*" + re.escape(value) + r"\b", line)
    ]


def _assigns_valid_signal(line: str, signal: str, value: str) -> bool:
    pattern = rf"\b{re.escape(signal)}\s*(?:<=|=)\s*{re.escape(value)}\b"
    return re.search(pattern, line) is not None
