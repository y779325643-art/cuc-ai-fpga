import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT / "contracts" / "system-his" / "system-his-v1.2.schema.json"
)
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "intent",
    "top",
    "state",
    "components",
    "instances",
    "data_flow",
    "control_flow",
    "timing",
    "resources",
    "verification",
    "artifacts",
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_system_his_schema_identity_and_closed_top_level() -> None:
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "https://sr2fpga.local/contracts/system-his/v1.2"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False


def test_system_his_schema_requires_canonical_v12_fields() -> None:
    schema = load_schema()
    assert set(schema["required"]) == REQUIRED_TOP_LEVEL_KEYS
    assert schema["properties"]["schema_version"]["const"] == "system-his-v1.2"
