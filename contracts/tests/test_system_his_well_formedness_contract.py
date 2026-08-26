import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "system-his" / "system-his-well-formedness-v1.json"


def test_well_formedness_contract_is_closed_and_ordered() -> None:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert set(payload) == {
        "contract_version",
        "system_his_version",
        "checker_api",
        "conformance_cases",
        "rules",
    }
    assert payload["contract_version"] == "system-his-well-formedness-v1"
    assert payload["system_his_version"] == "system-his-v1.2"
    assert [rule["rule_id"] for rule in payload["rules"]] == [f"W{index}" for index in range(1, 11)]
    for rule in payload["rules"]:
        assert set(rule) == {"rule_id", "h_stage", "applicability", "subject"}
        assert rule["h_stage"] in {"h1", "h1_h2", "h1_l0"}
        assert rule["applicability"] in {
            "always",
            "typed_connections_present",
            "combinational_declaration_present",
            "cdc_flow_present",
            "memory_intent_present",
        }
        assert rule["subject"]


def test_conformance_matrix_references_existing_tests() -> None:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert [case["case_id"] for case in payload["conformance_cases"]] == [
        "schema",
        "h0",
        "h1",
        "h2",
        "reset",
        "lowerer",
        "compatibility",
        "quarantine",
        "deterministic_writer",
    ]
    for case in payload["conformance_cases"]:
        assert set(case) == {"case_id", "positive_test", "negative_test"}
        for polarity in ("positive_test", "negative_test"):
            parts = case[polarity].split("::")
            relative_path, test_name = parts[0], parts[-1]
            source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            assert f"def {test_name}" in source
