"""Deterministic physical views of already checked PC 2.1 types.

These helpers describe packing. They never insert arithmetic, queues, layout
conversion, or sequence state into RTL.
"""

from __future__ import annotations

from itertools import product
from typing import Any, Iterator


ABI_VERSION = "pc21-packed-abi-v1"


def type_layout(value: dict[str, Any], *, offset: int = 0) -> dict[str, Any]:
    """Return explicit bit ranges; record field zero occupies the low bits."""
    kind = value["kind"]
    width = value["width"]
    result: dict[str, Any] = {"kind": kind, "lsb": offset, "width": width}
    if kind == "record":
        fields = []
        cursor = offset
        for field in value["fields"]:
            fields.append({"name": field["name"], **type_layout(field["type"], offset=cursor)})
            cursor += field["type"]["width"]
        result["fields"] = fields
    elif kind == "tensor_beat":
        descriptor = value["descriptor"]
        bits = descriptor["element"]["width"]
        lanes = descriptor["layout"]["lanes"]
        result.update({
            "descriptor": descriptor,
            "lanes": [{"lane": j, "lsb": offset + j * bits, "width": bits}
                      for j in range(lanes)],
            "mask": ({"lsb": offset + lanes * bits, "width": lanes}
                     if descriptor["layout"]["tail"] == "zero_pad_mask" else None),
        })
    else:
        result["signed"] = kind == "sint" or (kind == "fixed" and value["signed"])
        if kind == "fixed":
            result["fraction_bits"] = value["fraction_bits"]
    return result


def tensor_beats(descriptor: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield logical coordinates for accepted beats, including partial groups.

    No invocation or coordinate pins are added to hardware. Invalid tail lanes
    have ``None`` coordinates and must carry raw zero with a clear mask bit.
    """
    extents = {axis["axis"]: axis["extent"] for axis in descriptor["shape"]}
    order = descriptor["layout"]["order"]
    lane_axis = order[-1]
    lanes = descriptor["layout"]["lanes"]
    sequence = descriptor["sequence"]
    groups = sequence.get("groups", 1)
    coords = []
    for outer in product(*(range(extents[axis]) for axis in order[:-1])):
        for start in range(0, extents[lane_axis], lanes):
            coordinates = []
            for lane in range(lanes):
                coordinates.append(
                    {**dict(zip(order[:-1], outer)), lane_axis: start + lane}
                    if start + lane < extents[lane_axis] else None
                )
            coords.append(coordinates)
    indices = (product(range(groups), range(len(coords)))
               if sequence.get("group_order", "outermost") == "outermost"
               else ((group, index) for index in range(len(coords)) for group in range(groups)))
    for group, index in indices:
        yield {"group": group if sequence["kind"] == "partial_sum" else None,
               "coordinates": coords[index]}


def pack_tensor_beat(descriptor: dict[str, Any], raw_lanes: list[int | None]) -> int:
    """Pack raw integers; None denotes an invalid tail lane, never numeric zero."""
    lanes = descriptor["layout"]["lanes"]
    bits = descriptor["element"]["width"]
    signed = descriptor["element"]["kind"] == "sint"
    if len(raw_lanes) != lanes:
        raise ValueError("lane count does not match tensor ABI")
    lower = -(1 << (bits - 1)) if signed else 0
    upper = (1 << (bits - int(signed))) - 1
    payload = mask = 0
    for lane, raw in enumerate(raw_lanes):
        if raw is None:
            if descriptor["layout"]["tail"] != "zero_pad_mask":
                raise ValueError("exact tensor ABI cannot encode invalid lanes")
            continue
        if type(raw) is not int or not lower <= raw <= upper:
            raise ValueError("raw lane is outside element storage range")
        payload |= (raw & ((1 << bits) - 1)) << (lane * bits)
        mask |= 1 << lane
    if descriptor["layout"]["tail"] == "zero_pad_mask":
        payload |= mask << (lanes * bits)
    return payload
