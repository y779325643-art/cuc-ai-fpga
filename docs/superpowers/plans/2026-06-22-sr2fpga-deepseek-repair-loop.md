# SR2FPGA DeepSeek Repair Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first DeepSeek-backed repair loop so failed generated RTL projects can be repaired once, rerun through tools, and recorded as patch trajectories.

**Architecture:** Reuse the existing `DataGenerationAgent(repairer=..., max_attempts=...)` hook. Keep DeepSeek generation and repair provider logic in `deepseek.py`, build providers in `cli.py`, and keep dataset recording/export structure unchanged.

**Tech Stack:** Python stdlib, `unittest`, `difflib`, DeepSeek OpenAI-compatible chat API, Verilator, Icarus Verilog, Yosys.

---

## File Structure

- Modify `LLM/src/sr2fpga_agent/models.py`: move the shared `RepairResult` dataclass here so providers can return it without importing the orchestration module.
- Modify `LLM/src/sr2fpga_agent/agent.py`: import `RepairResult` from `models.py` and preserve the existing module-level import compatibility.
- Modify `LLM/src/sr2fpga_agent/deepseek.py`: add `diff_projects`, `DeepSeekRepairer`, and repair prompt construction.
- Modify `LLM/src/sr2fpga_agent/cli.py`: add `--repair-provider`, `--max-attempts`, and `build_repairer`.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add unit tests for diff generation, repairer behavior, and CLI repairer construction.
- Modify `LLM/tests/test_sr2fpga_agent_recorder.py`: extend the existing fake-repairer agent test to prove `failure_to_patch.jsonl` is exportable from an agent-produced repair trajectory.
- Do not commit generated dataset samples under `datasets/`.

---

### Task 1: Shared Repair Result Model

**Files:**
- Modify: `LLM/src/sr2fpga_agent/models.py`
- Modify: `LLM/src/sr2fpga_agent/agent.py`
- Test: `LLM/tests/test_sr2fpga_agent_recorder.py`

- [ ] **Step 1: Write the failing import compatibility test**

Add this assertion near the imports or inside an existing test in `LLM/tests/test_sr2fpga_agent_recorder.py`:

```python
from LLM.src.sr2fpga_agent.models import RepairResult as ModelRepairResult
```

Add this test method to `DatasetRecorderTest`:

```python
    def test_repair_result_is_shared_model_and_agent_compatible(self) -> None:
        self.assertIs(RepairResult, ModelRepairResult)
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder.DatasetRecorderTest.test_repair_result_is_shared_model_and_agent_compatible -q
```

Expected result before implementation:

```text
ImportError: cannot import name 'RepairResult'
```

- [ ] **Step 3: Move `RepairResult` to models**

In `LLM/src/sr2fpga_agent/models.py`, add this dataclass below `ToolResult`:

```python
@dataclass(frozen=True)
class RepairResult:
    """Project returned by a repairer plus the patch used to reach it."""

    generated_project: GeneratedProject
    patch_diff: str
```

In `LLM/src/sr2fpga_agent/agent.py`, change the import to include `RepairResult`:

```python
from LLM.src.sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
    RepairResult,
    ToolResult,
)
```

Then delete the local `@dataclass(frozen=True) class RepairResult` definition from `agent.py`.

If `dataclass` is no longer used in `agent.py`, remove:

```python
from dataclasses import dataclass
```

- [ ] **Step 4: Run recorder tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected result:

```text
OK
```

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add LLM/src/sr2fpga_agent/models.py LLM/src/sr2fpga_agent/agent.py LLM/tests/test_sr2fpga_agent_recorder.py
git commit -m "Share repair result model"
```

---

### Task 2: Project Diff Helper

**Files:**
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`

- [ ] **Step 1: Write failing diff helper tests**

Update the import in `LLM/tests/test_sr2fpga_agent_deepseek.py`:

```python
from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekProjectGenerator,
    _project_messages,
    diff_projects,
    parse_project_files,
)
```

Add this import:

```python
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
```

Add this test method to `DeepSeekProviderTest`:

