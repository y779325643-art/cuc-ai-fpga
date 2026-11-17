"""Gateway transactions with real budgets and local fake providers only.

No candidate model, network, external provider or EDA command is invoked.
"""

from dataclasses import dataclass
import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.execution.budgets import BudgetExceeded, BudgetLedger, BudgetLimits
from sr2fpga_agent.execution.gateway import (
    ClientTransport,
    ModelGateway,
    ModelStageFailure,
    ProviderCapacityTransport,
    ReplayTransport,
    create_provider_capacity_transport,
    create_provider_transport,
)


def authority(tmp_path, methods=("M1",), **changes):
    values = dict(
        max_total_input_tokens=10_000,
        max_total_output_tokens=2_000,
        max_single_output_tokens=256,
        # Generic compatibility guidance is part of every serialized prompt.
        # Boundary-specific tests below still override this with small ceilings.
        max_context_tokens=20_000,
        max_public_tool_calls=20,
        max_active_seconds=30,
        max_eda_seconds=30,
        max_cpu_seconds=60,
        max_memory_bytes=1_000_000,
    )
    values.update(changes)
    store = ArtifactStore(tmp_path / "store")
    ledger = BudgetLedger(
        store,
        "gateway-fixture",
        {method: BudgetLimits.for_method(method, **values) for method in methods},
    )
    return store, ledger


def call(gateway, operation="initial", consumers=("M1",), payload=None, stage="direct"):
    return gateway.call(
        operation,
        stage,
        consumers,
        {"public_text": "A fixed public RTL task"} if payload is None else payload,
        output_format="Return the declared fixture proposal.",
    )


def response_key(operation):
    return "pc21-model/" + hashlib.sha256(operation.encode()).hexdigest() + "/response"


@pytest.fixture
def fake_provider():
    @dataclass(frozen=True)
    class Configuration:
        api_key: str = "UNITTEST_PRIVATE_CREDENTIAL_DO_NOT_SERIALIZE"
        model: str = "local-fake-provider"
        max_tokens: int = 999
        timeout_seconds: float = 600
        transport_attempts: int = 7
        response_format: str = "json_object"

    class LocalProvider:
        instances = []
        calls = []
        content = "fixture-rtl"
        error = None
        usage = {"input_tokens": 13, "output_tokens": 7, "cached_tokens": 2}

        def __init__(self, config):
            self.config = config
            self.instances.append(self)

        def chat(self, messages):
            self.calls.append(messages)
            if self.error is not None:
                raise self.error
            return self.content

        def consume_token_usage(self):
            return self.usage

        def consume_transport_attempt_count(self):
            return 1

        def consume_response_provenance(self):
            return {
                "provider_model": self.config.model,
                "adapter": "unit-test-local-fake",
            }

    return LocalProvider, Configuration


def test_replay_is_explicitly_synthetic_and_shared_call_is_fully_attributed(tmp_path):
    store, ledger = authority(tmp_path, ("M0", "M1"))
    transport = ReplayTransport({"direct": ["fixture-rtl"]})
    gateway = ModelGateway(store, ledger, transport, max_call_seconds=2)
    response = call(gateway, consumers=("M0", "M1"))
    assert response.text == "fixture-rtl"
    assert transport.is_live is False and transport.source_class == "synthetic_fixture"
    snapshot = ledger.snapshot()
    assert snapshot["actual"]["used"]["model_calls"] == 1
    assert snapshot["methods"]["M0"]["used"]["model_calls"] == 1
    assert snapshot["methods"]["M1"]["used"]["model_calls"] == 1
    assert snapshot["budget_status"] == "compliant"
    assert len(transport.requests) == 1
    assert all(
        isinstance(message["content"], str)
        for message in transport.requests[0]["messages"]
    )


def test_provider_requires_explicit_execution_scope_without_dispatch(
    tmp_path, fake_provider
):
    Provider, Config = fake_provider
    store, ledger = authority(tmp_path)
    transport = ClientTransport(
        Provider(Config()), lambda messages: 13, tokenizer_id="fixture-exact-counter"
    )
    with pytest.raises(ValueError, match="explicit execution scope"):
        ModelGateway(store, ledger, transport)
    assert Provider.calls == []
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 0


