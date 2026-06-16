import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class ServingEntrypointsTest(unittest.TestCase):
    def test_shell_scripts_are_forced_to_lf_by_git(self) -> None:
        attributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")

        self.assertIn("*.sh text eol=lf", attributes)

    def test_runtime_scripts_use_persistent_e_drive_venv_by_default(self) -> None:
        scripts = [
            "setup_server.sh",
            "serve_qwen_vllm.sh",
            "serve_vllm.sh",
            "train_lora.sh",
            "merge_lora.sh",
        ]

        for script_name in scripts:
            script = (REPO_ROOT / f"LLM/scripts/{script_name}").read_text(encoding="utf-8")
            with self.subTest(script=script_name):
                self.assertIn("/mnt/e/Aowen/venvs/cuc-ai-fpga", script)
                self.assertIn("LLM_VENV_PATH", script)

    def _capture_vllm_args(
        self, script: Path, extra_env: dict[str, str] | None = None
    ) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            capture_file = temp_path / "args.txt"
            fake_vllm = temp_path / "vllm"
            fake_vllm.write_text(
                '#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$CAPTURE_FILE"\n',
                encoding="utf-8",
            )
            fake_vllm.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{temp_path}:{env['PATH']}"
            env["CAPTURE_FILE"] = str(capture_file)
            if extra_env:
                env.update(extra_env)
            subprocess.run(
                ["bash", str(script)],
                cwd=REPO_ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            return capture_file.read_text(encoding="utf-8").splitlines()

    def test_gemma_vllm_uses_known_local_path_and_text_only_flags(self) -> None:
        args = self._capture_vllm_args(REPO_ROOT / "LLM/scripts/serve_vllm.sh")

        self.assertEqual(args[0:2], ["serve", "/mnt/c/Users/Administrator/models/gemma-4-12B-it"])
        self.assertIn("--language-model-only", args)
        self.assertIn("--trust-remote-code", args)
        self.assertIn("--enforce-eager", args)
        self.assertNotIn("--limit-mm-per-prompt", args)
        self.assertNotIn("/mnt/c/Users/models/gemma-4-12B-it", args)

    def test_qwen_vllm_has_stable_coder_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as model_dir:
            args = self._capture_vllm_args(
                REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh",
                {"QWEN_MODEL_PATH": model_dir},
            )

        self.assertEqual(args[0:2], ["serve", model_dir])
        self.assertIn("--max-model-len", args)
        self.assertEqual(args[args.index("--max-model-len") + 1], "4096")
        self.assertEqual(args[args.index("--served-model-name") + 1], "cuc-ai-fpga")

    def test_qwen_vllm_defaults_to_verified_windows_model_path(self) -> None:
        script = (
            REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "/mnt/c/Users/Administrator/models/Qwen2.5-Coder-7B-Instruct",
            script,
        )

    def test_qwen_vllm_explains_how_to_download_a_missing_local_model(self) -> None:
        missing_path = "/tmp/definitely-missing-qwen-model"
        env = os.environ.copy()
        env["QWEN_MODEL_PATH"] = missing_path

        result = subprocess.run(
            ["bash", str(REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh")],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"Qwen model directory not found: {missing_path}", result.stderr)
        self.assertIn("modelscope download", result.stderr)

    def test_qwen_vllm_disables_flashinfer_sampler_without_nvcc(self) -> None:
        script = (
            REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh"
        ).read_text(encoding="utf-8")

        self.assertIn('export VLLM_USE_FLASHINFER_SAMPLER="${VLLM_USE_FLASHINFER_SAMPLER:-0}"', script)

    def test_transformers_smoke_test_uses_chat_template(self) -> None:
        script = (REPO_ROOT / "test_gemma_transformers.py").read_text(encoding="utf-8")

        self.assertIn("/mnt/c/Users/Administrator/models/gemma-4-12B-it", script)
        self.assertIn("tokenizer.apply_chat_template", script)
        self.assertIn("add_generation_prompt=True", script)
        self.assertIn('attn_implementation="eager"', script)
        self.assertIn("do_sample=False", script)
        self.assertIn("repetition_penalty=1.1", script)
        self.assertIn("eos_token_id=tokenizer.eos_token_id", script)
        self.assertIn("pad_token_id=tokenizer.eos_token_id", script)


if __name__ == "__main__":
    unittest.main()
