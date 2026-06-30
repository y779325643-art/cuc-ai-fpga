import unittest

from LLM.src.sr2fpga_agent.rtl_introspect import normalize_width, parse_module_ports, widths_equivalent


class RtlIntrospectTest(unittest.TestCase):
    def test_parse_module_ports_extracts_direction_and_width(self) -> None:
        rtl = "module top(input clk, input rst_n, input en, output reg [7:0] count);\nendmodule\n"

        ports = parse_module_ports(rtl, "top")

        self.assertEqual(ports["count"]["direction"], "output")
        self.assertEqual(normalize_width(ports["count"]["width"]), normalize_width(8))
        self.assertEqual(ports["clk"]["direction"], "input")

    def test_parse_module_ports_inherits_direction_for_grouped_ports(self) -> None:
        rtl = """
module top(
  input clk, rst_n,
  input [7:0] a, b,
  output reg [7:0] y
);
endmodule
"""

        ports = parse_module_ports(rtl, "top")

        self.assertEqual(ports["rst_n"]["direction"], "input")
        self.assertEqual(ports["b"]["direction"], "input")
        self.assertEqual(normalize_width(ports["b"]["width"]), normalize_width(8))

    def test_normalize_width_treats_range_and_int_equal(self) -> None:
        self.assertEqual(normalize_width("[7:0]"), normalize_width(8))

    def test_normalize_width_treats_concrete_minus_one_range_as_int_equal(self) -> None:
        self.assertEqual(normalize_width("[1-1:0]"), normalize_width(1))
        self.assertEqual(normalize_width("[8-1:0]"), normalize_width(8))

    def test_parse_module_ports_ignores_line_comments_in_port_list(self) -> None:
        rtl = """
module skid_buffer #(
  parameter DATA_WIDTH = 8
)(
  input wire clk,
  // input stream
  input wire in_valid,
  output reg in_ready,
  input wire [DATA_WIDTH-1:0] in_data,
  // output stream
  output reg out_valid,
  input wire out_ready,
  output reg [DATA_WIDTH-1:0] out_data
);
endmodule
"""

        ports = parse_module_ports(rtl, "skid_buffer")

        self.assertIn("in_valid", ports)
        self.assertIn("out_valid", ports)
        self.assertNotIn("input", ports)
        self.assertNotIn("output", ports)

    def test_normalize_width_treats_symbolic_range_as_parameter_width(self) -> None:
        self.assertEqual(normalize_width("[DATA_WIDTH-1:0]"), normalize_width("DATA_WIDTH"))

    def test_normalize_width_uses_dict_expr_before_resolved_value(self) -> None:
        self.assertEqual(
            normalize_width({"expr": "[DATA_WIDTH-1:0]", "resolved": 8}),
            normalize_width("[DATA_WIDTH-1:0]"),
        )

    def test_widths_equivalent_accepts_dict_resolved_against_concrete_rtl_width(self) -> None:
        self.assertTrue(widths_equivalent({"expr": "DATA_WIDTH", "resolved": 8}, 8))
        self.assertTrue(widths_equivalent({"expr": "[DATA_WIDTH-1:0]", "resolved": 8}, "[7:0]"))

    def test_widths_equivalent_accepts_single_bit_minus_one_rtl_range(self) -> None:
        rtl = "module top(input [1-1:0] clk, output [8-1:0] data);\nendmodule\n"

        ports = parse_module_ports(rtl, "top")

        self.assertTrue(widths_equivalent({"expr": "1", "resolved": 1}, ports["clk"]["width"]))
        self.assertTrue(widths_equivalent({"expr": "8", "resolved": 8}, ports["data"]["width"]))

    def test_widths_equivalent_accepts_complete_unbracketed_range_expr(self) -> None:
        self.assertTrue(widths_equivalent({"expr": "DATA_WIDTH-1:0", "resolved": None}, "[DATA_WIDTH-1:0]"))
        self.assertTrue(widths_equivalent({"expr": "2*DATA_WIDTH-1:0", "resolved": None}, "[2*DATA_WIDTH-1:0]"))

    def test_widths_equivalent_accepts_arithmetic_expr_against_rtl_range(self) -> None:
        self.assertTrue(widths_equivalent({"expr": "2*DATA_WIDTH", "resolved": 16}, "[2*DATA_WIDTH-1:0]"))


if __name__ == "__main__":
    unittest.main()
