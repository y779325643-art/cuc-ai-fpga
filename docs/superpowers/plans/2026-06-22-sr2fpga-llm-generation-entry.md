# SR2FPGA LLM Generation Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status (added 2026-06-27):** Delivered. DeepSeek provider entry is implemented.
> **Post-delivery note:** DeepSeek is the first provider example, not the only one.
> The `--provider deepseek` flag introduced here became the seed for the multi-teacher
> source architecture (`2026-06-25-sr2fpga-multi-teacher-source.md`), which generalizes
> to any OpenAI-compatible endpoint. Read this plan as the proof-of-concept phase.

**Goal:** Make the SR2FPGA data-generation CLI pass natural-language requirements into the DeepSeek-backed project generator and verify that LLM-generated project packages flow through the existing tool-recording pipeline.

**Architecture:** Keep the existing provider boundary: `cli.py` chooses a generator, `deepseek.py` parses LLM project files, and `DataGenerationAgent` writes, verifies, and records the generated project. This plan changes only the CLI request plumbing and adds regression tests proving that injected LLM-style generators are used instead of deterministic templates.

**Tech Stack:** Python stdlib, `unittest`, DeepSeek OpenAI-compatible chat API, Verilator, Icarus Verilog, Yosys.

---

## File Structure

- Modify `LLM/src/sr2fpga_agent/cli.py`: allow `main(argv)` in tests and set `ProjectRequest.description` from `--requirement`.
- Modify `LLM/tests/test_sr2fpga_agent_deepseek.py`: add CLI plumbing tests and DeepSeek list-format parser regression coverage.
- Modify `LLM/tests/test_sr2fpga_agent_recorder.py`: add an injected fake LLM generator regression test that verifies generated files are recorded by the agent.
- Do not modify `LLM/src/sr2fpga_agent/agent.py` unless the fake LLM regression test exposes a real orchestration gap.
- Do not commit generated dataset samples under `datasets/`.

---

### Task 1: CLI Requirement Plumbing

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`
- Modify: `LLM/src/sr2fpga_agent/cli.py`

- [ ] **Step 1: Write the failing CLI test**

Add this test method to `DeepSeekProviderTest` in `LLM/tests/test_sr2fpga_agent_deepseek.py`:

```python
    def test_cli_passes_requirement_into_project_request(self) -> None:
        from LLM.src.sr2fpga_agent import cli

        captured = {}

        class FakeAgent:
            def __init__(self, dataset_root, project_generator=None) -> None:
                captured["dataset_root"] = dataset_root
                captured["project_generator"] = project_generator

            def run_one(self, sample_id, requirement, request, platform):
                captured["sample_id"] = sample_id
                captured["requirement"] = requirement
                captured["request"] = request
                captured["platform"] = platform
                return {"sample_dir": "datasets/sr2fpga_rtl_v1/sample_llm_000001", "pass_level": "L0"}

        requirement = "Design an 8-bit counter with enable, reset, and a self-checking testbench."
        with (
            mock.patch.object(cli, "DataGenerationAgent", FakeAgent),
            mock.patch.object(cli, "build_project_generator", return_value="fake-llm-generator"),
            mock.patch("builtins.print"),
        ):
            cli.main(
                [
                    "--dataset-root",
                    "datasets/sr2fpga_rtl_v1",
                    "--sample-id",
                    "sample_llm_000001",
                    "--provider",
                    "deepseek",
                    "--task-type",
                    "counter",
                    "--width",
                    "8",
                    "--project-name",
                    "llm_counter_8bit",
                    "--requirement",
                    requirement,
                ]
            )

        self.assertEqual(captured["requirement"], requirement)
        self.assertEqual(captured["request"].description, requirement)
        self.assertEqual(captured["request"].task_type, "counter")
        self.assertEqual(captured["request"].width, 8)
        self.assertEqual(captured["request"].project_name, "llm_counter_8bit")
        self.assertEqual(captured["project_generator"], "fake-llm-generator")
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_cli_passes_requirement_into_project_request -q
```

Expected result before implementation:

```text
TypeError: main() takes 0 positional arguments but 1 was given
```

- [ ] **Step 3: Implement minimal CLI support**

Modify `LLM/src/sr2fpga_agent/cli.py` so `main` accepts an optional argv list and passes `description=requirement`:

```python
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate one SR2FPGA RTL dataset sample.")
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--task-type", default="counter")
    parser.add_argument("--width", default=8, type=int)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--requirement", default="")
    parser.add_argument("--platform", default="generic_verilog")
    parser.add_argument("--provider", choices=["deterministic", "deepseek"], default="deterministic")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    args = parser.parse_args(argv)

    requirement = args.requirement or f"Design a {args.width}-bit {args.task_type} RTL block with active-low reset."
    project_generator = build_project_generator(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )
    result = DataGenerationAgent(args.dataset_root, project_generator=project_generator).run_one(
        sample_id=args.sample_id,
        requirement=requirement,
        request=ProjectRequest(
            task_type=args.task_type,
            width=args.width,
            project_name=args.project_name,
            description=requirement,
        ),
        platform=PlatformProfile(name=args.platform, vendor="generic", toolchain="open_source"),
    )
    print(f"sample_dir={result['sample_dir']}")
    print(f"pass_level={result['pass_level']}")
