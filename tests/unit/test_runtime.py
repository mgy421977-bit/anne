from __future__ import annotations

from typing import Any

from anne.agent.runtime import AnneAgent
from anne.providers.openrouter import OpenRouterProvider


class _FakeOpenRouter(OpenRouterProvider):
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[
            tuple[list[dict[str, Any]], Any]
        ] = []

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((messages, tools))
        return self.responses.pop(0)


def _agent(model: _FakeOpenRouter) -> AnneAgent:
    agent = AnneAgent.__new__(AnneAgent)
    agent.model = model
    return agent


def test_openrouter_tool_round_is_followed_by_single_final_synthesis() -> None:
    model = _FakeOpenRouter(
        [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "github_search",
                                        "arguments": '{"query":"Hypothesis"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "<RESPONSE>Final synthesis.</RESPONSE>"
                                "<LEARNING>No new durable learning.</LEARNING>"
                                "<CONFIDENCE>0.9</CONFIDENCE>"
                            ),
                        }
                    }
                ]
            },
        ]
    )
    agent = _agent(model)
    agent._execute_tool = (  # type: ignore[method-assign]
        lambda name, arguments: {"ok": True, "result": "evidence"}
    )

    raw, tools_used = agent._openrouter_run("audit Hypothesis", "memory")

    assert "Final synthesis" in raw
    assert tools_used == ["github_search"]
    assert len(model.calls) == 2
    assert model.calls[1][1] is None
    tool_message = model.calls[1][0][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call_1"


def test_explicit_repository_paths_are_prefetched_in_one_model_turn() -> None:
    model = _FakeOpenRouter(
        [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "<RESPONSE>Audited.</RESPONSE>"
                                "<LEARNING>No new durable learning.</LEARNING>"
                                "<CONFIDENCE>0.95</CONFIDENCE>"
                            ),
                        }
                    }
                ]
            }
        ]
    )
    agent = _agent(model)
    seen_paths: list[str] = []

    def fake_execute(
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        seen_paths.append(arguments["path"])
        return {
            "ok": True,
            "result": f"content for {arguments['path']}",
        }

    agent._execute_tool = fake_execute  # type: ignore[method-assign]

    raw, tools_used = agent._openrouter_run(
        "Read src/anne/agent/runtime.py and "
        "src/anne/providers/openrouter.py",
        "memory",
    )

    assert "Audited" in raw
    assert seen_paths == [
        "src/anne/agent/runtime.py",
        "src/anne/providers/openrouter.py",
    ]
    assert tools_used == [
        "github_read_file",
        "github_read_file",
    ]
    assert len(model.calls) == 1
    evidence_message = model.calls[0][0][-1]
    assert evidence_message["role"] == "user"
    assert "AUTHORITATIVE REPOSITORY EVIDENCE" in evidence_message["content"]


def test_empty_final_response_does_not_repeat_final_synthesis() -> None:
    model = _FakeOpenRouter(
        [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                        }
                    }
                ]
            },
        ]
    )
    agent = _agent(model)

    raw, tools_used = agent._openrouter_run("Say hello", "memory")

    assert "did not return a final synthesis" in raw
    assert tools_used == []
    assert len(model.calls) == 2
