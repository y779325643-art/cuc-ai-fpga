import pytest

from sr2fpga_agent.path_safety import (
    UnsupportedSynthesisLanguageError,
    build_yosys_script,
)


def test_build_yosys_script_preserves_legacy_verilog_command() -> None:
    assert (
        build_yosys_script(["rtl/top.v"], "top")
        == "read_verilog rtl/top.v; synth -top top; stat"
    )


def test_build_yosys_script_reads_systemverilog_with_sv_mode() -> None:
    assert build_yosys_script(
        ["rtl/package.sv", "rtl/top.sv"],
        "top",
    ) == (
        "read_verilog -sv rtl/package.sv rtl/top.sv; "
        "synth -top top; stat"
    )


def test_build_yosys_script_preserves_mixed_language_source_order() -> None:
    assert build_yosys_script(
        ["rtl/defs.v", "rtl/core.sv", "rtl/wrapper.v"],
        "wrapper",
    ) == (
        "read_verilog rtl/defs.v; read_verilog -sv rtl/core.sv; "
        "read_verilog rtl/wrapper.v; synth -top wrapper; stat"
    )


def test_build_yosys_script_accepts_manifest_language_metadata() -> None:
    assert build_yosys_script(
        ["src/design.v"],
        "design_top",
        {"src/design.v": "systemverilog"},
    ).startswith("read_verilog -sv src/design.v;")


@pytest.mark.parametrize(
    ("source", "metadata"),
    [
        ("rtl/top.vhd", None),
        ("rtl/top.v", {"rtl/top.v": "vhdl"}),
    ],
)
def test_build_yosys_script_reports_vhdl_as_backend_capability_gap(
    source: str,
    metadata: dict[str, str] | None,
) -> None:
    with pytest.raises(
        UnsupportedSynthesisLanguageError,
        match="unsupported Yosys synthesis language 'vhdl'",
    ):
        build_yosys_script([source], "top", metadata)
