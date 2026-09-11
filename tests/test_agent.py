"""Unit tests for Victor agent loop and personality engine."""

import pytest
from victor.core.agent import VictorAgent
from victor.core.config import VictorConfig
from victor.core.personality import PersonalityEngine
from victor.models.base import BaseLLM, ChatMessage, LLMResponse


class MockLLM(BaseLLM):
    """Mock LLM for fast unit tests without Ollama."""

    def __init__(self, response_text: str = "Mock response"):
        super().__init__(model_name="mock-model")
        self.response_text = response_text

    async def is_available(self) -> bool:
        return True

    async def generate(self, messages, system_prompt=None, temperature=None, max_tokens=None):
        return LLMResponse(content=self.response_text, model="mock-model")

    async def stream(self, messages, system_prompt=None, temperature=None, max_tokens=None):
        yield self.response_text


def test_personality_prompt_generation():
    config = VictorConfig()
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt("tool descriptions here")
    assert "You are Victor" in prompt
    assert "curiosity is high" in prompt
    assert "tool descriptions here" in prompt


@pytest.mark.asyncio
async def test_agent_direct_slash_command():
    agent = VictorAgent(llm=MockLLM())
    res = await agent.chat("/calc 25 * 4")
    assert res["type"] == "tool_result"
    assert res["tool_executed"] == "calculator"
    assert "100" in res["content"]


@pytest.mark.asyncio
async def test_agent_tools_listing_command():
    agent = VictorAgent(llm=MockLLM())
    res = await agent.chat("/tools")
    assert res["type"] == "command_result"
    assert "calculator" in res["content"].lower()
    assert "web_search" in res["content"].lower()


@pytest.mark.asyncio
async def test_agent_extract_tool_call():
    agent = VictorAgent(llm=MockLLM())
    sample_text = (
        "I need to calculate this value.\n"
        "```json\n"
        '{"tool": "calculator", "parameters": {"expression": "12 * 12"}}\n'
        "```\n"
    )
    extracted = agent.extract_tool_call(sample_text)
    assert extracted is not None
    assert extracted["tool"] == "calculator"
    assert extracted["parameters"]["expression"] == "12 * 12"


def test_agent_autonomous_intent_classification():
    agent = VictorAgent(llm=MockLLM())
    math_intent = agent.classify_autonomous_intent("what is 144 * 12?")
    assert math_intent is not None
    assert math_intent[0] == "calculator"
    assert "144 * 12" in math_intent[1]["expression"]

    search_intent = agent.classify_autonomous_intent("search for latest developments in small language models")
    assert search_intent is not None
    assert search_intent[0] == "web_search"
    assert "developments in small language models" in search_intent[1]["query"]

    file_intent = agent.classify_autonomous_intent("read config/victor.yaml")
    assert file_intent is not None
    assert file_intent[0] == "filesystem"
    assert file_intent[1]["path"] == "config/victor.yaml"


@pytest.mark.asyncio
async def test_agent_autonomous_chat_routing():
    agent = VictorAgent(llm=MockLLM("50 * 20 is 1,000."))
    res = await agent.chat("what is 50 * 20?")
    assert res["tool_executed"] is not None
    assert res["tool_executed"]["name"] == "calculator"
    assert "1,000" in res["content"] or "1000" in res["content"]