```

Keep the existing `if __name__ == "__main__": main()` block unchanged.

- [ ] **Step 4: Run the CLI test to verify it passes**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek.DeepSeekProviderTest.test_cli_passes_requirement_into_project_request -q
```

Expected result:

```text
OK
```

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add LLM/src/sr2fpga_agent/cli.py LLM/tests/test_sr2fpga_agent_deepseek.py
git commit -m "Wire CLI requirements into LLM project requests"
```

---

### Task 2: Fake LLM Generator Recording Regression

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_recorder.py`

- [ ] **Step 1: Add the fake LLM generator test**

Add this test method to `DatasetRecorderTest` in `LLM/tests/test_sr2fpga_agent_recorder.py`:

```python
    def test_agent_records_project_from_injected_llm_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            llm_generator = FakeLLMProjectGenerator()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=llm_generator,
            )
            request = ProjectRequest(
                task_type="counter",
                width=8,
                project_name="llm_counter_8bit",
                description="Design a counter using an LLM-generated package.",
            )
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_llm_000001",
                requirement=request.description,
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_llm_000001"
            top_rtl = (sample_dir / "final/generated_project/rtl/top.v").read_text(encoding="utf-8")
            system_his = json.loads(
                (sample_dir / "final/generated_project/system_his.json").read_text(encoding="utf-8")
            )

            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(llm_generator.call_count, 1)
            self.assertIn("LLM_GENERATED_MARKER", top_rtl)
            self.assertEqual(system_his["system"]["description"], request.description)
            self.assertNotIn("count <= count +", top_rtl)
```

Add this helper class near the other fake classes in the same file:

```python
class FakeLLMProjectGenerator:
    def __init__(self) -> None:
        self.call_count = 0

    def generate(self, request, platform):
        self.call_count += 1
        files = {
            "system_his.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "task_type": request.task_type,
                    "system": {"description": request.description},
                    "platform": {"name": platform.name},
                }
            )
            + "\n",
            "manifest.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "top_module": "top",
                    "sources": ["rtl/top.v"],
                    "constraints": ["constraints/timing.sdc"],
                    "simulation": {"testbench": "sim/tb_top.v"},
                    "reports": ["reports/predicted_qor.json"],
                }
            )
            + "\n",
            "rtl/top.v": "module top(input wire clk, output wire out); assign out = clk; endmodule // LLM_GENERATED_MARKER\n",
            "constraints/timing.sdc": "create_clock -name clk -period 10.000 [get_ports clk]\n",
            "sim/tb_top.v": "module tb_top; initial begin $display(\"TEST_PASS\"); $finish; end endmodule\n",
            "reports/predicted_qor.json": json.dumps(
                {
                    "project_name": request.project_name,
                    "predicted": {"lut": 1, "ff": 0, "bram": 0, "dsp": 0},
                    "assumptions": {"generator": "fake_llm"},
                }
            )
            + "\n",
        }
        return GeneratedProject(project_name=request.project_name, files=files)
```

Add `GeneratedProject` to the existing imports:

```python
from LLM.src.sr2fpga_agent import GeneratedProject, PlatformProfile, ProjectGenerator, ProjectRequest
```