```python
    def test_diff_projects_outputs_unified_diff_for_changed_files(self) -> None:
        old = GeneratedProject(
            project_name="demo",
            files={
                "rtl/top.v": "module top; assign out = 1'b0; endmodule\n",
                "manifest.json": _valid_manifest(),
            },
        )
        new = GeneratedProject(
            project_name="demo",
            files={
                "rtl/top.v": "module top; assign out = 1'b1; endmodule\n",
                "manifest.json": _valid_manifest(),
            },
        )

        patch = diff_projects(old, new)

        self.assertIn("--- a/rtl/top.v", patch)
        self.assertIn("+++ b/rtl/top.v", patch)
        self.assertIn("-module top; assign out = 1'b0; endmodule", patch)
        self.assertIn("+module top; assign out = 1'b1; endmodule", patch)
        self.assertNotIn("manifest.json", patch)
```

Add this test method:

```python
    def test_diff_projects_includes_added_and_deleted_files(self) -> None:
        old = GeneratedProject(project_name="demo", files={"old.v": "module old; endmodule\n"})
        new = GeneratedProject(project_name="demo", files={"new.v": "module new; endmodule\n"})

        patch = diff_projects(old, new)

        self.assertIn("--- a/old.v", patch)
        self.assertIn("+++ b/old.v", patch)
        self.assertIn("--- a/new.v", patch)
        self.assertIn("+++ b/new.v", patch)
```

- [ ] **Step 2: Run the diff tests to verify they fail**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_diff_projects_outputs_unified_diff_for_changed_files \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_diff_projects_includes_added_and_deleted_files \
  -q
```

Expected result before implementation:

```text
ImportError: cannot import name 'diff_projects'
```

- [ ] **Step 3: Implement `diff_projects`**

In `LLM/src/sr2fpga_agent/deepseek.py`, add the import:

```python
import difflib
```

Add this function after `parse_project_files`:

```python
def diff_projects(old: GeneratedProject, new: GeneratedProject) -> str:
    """Return a unified diff between two generated project file maps."""
    chunks: list[str] = []
    for path in sorted(set(old.files) | set(new.files)):
        old_content = old.files.get(path, "")
        new_content = new.files.get(path, "")
        if old_content == new_content:
            continue
        chunks.extend(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
    return "".join(chunks)
```

- [ ] **Step 4: Run DeepSeek provider tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
```

Expected result:

```text
OK
```

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add LLM/src/sr2fpga_agent/deepseek.py LLM/tests/test_sr2fpga_agent_deepseek.py
git commit -m "Add project diff helper for repair trajectories"
```

---

### Task 3: DeepSeek Repairer

**Files:**
- Modify: `LLM/src/sr2fpga_agent/deepseek.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`

- [ ] **Step 1: Write failing repairer tests**

Update the DeepSeek import in `LLM/tests/test_sr2fpga_agent_deepseek.py`:

```python
from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
    _project_messages,
    _repair_messages,
    diff_projects,
    parse_project_files,
)
```

Add this test method to `DeepSeekProviderTest`:

```python
    def test_deepseek_repairer_uses_failure_context_and_returns_patch(self) -> None:
        original = GeneratedProject(
            project_name="counter_8bit",
            files={
                "system_his.json": "{}\n",
                "manifest.json": _valid_manifest(),
                "rtl/top.v": "module top(input wire clk); endmodule\n",
                "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                "sim/tb_top.v": "module tb_top; endmodule\n",
                "reports/predicted_qor.json": "{}\n",
            },
        )
        repaired_payload = json.dumps(
            {
                "files": {
                    "system_his.json": "{}\n",
                    "manifest.json": _valid_manifest(),
                    "rtl/top.v": "module top(input wire clk, input wire rst_n); endmodule\n",
                    "constraints/timing.sdc": "create_clock -name clk -period 10 [get_ports clk]\n",
                    "sim/tb_top.v": "module tb_top; endmodule\n",
                    "reports/predicted_qor.json": "{}\n",
                }
            }
        )
        client = FakeDeepSeekClient(repaired_payload)
        diagnosis = {
            "stage": "lint",
            "failure_type": "port_mismatch",
            "root_cause": "Port rst_n of module top is not declared",
            "affected_files": ["rtl/top.v"],
        }

        result = DeepSeekRepairer(client).repair(original, diagnosis)

        self.assertIn("rst_n", result.generated_project.files["rtl/top.v"])
        self.assertIn("--- a/rtl/top.v", result.patch_diff)
        self.assertIn("+++ b/rtl/top.v", result.patch_diff)
        self.assertIn("Port rst_n of module top is not declared", client.messages[1]["content"])
        self.assertIn("module top(input wire clk); endmodule", client.messages[1]["content"])
