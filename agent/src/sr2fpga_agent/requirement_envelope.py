"""Deterministic normalization and routing for open FPGA requirements.

This module records requirement facts and chooses either an exact declared
family or capability composition.  It never performs fuzzy/nearest-family
matching and it does not claim that a detected capability is implemented.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from sr2fpga_agent.models import PlatformProfile, ProjectRequest


_FACT_ORDER = (
    "declared_task_type",
    "functional_capabilities",
    "data_width_bits",
    "clock_frequencies_hz",
    "clock_domain_count",
    "reset_polarity",
    "numeric_representation",
    "interface_protocols",
    "latency_cycles",
    "throughput_constraint",
    "target_platform",
    "acceptance_criteria",
)

_CAPABILITY_PATTERNS = (
    ("adc_interface", r"(?<![a-z0-9_])adc(?![a-z0-9_])|模数转换|采样接口"),
    ("clock_domain_crossing", r"(?<![a-z0-9_])cdc(?![a-z0-9_])|dual[- ]clock|cross[- ]clock|双时钟|跨时钟|异步\s*fifo"),
    ("dma", r"(?<![a-z0-9_])dma(?![a-z0-9_])|直接存储器访问"),
    ("external_memory", r"(?<![a-z0-9_])(?:ddr\d*|hbm|sdram)(?![a-z0-9_])|外部(?:存储器|内存)"),
    ("on_chip_memory", r"(?<![a-z0-9_])(?:bram|sram)(?![a-z0-9_])|block\s*ram|片上(?:存储器|内存)"),
    ("pcie", r"(?<![a-z0-9_])pci[- ]?e(?![a-z0-9_])|(?<![a-z0-9_])pcie(?![a-z0-9_])"),
    ("axi_stream", r"axi\s*[-_ ]?stream|(?<![a-z0-9_])axis(?![a-z0-9_])"),
    ("spi", r"(?<![a-z0-9_])spi(?![a-z0-9_])"),
    ("i2c", r"(?<![a-z0-9_])i2c(?![a-z0-9_])|i²c"),
    ("uart", r"(?<![a-z0-9_])uart(?![a-z0-9_])"),
    ("streaming", r"(?<![a-z0-9_])stream(?:ing)?(?![a-z0-9_])|数据流|流式"),
    ("fifo", r"(?<![a-z0-9_])fifo(?![a-z0-9_])|先进先出"),
    ("dsp", r"matched\s+filter|(?<![a-z0-9_])(?:fir|fft|mac)(?![a-z0-9_])|滤波|乘加|傅里叶"),
    ("image_pipeline", r"sobel|convolution|图像|像素|帧缓存|\bpixel\b"),
    ("state_machine", r"state\s+machine|(?<![a-z0-9_])fsm(?![a-z0-9_])|状态机"),
    ("counter", r"(?<![a-z0-9_])(?:counter|count(?:s|ed|ing)?)(?![a-z0-9_])|计数(?:器)?"),
)

_PROTOCOL_PATTERNS = (
    ("axi_stream", _CAPABILITY_PATTERNS[6][1]),
    ("pcie", _CAPABILITY_PATTERNS[5][1]),
    ("spi", _CAPABILITY_PATTERNS[7][1]),
    ("i2c", _CAPABILITY_PATTERNS[8][1]),
    ("uart", _CAPABILITY_PATTERNS[9][1]),
    ("valid_ready", r"valid\s*[-_/ ]\s*ready|有效就绪"),
)

_INTERFACE_CLAUSE_PATTERN = r"(?<![a-z0-9_])(?:bus|protocol|interface)(?![a-z0-9_])|总线|协议|接口"
_NAMED_INTERFACE_PATTERN = (
    r"(?<![a-z0-9_])(?P<name>[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*"
    r"(?:\s+[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*)?)\s*"
    r"(?:bus|protocol|interface|总线|协议|接口)(?![a-z0-9_])"
)
_STANDALONE_OPAQUE_PROTOCOL_PATTERNS = (
    ("wishbone", r"(?<![a-z0-9_])wishbone(?![a-z0-9_])"),
)
_VAGUE_INTERFACE_NAMES = frozenset(
    {
        "a",
        "an",
        "the",
        "with",
        "via",
        "over",
        "through",
        "using",
        "and",
        "or",
        "to",
        "from",
        "for",
        "of",
        "custom",
        "standard",
        "simple",
        "host",
        "device",
        "peripheral",
        "processor",
        "client",
        "server",
        "master",
        "slave",
        "source",
        "sink",
        "fabric",
        "user",
        "application",
        "system",
        "memory",
        "sensor",
        "network",
        "external",
        "internal",
        "input",
        "output",
        "control",
        "configuration",
        "config",
        "status",
        "debug",
        "management",
        "clock",
        "reset",
        "data",
        "capture",
        "sample",
        "sampling",
        "channel",
        "port",
        "stream",
        "streaming",
        "serial",
        "parallel",
        "hardware",
        "software",
        "fpga",
        "rtl",
        "register",
        "read",
        "write",
        "handshake",
        "valid",
        "ready",
        "compatible",
    }
)

_CONDITIONAL_FACTS = {
    "adc_interface": ("adc_interface_contract",),
    "clock_domain_crossing": ("cdc_policy",),
    "dma": ("dma_transfer_contract",),
    "external_memory": ("memory_depth", "memory_access_contract"),
    "on_chip_memory": ("memory_depth", "memory_access_contract"),
    "pcie": ("pcie_endpoint_contract",),
}


@dataclass(frozen=True)
class RequirementFact:
    key: str
    value: Any
    origin: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class CriticalAmbiguity:
    key: str
    question: str
    reason: str


@dataclass(frozen=True)
class RequirementEnvelope:
    requirement_id: str
    raw_requirement: str
    facts: tuple[RequirementFact, ...]
    capability_labels: tuple[str, ...]
    critical_ambiguities: tuple[CriticalAmbiguity, ...]

    @property
    def explicit_facts(self) -> dict[str, Any]:
        return {fact.key: fact.value for fact in self.facts if fact.origin == "explicit"}

    @property
    def default_facts(self) -> dict[str, Any]:
        return {fact.key: fact.value for fact in self.facts if fact.origin == "default"}

    @property
    def assumption_facts(self) -> dict[str, Any]:
        return {fact.key: fact.value for fact in self.facts if fact.origin == "assumption"}

    @property
    def unknown_facts(self) -> tuple[str, ...]:
        return tuple(fact.key for fact in self.facts if fact.origin == "unknown")

    def to_prompt_payload(self) -> dict[str, Any]:
        """Return the bounded JSON payload intended for a generation prompt."""

        return {
            "requirement_id": self.requirement_id,
            "requirement_text": self.raw_requirement,
            "explicit_facts": _json_value(self.explicit_facts),
            "default_facts": _json_value(self.default_facts),
            "assumption_facts": _json_value(self.assumption_facts),
            "unknown_facts": list(self.unknown_facts),
            "capability_labels": list(self.capability_labels),
            "critical_ambiguities": [asdict(item) for item in self.critical_ambiguities],
        }

    def requirement_trace_template(self) -> dict[str, Any]:
        """Return the model-fillable trace skeleton for generic H3."""

        required_facts = {
            fact.key: {
                "value": _json_value(fact.value),
                "origin": fact.origin,
            }
            for fact in self.facts
            if fact.origin in {"explicit", "default", "assumption"}
        }
        return {
            "requirement_id": self.requirement_id,
            "required_facts": required_facts,
            "fact_to_his": {key: [] for key in required_facts},
            "unresolved_facts": [],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_prompt_payload()
        payload["facts"] = [_json_value(asdict(fact)) for fact in self.facts]
        return payload


@dataclass(frozen=True)
class ExactFamilyMetadata:
    declared_family: str
    matched_alias: str
    family_id: str


@dataclass(frozen=True)
class RequirementRouteResult:
    strategy: str
    readiness: str
    exact_family: ExactFamilyMetadata | None
    unmatched_declared_family: str | None
    capability_labels: tuple[str, ...]
    critical_ambiguity_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


def build_requirement_envelope(
    description: str,
    *,
    defaults: Mapping[str, Any] | None = None,
    assumptions: Mapping[str, Any] | None = None,
    clarifications: Mapping[str, Any] | None = None,
) -> RequirementEnvelope:
    """Extract explicit/default/unknown facts without inferring a family.

    Hardware defaults are never hidden here. A caller may provide trusted
    platform or request defaults; explicit text always takes precedence.
    """

    raw_requirement = description.strip()
    if not raw_requirement:
        raise ValueError("requirement description must not be empty")

    supplied_defaults = dict(defaults or {})
    supplied_assumptions = dict(assumptions or {})
    supplied_clarifications = dict(clarifications or {})
    default_assumption_overlap = sorted(
        set(supplied_defaults).intersection(supplied_assumptions)
    )
    if default_assumption_overlap:
        raise ValueError(
            "requirement facts cannot be both defaults and assumptions: "
            + ", ".join(default_assumption_overlap)
        )
    clarification_overlap = sorted(
        set(supplied_clarifications).intersection(supplied_defaults)
        | set(supplied_clarifications).intersection(supplied_assumptions)
    )
    if clarification_overlap:
        raise ValueError(
            "clarification facts cannot also be defaults or assumptions: "
            + ", ".join(clarification_overlap)
        )
    base_capabilities = _detect(raw_requirement, _CAPABILITY_PATTERNS)
    known_protocols = _detect(raw_requirement, _PROTOCOL_PATTERNS)
    opaque_protocols = _explicit_opaque_protocols(
        raw_requirement,
        known_protocols=known_protocols,
        known_capabilities=base_capabilities,
    )
    protocols = tuple(dict.fromkeys((*known_protocols, *opaque_protocols)))
    explicit = _extract_facts(raw_requirement, protocols)
    clarified_capabilities = _clarified_capabilities(
        supplied_clarifications.get("functional_decomposition")
    )
    capabilities = tuple(
        dict.fromkeys((*base_capabilities, *opaque_protocols, *clarified_capabilities))
    )
    if capabilities:
        explicit["functional_capabilities"] = (
            capabilities,
            tuple(
                (
                    "clarification_answer:functional_decomposition"
                    if label in clarified_capabilities
                    else f"detected:{label}"
                )
                for label in capabilities
            ),
        )
    keys = list(_FACT_ORDER)
    for capability in capabilities:
        for key in _CONDITIONAL_FACTS.get(capability, ()):
            if key not in keys:
                keys.append(key)
    keys.extend(
        sorted(
            (
                set(supplied_defaults)
                | set(supplied_assumptions)
                | set(supplied_clarifications)
            )
            - set(keys)
        )
    )

    facts: list[RequirementFact] = []
    for key in keys:
        if key in explicit:
            value, evidence = explicit[key]
            facts.append(RequirementFact(key, _freeze(value), "explicit", evidence))
        elif supplied_clarifications.get(key) is not None:
            facts.append(
                RequirementFact(
                    key,
                    _freeze(supplied_clarifications[key]),
                    "explicit",
                    (f"clarification_answer:{key}",),
                )
            )
        elif supplied_defaults.get(key) is not None:
            facts.append(
                RequirementFact(
                    key,
                    _freeze(supplied_defaults[key]),
                    "default",
                    (f"caller_default:{key}",),
                )
            )
        elif supplied_assumptions.get(key) is not None:
            facts.append(
                RequirementFact(
                    key,
                    _freeze(supplied_assumptions[key]),
                    "assumption",
                    (f"system_assumption:{key}",),
                )
            )
        else:
            facts.append(RequirementFact(key, None, "unknown"))

    fact_map = {fact.key: fact for fact in facts}
    return RequirementEnvelope(
        requirement_id=_requirement_id(raw_requirement, tuple(facts)),
        raw_requirement=raw_requirement,
        facts=tuple(facts),
        capability_labels=capabilities,
        critical_ambiguities=_ambiguities(
            capabilities,
            fact_map,
            vague_interface_clause=(
                bool(re.search(_INTERFACE_CLAUSE_PATTERN, raw_requirement, re.I))
                and not protocols
            ),
        ),
    )


def build_request_requirement_envelope(
    request: ProjectRequest,
    platform: PlatformProfile,
    *,
    clarification_facts: Mapping[str, Any] | None = None,
) -> RequirementEnvelope:
    """Build the shared request envelope used by routing, prompting, and H3."""

    defaults: dict[str, Any] = {
        "data_width_bits": request.width,
        "clock_frequencies_hz": (platform.clock_hz,),
        "reset_polarity": platform.reset_polarity,
        "target_platform": platform.name,
        "acceptance_criteria": (
            "independent evaluator must verify every explicit functional and protocol clause"
        ),
    }
    canonical_task_type = _canonical_task_type(request.task_type)
    if canonical_task_type and canonical_task_type != "unclassified":
        defaults["declared_task_type"] = canonical_task_type
    return build_requirement_envelope(
        effective_request_requirement(request),
        defaults=defaults,
        clarifications=clarification_facts,
    )


def effective_request_requirement(request: ProjectRequest) -> str:
    """Return the one effective requirement text used by every generation path."""

    description = request.description.strip()
    if description:
        return description
    task_label = _canonical_task_type(request.task_type).strip() or "unclassified"
    return f"Generate a {request.width}-bit {task_label} FPGA RTL project."


def _canonical_task_type(task_type: str) -> str:
    from sr2fpga_agent.task_families import TASK_TYPE_ALIASES

    return TASK_TYPE_ALIASES.get(task_type, task_type)


def route_requirement(
    envelope: RequirementEnvelope,
    *,
    declared_family: str | None = None,
    exact_family_aliases: Mapping[str, str] | None = None,
) -> RequirementRouteResult:
    """Use an exact declared alias or fall back to capability composition."""

    aliases: dict[str, str] = {}
    for alias, family_id in (exact_family_aliases or {}).items():
        normalized = _normalize(alias)
        if not normalized:
            raise ValueError("exact family alias must not be empty")
        if normalized in aliases and aliases[normalized] != family_id:
            raise ValueError(f"conflicting exact family alias: {alias}")
        aliases[normalized] = family_id

    declared = (declared_family or "").strip()
    family_id = aliases.get(_normalize(declared)) if declared else None
    exact_family = (
        ExactFamilyMetadata(declared, _normalize(declared), family_id)
        if family_id is not None
        else None
    )
    ambiguity_keys = tuple(
        item.key
        for item in envelope.critical_ambiguities
        if not (exact_family is not None and item.key == "functional_decomposition")
    )
    return RequirementRouteResult(
        strategy="exact_family" if exact_family else "capability_composition",
        readiness="needs_clarification" if ambiguity_keys else "ready",
        exact_family=exact_family,
        unmatched_declared_family=declared if declared and exact_family is None else None,
        capability_labels=envelope.capability_labels,
        critical_ambiguity_keys=ambiguity_keys,
    )


def _extract_facts(
    text: str,
    interface_protocols: tuple[str, ...],
) -> dict[str, tuple[Any, tuple[str, ...]]]:
    facts: dict[str, tuple[Any, tuple[str, ...]]] = {}

    widths = tuple(re.finditer(r"(?<!\d)(\d+)\s*(?:-\s*)?bits?(?![a-z])|(\d+)\s*位(?:宽|数据)?", text, re.I))
    if widths:
        values = tuple(dict.fromkeys(int(item.group(1) or item.group(2)) for item in widths))
        facts["data_width_bits"] = (values[0] if len(values) == 1 else values, _evidence(widths))

    clocks = tuple(re.finditer(r"(?<![\d.])(\d+(?:\.\d+)?)\s*(ghz|mhz|khz|hz|吉赫兹|兆赫兹|千赫兹|赫兹)", text, re.I))
    if clocks:
        values = tuple(dict.fromkeys(_hz(item.group(1), item.group(2)) for item in clocks))
        facts["clock_frequencies_hz"] = (values, _evidence(clocks))

    dual = re.search(r"dual[- ]clock|two\s+clock\s+domains?|双时钟|两个时钟域", text, re.I)
    single = re.search(r"single[- ]clock|单时钟|单一时钟域", text, re.I)
    if dual or single:
        match = dual or single
        assert match is not None
        facts["clock_domain_count"] = (2 if dual else 1, (match.group(0),))
    elif len(clocks) > 1:
        facts["clock_domain_count"] = (len(facts["clock_frequencies_hz"][0]), ("derived_from_explicit_clock_frequencies",))

    for value, pattern in (
        ("active_high", r"active[- ]?high|high[- ]?active|高电平有效|高有效"),
        ("active_low", r"active[- ]?low|low[- ]?active|低电平有效|低有效"),
    ):
        if match := re.search(pattern, text, re.I):
            facts["reset_polarity"] = (value, (match.group(0),))
            break

    if match := re.search(r"\bunsigned\b|无符号|\bsigned\b|有符号|fixed[- ]?point|定点|floating[- ]?point|浮点", text, re.I):
        token = match.group(0).casefold()
        value = "unsigned" if "unsigned" in token or "无符号" in token else "signed" if "signed" in token or "有符号" in token else "fixed_point" if "fixed" in token or "定点" in token else "floating_point"
        facts["numeric_representation"] = (value, (match.group(0),))

    if interface_protocols:
        facts["interface_protocols"] = (interface_protocols, interface_protocols)

    if match := re.search(r"latency\s*(?:of|=|:)?\s*(\d+)\s*cycles?|(\d+)\s*周期(?:延迟|时延)", text, re.I):
        facts["latency_cycles"] = (int(match.group(1) or match.group(2)), (match.group(0),))
    if match := re.search(r"(?:one|1)\s+(?:sample|word|item|result)\s+per\s+cycle|每周期(?:处理|接收|输出)?(?:一个|1个?)", text, re.I):
        facts["throughput_constraint"] = ("one_per_cycle", (match.group(0),))
    if match := re.search(r"(?:acceptance(?:\s+criteria)?|passes?\s+when|验收(?:条件)?|通过条件)\s*[:：]\s*(.+)$", text, re.I):
        facts["acceptance_criteria"] = (match.group(1).strip(), (match.group(0),))

    _extract_conditional_facts(text, facts)
    return facts


def _extract_conditional_facts(text: str, facts: dict[str, tuple[Any, tuple[str, ...]]]) -> None:
    patterns = (
        ("memory_depth", r"(?:depth|深度)\s*(?:of|为|=|:|：)?\s*(\d+)|(\d+)\s*[- ]?deep"),
        ("cdc_policy", r"two[- ]flop synchroni[sz]er|双触发器同步|asynchronous fifo|异步\s*fifo"),
        ("pcie_endpoint_contract", r"pci[- ]?e\s*gen\s*(\d+)\s*x\s*(\d+)"),
        ("dma_transfer_contract", r"burst\s+length\s*(?:of|=|:)?\s*(\d+)|突发长度\s*(?:为|=|:|：)?\s*(\d+)"),
        ("memory_access_contract", r"dual[- ]port|single[- ]port|双口|单口"),
    )
    for key, pattern in patterns:
        if not (match := re.search(pattern, text, re.I)):
            continue
        if key == "memory_depth":
            value: Any = int(match.group(1) or match.group(2))
        elif key == "pcie_endpoint_contract":
            value = f"gen{match.group(1)}_x{match.group(2)}"
        elif key == "dma_transfer_contract":
            value = f"burst_length_{match.group(1) or match.group(2)}"
        elif key == "cdc_policy":
            value = "async_fifo" if "fifo" in match.group(0).casefold() else "two_flop_synchronizer"
        else:
            value = _normalize(match.group(0))
        facts[key] = (value, (match.group(0),))


def _ambiguities(
    capabilities: tuple[str, ...],
    facts: Mapping[str, RequirementFact],
    *,
    vague_interface_clause: bool = False,
) -> tuple[CriticalAmbiguity, ...]:
    items: list[CriticalAmbiguity] = []
    if not capabilities:
        items.append(CriticalAmbiguity("functional_decomposition", "Which independently verifiable hardware capabilities make up the system?", "No capability label is grounded in the requirement text."))

    base = (
        ("data_width_bits", "What data widths cross the RTL boundary?", "Port widths change the interface contract."),
        ("clock_frequencies_hz", "What clock frequencies apply?", "Clock constraints depend on them."),
        ("reset_polarity", "What reset polarity is required?", "Reset behavior is externally observable."),
        ("target_platform", "Which FPGA platform or portable target is required?", "Available primitives and constraints are platform-dependent."),
        ("acceptance_criteria", "What public behavior must the project pass?", "A complete project needs an independent acceptance contract."),
    )
    items.extend(CriticalAmbiguity(*entry) for entry in base if _unknown(facts, entry[0]))
    if vague_interface_clause and _unknown(facts, "interface_protocols"):
        items.append(
            CriticalAmbiguity(
                "interface_protocols",
                "Which concrete bus or interface protocol and handshake rules apply?",
                "An interface is requested, but no concrete protocol is grounded in the text.",
            )
        )

    conditional = (
        ("adc_interface", "adc_interface_contract", "What sample format, rate, and interface timing does the ADC use?"),
        ("clock_domain_crossing", "cdc_policy", "Which CDC mechanism is allowed for each crossing?"),
        ("external_memory", "memory_depth", "What storage capacity is required?"),
        ("on_chip_memory", "memory_depth", "What storage capacity is required?"),
        ("external_memory", "memory_access_contract", "What read/write, latency, and ordering semantics apply?"),
        ("on_chip_memory", "memory_access_contract", "What port and read/write semantics apply?"),
        ("dma", "dma_transfer_contract", "What address, length, alignment, and completion contract applies?"),
        ("pcie", "pcie_endpoint_contract", "Which PCIe generation, lanes, and endpoint interface are required?"),
    )
    seen = {item.key for item in items}
    for capability, key, question in conditional:
        if capability in capabilities and key not in seen and _unknown(facts, key):
            items.append(CriticalAmbiguity(key, question, "The capability name alone is not a complete hardware contract."))
            seen.add(key)
    if {"dsp", "image_pipeline"}.intersection(capabilities) and _unknown(facts, "numeric_representation"):
        items.append(CriticalAmbiguity("numeric_representation", "What signedness and numeric format are required?", "Arithmetic semantics cannot be recovered from width alone."))
    return tuple(items)


def _detect(text: str, patterns: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    return tuple(label for label, pattern in patterns if re.search(pattern, text, re.I))


def _clarified_capabilities(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    values = (value,) if isinstance(value, str) else value
    if not isinstance(values, (tuple, list)) or not values:
        raise ValueError(
            "functional_decomposition clarification must be a capability ID or non-empty list"
        )
    capabilities: list[str] = []
    for item in values:
        if not isinstance(item, str) or not _normalize(item):
            raise ValueError("clarified capability IDs must be non-empty strings")
        capabilities.append(_normalize(item))
    return tuple(dict.fromkeys(capabilities))


def _explicit_opaque_protocols(
    text: str,
    *,
    known_protocols: tuple[str, ...],
    known_capabilities: tuple[str, ...],
) -> tuple[str, ...]:
    names = list(_detect(text, _STANDALONE_OPAQUE_PROTOCOL_PATTERNS))
    excluded = set(known_protocols).union(known_capabilities, _VAGUE_INTERFACE_NAMES)
    excluded.update(
        part
        for capability in known_capabilities
        for part in capability.split("_")
    )
    for match in re.finditer(_NAMED_INTERFACE_PATTERN, text, re.I):
        name = _normalize(match.group("name"))
        if name in excluded:
            continue
        parts = name.split("_")
        while parts and parts[0] in _VAGUE_INTERFACE_NAMES:
            parts.pop(0)
        name = "_".join(parts)
        if name in excluded:
            continue
        while parts and parts[-1] in _VAGUE_INTERFACE_NAMES:
            parts.pop()
        name = "_".join(parts)
        if name and name not in excluded:
            names.append(name)
    return tuple(dict.fromkeys(names))


def _unknown(facts: Mapping[str, RequirementFact], key: str) -> bool:
    return key not in facts or facts[key].origin == "unknown"


def _evidence(matches: tuple[re.Match[str], ...]) -> tuple[str, ...]:
    return tuple(match.group(0) for match in matches)


def _hz(value: str, unit: str) -> int:
    factors = {"ghz": 10**9, "吉赫兹": 10**9, "mhz": 10**6, "兆赫兹": 10**6, "khz": 10**3, "千赫兹": 10**3, "hz": 1, "赫兹": 1}
    return int(round(float(value) * factors[unit.casefold()]))


def _normalize(value: str) -> str:
    return re.sub(r"[\s_-]+", "_", value.strip().casefold()).strip("_")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple((str(key), _freeze(item)) for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _requirement_id(text: str, facts: tuple[RequirementFact, ...]) -> str:
    identity = {
        "schema": "requirement-envelope-v1",
        "requirement_text": " ".join(text.split()),
        "explicit_facts": {item.key: _json_value(item.value) for item in facts if item.origin == "explicit"},
        "default_facts": {item.key: _json_value(item.value) for item in facts if item.origin == "default"},
        "assumption_facts": {
            item.key: _json_value(item.value) for item in facts if item.origin == "assumption"
        },
    }
    canonical = json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"req-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value
