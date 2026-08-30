from __future__ import annotations

import json

import pytest

from reasoning_graph.providers import (
    build_anthropic_request,
    build_gemini_request,
    build_openai_request,
    normalize_anthropic_response,
    normalize_gemini_response,
    normalize_openai_response,
)


def test_openai_native_stateful_and_stateless_shapes():
    stateful = build_openai_request(
        model="configured-openai-model",
        input="question",
        effort="high",
        summary="auto",
        reasoning_context="all_turns",
        previous_response_id="resp_previous",
    )
    assert stateful == {
        "model": "configured-openai-model",
        "input": "question",
        "store": True,
        "reasoning": {"effort": "high", "summary": "auto", "context": "all_turns"},
        "previous_response_id": "resp_previous",
    }

    encrypted = {
        "type": "reasoning",
        "id": "rs_1",
        "encrypted_content": "opaque-secret",
    }
    stateless = build_openai_request(
        model="configured-openai-model",
        input="next",
        store=False,
        replay_items=[encrypted],
    )
    assert stateless["include"] == ["reasoning.encrypted_content"]
    assert stateless["input"][0] == encrypted
    assert stateless["input"][1] == {"role": "user", "content": "next"}
    with pytest.raises(ValueError, match="mutually exclusive"):
        build_openai_request(
            model="m", input="x", previous_response_id="r", conversation="c"
        )


def test_openai_normalization_preserves_replay_but_redacts_persistence():
    response = {
        "id": "resp_1",
        "model": "m",
        "status": "completed",
        "reasoning": {"context": "all_turns"},
        "output": [
            {
                "type": "reasoning",
                "id": "rs_1",
                "encrypted_content": "opaque-secret",
                "summary": [{"type": "summary_text", "text": "A provider summary"}],
            },
            {
                "type": "function_call",
                "call_id": "call_1",
                "name": "lookup",
                "arguments": "{}",
            },
            {"type": "message", "content": [{"type": "output_text", "text": "answer"}]},
        ],
        "usage": {
            "input_tokens": 4,
            "output_tokens": 7,
            "total_tokens": 11,
            "output_tokens_details": {"reasoning_tokens": 3},
        },
    }
    record = normalize_openai_response(response)
    assert record.text == "answer"
    assert record.reasoning_summaries == ("A provider summary",)
    assert record.usage["reasoning_tokens"] == 3
    assert record.continuity_payload()[0]["encrypted_content"] == "opaque-secret"
    assert [item["type"] for item in record.continuity_payload()] == [
        "reasoning",
        "function_call",
        "message",
    ]
    persisted = record.to_persistable_dict()
    assert "reasoning_summaries" not in persisted
    assert "opaque-secret" not in json.dumps(persisted)


def test_gemini_native_shapes_and_exact_signature_replay():
    stateful = build_gemini_request(
        model="configured-gemini-model",
        input="question",
        thinking_level="high",
        previous_interaction_id="v1_previous",
        store=True,
    )
    assert stateful["generation_config"] == {
        "thinking_level": "high",
        "thinking_summaries": "auto",
    }
    assert stateful["previous_interaction_id"] == "v1_previous"

    thought = {"type": "thought", "signature": "opaque-signature", "summary": []}
    stateless = build_gemini_request(
        model="configured-gemini-model",
        input="next",
        store=False,
        replay_steps=[thought],
    )
    assert stateless["input"][0] == thought
    with pytest.raises(ValueError, match="stateful"):
        build_gemini_request(
            model="m", input="x", store=False, previous_interaction_id="v1"
        )


def test_gemini_missing_summary_usage_tools_and_redaction():
    response = {
        "id": "v1_1",
        "model": "m",
        "status": "completed",
        "steps": [
            {"type": "thought", "signature": "opaque-signature"},
            {"type": "function_call", "name": "lookup", "arguments": {"q": "x"}},
            {"type": "model_output", "content": [{"type": "text", "text": "answer"}]},
        ],
        "usage": {
            "total_input_tokens": 2,
            "total_output_tokens": 4,
            "total_thought_tokens": 8,
            "total_tokens": 14,
        },
    }
    record = normalize_gemini_response(response)
    assert record.reasoning_summaries == ()
    assert record.text == "answer"
    assert record.usage == {
        "input_tokens": 2,
        "output_tokens": 4,
        "reasoning_tokens": 8,
        "total_tokens": 14,
    }
    assert record.continuity_payload()[0]["signature"] == "opaque-signature"
    assert [step["type"] for step in record.continuity_payload()] == [
        "thought",
        "function_call",
        "model_output",
    ]
    assert "opaque-signature" not in json.dumps(record.to_persistable_dict())


