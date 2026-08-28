import unittest

from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.prompts import (
    _system_his_v12_messages,
    _with_system_his_retry_feedback,
)


class SystemHisPromptTests(unittest.TestCase):
    def test_req2his_prompt_declares_canonical_h2_vocabulary(self) -> None:
        messages = _system_his_v12_messages(_request(), _platform())

        prompt = messages[-1]["content"]

        self.assertIn("H2 canonical semantic_kind values:", prompt)
        self.assertIn("accumulator, buffer, counter, fifo", prompt)
        self.assertIn("H2 canonical data_flow.protocol values: register, valid_ready, wire", prompt)
        self.assertIn(
            "verification.testbench and artifacts.testbench to be exactly sim/tb_top.v",
            prompt,
        )
        self.assertIn(
            'artifacts.constraints to be exactly ["constraints/timing.sdc"]',
            prompt,
        )
        self.assertIn(
            'artifacts.predicted_qor to be exactly "reports/predicted_qor.json"',
            prompt,
        )
        self.assertIn("H2 deterministic lowerer requires artifacts.constraints", prompt)
        self.assertIn("verification.scenarios entries must be canonical strings", prompt)
        self.assertIn("object is used, set kind to one canonical value", prompt)

    def test_req2his_retry_prompt_repeats_canonical_h2_vocabulary(self) -> None:
        messages = _with_system_his_retry_feedback(
            _system_his_v12_messages(_request(), _platform()),
            "H2 lowerability failed",
            "{}",
            task_type="fifo",
        )

        prompt = messages[-1]["content"]

        self.assertIn("H2 canonical semantic_kind values:", prompt)
        self.assertIn("H2 canonical data_flow.protocol values: register, valid_ready, wire", prompt)
        self.assertIn(
            "verification.testbench and artifacts.testbench to be exactly sim/tb_top.v",
            prompt,
        )
        self.assertIn(
            'artifacts.constraints to be exactly ["constraints/timing.sdc"]',
            prompt,
        )
        self.assertIn(
            'artifacts.predicted_qor to be exactly "reports/predicted_qor.json"',
            prompt,
        )
        self.assertIn("H2 deterministic lowerer requires artifacts.constraints", prompt)
        self.assertIn("verification.scenarios entries must be canonical strings", prompt)


def _request() -> ProjectRequest:
    return ProjectRequest(task_type="fifo", width=8, project_name="fifo_8bit")


def _platform() -> PlatformProfile:
    return PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")


if __name__ == "__main__":
    unittest.main()
