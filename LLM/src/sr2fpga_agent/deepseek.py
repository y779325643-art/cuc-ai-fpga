"""DeepSeek provider for SR2FPGA project generation."""

from __future__ import annotations

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

    def __init__(self, client: DeepSeekClient) -> None:
        self.client = client

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        content = self.client.chat(_project_messages(request, platform))
        files = parse_project_files(content)
        return GeneratedProject(project_name=request.project_name, files=files)


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

    missing = sorted(REQUIRED_PROJECT_FILES - set(files))
    if missing:
        raise ValueError(f"DeepSeek output is missing required files: {', '.join(missing)}")
    return files


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

Return JSON in this exact shape:
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

The Verilog must be synthesizable and the testbench must print TEST_PASS on success.
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
