"""Task-family metadata used by the deterministic project generator."""

from . import basic, datapath, ga, image, protocol, rl, stream


TASK_TYPE_ALIASES = {
    "mac_array": "matrix_vector_mac",
}

_FAMILY_MODULES = (basic, protocol, stream, datapath, image, rl, ga)
TASK_FAMILY_IDS = {
    task_type: family_id
    for module in _FAMILY_MODULES
    for task_type, family_id in module.TASK_FAMILY_IDS.items()
}
FAMILY_IDS = frozenset(TASK_FAMILY_IDS.values())
SUPPORTED_TASK_TYPES = set(TASK_FAMILY_IDS) | set(TASK_TYPE_ALIASES)


def canonical_task_type(task_type: str) -> str:
    """Return the generated task type used by the ProjectGenerator facade."""
    return TASK_TYPE_ALIASES.get(task_type, task_type)


def family_id_for_task_type(task_type: str) -> str:
    """Return a stable task-family ID for a supported task type or alias."""
    return TASK_FAMILY_IDS[canonical_task_type(task_type)]
