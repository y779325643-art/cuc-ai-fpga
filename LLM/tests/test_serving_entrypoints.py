from collections.abc import Iterable
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from LLM.src.sr2fpga_agent.local_tools import executable_env, resolve_executable


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
                newline="\n",
            )
            fake_vllm.chmod(0o755)

            bash = _bash_executable()
            env = _env_for_bash(os.environ.copy(), bash, prepend_path=temp_path)
            env["CAPTURE_FILE"] = _path_for_bash(capture_file, bash)
            if _is_windows_wsl_bash(bash):
                _add_wslenv_entries(env, ["CAPTURE_FILE"])
            if extra_env:
                env.update(extra_env)
                if _is_windows_wsl_bash(bash):
                    _add_wslenv_entries(env, extra_env.keys())
            subprocess.run(
                _bash_command(script, bash),
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
        bash = _bash_executable()
        with tempfile.TemporaryDirectory() as model_dir:
            model_path = _path_for_bash(model_dir, bash)
            args = self._capture_vllm_args(
                REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh",
                {"QWEN_MODEL_PATH": model_path},
            )

        self.assertEqual(args[0:2], ["serve", model_path])
        self.assertIn("--max-model-len", args)
        self.assertEqual(args[args.index("--max-model-len") + 1], "4096")
        self.assertEqual(args[args.index("--served-model-name") + 1], "cuc-ai-fpga")

    def test_qwen_vllm_defaults_to_persistent_e_drive_model_path(self) -> None:
        script = (
            REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct",
            script,
        )

    def test_qwen_vllm_explains_how_to_download_a_missing_local_model(self) -> None:
        missing_path = "/tmp/definitely-missing-qwen-model"
        env = os.environ.copy()
        env["QWEN_MODEL_PATH"] = missing_path
        bash = _bash_executable()

        result = subprocess.run(
            _bash_command(REPO_ROOT / "LLM/scripts/serve_qwen_vllm.sh", bash),
            cwd=REPO_ROOT,
            env=_env_for_bash(env, bash),
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


def _bash_executable() -> str:
    bash = resolve_executable("bash")
    return str(bash) if bash is not None else "bash"


def _bash_command(script: Path, bash: str) -> list[str]:
    return [bash, _path_for_bash(script, bash)]


def _env_for_bash(
    base_env: dict[str, str],
    bash: str,
    *,
    prepend_path: Path | None = None,
) -> dict[str, str]:
    env = executable_env(base_env)
    if not _is_windows_wsl_bash(bash):
        if prepend_path is not None:
            env["PATH"] = os.pathsep.join([str(prepend_path), env.get("PATH", "")])
        return env

    path_entries = []
    if prepend_path is not None:
        path_entries.append(_path_for_bash(prepend_path, bash))
    path_entries.extend(
        [
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ]
    )
    env["PATH"] = ":".join(path_entries)
    _add_wslenv_entries(
        env,
        [
            "PATH",
            *(
                key
                for key in ("LLM_VENV_PATH", "MODEL_PATH", "QWEN_MODEL_PATH")
                if key in env
            ),
        ],
    )
    return env


def _path_for_bash(path: Path | str, bash: str) -> str:
    path_text = str(path)
    if _is_windows_wsl_bash(bash):
        return _windows_path_to_wsl(path_text)
    return path_text


def _is_windows_wsl_bash(bash: str) -> bool:
    normalized = bash.replace("/", "\\").lower()
    return os.name == "nt" and (
        "\\windowsapps\\bash" in normalized or "\\system32\\bash" in normalized
    )


def _windows_path_to_wsl(path: str) -> str:
    if path.startswith("/"):
        return path
    path = str(Path(path).resolve(strict=False))
    drive, tail = os.path.splitdrive(path)
    if not drive:
        return path.replace("\\", "/")
    tail = tail.replace("\\", "/").lstrip("/")
    return f"/mnt/{drive[0].lower()}/{tail}"


def _add_wslenv_entries(env: dict[str, str], names: Iterable[object]) -> None:
    existing = [entry for entry in env.get("WSLENV", "").split(":") if entry]
    seen = {entry.split("/", 1)[0] for entry in existing}
    for name in names:
        name_text = str(name)
        if not name_text or name_text in seen:
            continue
        existing.append(name_text)
        seen.add(name_text)
    if existing:
        env["WSLENV"] = ":".join(existing)


if __name__ == "__main__":
    unittest.main()
