import json
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12_against_rtl


FIXTURE = Path("docs/system_his_examples/t4_dual_stream_join.system-his-v1.2.json")


class ContractSkeletonTest(unittest.TestCase):
    def test_builds_l0_clean_project_skeleton_from_system_his_v12(self) -> None:
        system_his = _fixture()
        request = ProjectRequest(
            task_type="composed_dual_stream_join",
            width=8,
            project_name="join_8bit",
            description="Generate a dual-stream join and accumulator project.",
        )
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = build_contract_skeleton_project(request, platform, system_his)

        self.assertEqual(json.loads(project.files["system_his.json"]), system_his)
        manifest = json.loads(project.files["manifest.json"])
        self.assertEqual(manifest["sources"], system_his["artifacts"]["rtl_sources"])
        self.assertIn("rtl/top.v", project.files)
        self.assertIn("rtl/stream_join.v", project.files)
        self.assertIn("BEHAVIOR_HOLE", project.files["rtl/stream_join.v"])
        self.assertRegex(project.files["rtl/top.v"], r"\bstream_join\b\s*(?:#\s*\(.*?\)\s*)?join_core\s*\(")
        self.assertIn("top dut", project.files["sim/tb_top.v"])
        self.assertIn("[get_ports clk]", project.files["constraints/timing.sdc"])

        result = check_system_his_v12_against_rtl(system_his, project)

        self.assertTrue(result.passed, result.errors)


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
