import json
import tempfile
import unittest
from pathlib import Path

from sr2fpga_agent.measurement_freeze import (
    build_measurement_freeze,
    freeze_fingerprint,
    write_or_validate_freeze,
)


class MeasurementFreezeTest(unittest.TestCase):
    def _manifest(self) -> dict:
        return build_measurement_freeze(
            run_id="phase-d",
            config_fingerprint="config-abc",
            sample_records=[
                {
                    "sample_id": "sample_gpt_fir",
                    "source": "gpt",
                    "family_id": "fir_filter",
                    "paired_requirement_id": "fir_filter:1234",
                    "requirement_sha256": "1" * 64,
                }
            ],
            source_records=[
                {"name": "gpt", "kind": "openai_compat", "model": "gpt-5.5"}
            ],
            max_attempts=3,
            timeouts={"generation_seconds": 600, "l4_open_seconds": 600},
            tool_versions={"verilator": "5.036", "yosys": "0.54"},
            l4_family_ids=["fir_filter"],
        )

    def test_fingerprint_is_independent_of_mapping_order(self) -> None:
        left = {"models": {"gpt": "gpt-5.5", "claude": "claude-opus-4-8"}, "seed": 7}
        right = {"seed": 7, "models": {"claude": "claude-opus-4-8", "gpt": "gpt-5.5"}}

        self.assertEqual(freeze_fingerprint(left), freeze_fingerprint(right))

    def test_build_rejects_secret_like_fields_recursively(self) -> None:
        for field in ("api_key", "authorization", "access_token", "client_secret"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "secret-like field"):
                    build_measurement_freeze(
                        run_id="phase-d",
                        config_fingerprint="abc",
                        sample_records=[],
                        source_records=[{"name": "gpt", "nested": {field: "forbidden"}}],
                        max_attempts=3,
                        timeouts={"generation_seconds": 600},
                        tool_versions={},
                        l4_family_ids=["fir_filter"],
                    )

    def test_write_fresh_and_validate_identical_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurement_freeze.json"
            manifest = self._manifest()

            first = write_or_validate_freeze(path, manifest, resume=False)
            resumed = write_or_validate_freeze(path, manifest, resume=True)

            self.assertEqual(first, resumed)
            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored["freeze_fingerprint"], first)
            self.assertEqual(stored["sample_count"], 1)

    def test_resume_rejects_changed_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurement_freeze.json"
            manifest = self._manifest()
            write_or_validate_freeze(path, manifest, resume=False)
            changed = {**manifest, "max_attempts": 2}

            with self.assertRaisesRegex(RuntimeError, "measurement freeze mismatch"):
                write_or_validate_freeze(path, changed, resume=True)

    def test_resume_rejects_missing_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurement_freeze.json"

            with self.assertRaisesRegex(RuntimeError, "measurement freeze missing"):
                write_or_validate_freeze(path, self._manifest(), resume=True)


if __name__ == "__main__":
    unittest.main()