def test_client_limits_one_transport_attempt_and_keeps_credentials_out_of_artifacts(
    tmp_path, fake_provider
):
    Provider, Config = fake_provider
    config = Config()
    store, ledger = authority(tmp_path, max_single_output_tokens=64)
    transport = ClientTransport(
        Provider(config), lambda messages: 13, tokenizer_id="fixture-exact-counter"
    )
    gateway = ModelGateway(
        store, ledger, transport, allow_model_calls=True, max_call_seconds=1.25
    )
    response = call(gateway)
    dispatched = Provider.instances[-1].config
    assert dispatched.max_tokens == 64
    assert dispatched.timeout_seconds == 1.25
    assert dispatched.transport_attempts == 1
    assert dispatched.response_format == "text"
    assert config.max_tokens == 999 and config.transport_attempts == 7
    assert (
        response.input_tokens == 13
        and response.output_tokens == 7
        and response.cached_tokens == 2
    )
    assert response.transport_attempts == 1
    usage = ledger.snapshot()["actual"]["observed"]
    assert usage["input_tokens"] == 13 and usage["output_tokens"] == 7
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 1
    secret = config.api_key.encode()
    assert all(
        secret not in path.read_bytes()
        for path in store.root.rglob("*")
        if path.is_file()
    )


def test_known_response_reopen_reads_original_without_another_dispatch(tmp_path):
    store, ledger = authority(tmp_path)
    first = ReplayTransport({"direct": ["original-response"]})
    expected = call(ModelGateway(store, ledger, first, max_call_seconds=2))
    _, reopened = authority(tmp_path)
    second = ReplayTransport({"direct": ["unrequested-second-response"]})
    observed = call(ModelGateway(store, reopened, second, max_call_seconds=2))
    assert observed == expected
    assert first.requests and second.requests == []
    assert reopened.snapshot()["actual"]["used"]["model_calls"] == 1


def test_spent_call_ceiling_allows_receipt_read_but_never_new_model_opportunity(
    tmp_path,
):
    store, ledger = authority(tmp_path, ("M0",))
    transport = ReplayTransport({"direct": ["first", "unused"]})
    gateway = ModelGateway(store, ledger, transport)
    first = call(gateway, consumers=("M0",))
    assert ledger.remaining("M0", "model_calls") == 0
    assert call(gateway, consumers=("M0",)) == first
    with pytest.raises(BudgetExceeded, match="model_calls"):
        call(gateway, operation="another-request", consumers=("M0",))
    assert len(transport.requests) == 1


@pytest.mark.parametrize("value", [True, -1, 1.5, None])
def test_client_requires_an_exact_nonnegative_input_token_count(fake_provider, value):
    Provider, Config = fake_provider
    transport = ClientTransport(
        Provider(Config()), lambda messages: value, tokenizer_id="fixture-counter"
    )
    with pytest.raises(ValueError, match="exact nonnegative"):
        transport.count_input_tokens([])
    assert Provider.calls == []


@pytest.mark.parametrize(
    "change", ["stage", "public_payload", "output_format", "consumers"]
)
def test_reused_operation_rejects_changed_request_identity(tmp_path, change):
    store, ledger = authority(tmp_path, ("M0", "M1"))
    transport = ReplayTransport({"direct": ["first"]})
    gateway = ModelGateway(store, ledger, transport)
    call(gateway)
    args = {
        "operation_id": "initial",
        "stage": "direct",
        "consumers": ("M1",),
        "public_payload": {"public_text": "A fixed public RTL task"},
        "output_format": "Return the declared fixture proposal.",
    }
    args[change] = {
        "stage": "another-stage",
        "public_payload": {"public_text": "changed"},
        "output_format": "another format",
        "consumers": ("M0", "M1"),
    }[change]
    with pytest.raises(ModelStageFailure, match="identity_changed"):
        gateway.call(**args)
    assert len(transport.requests) == 1
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 1


def test_provider_failure_is_sanitized_and_spends_one_call(tmp_path, fake_provider):
    Provider, Config = fake_provider
    secret = Config().api_key
    Provider.error = RuntimeError("remote rejected credential " + secret)
    store, ledger = authority(tmp_path)
    transport = ClientTransport(
        Provider(Config()), lambda messages: 13, tokenizer_id="fixture-exact-counter"
    )
    gateway = ModelGateway(store, ledger, transport, allow_model_calls=True)
    with pytest.raises(ModelStageFailure, match="provider_call_failed") as caught:
        call(gateway)
    assert secret not in str(caught.value)
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 1
    assert len(Provider.calls) == 1
    assert all(
        secret.encode() not in path.read_bytes()
        for path in store.root.rglob("*")
        if path.is_file()
    )
    with pytest.raises(ModelStageFailure, match="provider_call_failed"):
        call(gateway)
    assert len(Provider.calls) == 1


