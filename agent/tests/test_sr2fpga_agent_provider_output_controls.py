import io
import json
from dataclasses import replace

import pytest

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.episode_executor import EpisodeExecutor, PreCandidateState
from sr2fpga_agent.generation.context_his import FrozenContextSystemHisFacade, FrozenContextSystemHisValidationFacade, FrozenContextSystemHisCorrectionFacade
from sr2fpga_agent.generation.context_plan import FrozenContextUntypedPlanFacade
from sr2fpga_agent.method_adapters import GenerationServices, MethodAdapterRegistry, MethodArtifactGateway
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.prompts import _canonical_project_manifest_guidance, _frozen_direct_project_messages, _frozen_project_from_untyped_plan_messages, _frozen_his_free_project_messages
from sr2fpga_agent.providers import OpenAICompatibleClient, OpenAICompatibleConfig, ModelOutputTruncated, ModelOutputEmpty
from sr2fpga_agent.runner import SourceConnection, _load_sources
from test_sr2fpga_agent_context_generation import _context, _platform


def _wire(content='{"ok":true}', finish="stop", reasoning_tokens=0):
    event = {"id": "response-fixture", "choices": [{"delta": {"content": content}, "finish_reason": finish}],
             "usage": {"prompt_tokens": 9, "completion_tokens": 20,
                       "completion_tokens_details": {"reasoning_tokens": reasoning_tokens}}}
    return io.BytesIO(("data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n").encode())


def test_deepseek_no_local_token_limit_and_explicit_thinking():
    client = OpenAICompatibleClient(OpenAICompatibleConfig(api_key="unused", max_tokens=0, thinking_mode="disabled"))
    payload = client._chat_payload([{"role": "user", "content": "Return JSON"}])
    assert "max_tokens" not in payload
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["response_format"] == {"type": "json_object"}
    assert client.with_output_format("text")._chat_payload([])["response_format"] == {"type": "text"}
    with pytest.raises(ValueError, match="only for DeepSeek"):
        replace(client.config, model="other-provider-model")


@pytest.mark.parametrize("stream", [False, True])
def test_length_stop_retains_raw_answer_and_is_not_transport_retried(monkeypatch, stream):
    client = OpenAICompatibleClient(OpenAICompatibleConfig(api_key="unused", transport_attempts=3))
    requests = []
    def request(payload, reader):
        requests.append(payload)
        response = _wire('{"unfinished":', "length", 18) if stream else io.BytesIO(json.dumps({
            "id": "response-fixture", "choices": [{"message": {"content": '{"unfinished":'}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 9, "completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": 18}},
        }).encode())
        return reader(response)
    monkeypatch.setattr(client, "_request_once", request)
    budget = ModelCallBudget(1)
    wrapped = budget.client(client, "req2his")
    with pytest.raises(ModelOutputTruncated):
        getattr(wrapped, "stream_chat" if stream else "chat")([{"role": "user", "content": "JSON"}])
    assert len(requests) == 1
    record = budget.summary()["calls"][0]
    assert record["error"] == "output_truncated"
    assert record["output_tokens"] == 20
    assert record["provider_response_details"]["finish_reason"] == "length"
    assert record["provider_response_details"]["reasoning_tokens"] == 18
    assert record["provider_response_details"]["output_text"] == '{"unfinished":'


def test_empty_final_content_is_explicit_and_recorded(monkeypatch):
    client = OpenAICompatibleClient(OpenAICompatibleConfig(api_key="unused"))
    monkeypatch.setattr(client, "_request_once", lambda payload, reader: reader(_wire("", "stop", 20)))
    with pytest.raises(ModelOutputEmpty):
        client.stream_chat([])
    assert client.consume_response_details()["output_text"] == ""


def test_m2_plan_uses_text_format_without_losing_global_budget(monkeypatch):
    payloads = []
    def request(self, payload, reader):
        payloads.append(payload)
        return reader(_wire("Use a register and an enable."))
    monkeypatch.setattr(OpenAICompatibleClient, "_request_once", request)
    budget = ModelCallBudget(1)
    base = OpenAICompatibleClient(OpenAICompatibleConfig(api_key="unused"))
    plan = FrozenContextUntypedPlanFacade(budget.client(base, "req2his"), None).emit_plan(_context())
    assert payloads[0]["response_format"] == {"type": "text"}
    assert plan == {"plan_text": "Use a register and an enable."}
    assert budget.calls_used == 1
    assert base.config.response_format == "json_object"