def test_anthropic_adaptive_manual_and_validation_shapes():
    adaptive = build_anthropic_request(
        model="configured-anthropic-model",
        messages=[{"role": "user", "content": "question"}],
        effort="medium",
    )
    assert adaptive["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert adaptive["output_config"] == {"effort": "medium"}

    manual = build_anthropic_request(
        model="legacy-configured-model",
        messages=[],
        thinking_mode="enabled",
        budget_tokens=2048,
        display="omitted",
    )
    assert manual["thinking"] == {
        "type": "enabled",
        "display": "omitted",
        "budget_tokens": 2048,
    }
    with pytest.raises(ValueError, match="requires budget_tokens"):
        build_anthropic_request(model="m", messages=[], thinking_mode="enabled")
    with pytest.raises(ValueError, match="at least 1024"):
        build_anthropic_request(
            model="m",
            messages=[],
            thinking_mode="enabled",
            budget_tokens=512,
        )
    with pytest.raises(ValueError, match="display is invalid"):
        build_anthropic_request(
            model="m", messages=[], thinking_mode="disabled", display="summarized"
        )


def test_anthropic_preserves_signed_blocks_and_normalizes_error():
    signed = {
        "type": "thinking",
        "thinking": "A provider summary",
        "signature": "opaque-signature",
    }
    tool_use = {"type": "tool_use", "id": "tool_1", "name": "lookup", "input": {}}
    record = normalize_anthropic_response(
        {
            "id": "msg_1",
            "model": "m",
            "stop_reason": "tool_use",
            "content": [signed, tool_use],
            "usage": {"input_tokens": 3, "output_tokens": 5},
        }
    )
    assert record.continuity_payload() == [signed, tool_use]
    assert record.stop_reason == "tool_use"
    assert "opaque-signature" not in json.dumps(record.to_persistable_dict())

    failed = normalize_anthropic_response(
        {"status": "failed", "error": {"type": "api_error", "message": "down"}}
    )
    assert failed.status == "failed"
    assert failed.error["type"] == "api_error"


def test_continuity_payload_is_a_defensive_copy():
    record = normalize_gemini_response(
        {"steps": [{"type": "thought", "signature": "keep"}]}
    )
    payload = record.continuity_payload()
    payload[0]["signature"] = "changed"
    assert record.continuity_payload()[0]["signature"] == "keep"


def test_anthropic_replay_stays_before_the_tool_result():
    signed = {"type": "thinking", "thinking": "", "signature": "opaque"}
    tool_use = {"type": "tool_use", "id": "t1", "name": "lookup", "input": {}}
    messages = [
        {"role": "user", "content": "look it up"},
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "t1", "content": "done"}
            ],
        },
    ]
    request = build_anthropic_request(
        model="configured", messages=messages, replay_content=[signed, tool_use]
    )
    assert request["messages"][0] == messages[0]
    assert request["messages"][1] == {
        "role": "assistant",
        "content": [signed, tool_use],
    }
    assert request["messages"][2] == messages[1]
    with pytest.raises(ValueError, match="complete assistant content"):
        build_anthropic_request(
            model="configured", messages=messages, replay_content=[signed]
        )
    with pytest.raises(ValueError, match="thinking/redacted_thinking"):
        build_anthropic_request(
            model="configured", messages=messages, replay_content=[tool_use]
        )


def test_signed_tool_calls_are_scrubbed_from_persistence():
    record = normalize_gemini_response(
        {
            "steps": [
                {
                    "type": "google_search_call",
                    "signature": "opaque-tool-signature",
                    "arguments": {"query": "docs"},
                }
            ]
        }
    )
    assert record.continuity_payload()[0]["signature"] == "opaque-tool-signature"
    assert "opaque-tool-signature" not in json.dumps(record.to_persistable_dict())
