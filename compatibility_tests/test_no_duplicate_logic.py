import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SOURCE = REPO_ROOT / "LLM" / "src"

ALLOWED_FUNCTIONS = {
    "_legacy_module_requested_for_execution",
    "main",
    "run_module",
    "warn_replacement",
}
BUSINESS_FUNCTION_NAMES = {
    "convert_jsonl",
    "dry_run_chat_jsonl",
    "generate_project",
    "load_config",
    "merge_behavior_files",
    "repair_project",
    "run_batch",
    "validate_system_his",
}


def test_legacy_python_files_remain_thin_forwarders() -> None:
    violations: list[str] = []

    for path in LEGACY_SOURCE.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        non_blank_lines = [line for line in source.splitlines() if line.strip()]
        tree = ast.parse(source, filename=str(path))
        functions = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]

        reasons: list[str] = []
        if len(non_blank_lines) >= 80:
            reasons.append(f"{len(non_blank_lines)} non-blank lines")
        if classes:
            reasons.append(f"classes={classes}")
        unexpected_functions = functions - ALLOWED_FUNCTIONS
        if unexpected_functions:
            reasons.append(f"functions={sorted(unexpected_functions)}")
        business_functions = functions & BUSINESS_FUNCTION_NAMES
        if business_functions:
            reasons.append(f"business={sorted(business_functions)}")
        if reasons:
            violations.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: "
                + ", ".join(reasons)
            )

    assert violations == []