```

Add this test method:

```python
    def test_repair_prompt_requests_complete_project_package(self) -> None:
        project = GeneratedProject(
            project_name="counter_8bit",
            files={
                "manifest.json": _valid_manifest(),
                "rtl/top.v": "module top; endmodule\n",
            },
        )
        diagnosis = {"stage": "lint", "failure_type": "syntax_error", "root_cause": "syntax error"}

        messages = _repair_messages(project, diagnosis)
        prompt = messages[1]["content"]

        self.assertIn("Return JSON in this exact shape", prompt)
        self.assertIn('"manifest.json"', prompt)
        self.assertIn('"top_module": "top"', prompt)
        self.assertIn("syntax error", prompt)
```

- [ ] **Step 2: Run the repairer tests to verify they fail**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_deepseek_repairer_uses_failure_context_and_returns_patch \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_repair_prompt_requests_complete_project_package \
  -q
```

Expected result before implementation:

```text
ImportError: cannot import name 'DeepSeekRepairer'
```

- [ ] **Step 3: Implement repair prompt and repairer**

In `LLM/src/sr2fpga_agent/deepseek.py`, update the models import:

```python
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, RepairResult
```

Add this class after `DeepSeekProjectGenerator`:

```python
class DeepSeekRepairer:
    """Repair a generated project package using DeepSeek and a tool diagnosis."""

    def __init__(self, client: DeepSeekClient, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def repair(self, project: GeneratedProject, diagnosis: dict[str, object]) -> RepairResult:
        messages = _repair_messages(project, diagnosis)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(content)
                repaired_project = GeneratedProject(project_name=project.project_name, files=files)
                return RepairResult(
                    generated_project=repaired_project,
                    patch_diff=diff_projects(project, repaired_project),
                )
            except ValueError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise RuntimeError("DeepSeek repairer did not run")
```

Add this helper near `_project_messages`:

```python
def _repair_messages(project: GeneratedProject, diagnosis: dict[str, object]) -> list[dict[str, str]]:
    files_text = "\n\n".join(
        f"### {path}\n{content}" for path, content in sorted(project.files.items())
    )
    diagnosis_text = json.dumps(diagnosis, ensure_ascii=False, indent=2)
    required_files = "\n".join(f"- {path}" for path in sorted(REQUIRED_PROJECT_FILES))
    system = (
        "You repair FPGA RTL project packages as JSON. "
        "Return only valid JSON. Do not include markdown. "
        "Do not generate vendor IP, HLS, bitstreams, or real tool reports."
    )
    user = f"""
Repair this SR2FPGA project package.

Failure diagnosis:
{diagnosis_text}

Current project files:
{files_text}

Required files:
{required_files}

Return JSON in this exact shape. The value of each file must be a JSON string;
escape newlines as \\n and escape any double quotes inside file contents:
{{
  "files": {{
    "system_his.json": "...",
    "manifest.json": "...",
    "rtl/top.v": "...",
    "constraints/timing.sdc": "...",
    "sim/tb_top.v": "...",
    "reports/predicted_qor.json": "..."
  }}
}}

The manifest.json file content must itself be JSON and must contain this tool
pipeline schema:
{{
  "project_name": "{project.project_name}",
  "top_module": "top",
  "sources": ["rtl/top.v"],
  "constraints": ["constraints/timing.sdc"],
  "simulation": {{"testbench": "sim/tb_top.v"}},
  "reports": ["reports/predicted_qor.json"]
}}

Make the smallest practical fix for the failing tool log. Preserve pure
Verilog RTL and ensure the testbench prints TEST_PASS on success.
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
```

- [ ] **Step 4: Run DeepSeek provider tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
```

Expected result:

```text
OK
```

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add LLM/src/sr2fpga_agent/deepseek.py LLM/tests/test_sr2fpga_agent_deepseek.py
git commit -m "Add DeepSeek repairer"
```

---

### Task 4: CLI Repair Wiring

**Files:**
- Modify: `LLM/src/sr2fpga_agent/cli.py`
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/README.md`

- [ ] **Step 1: Write failing CLI repair tests**

In `LLM/tests/test_sr2fpga_agent_deepseek.py`, update the DeepSeek import to include `DeepSeekRepairer` if Task 3 did not already do so.

Add this test method to `DeepSeekProviderTest`:

```python
    def test_cli_builds_no_repairer_by_default(self) -> None:
        from LLM.src.sr2fpga_agent.cli import build_repairer

        repairer = build_repairer(
            provider="none",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
        )

        self.assertIsNone(repairer)