def test_full_project_prompts_share_registered_manifest_format():
    context = _context()
    guidance = _canonical_project_manifest_guidance("example")
    for messages in (_frozen_direct_project_messages(context, project_name="example"),
                     _frozen_project_from_untyped_plan_messages(context, "plain plan", project_name="example"),
                     _frozen_his_free_project_messages(context, {}, project_name="example")):
        assert guidance in messages[1]["content"]
    assert '"interface"' in guidance and '"applicability"' in guidance
    assert '"path"' in guidance and '"sources"' in guidance


@pytest.mark.parametrize("method", ["M3", "M4"])
def test_unparsed_his_is_retained_and_cannot_bypass_h0(tmp_path, method):
    class Client:
        def stream_chat(self, messages):
            return '{"broken":'
    store = ArtifactStore(tmp_path / "store")
    facade = FrozenContextSystemHisFacade(Client(), None, _platform())
    services = GenerationServices(artifacts=MethodArtifactGateway(store), episode_id="bad-json",
                                  system_his=facade, his_validation=FrozenContextSystemHisValidationFacade(_platform()))
    outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create(method), _context(), services,
    )
    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.his_corrections_used == 0
    raw = store.read_verified(outcome.planning_artifact.artifact_ref)
    payload = json.loads(raw)
    assert payload["raw_output"] == '{"broken":'
    assert not ContractRegistry().load_schema("unparsed_system_his_output").validate(payload)
    assert outcome.h_report["h0"]["status"] == "fail"


@pytest.mark.parametrize("raw", ['{"broken":', ModelOutputTruncated('{"truncated":')], ids=["syntax", "length"])
def test_m5_unparsed_his_correction_closes_with_existing_budget(tmp_path, monkeypatch, raw):
    from test_sr2fpga_agent_pre_candidate_stop_outcome import test_real_runner_m5_h_correction_acceptance_is_artifact_derived_and_fail_closed as exercise
    exercise(tmp_path, monkeypatch, "h0", initial_raw_response=raw)
    run_dir = tmp_path / "runs" / "m5-h0-correction"
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    completion = next(event for event in events if event["event"] == "sample_completed")
    store = ArtifactStore(run_dir / "method_artifacts")
    outcome = json.loads(store.read_verified(ArtifactRef(**completion["development_his_correction_outcome_ref"])))
    initial = json.loads(store.read_verified(ArtifactRef(**outcome["initial_his_ref"])))
    assert initial["contract_version"] == "unparsed-system-his-output-v1"
    assert initial["raw_output"] == (raw.content if isinstance(raw, ModelOutputTruncated) else raw)


def test_runner_source_loads_thinking_mode_and_unlimited_local_output():
    source = _load_sources({"ds": {"kind": "openai_compat", "model": "deepseek-v4-pro", "thinking_mode": "disabled", "max_tokens": 0}})["ds"]
    assert isinstance(source, SourceConnection)
    assert source.thinking_mode == "disabled" and source.max_tokens == 0


def test_generation_and_repair_builders_forward_thinking_and_unlimited_output(monkeypatch):
    from sr2fpga_agent import cli
    captured = []
    def client(config):
        captured.append(config)
        return object()
    monkeypatch.setenv("TEST_DEEPSEEK_KEY", "unused-test-key")
    monkeypatch.setattr(cli, "OpenAICompatibleClient", client)
    source = SourceConnection(name="ds", kind="deepseek", model="deepseek-v4-pro",
                              api_key_env="TEST_DEEPSEEK_KEY", thinking_mode="disabled", max_tokens=0)
    cli.build_project_generator_for_connection(source)
    cli.build_repairer_for_connection(source)
    assert len(captured) == 2
    assert all(config.thinking_mode == "disabled" and config.max_tokens == 0 for config in captured)


def test_m5_bad_correction_stops_after_one_budgeted_attempt(tmp_path):
    class Client:
        def __init__(self):
            self.outputs = iter(['{"first":', '{"second":'])
        def stream_chat(self, messages):
            return next(self.outputs)
    budget = ModelCallBudget(3)
    base = Client()
    store = ArtifactStore(tmp_path / "store")
    services = GenerationServices(
        artifacts=MethodArtifactGateway(store), episode_id="bad-twice",
        system_his=FrozenContextSystemHisFacade(budget.client(base, "req2his"), None, _platform()),
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        repair=FrozenContextSystemHisCorrectionFacade(budget.client(base, "system_his_repair"), _platform()),
    )
    outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create("M5"), _context(), services,
    )
    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.his_corrections_used == 1
    assert budget.calls_used == 2
    assert outcome.candidate is None
