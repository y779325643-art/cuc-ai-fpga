"""Read-only name index derived solely from the public entry boundary.

This is a prompt aid, not a second requirement or a semantic validator. It does
not inspect proposed modules, reference designs, assets or evaluator material.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from sr2fpga_agent.models import canonical_json_bytes


PUBLIC_INTERFACE_INDEX_VERSION = "pc21-public-interface-index-v1"


def public_interface_index(boundary: Mapping[str, Any]) -> dict[str, Any]:
    """Relate public logical ports, tensor identifiers and physical ABI names.

    The caller supplies an already admitted public boundary. Keep symbolic
    widths and tensor semantics in that authority instead of reinterpreting
    them here. Whitelisting fields also excludes unrelated caller metadata.
    """
    signature, abi = boundary["signature"], boundary["abi"]
    ports = []
    for name, port in sorted(signature["ports"].items()):
        pins = abi["ports"][name]
        item = {
            "logical_port": name,
            "kind": port["kind"],
            "direction": port["direction"],
            "domain": port.get("domain"),
            "abi": {key: pins[key] for key in ("signal", "payload", "valid", "ready") if key in pins},
        }
        if port["kind"] == "stream":
            item["protocol"] = port["protocol"]
            item["payload_kind"] = port["payload"]["kind"]
            if item["payload_kind"] == "tensor_beat":
                item["tensor_contract"] = port["payload"]["contract"]
        ports.append(item)
    result = {
        "view_version": PUBLIC_INTERFACE_INDEX_VERSION,
        "scope": "requirement_entry_boundary",
        "rtl_top": boundary["rtl_top"],
        "parameter_values": dict(boundary["parameter_values"]),
        "domains": [
            {"domain": name, "abi": {key: abi["domains"][name][key] for key in ("clock", "reset")}}
            for name in sorted(signature["domains"])
        ],
        "ports": ports,
    }
    # The view must not alias any nested input, including ABI maps.
    return json.loads(canonical_json_bytes(result))


def indexed_public_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Add the same derived entry index to every model stage with a task.

    The controller owns the index. Its content and version become part of the
    exact serialized request identity and the transport's input accounting.
    """
    if "public_interface_index" in payload:
        raise ValueError("public_interface_index is derived by the model gateway")
    result = dict(payload)
    if "public_task" in result:
        result["public_interface_index"] = public_interface_index(result["public_task"]["boundary"])
    return result
