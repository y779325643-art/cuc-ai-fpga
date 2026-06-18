import json
import re
import unittest

from LLM.src.sr2fpga_agent import PlatformProfile, ProjectGenerator, ProjectRequest


class ProjectGeneratorTest(unittest.TestCase):
    def test_generates_minimal_counter_project_package(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(
            name="generic_verilog",
            vendor="generic",
            toolchain="open_source",
            clock_hz=100_000_000,
        )

        project = ProjectGenerator().generate(request, platform)

        expected_paths = {
            "system_his.json",
            "manifest.json",
            "rtl/top.v",
            "constraints/timing.sdc",
            "sim/tb_top.v",
            "reports/predicted_qor.json",
        }
        self.assertEqual(set(project.files), expected_paths)

        manifest = json.loads(project.files["manifest.json"])
        self.assertEqual(manifest["project_name"], "counter_8bit")
        self.assertEqual(manifest["top_module"], "top")
        self.assertEqual(manifest["sources"], ["rtl/top.v"])
        self.assertEqual(manifest["simulation"]["testbench"], "sim/tb_top.v")

        rtl = project.files["rtl/top.v"]
        self.assertRegex(rtl, r"module\s+top\s*\(")
        self.assertIn("input wire clk", rtl)
        self.assertIn("input wire rst_n", rtl)
        self.assertIn("input wire en", rtl)
        self.assertIn("output reg [7:0] count", rtl)

        testbench = project.files["sim/tb_top.v"]
        self.assertRegex(testbench, r"top\s+dut\s*\(")
        self.assertIn(".count(count)", testbench)
        self.assertIn("TEST_PASS", testbench)

        predicted_qor = json.loads(project.files["reports/predicted_qor.json"])
        self.assertEqual(predicted_qor["project_name"], "counter_8bit")
        self.assertEqual(predicted_qor["assumptions"]["counter_width"], 8)
        for key in ("lut", "ff", "bram", "dsp", "fmax_mhz", "confidence"):
            self.assertIn(key, predicted_qor["predicted"])

    def test_manifest_top_module_matches_rtl_module_name(self) -> None:
        request = ProjectRequest(task_type="counter", width=4, project_name="counter_4bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = ProjectGenerator().generate(request, platform)

        manifest = json.loads(project.files["manifest.json"])
        rtl = project.files["rtl/top.v"]
        module_name = re.search(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\s*\(", rtl)
        self.assertIsNotNone(module_name)
        self.assertEqual(manifest["top_module"], module_name.group(1))


if __name__ == "__main__":
    unittest.main()
