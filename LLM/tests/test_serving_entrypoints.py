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

    def _capture_vllm_args(self, script: Path) -> list[str]:
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
        args = self._capture_vllm_args(REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh")

        self.assertEqual(args[0:2], ["serve", "Qwen/Qwen2.5-Coder-7B-Instruct"])
        self.assertIn("--max-model-len", args)
        self.assertEqual(args[args.index("--max-model-len") + 1], "4096")
        self.assertEqual(args[args.index("--served-model-name") + 1], "cuc-ai-fpga")

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