def test_truncated_provider_response_retains_raw_partial_output_and_call(
    tmp_path, fake_provider
):
    Provider, Config = fake_provider

    class Truncated(RuntimeError):
        failure_category = "output_truncated"
        content = "partial-generated-rtl"

    Provider.error = Truncated("provider-length-stop")
    store, ledger = authority(tmp_path)
    gateway = ModelGateway(
        store,
        ledger,
        ClientTransport(
            Provider(Config()),
            lambda messages: 13,
            tokenizer_id="fixture-exact-counter",
        ),
        allow_model_calls=True,
    )
    with pytest.raises(ModelStageFailure, match="output_truncated") as caught:
        call(gateway)
    assert caught.value.response.text == "partial-generated-rtl"
    record = json.loads(store.read_verified(response_key("initial")))
    assert record["text"] == "partial-generated-rtl"
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 1


@pytest.mark.parametrize("content", ["", "  \n\t"])
def test_empty_response_is_failure_and_does_not_become_free_retry(tmp_path, content):
    store, ledger = authority(tmp_path)
    transport = ReplayTransport({"direct": [content, "unused"]})
    gateway = ModelGateway(store, ledger, transport)
    for _ in range(2):
        with pytest.raises(ModelStageFailure, match="empty_model_output"):
            call(gateway)
    assert len(transport.requests) == 1
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 1
    assert json.loads(store.read_verified(response_key("initial")))["text"] == content


def test_unknown_usage_retains_upper_bounds_and_never_claims_measured_zero(tmp_path):
    store, ledger = authority(tmp_path, max_single_output_tokens=64)
    transport = ReplayTransport(
        {
            "direct": [
                {
                    "text": "valid-but-unmetered",
                    "input_tokens": None,
                    "output_tokens": None,
                }
            ]
        }
    )
    gateway = ModelGateway(store, ledger, transport)
    assert call(gateway).text == "valid-but-unmetered"
    snapshot = ledger.snapshot()
    assert snapshot["budget_status"] == "unverifiable"
    assert snapshot["actual"]["used"]["output_tokens"] == 64
    assert "output_tokens" in snapshot["actual"]["unavailable_axes"]
    record = json.loads(store.read_verified(response_key("initial")))
    assert record["observed_usage"]["output_tokens"] is None
    assert call(gateway).text == "valid-but-unmetered"
    assert len(transport.requests) == 1


def test_transport_execution_unknown_survives_reopen_without_dispatch(tmp_path):
    class UnknownTransport(ReplayTransport):
        def generate(self, *args, **kwargs):
            self.requests.append({"attempted": True})
            raise RuntimeError("untrusted provider diagnostic must not be persisted")

    store, ledger = authority(tmp_path)
    first = UnknownTransport({})
    with pytest.raises(ModelStageFailure, match="transport_execution_unknown"):
        call(ModelGateway(store, ledger, first))
    _, reopened = authority(tmp_path)
    retry = ReplayTransport({"direct": ["not-dispatched"]})
    with pytest.raises(ModelStageFailure, match="dispatch_unresolved"):
        call(ModelGateway(store, reopened, retry))
    assert len(first.requests) == 1 and retry.requests == []
    assert reopened.snapshot()["budget_status"] == "unverifiable"
    assert reopened.snapshot()["actual"]["used"]["model_calls"] == 1


def test_input_context_bound_prevents_dispatch_or_budget_spend(tmp_path):
    store, ledger = authority(tmp_path, max_context_tokens=16)
    transport = ReplayTransport({"direct": ["unused"]})
    with pytest.raises(ModelStageFailure, match="budget_exhausted"):
        call(ModelGateway(store, ledger, transport))
    assert transport.requests == []
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 0


def test_input_total_budget_is_enforced_before_provider_side_effect(tmp_path):
    store, ledger = authority(tmp_path, max_total_input_tokens=1)
    transport = ReplayTransport({"direct": ["unused"]})
    with pytest.raises(BudgetExceeded, match="input_tokens"):
        call(ModelGateway(store, ledger, transport))
    assert transport.requests == []
    assert ledger.snapshot()["actual"]["used"]["model_calls"] == 0


def test_output_overage_is_preserved_and_never_returned_as_a_valid_stage(tmp_path):
    store, ledger = authority(tmp_path, max_single_output_tokens=8)
    transport = ReplayTransport({"direct": ["123456789"]})
    gateway = ModelGateway(store, ledger, transport)
    for _ in range(2):
        with pytest.raises(ModelStageFailure, match="budget_exceeded"):
            call(gateway)
    assert ledger.snapshot()["budget_status"] == "exceeded"
    assert ledger.snapshot()["actual"]["observed"]["output_tokens"] == 9
    assert (
        json.loads(store.read_verified(response_key("initial")))["text"] == "123456789"
    )
    assert len(transport.requests) == 1