- [ ] **Step 2: Run the fake LLM regression test**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder.DatasetRecorderTest.test_agent_records_project_from_injected_llm_generator -q
```

Expected result:

```text
OK
```

If this fails, fix only the specific orchestration gap exposed by the failure. Do not rewrite the recorder or tool runner.

- [ ] **Step 3: Run recorder tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_recorder -q
```

Expected result:

```text
OK
```

- [ ] **Step 4: Commit Task 2**

Run:

```bash
git add LLM/tests/test_sr2fpga_agent_recorder.py
git commit -m "Test recording injected LLM generated projects"
```

---

### Task 3: DeepSeek Parser Format Regression

**Files:**
- Modify: `LLM/tests/test_sr2fpga_agent_deepseek.py`

- [ ] **Step 1: Add list-format parser coverage**

Add this test method to `DeepSeekProviderTest` in `LLM/tests/test_sr2fpga_agent_deepseek.py`:

```python
    def test_parse_project_files_accepts_files_list(self) -> None:
        content = json.dumps(
            {
                "files": [
                    {"path": "system_his.json", "content": "{}\n"},
                    {"path": "manifest.json", "content": "{}\n"},
                    {"path": "rtl/top.v", "content": "module top; endmodule\n"},
                    {"path": "constraints/timing.sdc", "content": "create_clock -name clk -period 10 [get_ports clk]\n"},
                    {"path": "sim/tb_top.v", "content": "module tb_top; endmodule\n"},
                    {"path": "reports/predicted_qor.json", "content": "{}\n"},
                ]
            }
        )

        files = parse_project_files(content)

        self.assertEqual(files["rtl/top.v"], "module top; endmodule\n")
        self.assertEqual(files["sim/tb_top.v"], "module tb_top; endmodule\n")
```

- [ ] **Step 2: Run DeepSeek provider tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_deepseek -q
```

Expected result:

```text
OK
```

- [ ] **Step 3: Commit Task 3**

Run:

```bash
git add LLM/tests/test_sr2fpga_agent_deepseek.py
git commit -m "Cover DeepSeek list project file responses"
```

---

### Task 4: Full Verification And One Real LLM Smoke

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

- [ ] **Step 2: Run deterministic CLI smoke**

Run:

```bash
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_cli_000001 \
  --provider deterministic \
  --task-type counter \
  --width 8 \
  --project-name cli_counter_8bit \
  --requirement "Design an 8-bit synchronous counter with enable, active-low reset, self-checking testbench, and predicted QoR."
```

Expected output:

```text
sample_dir=datasets/sr2fpga_rtl_v1/sample_cli_000001
pass_level=L3
```

- [ ] **Step 3: Run DeepSeek CLI smoke if the key is available**

Run this only when `DEEPSEEK_API_KEY` is set in the shell environment:

```bash
python3 -m LLM.src.sr2fpga_agent.cli \
  --dataset-root datasets/sr2fpga_rtl_v1 \
  --sample-id sample_llm_000001 \
  --provider deepseek \
  --task-type counter \
  --width 8 \
  --project-name llm_counter_8bit \
  --requirement "Design an 8-bit synchronous counter with enable, active-low reset, self-checking Verilog testbench, timing constraint, manifest, system_his, and predicted QoR."
```

Expected output shape:

```text
sample_dir=datasets/sr2fpga_rtl_v1/sample_llm_000001
pass_level=<L0|L1|L2|L3>
```

Any pass level is acceptable for the first real LLM smoke because failed lint,
simulation, or synthesis is useful evidence. The command must write a sample
directory with generated files and `eval/labels.json`.

- [ ] **Step 4: Export training views**

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
requirement_to_his.jsonl, his_to_project.jsonl, requirement_to_project.jsonl,
project_to_predicted_qor.jsonl, and project_to_measured_qor.jsonl have at least
the previously generated 9 rows. Failure views may still be 0 until repair data
collection is implemented.
```

- [ ] **Step 5: Final status check**

Run:

```bash
git status --short
```

Expected result:

```text
Only expected untracked dataset, local config, report PDF, or tmp artifacts remain.
No tracked code files are modified.
```
