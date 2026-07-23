import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sr2fpga_agent import runner as runner_module
from sr2fpga_agent.cli import build_project_generator_for_connection
from sr2fpga_agent.deepseek import (
    AnthropicCompatibleConfig,
    DeepSeekOracleHisProjectGenerator,
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
    DeepSeekTwoStageProjectGenerator,
    OpenAICompatibleConfig,
)
from sr2fpga_agent.runner import (
    PlannedSample,
    RunnerConfig,
    SourceConnection,
    TaskConfig,
    _calibration_breakdown,
    _project_generator_for_sample,
    load_runner_config,
    resolve_source_connection,
    runner_preflight,
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

    def test_openai_compat_without_generation_mode_defaults_to_two_stage_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "claude": {
                        "kind": "openai_compat",
                        "model": "claude-opus-4-8",
                        "base_url": "https://api.anthropic.com/v1",
                        "api_key_env": "ANTHROPIC_API_KEY",
                    }
                },
            )
            config = load_runner_config(path)
            conn = config.sources["claude"]
            self.assertEqual(conn.generation_mode, "two_stage")
            metadata = PlannedSample(
                sample_id="s_claude", source="claude", task_type="counter", width=8,
                project_name="p", requirement="r",
            ).metadata(config)
            self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.1")
            self.assertEqual(metadata["training_split"], "quarantine")

    def test_deepseek_his_v12_without_generation_mode_defaults_to_two_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "ds12": {
                        "kind": "deepseek-his-v12",
                        "model": "deepseek-v4-flash",
                        "base_url": "https://api.deepseek.com",
                        "api_key_env": "DEEPSEEK_API_KEY",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["ds12"].generation_mode, "two_stage")

    def test_deepseek_without_generation_mode_defaults_to_direct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "ds": {
                        "kind": "deepseek",
                        "model": "deepseek-v4-flash",
                        "base_url": "https://api.deepseek.com",
                        "api_key_env": "DEEPSEEK_API_KEY",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["ds"].generation_mode, "direct")

    def test_deterministic_without_generation_mode_stays_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "det": {
                        "kind": "deterministic",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["det"].generation_mode, "")

    def test_explicit_two_stage_is_left_untouched(self) -> None:
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
            self.assertEqual(config.sources["claude"].generation_mode, "two_stage")

    def test_anthropic_compat_defaults_to_two_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "claude": {
                        "kind": "anthropic_compat",
                        "model": "claude-opus-4-8",
                        "base_url": "https://w.ciykj.cn/v1",
                        "api_key_env": "ANTHROPIC_API_KEY",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["claude"].kind, "anthropic_compat")
            self.assertEqual(config.sources["claude"].generation_mode, "two_stage")

    def test_multi_teacher_example_uses_anthropic_client_for_official_claude_endpoint(self) -> None:
        config = load_runner_config(Path("configs/legacy/sr2fpga_multi_teacher.example.yaml"))
        claude = config.sources["claude"]

        self.assertEqual(claude.kind, "anthropic_compat")
        self.assertEqual(claude.base_url, "https://api.anthropic.com/v1")

    def test_openai_compat_explicit_direct_mode_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "claude": {
                        "kind": "openai_compat",
                        "model": "claude-opus-4-8",
                        "base_url": "https://api.anthropic.com/v1",
                        "api_key_env": "ANTHROPIC_API_KEY",
                        "generation_mode": "direct",
                    }
                },
            )
            with self.assertRaises(SystemExit):
                load_runner_config(path)


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

    def test_legacy_deepseek_oracle_his_falls_back_to_global(self) -> None:
        config = _base_config(api_key_env="DEEPSEEK_API_KEY")
        conn = resolve_source_connection(config, "deepseek-oracle-his-v12")
        self.assertEqual(conn.kind, "deepseek-oracle-his-v12")
        self.assertEqual(conn.generation_mode, "oracle_his2project")


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

    def test_anthropic_compat_builds_two_stage_with_official_client(self) -> None:
        conn = SourceConnection(
            name="claude", kind="anthropic_compat", model="claude-opus-4-8",
            base_url="https://w.ciykj.cn/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator, DeepSeekTwoStageProjectGenerator)
        client_config = generator.his_project_generator.client.config
        self.assertIsInstance(client_config, AnthropicCompatibleConfig)
        self.assertEqual(client_config.model, "claude-opus-4-8")
        self.assertEqual(client_config.base_url, "https://w.ciykj.cn/v1")
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

    def test_deepseek_oracle_his_kind_builds_oracle_his_project_generator(self) -> None:
        conn = SourceConnection(
            name="deepseek-oracle-his-v12", kind="deepseek-oracle-his-v12", model="deepseek-v4-pro",
            base_url="https://api.deepseek.com", api_key_env="DEEPSEEK_API_KEY",
            generation_mode="oracle_his2project",
        )
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-ds"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator, DeepSeekOracleHisProjectGenerator)

    def test_missing_key_raises(self) -> None:
        conn = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY_ABSENT_FOR_TEST",
            generation_mode="two_stage",
        )
        with self.assertRaises(SystemExit):
            build_project_generator_for_connection(conn)

    def test_anthropic_compat_builds_repairer_with_official_client(self) -> None:
        from sr2fpga_agent.cli import build_repairer_for_connection

        conn = SourceConnection(
            name="claude-repair", kind="anthropic_compat", model="claude-opus-4-8",
            base_url="https://w.ciykj.cn/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            repairer = build_repairer_for_connection(conn)
        self.assertIsInstance(repairer, DeepSeekRepairer)
        client_config = repairer.client.config
        self.assertIsInstance(client_config, AnthropicCompatibleConfig)
        self.assertEqual(client_config.model, "claude-opus-4-8")
        self.assertEqual(client_config.base_url, "https://w.ciykj.cn/v1")

    def test_repairer_inherits_frozen_transport_and_token_settings(self) -> None:
        from sr2fpga_agent.cli import build_repairer_for_connection

        connections = [
            SourceConnection(
                name="claude-repair",
                kind="anthropic_compat",
                model="claude-opus-4-8",
                base_url="https://api.anthropic.com/v1",
                api_key_env="ANTHROPIC_API_KEY",
                generation_mode="two_stage",
                timeout_seconds=600,
                transport_attempts=5,
                max_tokens=32768,
            ),
            SourceConnection(
                name="gpt-repair",
                kind="openai_compat",
                model="gpt-5.5",
                base_url="https://api.openai.com/v1",
                api_key_env="OPENAI_API_KEY",
                generation_mode="two_stage",
                timeout_seconds=600,
                transport_attempts=5,
                max_tokens=32768,
            ),
        ]

        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "sk-a", "OPENAI_API_KEY": "sk-o"},
            clear=False,
        ):
            repairers = [build_repairer_for_connection(connection) for connection in connections]

        for repairer in repairers:
            self.assertEqual(repairer.client.config.timeout_seconds, 600)
            self.assertEqual(repairer.client.config.transport_attempts, 5)
            self.assertEqual(repairer.client.config.max_tokens, 32768)


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


