# SR2FPGA System-HIS v1.2 Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal structural checker for `system-his-v1.2-topdown` so REQ2HIS output can be validated before HIS2PROJECT generation.

**Architecture:** Create a focused checker module that validates a System-HIS JSON object independently of RTL files. The checker verifies required sections, component/instance consistency, endpoint validity, state references, flow references, and artifact shape. Keep it separate from the existing v1.1 `system_his_checker.py` until the pipeline intentionally switches schema versions.

**Tech Stack:** Python 3, dataclasses, unittest, JSON fixtures.

---

### Task 1: Add v1.2 Checker Tests

**Files:**
- Create: `LLM/tests/test_sr2fpga_agent_system_his_v12_checker.py`
- Read fixture: `docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json`

- [ ] **Step 1: Write the failing test**

```python
import copy
import json
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12


FIXTURE = Path("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json")


class SystemHisV12CheckerTest(unittest.TestCase):
    def test_accepts_t4_topdown_example(self) -> None:
        result = check_system_his_v12(_fixture())

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.errors, [])

    def test_rejects_instance_that_references_missing_component(self) -> None:
        payload = _fixture()
        payload["instances"][0]["component"] = "missing_component"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("instances[0] references missing component 'missing_component'", result.errors)

    def test_rejects_data_flow_endpoint_that_uses_component_instead_of_instance(self) -> None:
        payload = _fixture()
        payload["data_flow"][0]["path"][1] = "skid_buffer.in_data"

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("data_flow 'input0_payload_to_join' endpoint 'skid_buffer.in_data' is not a valid top or instance port", result.errors)

    def test_rejects_control_rule_references_to_missing_state_and_flow(self) -> None:
        payload = _fixture()
        payload["control_flow"][0]["related_state"].append("missing_state")
        payload["control_flow"][0]["related_flows"].append("missing_flow")

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("control_flow 'reset_all_state' references missing state 'missing_state'", result.errors)
        self.assertIn("control_flow 'reset_all_state' references missing data_flow 'missing_flow'", result.errors)

    def test_rejects_missing_required_sections(self) -> None:
        payload = _fixture()
        del payload["top"]

        result = check_system_his_v12(payload)

        self.assertFalse(result.passed)
        self.assertIn("system_his.top is required", result.errors)


def _fixture() -> dict[str, object]:
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_v12_checker -q`

Expected: FAIL or import error because `system_his_v12_checker` does not exist.

### Task 2: Implement Minimal v1.2 Checker

**Files:**
- Create: `LLM/src/sr2fpga_agent/system_his_v12_checker.py`

- [ ] **Step 1: Write minimal implementation**

Implement:

- `SystemHisV12CheckResult`
- `check_system_his_v12(payload: dict[str, Any]) -> SystemHisV12CheckResult`
- required section validation
- component name collection
- instance name collection
- top/component port endpoint validation
- state name collection
- data flow name collection
- control-flow reference validation

- [ ] **Step 2: Run test to verify it passes**

Run: `python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_v12_checker -q`

Expected: PASS.

### Task 3: Verify Existing Suite

**Files:**
- No additional files.

- [ ] **Step 1: Run focused and full tests**

Run:

```bash
python3 -m unittest LLM.tests.test_sr2fpga_agent_system_his_v12_checker -q
python3 -m unittest discover -s LLM/tests -q
```

Expected: all tests pass.

### Task 4: Update Status Documentation

**Files:**
- Modify: `docs/current-status.md`

- [ ] **Step 1: Add checker status note**

Add a concise note that the v1.2 prototype now has a standalone structural checker for REQ2HIS validation, while the main runner still uses v1.1.

- [ ] **Step 2: Run docs/search check**

Run:

```bash
rg -n "system_his_v12_checker|System-HIS v1.2" docs/current-status.md LLM/src/sr2fpga_agent LLM/tests
```

Expected: new checker, tests, and status note are discoverable.
