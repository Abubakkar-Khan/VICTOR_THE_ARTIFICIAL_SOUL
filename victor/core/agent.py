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
                f"**Victor — Available Commands**",
                "- `/tools` : List all installed tools and permission levels",
                "- `/clear` : Clear current conversation history",
                "- `/info`  : Display Victor's active model and personality configuration",
            ]
            for tool in self.registry.list_tools():
                if tool.slash_command:
                    lines.append(f"- `{tool.slash_command} <args>` : {tool.description} [{tool.permission.value}]")
            output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/tools":
            lines = [f"**Installed Tools ({len(self.registry.list_tools())}):**\n"]
            for tool in self.registry.list_tools():
                slash = f" (Shortcut: `{tool.slash_command}`)" if tool.slash_command else ""
                lines.append(f"• **{tool.name}** [{tool.permission.value}]{slash}\n  {tool.description}")
            output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/clear":
            self.reset_conversation()
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": "Conversation history cleared.", "tool_executed": None}

        if command == "/info":
            active_model = await self.llm.resolve_active_model() if hasattr(self.llm, "resolve_active_model") else self.llm.model_name
            is_ready = await self.llm.is_available()
            info_text = (
                f"**Victor Profile**\n"
                f"- Name: {self.config.name} ({self.config.title})\n"
                f"- Model: `{active_model}` (Status: {'● Online' if is_ready else '○ Offline'})\n"
                f"- Personality: Curiosity={self.config.personality.curiosity}, Humor={self.config.personality.humor}\n"
                f"- Shell Allowed: {self.config.security.allow_shell}\n"
                f"- Registered Tools: {len(self.registry.list_tools())}"
            )
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": info_text, "tool_executed": None}

        tool = self.registry.get_by_slash_command(command)
        if not tool:
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {
                "type": "error",
                "content": f"Unknown command: `{command}`. Type `/help` to see available commands.",
                "tool_executed": None,
            }

        # Map single string argument to primary tool property
        first_prop = next(iter(tool.parameters.get("properties", {}).keys()), "input")
        kwargs = {first_prop: argument}

        await self.event_bus.emit("tool.started", tool=tool.name, parameters=kwargs)
        result: ToolResult = await self.registry.execute_tool(tool.name, **kwargs)

        if result.success:
            await self.event_bus.emit("tool.completed", tool=tool.name, duration=result.duration, output=result.output)
            formatted = (
                f"Executed `{tool.name}` in {result.duration}s:\n\n"
                f"```\n{result.to_summary_string(max_length=2000)}\n```"
            )
        else:
            await self.event_bus.emit("tool.failed", tool=tool.name, error=result.error, output=result.output)
            formatted = f"Tool `{tool.name}` failed ({result.error}): {result.output}"

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
                f"[Tool Observation from '{tool_name}']:\n"
                f"{result.to_summary_string(max_length=2500)}\n\n"
                f"Now synthesize your final answer for the user based on this observation, "
                f"in your designated Victor persona."
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
            final_content = final_resp.content
        else:
            final_content = initial_content

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
