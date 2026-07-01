"""Build and score SR2FPGA REQ2FILE evaluation files."""

from __future__ import annotations

import argparse
import http.client
import json
import re
from pathlib import Path
import shutil
import time
from typing import Any, Protocol
import urllib.error
import urllib.request

from LLM.src.sr2fpga_agent.models import GeneratedProject
from LLM.src.sr2fpga_agent.log_parser import parse_yosys_stats
from LLM.src.sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0
from LLM.src.sr2fpga_agent.testbench_checker import check_testbench_static_issues
from LLM.src.sr2fpga_agent.tool_runner import CommandRunner


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str:
        """Return assistant content for chat messages."""


def build_eval_set(
    source: Path,
    target: Path,
    *,
    sample_id_prefix: str = "",
    exclude_file_paths: set[str] | None = None,
    limit: int = 0,
) -> int:
    """Create a user-prompt eval JSONL from ``requirement_to_file`` rows."""
    excluded_paths = exclude_file_paths or set()
    count = 0
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8") as input_file, target.open("w", encoding="utf-8") as output_file:
        for line in input_file:
            if not line.strip():
                continue
            row = json.loads(line)
            if sample_id_prefix and not str(row.get("sample_id", "")).startswith(sample_id_prefix):
                continue
            file_path = str(row.get("file_path", "")).strip()
            if file_path in excluded_paths:
                continue
            eval_row = {
                "sample_id": str(row.get("sample_id", "")),
                "file_path": file_path,
                "requirement": str(row.get("requirement", "")).strip(),
                "messages": [{"role": "user", "content": _req2file_prompt(row)}],
                "expected_file_content": str(row.get("file_content", "")),
            }
            output_file.write(json.dumps(eval_row, ensure_ascii=False) + "\n")
            count += 1
            if limit and count >= limit:
                break
    return count


def score_predictions(predictions: Path) -> dict[str, Any]:
    """Score model-filled REQ2FILE prediction rows without running EDA tools."""
    counters = {
        "rows": 0,
        "exact_match": 0,
        "non_empty": 0,
        "json_rows": 0,
        "json_valid": 0,
        "verilog_rows": 0,
        "verilog_module_present": 0,
        "testbench_rows": 0,
        "testbench_oracle_present": 0,
        "sdc_rows": 0,
        "sdc_clock_present": 0,
    }
    with predictions.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            file_path = str(row.get("file_path", "")).strip()
            expected = str(row.get("expected_file_content", "")).strip()
            predicted = _prediction_text(row, line_number).strip()
            counters["rows"] += 1
            if predicted:
                counters["non_empty"] += 1
            if predicted == expected:
                counters["exact_match"] += 1
            if file_path.endswith(".json"):
                counters["json_rows"] += 1
                if _is_valid_json(predicted):
                    counters["json_valid"] += 1
            if file_path.endswith(".v"):
                counters["verilog_rows"] += 1
                if re.search(r"\bmodule\s+\w+", predicted):
                    counters["verilog_module_present"] += 1
            if file_path == "sim/tb_top.v":
                counters["testbench_rows"] += 1
                if "TEST_PASS" in predicted and "TEST_FAIL" in predicted and re.search(r"\bif\s*\(", predicted):
                    counters["testbench_oracle_present"] += 1
            if file_path.endswith(".sdc"):
                counters["sdc_rows"] += 1
                if "create_clock" in predicted and "get_ports" in predicted:
                    counters["sdc_clock_present"] += 1

    report: dict[str, Any] = dict(counters)
    rows = int(counters["rows"])
    report["exact_match_ratio"] = round(int(counters["exact_match"]) / rows, 4) if rows else 0.0
    report["non_empty_ratio"] = round(int(counters["non_empty"]) / rows, 4) if rows else 0.0
    report["json_valid_ratio"] = _ratio(counters["json_valid"], counters["json_rows"])
    report["verilog_module_present_ratio"] = _ratio(counters["verilog_module_present"], counters["verilog_rows"])
    report["testbench_oracle_present_ratio"] = _ratio(
        counters["testbench_oracle_present"],
        counters["testbench_rows"],
    )
    report["sdc_clock_present_ratio"] = _ratio(counters["sdc_clock_present"], counters["sdc_rows"])
    return report


