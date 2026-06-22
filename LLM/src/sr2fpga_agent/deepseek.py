"""DeepSeek provider for SR2FPGA project generation."""

from __future__ import annotations

import difflib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


REQUIRED_PROJECT_FILES = {
    "system_his.json",
    "manifest.json",
    "rtl/top.v",
    "constraints/timing.sdc",
    "sim/tb_top.v",
    "reports/predicted_qor.json",
}


@dataclass(frozen=True)
class DeepSeekConfig:
    """OpenAI-compatible DeepSeek API configuration."""

    api_key: str
    model: str = "deepseek-v4-flash"
    base_url: str = "https://api.deepseek.com"
    timeout_seconds: int = 120


class DeepSeekClient:
    """Small stdlib HTTP client for DeepSeek chat completions."""

    def __init__(self, config: DeepSeekConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DeepSeek API request failed with HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"DeepSeek API request failed: {exc.reason}") from exc

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("DeepSeek API response did not contain choices[0].message.content") from exc


class DeepSeekProjectGenerator:
    """Generate a project package by asking DeepSeek for required files."""

    def __init__(self, client: DeepSeekClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        messages = _project_messages(request, platform)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(content)
                return GeneratedProject(project_name=request.project_name, files=files)
            except ValueError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek generator did not run")


def parse_project_files(content: str) -> dict[str, str]:
    """Parse DeepSeek JSON output into project files."""
    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek output is not valid JSON: {exc.msg}") from exc

    raw_files = payload.get("files")
    if isinstance(raw_files, dict):
        files = {str(path): str(file_content) for path, file_content in raw_files.items()}
    elif isinstance(raw_files, list):
        files = _files_from_list(raw_files)
    else:
        raise ValueError("DeepSeek output must contain files as an object or list")

    files = {path: _ensure_trailing_newline(content) for path, content in files.items()}
    missing = sorted(REQUIRED_PROJECT_FILES - set(files))
    if missing:
        raise ValueError(f"DeepSeek output is missing required files: {', '.join(missing)}")
    _validate_manifest(files)
    return files


def diff_projects(old: GeneratedProject, new: GeneratedProject) -> str:
    """Return a unified diff between two generated project file maps."""
    chunks: list[str] = []
    for path in sorted(set(old.files) | set(new.files)):
        old_content = old.files.get(path, "")
        new_content = new.files.get(path, "")
        if old_content == new_content:
            continue
        chunks.extend(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
    return "".join(chunks)


def _ensure_trailing_newline(content: str) -> str:
    return content if content.endswith("\n") else content + "\n"


def _validate_manifest(files: dict[str, str]) -> None:
    try:
        manifest = json.loads(files["manifest.json"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc

    missing_fields: list[str] = []
    if not isinstance(manifest.get("top_module"), str) or not manifest["top_module"]:
        missing_fields.append("top_module")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        missing_fields.append("sources")

    simulation = manifest.get("simulation")
    testbench = simulation.get("testbench") if isinstance(simulation, dict) else None
    if not isinstance(testbench, str) or not testbench:
        missing_fields.append("simulation.testbench")

    if missing_fields:
        raise ValueError(f"manifest.json missing required fields: {', '.join(missing_fields)}")

    missing_sources = sorted(path for path in sources if path not in files)
    if missing_sources:
        raise ValueError(f"manifest.json references missing source files: {', '.join(missing_sources)}")
    if testbench not in files:
        raise ValueError(f"manifest.json references missing testbench file: {testbench}")


def _files_from_list(raw_files: list[Any]) -> dict[str, str]:
    files: dict[str, str] = {}
    for item in raw_files:
        if not isinstance(item, dict) or "path" not in item or "content" not in item:
            raise ValueError("Each file entry must contain path and content")
        files[str(item["path"])] = str(item["content"])
    return files


def _strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _project_messages(request: ProjectRequest, platform: PlatformProfile) -> list[dict[str, str]]:
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    system = (
        "You generate complete FPGA RTL project packages as JSON. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Generate a Verilog RTL project package for SR2FPGA.

Project:
- project_name: {request.project_name}
- task_type: {request.task_type}
- width: {request.width}
- description: {request.description or "No extra description provided."}

Platform:
- name: {platform.name}
- vendor: {platform.vendor}
- toolchain: {platform.toolchain}
- clock_hz: {platform.clock_hz}
- reset_polarity: {platform.reset_polarity}

Required files:
{required_files}

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
    "constraints/timing.sdc": "...",
    "sim/tb_top.v": "...",
    "reports/predicted_qor.json": "..."
  }}
}}

The manifest.json file content must itself be JSON and must contain this tool
pipeline schema:
{{
  "project_name": "{request.project_name}",
  "top_module": "top",
  "sources": ["rtl/top.v"],
  "constraints": ["constraints/timing.sdc"],
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}

The Verilog must be synthesizable and the testbench must print TEST_PASS on success.
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