```

Add this test method:

```python
    def test_cli_builds_deepseek_repairer_from_env_without_exposing_key(self) -> None:
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "secret-value"}):
            from LLM.src.sr2fpga_agent.cli import build_repairer

            repairer = build_repairer(
                provider="deepseek",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
            )

        self.assertIsInstance(repairer, DeepSeekRepairer)
```

Update `test_cli_passes_requirement_into_project_request` so its `FakeAgent.__init__` accepts and captures repairer and max attempts:

```python
        class FakeAgent:
            def __init__(
                self,
                dataset_root,
                project_generator=None,
                repairer=None,
                max_attempts=1,
            ) -> None:
                captured["dataset_root"] = dataset_root
                captured["project_generator"] = project_generator
                captured["repairer"] = repairer
                captured["max_attempts"] = max_attempts
```

Patch `build_repairer` in that test:

```python
            mock.patch.object(cli, "build_repairer", return_value="fake-repairer"),
```

Add these CLI args in that test:

```python
                    "--repair-provider",
                    "deepseek",
                    "--max-attempts",
                    "2",
```

Add assertions:

```python
        self.assertEqual(captured["repairer"], "fake-repairer")
        self.assertEqual(captured["max_attempts"], 2)
```

Add this test method:

```python
    def test_cli_rejects_non_positive_max_attempts(self) -> None:
        from LLM.src.sr2fpga_agent import cli

        with self.assertRaisesRegex(SystemExit, "--max-attempts must be >= 1"):
            cli.main(
                [
                    "--dataset-root",
                    "datasets/sr2fpga_rtl_v1",
                    "--sample-id",
                    "sample_bad_attempts",
                    "--provider",
                    "deterministic",
                    "--task-type",
                    "counter",
                    "--width",
                    "8",
                    "--project-name",
                    "bad_attempts",
                    "--max-attempts",
                    "0",
                ]
            )
```

- [ ] **Step 2: Run CLI repair tests to verify they fail**

Run:

```bash
python3 -m unittest \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_cli_builds_no_repairer_by_default \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_cli_builds_deepseek_repairer_from_env_without_exposing_key \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_cli_passes_requirement_into_project_request \
  LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_cli_rejects_non_positive_max_attempts \
  -q
```

Expected result before implementation:

```text
ImportError: cannot import name 'build_repairer'
```

- [ ] **Step 3: Implement CLI repair wiring**

In `LLM/src/sr2fpga_agent/cli.py`, update the import:

```python
from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekClient,
    DeepSeekConfig,
    DeepSeekProjectGenerator,
    DeepSeekRepairer,
)
```

Add parser args in `main`:

```python
    parser.add_argument("--repair-provider", choices=["none", "deepseek"], default="none")
    parser.add_argument("--max-attempts", default=1, type=int)
```

After parsing args, reject invalid attempt counts before building providers:

```python
    if args.max_attempts < 1:
        raise SystemExit("--max-attempts must be >= 1")
```

Build the repairer:

```python
    repairer = build_repairer(
        provider=args.repair_provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )
```

Pass repairer and max attempts into `DataGenerationAgent`:

```python
    result = DataGenerationAgent(
        args.dataset_root,
        project_generator=project_generator,
        repairer=repairer,
        max_attempts=args.max_attempts,
    ).run_one(
```

Add `build_repairer` below `build_project_generator`:

```python
def build_repairer(
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
):
    if provider == "none":
        return None
    if provider == "deepseek":
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set")
        return DeepSeekRepairer(
            DeepSeekClient(
                DeepSeekConfig(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                )
            )
        )
    raise SystemExit(f"Unsupported repair provider: {provider}")
```

- [ ] **Step 4: Update README**

In `LLM/README.md`, add a short example after the DeepSeek generation example:

```
Use DeepSeek for generation and one repair attempt:

    export DEEPSEEK_API_KEY="your-key"

    python3 -m LLM.src.sr2fpga_agent.cli \
      --dataset-root datasets/sr2fpga_rtl_v1 \
      --sample-id sample_llm_repair_000001 \
      --provider deepseek \
      --repair-provider deepseek \
      --max-attempts 2 \
      --task-type counter \
      --width 8 \
      --project-name llm_counter_repair_8bit \
      --requirement "Design an 8-bit synchronous counter with enable, active-low reset, self-checking Verilog testbench, timing constraint, manifest, system_his, and predicted QoR."
```

- [ ] **Step 5: Run DeepSeek provider tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
```

Expected result:

```text
OK
```

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add LLM/src/sr2fpga_agent/cli.py LLM/tests/test_sr2fpga_agent_deepseek.py LLM/README.md
git commit -m "Wire DeepSeek repairer into CLI"
```

---

### Task 5: Export Repair Trajectory Rows From Agent Runs

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_recorder.py`

- [ ] **Step 1: Extend the existing fake repairer test**

In `test_agent_records_failed_attempt_patch_and_repaired_attempt`, after the existing trajectory assertions, add:

```python
            export_dir = Path(tmp) / "exports"
            DatasetRecorder(root).export_training_views(export_dir)
            patch_rows = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(patch_rows), 1)
            patch_row = json.loads(patch_rows[0])
            self.assertEqual(patch_row["sample_id"], "sample_000002")
            self.assertEqual(patch_row["diagnosis"]["failure_type"], "port_mismatch")
            self.assertIn("fix reset port", patch_row["patch"])
```

- [ ] **Step 2: Run recorder tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected result:

```text
OK
```

If it fails, fix only the recorder/export behavior needed for agent-produced repair attempts. Do not change the dataset directory shape.

- [ ] **Step 3: Commit Task 5**

Run:

```bash
git add LLM/tests/test_sr2fpga_agent_recorder.py
git commit -m "Verify agent repair patches export to training views"
```

---

### Task 6: Full Verification And DeepSeek Repair Smoke

**Files:**
- No code files should be modified in this task.
- Generated samples under `datasets/` remain untracked unless the user explicitly requests committing data.

- [ ] **Step 1: Run all tests**

Run:

```bash
python3 -m unittest discover -s LLM/tests -q
```

Expected result:

```text
OK
```

- [ ] **Step 2: Run deterministic CLI smoke without repair**

Run:

```bash
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_cli_repair_baseline_000001 \
  --provider deterministic \
  --repair-provider none \
  --max-attempts 1 \
  --task-type counter \
  --width 8 \
  --project-name cli_repair_baseline_counter_8bit \
  --requirement "Design an 8-bit synchronous counter with enable, active-low reset, self-checking testbench, and predicted QoR."
```

Expected output:

```text
sample_dir=datasets/sr2fpga_rtl_v1/sample_cli_repair_baseline_000001
pass_level=L3
```

- [ ] **Step 3: Run DeepSeek repair smoke with the current key**

Use the current thread's DeepSeek key as a temporary environment variable. Do
not write it to files.

Run:

```bash
DEEPSEEK_API_KEY="..." python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_llm_repair_000001 \
  --provider deepseek \
  --repair-provider deepseek \
  --max-attempts 2 \
  --task-type counter \
  --width 8 \
  --project-name llm_counter_repair_8bit \
  --requirement "Design an 8-bit synchronous counter with enable, active-low reset, self-checking Verilog testbench, timing constraint, manifest, system_his, and predicted QoR."
```

Expected output shape:

```text
sample_dir=datasets/sr2fpga_rtl_v1/sample_llm_repair_000001
pass_level=<L0|L1|L2|L3>
```

Passing L3 is welcome but not required. The important evidence is whether the
sample records attempts, labels, and, if attempt 0 fails and repair runs,
`attempts/attempt_000/patch.diff`.

- [ ] **Step 4: Inspect repair sample labels and patch presence**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

base = Path("datasets/sr2fpga_rtl_v1/sample_llm_repair_000001")
labels = json.loads((base / "eval/labels.json").read_text())
print(labels)
for patch in sorted(base.glob("attempts/*/patch.diff")):
    print(patch, patch.stat().st_size)
PY
```

Expected result:

```text
Labels print successfully. Patch files print if repair was triggered.
```

- [ ] **Step 5: Export training views**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from LLM.src.sr2fpga_agent.recorder import DatasetRecorder

DatasetRecorder(Path("datasets/sr2fpga_rtl_v1")).export_training_views(
    Path("datasets/sr2fpga_rtl_v1_exports")
)
PY
wc -l datasets/sr2fpga_rtl_v1_exports/*.jsonl
```

Expected result:

```text
Success views remain populated. failure_to_patch.jsonl is nonzero if a repair
attempt was triggered and patch.diff was recorded.
```

- [ ] **Step 6: Final status check**

Run:

```bash
git status --short
```

Expected result:

```text
Only expected untracked dataset, local config, report PDF, or tmp artifacts remain.
No tracked code files are modified.
```
