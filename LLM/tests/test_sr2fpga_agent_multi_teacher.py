import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.runner import (
    RunnerConfig,
    SourceConnection,
    load_runner_config,
)


def _write_config(tmp: str, sources: dict) -> Path:
    config_path = Path(tmp) / "runner.json"
    config_path.write_text(
        json.dumps(
            {
                "dataset_root": "datasets/sr2fpga_rtl_v1",
                "export_root": "datasets/sr2fpga_rtl_v1_exports",
                "run_root": "tmp/sr2fpga_runs",
                "provider": "deterministic",
                "repair_provider": "none",
                "max_attempts": 1,
                "refresh_exports": True,
                "line_b_targets": {},
                "sources": sources,
                "tasks": [
                    {"source": "claude", "task_type": "counter", "widths": [8], "count": 1}
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


class SourcesParsingTest(unittest.TestCase):
    def test_sources_block_parsed_into_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "claude": {
                        "kind": "openai_compat",
                        "model": "claude-opus-4-8",
                        "base_url": "https://api.anthropic.com/v1",
                        "api_key_env": "ANTHROPIC_API_KEY",
                        "generation_mode": "two_stage",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertIn("claude", config.sources)
            conn = config.sources["claude"]
            self.assertEqual(conn.kind, "openai_compat")
            self.assertEqual(conn.model, "claude-opus-4-8")
            self.assertEqual(conn.base_url, "https://api.anthropic.com/v1")
            self.assertEqual(conn.api_key_env, "ANTHROPIC_API_KEY")
            self.assertEqual(conn.generation_mode, "two_stage")

    def test_missing_sources_block_defaults_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runner.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dataset_root": "d",
                        "export_root": "e",
                        "run_root": "r",
                        "tasks": [],
                    }
                ),
                encoding="utf-8",
            )
            config = load_runner_config(config_path)
            self.assertEqual(config.sources, {})