def capacity_transport(Provider, Config, **changes):
    values = dict(input_token_bound=300, context_capacity=300, output_capacity=64,
                  capacity_source="unit-test-provider-capacity-v1")
    values.update(changes)
    return ProviderCapacityTransport(Provider(Config()), **values)


def test_provider_capacity_reserves_an_explicit_envelope_and_reconciles_real_usage(tmp_path, fake_provider):
    Provider, Config = fake_provider
    store, ledger = authority(tmp_path)
    transport = capacity_transport(Provider, Config)
    response = call(ModelGateway(store, ledger, transport, allow_model_calls=True))
    assert response.input_tokens == 13 and response.output_tokens == 7
    assert transport.tokenizer_id == "unavailable"
    assert Provider.instances[-1].config.max_tokens == 64
    reservation = next(iter(ledger.snapshot()["reservations"].values()))
    assert reservation["resources"]["input_tokens"] == 300
    assert reservation["resources"]["output_tokens"] == 64
    assert reservation["resources"]["context_tokens"] == 364
    metadata = reservation["metadata"]
    assert metadata["token_bound_source"] == "provider_capacity_upper_bound+provider_output_ceiling"
    accounting = metadata["input_accounting"]
    assert accounting["kind"] == "provider_capacity_upper_bound"
    assert accounting["context_capacity"] == 300
    assert accounting["ledger_context_envelope"] == "input_bound_plus_output_ceiling"
    prefix = response_key("initial").removesuffix("/response")
    request = json.loads(store.read_verified(prefix + "/request"))
    assert request["input_accounting"] == accounting
    assert request["model_identity"]["input_accounting"] == accounting
    assert ledger.snapshot()["actual"]["observed"]["input_tokens"] == 13
    assert ledger.snapshot()["actual"]["used"]["context_tokens"] == 20
    assert all(Config().api_key.encode() not in path.read_bytes()
               for path in store.root.rglob("*") if path.is_file())


@pytest.mark.parametrize("changes", [
    {"input_token_bound": True}, {"input_token_bound": 0}, {"input_token_bound": -1},
    {"input_token_bound": 1.5}, {"input_token_bound": 299}, {"input_token_bound": 301},
    {"context_capacity": None}, {"context_capacity": False}, {"output_capacity": 0},
    {"output_capacity": 301}, {"output_capacity": 2.5}, {"capacity_source": ""},
    {"capacity_source": "  "}, {"capacity_source": None},
])
def test_provider_capacity_rejects_invalid_bounds_without_dispatch(fake_provider, changes):
    Provider, Config = fake_provider
    with pytest.raises(ValueError):
        capacity_transport(Provider, Config, **changes)
    assert Provider.calls == []


def test_provider_capacity_keeps_missing_usage_unknown_and_full_reservation(tmp_path, fake_provider):
    Provider, Config = fake_provider
    Provider.usage = None
    store, ledger = authority(tmp_path)
    gateway = ModelGateway(store, ledger, capacity_transport(Provider, Config), allow_model_calls=True)
    first = call(gateway)
    assert first.input_tokens is None and first.output_tokens is None
    snapshot = ledger.snapshot()
    assert snapshot["budget_status"] == "unverifiable"
    assert snapshot["actual"]["used"]["input_tokens"] == 300
    assert snapshot["actual"]["used"]["output_tokens"] == 64
    assert snapshot["actual"]["used"]["context_tokens"] == 364
    assert {"input_tokens", "output_tokens", "context_tokens"} <= set(snapshot["actual"]["unavailable_axes"])
    record = json.loads(store.read_verified(response_key("initial")))
    assert all(record["observed_usage"][axis] is None
               for axis in ("input_tokens", "output_tokens", "context_tokens"))
    assert call(gateway) == first
    assert len(Provider.calls) == 1


@pytest.mark.parametrize("changes", [
    {"input_token_bound": 301, "context_capacity": 301},
    {"output_capacity": 65}, {"capacity_source": "unit-test-provider-capacity-v2"},
])
def test_provider_capacity_policy_is_bound_to_persisted_request(tmp_path, fake_provider, changes):
    Provider, Config = fake_provider
    store, ledger = authority(tmp_path)
    call(ModelGateway(store, ledger, capacity_transport(Provider, Config), allow_model_calls=True))
    _, reopened = authority(tmp_path)
    altered = ModelGateway(store, reopened, capacity_transport(Provider, Config, **changes), allow_model_calls=True)
    with pytest.raises(ModelStageFailure, match="identity_changed"):
        call(altered)
    assert len(Provider.calls) == 1
    assert reopened.snapshot()["actual"]["used"]["model_calls"] == 1