class SameSourceRepairTest(unittest.TestCase):
    def _sample(self, source: str) -> PlannedSample:
        return PlannedSample(
            sample_id=f"sample_{source}",
            source=source,
            task_type="counter",
            width=8,
            project_name=f"project_{source}",
            requirement="Generate an 8-bit counter.",
            requirement_style="simple_prompt",
        )

    def test_same_as_source_builds_and_caches_each_teachers_repairer(self) -> None:
        sources = {
            "gpt": SourceConnection(
                name="gpt",
                kind="openai_compat",
                model="gpt-5.5",
                base_url="https://api.openai.com/v1",
                api_key_env="OPENAI_API_KEY",
                generation_mode="two_stage",
            ),
            "claude": SourceConnection(
                name="claude",
                kind="anthropic_compat",
                model="claude-opus-4-8",
                base_url="https://api.anthropic.com/v1",
                api_key_env="ANTHROPIC_API_KEY",
                generation_mode="two_stage",
            ),
        }
        config = _base_config(repair_provider="same_as_source", max_attempts=3, sources=sources)
        built: list[str] = []

        def build(connection: SourceConnection) -> object:
            built.append(connection.name)
            return object()

        cache: dict[str, object | None] = {}
        with patch.object(runner_module, "build_repairer_for_connection", side_effect=build):
            gpt_first = runner_module._repairer_for_sample(cache, config, self._sample("gpt"))
            gpt_second = runner_module._repairer_for_sample(cache, config, self._sample("gpt"))
            claude = runner_module._repairer_for_sample(cache, config, self._sample("claude"))

        self.assertIs(gpt_first, gpt_second)
        self.assertIsNot(gpt_first, claude)
        self.assertEqual(built, ["gpt", "claude"])
        self.assertEqual(set(cache), {"gpt", "claude"})

    def test_same_as_source_returns_none_for_deterministic_sample(self) -> None:
        config = _base_config(repair_provider="same_as_source", max_attempts=3)

        repairer = runner_module._repairer_for_sample({}, config, self._sample("deterministic"))

        self.assertIsNone(repairer)

    def test_same_as_source_is_not_checked_as_a_literal_provider(self) -> None:
        source = SourceConnection(
            name="gpt",
            kind="openai_compat",
            model="gpt-5.5",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(
            repair_provider="same_as_source",
            max_attempts=3,
            sources={"gpt": source},
            tasks=[TaskConfig(source="gpt", task_type="counter", widths=[8], count=1)],
        )
        sample = self._sample("gpt")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            diagnostics, errors = runner_module._source_auth_diagnostics(
                config,
                [sample],
                validate_provider=False,
            )

        self.assertEqual(errors, [])
        self.assertEqual(set(diagnostics), {"gpt"})
        self.assertNotIn("same_as_source", diagnostics)

    def test_same_as_source_metadata_records_policy_and_resolved_source(self) -> None:
        source = SourceConnection(
            name="gpt",
            kind="openai_compat",
            model="gpt-5.5",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(
            repair_provider="same_as_source",
            max_attempts=3,
            sources={"gpt": source},
        )

        metadata = self._sample("gpt").metadata(config)

        self.assertEqual(metadata["repair_provider_policy"], "same_as_source")
        self.assertEqual(metadata["repair_provider_resolved"], "gpt")


class MetadataTest(unittest.TestCase):
    def _sample(self, source: str) -> PlannedSample:
        return PlannedSample(
            sample_id=f"s_{source}", source=source, task_type="counter", width=8,
            project_name="p", requirement="r", requirement_style="simple_prompt",
            difficulty_tier="T1",
        )

    def test_openai_compat_two_stage_is_quarantined_until_vetted(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            generation_mode="two_stage",
        )
        config = _base_config(sources={"claude": claude})
        metadata = self._sample("claude").metadata(config)
        self.assertEqual(metadata["failure_origin"], "natural_llm")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.1")
        self.assertEqual(metadata["training_split"], "quarantine")
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

    def test_deepseek_oracle_his_metadata_is_clean_v12_behavior_files(self) -> None:
        config = _base_config(api_key_env="DEEPSEEK_API_KEY")
        metadata = self._sample("deepseek-oracle-his-v12").metadata(config)
        self.assertEqual(metadata["failure_origin"], "natural_llm")
        self.assertEqual(metadata["system_his_schema_version"], "system-his-v1.2")
        self.assertEqual(metadata["training_split"], "clean")
        self.assertEqual(metadata["contract_skeleton_mode"], "behavior_files")


class PreflightAuthTest(unittest.TestCase):
    def test_missing_key_for_one_source_only(self) -> None:
        claude = SourceConnection(
            name="claude", kind="openai_compat", model="claude-opus-4-8",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_KEY_PRESENT",
            generation_mode="two_stage",
        )
        gpt = SourceConnection(
            name="gpt55", kind="openai_compat", model="gpt-5.5",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_KEY_ABSENT",
            generation_mode="two_stage",
        )
        config = _base_config(
            sources={"claude": claude, "gpt55": gpt},
            tasks=[
                TaskConfig(source="claude", task_type="counter", widths=[8], count=1),
                TaskConfig(source="gpt55", task_type="counter", widths=[8], count=1),
            ],
        )
        env = {"ANTHROPIC_KEY_PRESENT": "sk-a"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("OPENAI_KEY_ABSENT", None)
            report = runner_preflight(config, run_id=None, validate_provider=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("OPENAI_KEY_ABSENT" in e for e in report["errors"]))
        self.assertFalse(any("ANTHROPIC_KEY_PRESENT" in e for e in report["errors"]))
        self.assertIn("gpt55", report["provider_auth"])
        self.assertEqual(report["provider_auth"]["claude"]["status"], "not_checked")

    def test_repair_provider_missing_key_fails_preflight(self) -> None:
        config = _base_config(
            repair_provider="deepseek",
            api_key_env="DEEPSEEK_API_KEY",
            tasks=[
                TaskConfig(source="deterministic", task_type="counter", widths=[8], count=1),
            ],
        )
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DEEPSEEK_API_KEY", None)
            report = runner_preflight(config, run_id=None, validate_provider=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("DEEPSEEK_API_KEY" in e for e in report["errors"]))
        self.assertIn("deepseek", report["provider_auth"])
        self.assertEqual(report["provider_auth"]["deepseek"]["status"], "skipped")

    def test_repair_provider_present_key_not_checked(self) -> None:
        config = _base_config(
            repair_provider="deepseek",
            api_key_env="DEEPSEEK_API_KEY",
            tasks=[
                TaskConfig(source="deterministic", task_type="counter", widths=[8], count=1),
            ],
        )
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-repair"}, clear=False):
            report = runner_preflight(config, run_id=None, validate_provider=False)
        self.assertIn("deepseek", report["provider_auth"])
        self.assertEqual(report["provider_auth"]["deepseek"]["status"], "not_checked")
        self.assertFalse(any("DEEPSEEK_API_KEY" in e for e in report["errors"]))


class PerTeacherReportingTest(unittest.TestCase):
    def test_calibration_matrix_has_one_row_per_teacher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_root = Path(tmp)
            for source, pass_level in (("claude", "L3"), ("gpt55", "L0")):
                sample_id = f"sample_{source}"
                sample_dir = dataset_root / sample_id
                (sample_dir / "eval").mkdir(parents=True)
                (sample_dir / "eval" / "labels.json").write_text(
                    json.dumps({"pass_level": pass_level, "checks": {}, "failure_count": 0}),
                    encoding="utf-8",
                )
                (sample_dir / "metadata.json").write_text(
                    json.dumps({"source": source, "difficulty_tier": "T1"}),
                    encoding="utf-8",
                )
            breakdown = _calibration_breakdown(dataset_root, ["sample_claude", "sample_gpt55"])
            source_matrix = breakdown["calibration_matrix"]["source"]
            self.assertIn("claude", source_matrix)
            self.assertIn("gpt55", source_matrix)
            self.assertEqual(source_matrix["claude"]["l3_pass_rate"], 1.0)
            self.assertEqual(source_matrix["gpt55"]["l3_pass_rate"], 0.0)


class TimeoutConfigTest(unittest.TestCase):
    def test_load_sources_parses_timeout_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "slow": {
                        "kind": "openai_compat",
                        "model": "qwen3.7-plus",
                        "base_url": "https://example/v1",
                        "api_key_env": "X_API_KEY",
                        "generation_mode": "two_stage",
                        "timeout_seconds": 600,
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["slow"].timeout_seconds, 600)

    def test_load_sources_parses_transport_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "single_try": {
                        "kind": "openai_compat",
                        "model": "qwen3.7-plus",
                        "base_url": "https://example/v1",
                        "api_key_env": "X_API_KEY",
                        "generation_mode": "two_stage",
                        "transport_attempts": 1,
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["single_try"].transport_attempts, 1)

    def test_load_sources_parses_max_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "bounded": {
                        "kind": "openai_compat",
                        "model": "qwen3.7-plus",
                        "base_url": "https://example/v1",
                        "api_key_env": "X_API_KEY",
                        "generation_mode": "two_stage",
                        "max_tokens": 4096,
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["bounded"].max_tokens, 4096)

    def test_timeout_seconds_defaults_to_120_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(
                tmp,
                {
                    "fast": {
                        "kind": "openai_compat",
                        "model": "qwen3.7-plus",
                        "base_url": "https://example/v1",
                        "api_key_env": "X_API_KEY",
                        "generation_mode": "two_stage",
                    }
                },
            )
            config = load_runner_config(path)
            self.assertEqual(config.sources["fast"].timeout_seconds, 120)

    def test_builder_passes_timeout_to_client(self) -> None:
        conn = SourceConnection(
            name="slow", kind="openai_compat", model="qwen3.7-plus",
            base_url="https://example/v1", api_key_env="X_API_KEY",
            generation_mode="two_stage", timeout_seconds=600,
        )
        with patch.dict(os.environ, {"X_API_KEY": "sk-test"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator.his_project_generator.client.config, OpenAICompatibleConfig)
        self.assertEqual(
            generator.his_project_generator.client.config.timeout_seconds, 600
        )

    def test_builder_passes_transport_attempts_to_client(self) -> None:
        conn = SourceConnection(
            name="single_try", kind="openai_compat", model="qwen3.7-plus",
            base_url="https://example/v1", api_key_env="X_API_KEY",
            generation_mode="two_stage", transport_attempts=1,
        )
        with patch.dict(os.environ, {"X_API_KEY": "sk-test"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator.his_project_generator.client.config, OpenAICompatibleConfig)
        self.assertEqual(
            generator.his_project_generator.client.config.transport_attempts, 1
        )

    def test_builder_passes_max_tokens_to_openai_compatible_client(self) -> None:
        conn = SourceConnection(
            name="bounded", kind="openai_compat", model="qwen3.7-plus",
            base_url="https://example/v1", api_key_env="X_API_KEY",
            generation_mode="two_stage", max_tokens=4096,
        )
        with patch.dict(os.environ, {"X_API_KEY": "sk-test"}, clear=False):
            generator = build_project_generator_for_connection(conn)
        self.assertIsInstance(generator.his_project_generator.client.config, OpenAICompatibleConfig)
        self.assertEqual(
            generator.his_project_generator.client.config.max_tokens, 4096
        )
