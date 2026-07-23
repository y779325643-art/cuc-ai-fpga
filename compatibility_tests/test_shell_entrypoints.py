import os
from pathlib import Path
import shutil
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAMES = (
    "setup_server.sh",
    "serve_qwen_vllm.sh",
    "serve_vllm.sh",
    "train_lora.sh",
    "merge_lora.sh",
    "test_api.sh",
)


@pytest.mark.parametrize("script_name", SCRIPT_NAMES)
def test_legacy_shell_entrypoint_is_a_thin_lf_wrapper(
    script_name: str,
) -> None:
    wrapper = REPO_ROOT / "LLM" / "scripts" / script_name
    raw = wrapper.read_bytes()
    source = raw.decode("utf-8")

    assert b"\r\n" not in raw
    assert source.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert (
        f"DEPRECATED: LLM/scripts/{script_name} "
        f"-> training/scripts/{script_name}"
    ) in source
    assert f'training/scripts/{script_name}" "$@"' in source
    assert len([line for line in source.splitlines() if line.strip()]) <= 7

    forbidden_implementation_tokens = (
        "TRAINING_VENV_PATH",
        "QWEN_MODEL_PATH",
        "MODEL_PATH",
        "VLLM_",
        "CUDA_",
        "curl ",
        "python -m",
    )
    assert not any(
        token in source for token in forbidden_implementation_tokens
    )


@pytest.mark.parametrize("script_name", SCRIPT_NAMES)
def test_legacy_shell_entrypoint_forwards_arguments_in_order(
    tmp_path: Path,
    script_name: str,
) -> None:
    wrapper_source = (
        REPO_ROOT / "LLM" / "scripts" / script_name
    ).read_text(encoding="utf-8")
    legacy_dir = tmp_path / "LLM" / "scripts"
    training_dir = tmp_path / "training" / "scripts"
    legacy_dir.mkdir(parents=True)
    training_dir.mkdir(parents=True)

    wrapper = legacy_dir / script_name
    downstream = training_dir / script_name
    wrapper.write_text(wrapper_source, encoding="utf-8", newline="\n")
    downstream.write_text(
        '#!/usr/bin/env bash\nprintf "<%s>\\n" "$@"\n',
        encoding="utf-8",
        newline="\n",
    )
    wrapper.chmod(0o755)
    downstream.chmod(0o755)

    bash = shutil.which("bash") or "bash"
    completed = subprocess.run(
        [
            bash,
            _path_for_bash(wrapper, bash),
            "--alpha",
            "two words",
            "--beta=3",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines() == [
        "<--alpha>",
        "<two words>",
        "<--beta=3>",
    ]
    assert (
        f"DEPRECATED: LLM/scripts/{script_name} "
        f"-> training/scripts/{script_name}"
    ) in completed.stderr


def _path_for_bash(path: Path, bash: str) -> str:
    if not _is_windows_wsl_bash(bash):
        return str(path)
    resolved = str(path.resolve(strict=False))
    drive, tail = os.path.splitdrive(resolved)
    tail = tail.replace("\\", "/").lstrip("/")
    return f"/mnt/{drive[0].lower()}/{tail}"


def _is_windows_wsl_bash(bash: str) -> bool:
    normalized = bash.replace("/", "\\").lower()
    return os.name == "nt" and (
        "\\windowsapps\\bash" in normalized
        or "\\system32\\bash" in normalized
    )