@pytest.mark.parametrize("usage", [
    {"input_tokens": 301, "output_tokens": 7},
    {"input_tokens": 290, "output_tokens": 20},
    {"input_tokens": 13, "output_tokens": 65},
])
def test_provider_capacity_violation_preserves_actual_usage_and_stops_new_dispatch(tmp_path, fake_provider, usage):
    Provider, Config = fake_provider
    Provider.usage = usage
    store, ledger = authority(tmp_path)
    gateway = ModelGateway(store, ledger, capacity_transport(Provider, Config), allow_model_calls=True)
    for operation in ("initial", "initial", "unused-second-operation"):
        with pytest.raises(ModelStageFailure, match="provider_capacity_bound_exceeded"):
            call(gateway, operation=operation)
    record = json.loads(store.read_verified(response_key("initial")))
    assert record["failure"] == "provider_capacity_bound_exceeded"
    assert record["input_tokens"] == usage["input_tokens"]
    assert record["output_tokens"] == usage["output_tokens"]
    assert ledger.snapshot()["actual"]["observed"]["input_tokens"] == usage["input_tokens"]
    assert ledger.snapshot()["actual"]["observed"]["output_tokens"] == usage["output_tokens"]
    assert store.reference("model-capacity-invalid") is not None
    assert len(Provider.calls) == 1
    _, reopened = authority(tmp_path)
    restored = ModelGateway(store, reopened, capacity_transport(Provider, Config), allow_model_calls=True)
    with pytest.raises(ModelStageFailure, match="provider_capacity_bound_exceeded"):
        call(restored, operation="after-reopen")
    assert len(Provider.calls) == 1


def test_capacity_factory_uses_environment_credentials_and_explicit_thinking_mode(tmp_path, fake_provider, monkeypatch):
    Provider, _ = fake_provider
    secret = "UNITTEST_CAPACITY_ENV_CREDENTIAL_DO_NOT_SERIALIZE"
    monkeypatch.setenv("UNITTEST_PC21_CAPACITY_API_KEY", secret)
    monkeypatch.setattr("sr2fpga_agent.providers.OpenAICompatibleClient", Provider)
    settings = {"model": "deepseek-unit-test", "base_url": "https://provider.example.invalid",
                "api_key_env": "UNITTEST_PC21_CAPACITY_API_KEY", "input_token_bound": 300,
                "context_capacity": 300, "output_capacity": 64, "capacity_source": "unit-test-capacity-v1",
                "thinking_mode": "enabled"}
    transport = create_provider_capacity_transport(settings)
    assert transport.client.config.api_key == secret
    assert transport.client.config.thinking_mode == "enabled"
    assert transport.client.config.transport_attempts == 1
    assert Provider.calls == []
    store, ledger = authority(tmp_path)
    call(ModelGateway(store, ledger, transport, allow_model_calls=True))
    assert all(secret.encode() not in path.read_bytes() for path in store.root.rglob("*") if path.is_file())
    with pytest.raises(ValueError, match="capacity identities"):
        create_provider_capacity_transport({**settings, "api_key": secret})
    assert len(Provider.calls) == 1


def test_exact_provider_factory_keeps_explicit_tokenizer_and_accepts_thinking_mode(fake_provider, monkeypatch):
    Provider, _ = fake_provider
    monkeypatch.setenv("UNITTEST_PC21_EXACT_API_KEY", "UNITTEST_ONLY_SECRET")
    monkeypatch.setattr("sr2fpga_agent.providers.OpenAICompatibleClient", Provider)
    monkeypatch.setattr("sr2fpga_agent.execution.integration.load_callable", lambda spec: lambda settings: lambda messages: 13)
    transport = create_provider_transport({"model": "deepseek-unit-test", "base_url": "https://provider.example.invalid",
        "api_key_env": "UNITTEST_PC21_EXACT_API_KEY", "tokenizer_factory": "unit_test:counter",
        "tokenizer_id": "unit-test-exact-tokenizer", "thinking_mode": "disabled"})
    assert type(transport) is ClientTransport
    assert transport.count_input_tokens([]) == 13
    assert transport.tokenizer_id == "unit-test-exact-tokenizer"
    assert transport.client.config.thinking_mode == "disabled"
    assert Provider.calls == []
