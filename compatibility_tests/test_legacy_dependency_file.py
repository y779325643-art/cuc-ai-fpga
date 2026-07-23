from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_requirements_is_a_lightweight_editable_aggregate() -> None:
    requirements = REPO_ROOT / "LLM" / "requirements.txt"
    lines = [
        line.strip()
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    assert lines == ["-e ../agent", "-e ../training"]


def test_legacy_requirements_does_not_force_heavy_training_dependencies() -> None:
    source = (
        REPO_ROOT / "LLM" / "requirements.txt"
    ).read_text(encoding="utf-8").lower()

    for dependency in (
        "accelerate",
        "bitsandbytes",
        "datasets",
        "peft",
        "torch",
        "transformers",
        "trl",
        "vllm",
    ):
        assert dependency not in source
