"""Unit tests for Victor agent loop, personality, and tool routing."""

import pytest
from dexter.core.agent import DexterAgent
from dexter.core.config import DexterConfig
from dexter.core.personality import PersonalityEngine
from dexter.models.base import BaseLLM, ChatMessage, LLMResponse
from dexter.tools.router import ToolRouter
from dexter.tools.factory import create_tool_registry


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
    config = DexterConfig()
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt("tool descriptions here")
    assert "Dexter" in prompt
    assert "curiosity" in prompt.lower()
    assert "tool descriptions here" in prompt


def test_tool_router_math_intent():
    registry = create_tool_registry()
    router = ToolRouter(registry)

    result = router.route("what is 144 * 12?")
    assert result is not None
    assert result[0] == "calculator"
    assert "144 * 12" in result[1].get("expression", "")


def test_tool_router_search_intent():
    registry = create_tool_registry()
    router = ToolRouter(registry)

    result = router.route("search for latest developments in small language models")
    assert result is not None
    assert result[0] == "web_search"
    assert "developments in small language models" in result[1].get("query", "")


def test_tool_router_file_intent():
    registry = create_tool_registry()
    router = ToolRouter(registry)

    result = router.route("read config/victor.yaml")
    assert result is not None
    assert result[0] == "filesystem"
    assert "config/victor.yaml" in result[1].get("path", "")


@pytest.mark.asyncio
async def test_agent_direct_slash_command():
    agent = DexterAgent(llm=MockLLM())
    res = await agent.chat("/calc 25 * 4")
    assert res["type"] == "tool_result"
    assert res["tool_executed"] == "calculator"
    assert "100" in res["content"]


@pytest.mark.asyncio
async def test_agent_tools_listing_command():
    agent = DexterAgent(llm=MockLLM())
    res = await agent.chat("/tools")
    assert res["type"] == "command_result"
    assert "calculator" in res["content"].lower()
    assert "web_search" in res["content"].lower()


@pytest.mark.asyncio
async def test_agent_extract_tool_call():
    agent = DexterAgent(llm=MockLLM())
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


@pytest.mark.asyncio
async def test_agent_autonomous_chat_routing():
    agent = DexterAgent(llm=MockLLM("50 * 20 is 1,000."))
    res = await agent.chat("what is 50 * 20?")
    assert res["tool_executed"] is not None
    assert res["tool_executed"]["name"] == "calculator"
    assert "1,000" in res["content"] or "1000" in res["content"]


@pytest.mark.asyncio
async def test_agent_emotion_and_brevity():
    agent = DexterAgent(llm=MockLLM("Understood. System is optimal."))
    assert agent.emotion == "idle"
    await agent.set_emotion("happy", reason="Greeting test")
    assert agent.emotion == "happy"

    res = await agent.chat("Are you working?")
    assert "System is optimal" in res["content"]
    assert res["emotion"] in ["happy", "neutral"]


@pytest.mark.asyncio
async def test_anti_lying_interception():
    # If LLM hallucinates an action completion when no tool was executed
    agent = DexterAgent(llm=MockLLM("I have opened Google Chrome and searched for you."))
    res = await agent.chat("Do something undefined without tool")
    assert "didn't perform that action" in res["content"].lower() or "did not perform that action" in res["content"].lower()
    assert res["emotion"] == "concerned"


@pytest.mark.asyncio
async def test_honest_failure_reporting():
    agent = DexterAgent(llm=MockLLM("I successfully read the file!"))
    # Request a non-existent file
    res = await agent.chat("read file definitely_non_existent_file_xyz_123.txt")
    assert res["tool_executed"] is not None
    assert "error" in res["content"].lower() or "failed" in res["content"].lower() or "not found" in res["content"].lower()
    assert "successfully read" not in res["content"].lower()

