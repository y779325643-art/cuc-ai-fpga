"""PC 2.1 input boundary; schema acceptance is not semantic correctness."""

from .inputs import (
    BindingError,
    ParseLimits,
    PcInputError,
    PcParseError,
    PcSchemaError,
    TrustedContext,
    TrustedSource,
    assemble_project_contract,
    parse_design_proposal,
    parse_project_contract,
)
from .semantics import (
    PcSemanticError,
    validate_acyclic_modules,
    validate_entry_module,
    validate_instance_parameter_names,
    validate_instance_modules,
    validate_reachable_modules,
    validate_signature_sources,
)

__all__ = [
    "BindingError", "ParseLimits", "PcInputError", "PcParseError",
    "PcSchemaError", "TrustedContext", "TrustedSource",
    "assemble_project_contract", "parse_design_proposal", "parse_project_contract",
    "PcSemanticError", "validate_entry_module",
    "validate_instance_modules", "validate_acyclic_modules",
    "validate_reachable_modules",
    "validate_signature_sources",
    "validate_instance_parameter_names",
]