def run_inference(
    eval_path: Path,
    output_path: Path,
    *,
    client: ChatClient,
    limit: int = 0,
) -> int:
    """Run a chat client over REQ2FILE eval rows and write prediction JSONL."""
    count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with eval_path.open("r", encoding="utf-8") as input_file, output_path.open("w", encoding="utf-8") as output_file:
        for line in input_file:
            if not line.strip():
                continue
            row = json.loads(line)
            messages = _validate_eval_messages(row.get("messages"))
            predicted = client.chat(messages)
            output_row = dict(row)
            output_row["predicted_file_content"] = predicted
            output_file.write(json.dumps(output_row, ensure_ascii=False) + "\n")
            count += 1
            if limit and count >= limit:
                break
    return count


def assemble_predictions(
    predictions: Path,
    output_root: Path,
    *,
    reference_dataset_root: Path | None = None,
    backfill_reference_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Write predicted REQ2FILE rows into per-sample generated_project dirs."""
    grouped: dict[str, dict[str, str]] = {}
    with predictions.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            sample_id = str(row.get("sample_id", "")).strip()
            file_path = str(row.get("file_path", "")).strip()
            if not sample_id or not file_path:
                raise ValueError(f"Prediction row {line_number} is missing sample_id or file_path")
            grouped.setdefault(sample_id, {})[file_path] = _prediction_text(row, line_number)

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    written_files = 0
    backfilled_files = 0
    missing_backfills: list[str] = []
    backfill_paths = backfill_reference_paths or set()
    for sample_id, files in sorted(grouped.items()):
        project_dir = output_root / sample_id / "generated_project"
        for relative_path, content in sorted(files.items()):
            _write_project_file(project_dir, relative_path, content)
            written_files += 1
        if reference_dataset_root is not None:
            for relative_path in sorted(backfill_paths):
                if (project_dir / relative_path).exists():
                    continue
                reference_path = reference_dataset_root / sample_id / "final" / "generated_project" / relative_path
                if not reference_path.exists():
                    missing_backfills.append(f"{sample_id}:{relative_path}")
                    continue
                _write_project_file(project_dir, relative_path, reference_path.read_text(encoding="utf-8"))
                backfilled_files += 1

    return {
        "projects": len(grouped),
        "written_files": written_files,
        "backfilled_files": backfilled_files,
        "missing_backfills": missing_backfills,
        "output_root": str(output_root),
    }


def verify_assembled_projects(project_root: Path) -> dict[str, Any]:
    """Run no-EDA static project checks over assembled generated_project dirs."""
    project_results: list[dict[str, Any]] = []
    for project_dir in sorted(project_root.glob("*/generated_project")):
        sample_id = project_dir.parent.name
        files = _read_project_files(project_dir)
        project = GeneratedProject(project_name=sample_id, files=files)
        result = _verify_one_project(sample_id, project)
        project_results.append(result)

    return {
        "projects": len(project_results),
        "l0_passed": sum(1 for item in project_results if item["checks"]["l0"]["passed"]),
        "rtl_identifier_passed": sum(
            1 for item in project_results if item["checks"]["rtl_identifier"]["passed"]
        ),
        "testbench_static_passed": sum(
            1 for item in project_results if item["checks"]["testbench_static"]["passed"]
        ),
        "project_results": project_results,
    }


def verify_assembled_projects_with_tools(
    project_root: Path,
    *,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Run Verilator/Icarus simulation checks over assembled generated_project dirs."""
    runner = command_runner or CommandRunner()
    project_results: list[dict[str, Any]] = []
    for project_dir in sorted(project_root.glob("*/generated_project")):
        project_results.append(_verify_one_project_with_tools(project_dir, runner))

    return {
        "projects": len(project_results),
        "lint_passed": sum(1 for item in project_results if _stage_status(item, "lint") == "passed"),
        "sim_compile_passed": sum(
            1 for item in project_results if _stage_status(item, "sim_compile") == "passed"
        ),
        "sim_run_passed": sum(1 for item in project_results if _stage_status(item, "sim_run") == "passed"),
        "project_results": project_results,
    }


def verify_assembled_projects_with_synth(
    project_root: Path,
    *,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Run Yosys synthesis checks over assembled generated_project dirs."""
    runner = command_runner or CommandRunner()
    project_results: list[dict[str, Any]] = []
    for project_dir in sorted(project_root.glob("*/generated_project")):
        project_results.append(_verify_one_project_with_synth(project_dir, runner))

    return {
        "projects": len(project_results),
        "synth_passed": sum(1 for item in project_results if item["stage"]["status"] == "passed"),
        "project_results": project_results,
    }


def _req2file_prompt(row: dict[str, Any]) -> str:
    return (
        "Generate this SR2FPGA project file from the requirement.\n\n"
        f"SR2FPGA requirement:\n{str(row.get('requirement', '')).strip()}\n\n"
        f"File path:\n{str(row.get('file_path', '')).strip()}"
    )


def _prediction_text(row: dict[str, Any], line_number: int) -> str:
    for key in ("predicted_file_content", "prediction", "output", "content"):
        if key in row:
            return str(row[key])
    messages = row.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "assistant":
                return str(message.get("content", ""))
    raise ValueError(f"Prediction row {line_number} is missing predicted file content")


def _validate_eval_messages(messages: Any) -> list[dict[str, str]]:
    if not isinstance(messages, list) or not messages:
        raise ValueError("REQ2FILE eval row messages must be a non-empty list")
    normalized: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("REQ2FILE eval row messages must contain objects")
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"REQ2FILE eval row has unsupported role: {role}")
        if not content:
            raise ValueError("REQ2FILE eval row has empty message content")
        normalized.append({"role": role, "content": content})
    return normalized


def _write_project_file(project_dir: Path, relative_path: str, content: str) -> None:
    target = project_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _read_project_files(project_dir: Path) -> dict[str, str]:
    return {
        str(path.relative_to(project_dir)): path.read_text(encoding="utf-8")
        for path in sorted(project_dir.rglob("*"))
        if path.is_file()
    }


def _verify_one_project(sample_id: str, project: GeneratedProject) -> dict[str, Any]:
    manifest = _load_manifest(project.files.get("manifest.json", ""))
    sources = [str(item) for item in manifest.get("sources", [])] if isinstance(manifest, dict) else []
    testbench = ""
    if isinstance(manifest, dict) and isinstance(manifest.get("simulation"), dict):
        testbench = str(manifest["simulation"].get("testbench", ""))

    l0_result = check_project_l0(project)
    rtl_issues = check_rtl_identifiers(project, sources)
    testbench_issues = check_testbench_static_issues(project.files.get(testbench, "")) if testbench else []
    checks = {
        "l0": {
            "passed": l0_result.passed,
            "errors": l0_result.errors,
            "warnings": l0_result.warnings,
        },
        "rtl_identifier": {
            "passed": not rtl_issues,
            "issues": [
                {
                    "path": issue.path,
                    "line": issue.line,
                    "identifier": issue.identifier,
                    "context": issue.context,
                }
                for issue in rtl_issues
            ],
        },
        "testbench_static": {
            "passed": not testbench_issues,
            "issues": [
                {
                    "line": issue.line,
                    "failure_type": issue.failure_type,
                    "message": issue.message,
                }
                for issue in testbench_issues
            ],
        },
    }
    return {
        "sample_id": sample_id,
        "status": "passed" if all(check["passed"] for check in checks.values()) else "failed",
        "checks": checks,
    }


def _verify_one_project_with_tools(project_dir: Path, runner: CommandRunner) -> dict[str, Any]:
    sample_id = project_dir.parent.name
    manifest = _load_manifest((project_dir / "manifest.json").read_text(encoding="utf-8") if (project_dir / "manifest.json").exists() else "")
    sources = [str(item) for item in manifest.get("sources", [])] if isinstance(manifest, dict) else []
    testbench = ""
    top_module = str(manifest.get("top_module", "top")) if isinstance(manifest, dict) else "top"
    if isinstance(manifest, dict) and isinstance(manifest.get("simulation"), dict):
        testbench = str(manifest["simulation"].get("testbench", ""))

    stages: list[dict[str, Any]] = []
    lint = runner.run(["verilator", "--lint-only", "-Wall", *sources], cwd=project_dir, stage="lint")
    stages.append(_tool_result_dict(lint))
    if lint.status != "passed":
        return {"sample_id": sample_id, "status": "failed", "stages": stages}

    sim_compile = runner.run(
        ["iverilog", "-g2012", "-o", "sim.out", *sources, testbench],
        cwd=project_dir,
        stage="sim_compile",
    )
    stages.append(_tool_result_dict(sim_compile))
    if sim_compile.status != "passed":
        return {"sample_id": sample_id, "status": "failed", "stages": stages}

    sim_run = runner.run(["vvp", "sim.out"], cwd=project_dir, stage="sim_run")
    if sim_run.status == "passed" and "TEST_FAIL" in sim_run.stdout:
        sim_run = _replace_tool_status(sim_run, status="failed", stderr="Simulation printed TEST_FAIL\n")
    if sim_run.status == "passed" and "TEST_PASS" not in sim_run.stdout:
        sim_run = _replace_tool_status(sim_run, status="failed", stderr="Simulation did not print TEST_PASS\n")
    stages.append(_tool_result_dict(sim_run))
    return {
        "sample_id": sample_id,
        "status": "passed" if sim_run.status == "passed" else "failed",
        "top_module": top_module,
        "stages": stages,
    }


def _verify_one_project_with_synth(project_dir: Path, runner: CommandRunner) -> dict[str, Any]:
    sample_id = project_dir.parent.name
    manifest = _load_manifest((project_dir / "manifest.json").read_text(encoding="utf-8") if (project_dir / "manifest.json").exists() else "")
    sources = [str(item) for item in manifest.get("sources", [])] if isinstance(manifest, dict) else []
    top_module = str(manifest.get("top_module", "top")) if isinstance(manifest, dict) else "top"
    yosys_script = f"read_verilog {' '.join(sources)}; synth -top {top_module}; stat"
    synth = runner.run(["yosys", "-p", yosys_script], cwd=project_dir, stage="synth", timeout_seconds=60)
    measured_qor = parse_yosys_stats(f"{synth.stdout}\n{synth.stderr}") if synth.status == "passed" else {}
    return {
        "sample_id": sample_id,
        "status": "passed" if synth.status == "passed" else "failed",
        "top_module": top_module,
        "stage": _tool_result_dict(synth),
        "measured_qor": measured_qor,
    }


def _tool_result_dict(result: Any) -> dict[str, Any]:
    return {
        "stage": result.stage,
        "status": result.status,
        "exit_code": result.exit_code,
        "command": result.command,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _replace_tool_status(result: Any, *, status: str, stderr: str) -> Any:
    return type(result)(
        stage=result.stage,
        command=result.command,
        status=status,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=stderr,
        duration_seconds=result.duration_seconds,
    )


def _stage_status(project_result: dict[str, Any], stage: str) -> str:
    for item in project_result.get("stages", []):
        if item.get("stage") == stage:
            return str(item.get("status", ""))
    return ""


def _load_manifest(content: str) -> dict[str, Any]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _is_valid_json(text: str) -> bool:
    try:
        json.loads(text)
    except json.JSONDecodeError:
        return False
    return True


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


class OpenAIChatCompletionsClient:
    """Minimal OpenAI-compatible client for raw file-content generation."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        max_tokens: int,
        temperature: float,
        transport_attempts: int,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.transport_attempts = max(1, transport_attempts)

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.max_tokens > 0:
            payload["max_tokens"] = self.max_tokens
        data = self._request_with_retries(payload)
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenAI-compatible response did not contain choices[0].message.content") from exc

    def _request_with_retries(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.transport_attempts):
            try:
                return self._request_once(payload)
            except (TimeoutError, urllib.error.URLError, http.client.IncompleteRead) as exc:
                last_error = exc
                if attempt + 1 >= self.transport_attempts:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"OpenAI-compatible request failed: {last_error}") from last_error

    def _request_once(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI-compatible request failed with HTTP {exc.code}: {body}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or score SR2FPGA REQ2FILE evaluation JSONL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build eval prompts from requirement_to_file JSONL.")
    build_parser.add_argument("--input", required=True, type=Path)
    build_parser.add_argument("--output", required=True, type=Path)
    build_parser.add_argument("--sample-id-prefix", default="")
    build_parser.add_argument("--exclude-file-path", action="append", default=[])
    build_parser.add_argument("--limit", type=int, default=0)

    infer_parser = subparsers.add_parser("infer", help="Run OpenAI-compatible inference over eval prompts.")
    infer_parser.add_argument("--input", required=True, type=Path)
    infer_parser.add_argument("--output", required=True, type=Path)
    infer_parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    infer_parser.add_argument("--api-key", default="EMPTY")
    infer_parser.add_argument("--model", required=True)
    infer_parser.add_argument("--timeout-seconds", type=int, default=120)
    infer_parser.add_argument("--max-tokens", type=int, default=4096)
    infer_parser.add_argument("--temperature", type=float, default=0.0)
    infer_parser.add_argument("--transport-attempts", type=int, default=1)
    infer_parser.add_argument("--limit", type=int, default=0)

    score_parser = subparsers.add_parser("score", help="Score model prediction JSONL.")
    score_parser.add_argument("--input", required=True, type=Path)
    score_parser.add_argument("--output", type=Path)

    assemble_parser = subparsers.add_parser("assemble", help="Assemble prediction rows into project dirs.")
    assemble_parser.add_argument("--input", required=True, type=Path)
    assemble_parser.add_argument("--output-root", required=True, type=Path)
    assemble_parser.add_argument("--reference-dataset-root", type=Path)
    assemble_parser.add_argument("--backfill-reference-path", action="append", default=[])

    verify_parser = subparsers.add_parser("verify-static", help="Run no-EDA static checks over assembled projects.")
    verify_parser.add_argument("--project-root", required=True, type=Path)
    verify_parser.add_argument("--output", type=Path)

    verify_tools_parser = subparsers.add_parser("verify-tools", help="Run Verilator/Icarus checks over assembled projects.")
    verify_tools_parser.add_argument("--project-root", required=True, type=Path)
    verify_tools_parser.add_argument("--output", type=Path)

    verify_synth_parser = subparsers.add_parser("verify-synth", help="Run Yosys synthesis over assembled projects.")
    verify_synth_parser.add_argument("--project-root", required=True, type=Path)
    verify_synth_parser.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "build":
        count = build_eval_set(
            args.input,
            args.output,
            sample_id_prefix=args.sample_id_prefix,
            exclude_file_paths=set(args.exclude_file_path),
            limit=args.limit,
        )
        print(f"Built {count} REQ2FILE eval rows at {args.output}")
        return

    if args.command == "infer":
        client = OpenAIChatCompletionsClient(
            base_url=args.base_url,
            api_key=args.api_key,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            transport_attempts=args.transport_attempts,
        )
        count = run_inference(args.input, args.output, client=client, limit=args.limit)
        print(f"Wrote {count} REQ2FILE prediction rows to {args.output}")
        return

    if args.command == "assemble":
        report = assemble_predictions(
            args.input,
            args.output_root,
            reference_dataset_root=args.reference_dataset_root,
            backfill_reference_paths=set(args.backfill_reference_path),
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.command == "verify-static":
        report = verify_assembled_projects(args.project_root)
        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return

    if args.command == "verify-tools":
        report = verify_assembled_projects_with_tools(args.project_root)
        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return

    if args.command == "verify-synth":
        report = verify_assembled_projects_with_synth(args.project_root)
        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return

    report = score_predictions(args.input)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
