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


from LLM.src.sr2fpga_agent.runner import resolve_source_connection


def _base_config(**overrides) -> RunnerConfig:
    base = dict(
        dataset_root=Path("d"),
        export_root=Path("e"),
        run_root=Path("r"),
        provider="deterministic",
        repair_provider="none",
        max_attempts=1,
        refresh_exports=True,
        line_b_targets={},
        tasks=[],
    )
    base.update(overrides)
    return RunnerConfig(**base)


class ResolveSourceTest(unittest.TestCase):
    def test_resolves_named_source_from_table(self) -> None:
        conn = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": conn})
        self.assertIs(resolve_source_connection(config, "claude"), conn)

    def test_deterministic_source_needs_no_entry(self) -> None:
        config = _base_config()
        conn = resolve_source_connection(config, "deterministic")
        self.assertEqual(conn.kind, "deterministic")

    def test_legacy_deepseek_his_v12_falls_back_to_global(self) -> None:
        config = _base_config(
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
        )
        conn = resolve_source_connection(config, "deepseek-his-v12")
        self.assertEqual(conn.kind, "deepseek-his-v12")
        self.assertEqual(conn.generation_mode, "two_stage")
        self.assertEqual(conn.model, "deepseek-v4-flash")
        self.assertEqual(conn.api_key_env, "DEEPSEEK_API_KEY")

    def test_legacy_deepseek_direct_falls_back_to_global(self) -> None:
        config = _base_config(api_key_env="DEEPSEEK_API_KEY")
        conn = resolve_source_connection(config, "deepseek")
        self.assertEqual(conn.kind, "deepseek")
        self.assertEqual(conn.generation_mode, "direct")


import os
from unittest.mock import patch

from LLM.src.sr2fpga_agent.cli import build_project_generator_for_connection
from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekProjectGenerator,
    DeepSeekTwoStageProjectGenerator,
)


class ConnectionBuilderTest(unittest.TestCase):
    def test_deterministic_connection_returns_none(self) -> None:
        conn = SourceConnection(name="deterministic", kind="deterministic")
        self.assertIsNone(build_project_generator_for_connection(conn))

    def test_openai_compat_builds_two_stage_with_resolved_endpoint(self) -> None:
        conn = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator, DeepSeekTwoStageProjectGenerator)
        client_config = generator.his_project_generator.client.config
        self.assertEqual(client_config.model, "claude-opus-4-8")
        self.assertEqual(client_config.base_url, "https://api.anthropic.com/v1")
        self.assertEqual(client_config.api_key, "sk-test")

    def test_legacy_deepseek_kind_builds_single_stage(self) -> None:
        conn = SourceConnection(
            name="deepseek", kind="deepseek", model="deepseek-v4-flash",
            base_url="https://api.deepseek.com", api_key_env="DEEPSEEK_API_KEY",
            generation_mode="direct",
        )
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-ds"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator, DeepSeekProjectGenerator)

    def test_missing_key_raises(self) -> None:
        conn = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY_ABSENT_FOR_TEST",
            generation_mode="two_stage",
        )
        with self.assertRaises(SystemExit):
            build_project_generator_for_connection(conn)


from LLM.src.sr2fpga_agent.runner import PlannedSample, _project_generator_for_sample


class PerSampleDispatchTest(unittest.TestCase):
    def test_two_different_teachers_resolve_to_different_endpoints(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        gpt = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": claude, "gpt55": gpt})

        def make_sample(source: str) -> PlannedSample:
            return PlannedSample(
                sample_id=f"sample_{source}", source=source, task_type="counter",
                width=8, project_name=source, requirement="r",
                requirement_style="simple_prompt",
            )

        cache: dict = {}
        events = Path("ignored")
        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "sk-a", "OPENAI_API_KEY": "sk-o"},
            clear=False,
        ):
            gen_claude = _project_generator_for_sample(cache, config, make_sample("claude"), events)
            gen_gpt = _project_generator_for_sample(cache, config, make_sample("gpt55"), events)

        self.assertEqual(
            gen_claude.his_project_generator.client.config.base_url,
            "https://api.anthropic.com/v1",
        )
        self.assertEqual(gen_gpt.his_project_generator.client.config.model, "gpt-5.5")


class MetadataTest(unittest.TestCase):
    def _sample(self, source: str) -> PlannedSample:
        return PlannedSample(
            sample_id=f"s_{source}", source=source, task_type="counter", width=8,
            project_name="p", requirement="r", requirement_style="simple_prompt",
            difficulty_tier="T1",
        )

    def test_openai_compat_two_stage_is_clean_v12_natural_llm(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": claude})
        metadata = self._sample("claude").metadata(config)
        self.assertEqual(metadata["failure_origin"], "natural_llm")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.2")
        self.assertEqual(metadata["training_split"], "clean")
        self.assertEqual(metadata["model"], "claude-opus-4-8")

    def test_deterministic_metadata_unchanged(self) -> None:
        config = _base_config()
        metadata = self._sample("deterministic").metadata(config)
        self.assertEqual(metadata["failure_origin"], "deterministic_template")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.2")

    def test_legacy_deepseek_direct_is_v11_quarantine(self) -> None:
        config = _base_config(api_key_env="DEEPSEEK_API_KEY")
        metadata = self._sample("deepseek").metadata(config)
        self.assertEqual(metadata["failure_origin"], "natural_llm")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.1")
        self.assertEqual(metadata["training_split"], "quarantine")
