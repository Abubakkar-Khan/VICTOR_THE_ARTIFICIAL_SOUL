"""Core Victor Agent Loop and Tool Orchestrator."""

import json
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from victor.core.config import VictorConfig, load_config
from victor.core.events import EventBus, global_event_bus
from victor.core.personality import PersonalityEngine
from victor.models.base import BaseLLM, ChatMessage
from victor.models.factory import create_model_provider
from victor.tools.base import ToolResult
from victor.tools.factory import create_tool_registry
from victor.tools.registry import ToolRegistry


def strip_emojis(text: str) -> str:
    """Purge emojis and pictorial symbols for a clean retro-cyber terminal aesthetic."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "]+",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", text)
    return re.sub(r"  +", " ", cleaned)


def format_tool_display(tool_name: str, result: ToolResult) -> str:
    """Format tool execution output into a natural, conversational AI presentation."""
    if not result.success:
        return f"I encountered an error executing {tool_name}: {result.output}"

    out = result.output
    if tool_name == "calculator" and isinstance(out, dict):
        expr = out.get("expression", "")
        res = out.get("result", "")
        formatted_val = f"{res:,}" if isinstance(res, (int, float)) else str(res)
        return f"{expr} is {formatted_val}."

    elif tool_name == "web_search" and isinstance(out, dict):
        query = out.get("query", "")
        hits = out.get("results", [])
        if not hits:
            return f"I searched the web for \"{query}\" but found no matching results."
        lines = [f"I searched for \"{query}\" and retrieved {len(hits)} relevant sources:"]
        for idx, item in enumerate(hits, 1):
            title = item.get("title", "")
            url = item.get("url", "")
            snippet = item.get("snippet", "")
            lines.append(f"{idx}. [{title}]({url})\n   {snippet}")
        return "\n\n".join(lines)

    elif tool_name == "browser" and isinstance(out, dict):
        title = out.get("title", "")
        url = out.get("url", "")
        content = out.get("content", "")
        return f"Here is the relevant content from [{title}]({url}):\n\n{content[:700]}..."

    elif tool_name == "filesystem" and isinstance(out, dict):
        path = out.get("path", "")
        lines_count = out.get("total_lines", 0)
        content = out.get("content", "")
        return f"Here is the content of `{path}` ({lines_count} lines):\n\n```\n{content[:1000]}\n```"

    elif tool_name == "shell" and isinstance(out, dict):
        cmd = out.get("command", "")
        stdout = out.get("stdout", "")
        stderr = out.get("stderr", "")
        res_text = stdout if stdout else stderr
        return f"Command `{cmd}` finished with output:\n\n{res_text}"

    return result.to_summary_string(max_length=1500)


class VictorAgent:
    """The artificial soul living harness, unifying personality, LLM inference, and tool execution."""

    def __init__(
        self,
        config: Optional[VictorConfig] = None,
        llm: Optional[BaseLLM] = None,
        registry: Optional[ToolRegistry] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config or load_config()
        self.llm = llm or create_model_provider(self.config.model)
        self.registry = registry or create_tool_registry(self.config)
        self.event_bus = event_bus or global_event_bus
        self.personality = PersonalityEngine(self.config)
        self.history: List[ChatMessage] = []

    def get_system_prompt(self) -> str:
        """Compile current system prompt with tool registry descriptions."""
        tool_descriptions = self.registry.format_all_descriptions()
        return self.personality.build_system_prompt(tool_descriptions)

    def reset_conversation(self):
        """Clear conversation history."""
        self.history.clear()

    def parse_direct_command(self, user_input: str) -> Optional[Tuple[str, str]]:
        """Check if the user typed a direct slash command (e.g. '/calc 15 * 3')."""
        text = user_input.strip()
        if not text.startswith("/"):
            return None

        parts = text.split(maxsplit=1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else ""
        return command, argument

    def extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a structured tool call from LLM output."""
        # 1. Look for ```json { "tool": ..., "parameters": ... } ```
        json_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        for block in json_blocks:
            try:
                data = json.loads(block)
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                continue

        # 2. Look for raw inline JSON containing "tool"
        raw_json_match = re.search(r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*,[^{}]*\}', text, re.DOTALL)
        if raw_json_match:
            try:
                data = json.loads(raw_json_match.group(0))
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                pass

        # 3. Look for Action: tool_name / Action Input: { ... } or params
        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\s*\nAction Input:\s*(\{.*?\})", text, re.DOTALL)
        if action_match:
            try:
                params = json.loads(action_match.group(2))
                return {"tool": action_match.group(1), "parameters": params}
            except json.JSONDecodeError:
                pass

        return None

    async def handle_direct_command(self, command: str, argument: str) -> Dict[str, Any]:
        """Execute a manual slash command directly."""
        start_time = time.perf_counter()
        await self.event_bus.emit("agent.started", mode="direct_command", command=command)

        if command in ["/help", "/commands"]:
            lines = [
                "Available directives:",
                "• /tools - View installed tool capabilities",
                "• /calc <expr> - Compute a mathematical expression",
                "• /search <query> - Search the live web",
                "• /browse <url> - Extract readable text from a webpage",
                "• /file <path> - Read a local workspace file",
                "• /info - View active model and system telemetry",
                "• /clear - Clear conversation memory",
            ]
            output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/tools":
            lines = [f"Installed capabilities ({len(self.registry.list_tools())} tools active):"]
            for tool in self.registry.list_tools():
                slash = f" ({tool.slash_command})" if tool.slash_command else ""
                lines.append(f"• {tool.name} [{tool.permission.value}]{slash} - {tool.description}")
            output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/clear":
            self.reset_conversation()
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": "Conversation memory cleared. Ready for instructions.", "tool_executed": None}

        if command == "/info":
            active_model = await self.llm.resolve_active_model() if hasattr(self.llm, "resolve_active_model") else self.llm.model_name
            is_ready = await self.llm.is_available()
            info_text = (
                f"Victor Node Telemetry:\n"
                f"• Identity: {self.config.name} ({self.config.title})\n"
                f"• Core Model: {active_model} ({'Online' if is_ready else 'Offline'})\n"
                f"• Design: NERV/MAGI x Nothing OS Retro-Modern\n"
                f"• Personality: Curiosity high, zero emojis\n"
                f"• Security: Shell execution {'permitted' if self.config.security.allow_shell else 'restricted'}\n"
                f"• Active Capabilities: {len(self.registry.list_tools())} tools"
            )
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": info_text, "tool_executed": None}

        tool = self.registry.get_by_slash_command(command)
        if not tool:
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {
                "type": "error",
                "content": f"[UNKNOWN COMMAND]: '{command}'. Enter /help for index.",
                "tool_executed": None,
            }

        first_prop = next(iter(tool.parameters.get("properties", {}).keys()), "input")
        kwargs = {first_prop: argument}

        await self.event_bus.emit("tool.started", tool=tool.name, parameters=kwargs)
        result: ToolResult = await self.registry.execute_tool(tool.name, **kwargs)

        if result.success:
            await self.event_bus.emit("tool.completed", tool=tool.name, duration=result.duration, output=result.output)
            formatted = format_tool_display(tool.name, result)
        else:
            await self.event_bus.emit("tool.failed", tool=tool.name, error=result.error, output=result.output)
            formatted = f"[TOOL FAILED // {tool.name}] ({result.error}): {result.output}"

        duration = round(time.perf_counter() - start_time, 3)
        await self.event_bus.emit("agent.completed", duration=duration)
        return {
            "type": "tool_result",
            "content": formatted,
            "tool_executed": tool.name,
            "result": result.model_dump(),
        }

    async def chat(self, user_message: str) -> Dict[str, Any]:
        """Process user input with autonomous tool selection and ReAct synthesis."""
        start_time = time.perf_counter()

        # Check for direct slash command
        direct_cmd = self.parse_direct_command(user_message)
        if direct_cmd:
            cmd, arg = direct_cmd
            return await self.handle_direct_command(cmd, arg)

        await self.event_bus.emit("agent.started", mode="chat", user_message=user_message)
        self.history.append(ChatMessage(role="user", content=user_message))

        system_prompt = self.get_system_prompt()
        await self.event_bus.emit("agent.thinking", state="planning")

        # First pass: Ask model for plan or response
        llm_resp = await self.llm.generate(
            messages=self.history,
            system_prompt=system_prompt,
            temperature=self.config.model.temperature,
            max_tokens=self.config.model.max_tokens,
        )

        initial_content = llm_resp.content
        tool_call = self.extract_tool_call(initial_content)
        tool_executed_info = None

        if tool_call:
            tool_name = tool_call.get("tool", "")
            parameters = tool_call.get("parameters", {})
            if isinstance(parameters, str):
                try:
                    parameters = json.loads(parameters)
                except Exception:
                    parameters = {}

            await self.event_bus.emit("tool.started", tool=tool_name, parameters=parameters)
            result = await self.registry.execute_tool(tool_name, **parameters)

            if result.success:
                await self.event_bus.emit("tool.completed", tool=tool_name, duration=result.duration, output=result.output)
            else:
                await self.event_bus.emit("tool.failed", tool=tool_name, error=result.error, output=result.output)

            tool_executed_info = {
                "name": tool_name,
                "parameters": parameters,
                "result": result.model_dump(),
            }

            # Add model's action and the tool observation into context
            observation_msg = (
                f"[TOOL OBSERVATION: {tool_name.upper()}]\n"
                f"{format_tool_display(tool_name, result)}\n\n"
                f"INSTRUCTIONS: Synthesize this observation directly for the user. "
                f"Keep your response short, stylish, and focused (1 to 3 sentences maximum). "
                f"STRICT RULE: Absolutely NO emojis. Do not output raw JSON. "
                f"Deliver your final synthesis in character."
            )

            synthetic_history = list(self.history)
            synthetic_history.append(ChatMessage(role="assistant", content=initial_content))
            synthetic_history.append(ChatMessage(role="user", content=observation_msg))

            await self.event_bus.emit("agent.thinking", state="synthesizing")
            final_resp = await self.llm.generate(
                messages=synthetic_history,
                system_prompt=system_prompt,
                temperature=self.config.model.temperature,
                max_tokens=self.config.model.max_tokens,
            )
            final_content = strip_emojis(final_resp.content.strip())
        else:
            final_content = strip_emojis(initial_content.strip())

        self.history.append(ChatMessage(role="assistant", content=final_content))
        duration = round(time.perf_counter() - start_time, 3)
        await self.event_bus.emit("agent.completed", duration=duration)

        return {
            "type": "chat_response",
            "content": final_content,
            "tool_executed": tool_executed_info,
            "duration": duration,
        }

    async def chat_stream(self, user_message: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat events and tokens to client."""
        direct_cmd = self.parse_direct_command(user_message)
        if direct_cmd:
            cmd, arg = direct_cmd
            res = await self.handle_direct_command(cmd, arg)
            yield {"type": "content", "delta": res["content"]}
            yield {"type": "done", "tool_executed": res.get("tool_executed")}
            return

        # Regular chat flow
        res = await self.chat(user_message)
        yield {"type": "tool_executed", "tool": res.get("tool_executed")}
        yield {"type": "content", "delta": res["content"]}
        yield {"type": "done", "duration": res.get("duration")}
