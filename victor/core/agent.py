"""Core Victor Agent Loop and Tool Orchestrator."""

import json
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from victor.core.config import VictorConfig, load_config
from victor.core.events import EventBus, global_event_bus
from victor.core.personality import PersonalityEngine
from victor.memory.store import MemoryStore
from victor.models.base import BaseLLM, ChatMessage
from victor.models.factory import create_model_provider
from victor.permissions.manager import PermissionManager
from victor.tasks.manager import TaskManager
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

    elif tool_name == "youtube" and isinstance(out, dict):
        q = out.get("query", "")
        videos = out.get("videos", [])
        if not videos:
            return f"I searched YouTube for \"{q}\" but found no videos."
        lines = [f"I searched YouTube for \"{q}\" and found {len(videos)} videos:"]
        for idx, v in enumerate(videos, 1):
            title = v.get("title", "")
            url = v.get("url", "")
            desc = v.get("description", "")
            lines.append(f"{idx}. [{title}]({url})\n   {desc}")
        return "\n\n".join(lines)

    elif tool_name == "applications" and isinstance(out, dict):
        app = out.get("application", "")
        status = out.get("status", "")
        if status == "launched":
            return f"I launched {app} for you."
        return out.get("message", f"Application {app} status: {status}")

    elif tool_name == "computer" and isinstance(out, dict):
        act = out.get("action", "")
        if act == "click":
            return f"Clicked mouse at ({out.get('x')}, {out.get('y')})."
        elif act == "window_info":
            return f"Active window: \"{out.get('active_window', '')}\" at cursor ({out.get('cursor', {}).get('x')}, {out.get('cursor', {}).get('y')})."
        elif act == "screen_info":
            return f"Screen resolution: {out.get('screen_width')}x{out.get('screen_height')}."
        return f"Computer action '{act}' executed successfully."

    elif tool_name == "notifications" and isinstance(out, dict):
        return f"Notification delivered: \"{out.get('message', '')}\"."

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
        memory: Optional[MemoryStore] = None,
        permissions: Optional[PermissionManager] = None,
        tasks: Optional[TaskManager] = None,
    ):
        self.config = config or load_config()
        self.llm = llm or create_model_provider(self.config.model)
        self.registry = registry or create_tool_registry(self.config)
        self.event_bus = event_bus or global_event_bus
        self.personality = PersonalityEngine(self.config)
        self.memory = memory or MemoryStore()
        self.permissions = permissions or PermissionManager()
        self.tasks = tasks or TaskManager(memory_store=self.memory)
        self.history: List[ChatMessage] = []

    def get_system_prompt(self) -> str:
        """Compile current system prompt with tool registry descriptions and remembered memory context."""
        tool_descriptions = self.registry.format_all_descriptions()
        base_prompt = self.personality.build_system_prompt(tool_descriptions)
        mem_summary = self.memory.get_context_summary()
        if mem_summary:
            return f"{base_prompt}\n\n{mem_summary}"
        return base_prompt

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
                f"Victor System Telemetry:\n"
                f"• Identity: {self.config.name} ({self.config.title})\n"
                f"• Core Model: {active_model} ({'Online' if is_ready else 'Offline'})\n"
                f"• Architecture: Modern Lively Minimal with Hierarchical Flow\n"
                f"• Reasoning: Autonomous Intent Router & Recursive Verification\n"
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

    def classify_autonomous_intent(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Autonomously identify required tool capabilities from natural language."""
        cleaned = text.strip()
        lower = cleaned.lower()

        # 1. Direct URL or web browsing intent
        url_match = re.search(r"https?://[^\s]+", text)
        if url_match:
            return ("browser", {"url": url_match.group(0)})
        if lower.startswith(("browse ", "visit ", "open url ")):
            parts = cleaned.split(maxsplit=1)
            if len(parts) > 1:
                target = parts[1].strip()
                if not target.startswith("http"):
                    target = f"https://{target}"
                return ("browser", {"url": target})

        # 2. YouTube Search intent
        youtube_patterns = [
            r"^(?:search\s+youtube\s+for|open\s+youtube\s+and\s+search(?:\s+for)?|youtube|find\s+videos?\s+(?:on|about))\s+(.+)$",
            r"^(.+)\s+(?:on|in)\s+youtube\??$",
        ]
        for pattern in youtube_patterns:
            m = re.match(pattern, lower)
            if m:
                query = m.group(1).strip().rstrip("?.!")
                if query:
                    return ("youtube", {"query": query})

        # 3. Application Launch intent
        app_patterns = [
            r"^(?:open|launch|start|run)\s+(chrome|google\s+chrome|edge|firefox|vscode|code|vs\s+code|notepad|terminal|powershell|cmd|explorer|calculator|spotify)\b\s*(.*)$",
        ]
        for pattern in app_patterns:
            m = re.match(pattern, lower)
            if m:
                app_target = m.group(1).strip()
                extra_args = m.group(2).strip() if len(m.groups()) > 1 else ""
                return ("applications", {"action": "open", "app_name": app_target, "args": extra_args})

        # 4. Computer control & active window inspection
        if lower in ["what is the active window", "active window", "what window is open", "current window"]:
            return ("computer", {"action": "window_info"})
        if lower in ["screen size", "screen resolution", "display size"]:
            return ("computer", {"action": "screen_info"})
        computer_click_match = re.match(r"^click\s+(?:mouse\s+)?(?:at\s+)?([0-9]+)[,\s]+([0-9]+)$", lower)
        if computer_click_match:
            return ("computer", {"action": "click", "x": int(computer_click_match.group(1)), "y": int(computer_click_match.group(2))})

        # 5. Notification intent
        notify_patterns = [
            r"^(?:notify(?:\s+me)?|send\s+notification|alert\s+me)\s+(.+)$",
        ]
        for pattern in notify_patterns:
            m = re.match(pattern, lower)
            if m:
                return ("notifications", {"message": m.group(1).strip()})

        # 6. Mathematical expression or calculation
        math_patterns = [
            r"^(?:calculate|compute|solve|eval(?:uate)?)\s+(.+)$",
            r"^(?:what(?:'s|\s+is))\s+([0-9\.\s\+\-\*\/\^\(\)\%\,]+(?:\s*[\+\-\*\/\^\%]\s*[0-9\.\s\+\-\*\/\^\(\)\%\,]+)+)\??$",
            r"^(?:what(?:'s|\s+is))\s+(?:the\s+)?(?:value|result)\s+of\s+(.+)\??$",
            r"^how\s+much\s+is\s+([0-9\.\s\+\-\*\/\^\(\)\%\,]+(?:\s*[\+\-\*\/\^\%]\s*[0-9\.\s\+\-\*\/\^\(\)\%\,]+)+)\??$",
            r"^how\s+much\s+is\s+([0-9\.]+)%\s+of\s+([0-9\.]+)\??$",
            r"^([0-9\.\s\+\-\*\/\^\(\)\%\,]{2,}\s*[\+\-\*\/\^]\s*[0-9\.\s\+\-\*\/\^\(\)\%\,]+)\s*=?\??$",
            r"^(?:sqrt|sin|cos|tan|log|exp)\s*\([0-9\.\s\+\-\*\/]+\)$",
        ]
        for pattern in math_patterns:
            m = re.match(pattern, lower)
            if m:
                groups = m.groups()
                if len(groups) == 2 and "of" in lower:
                    expr = f"{groups[1]} * ({groups[0]} / 100)"
                    return ("calculator", {"expression": expr})
                elif groups:
                    raw_expr = groups[0].strip().rstrip("=?").strip()
                    if re.search(r"\d", raw_expr):
                        return ("calculator", {"expression": raw_expr})

        # 7. Web Search intent
        search_patterns = [
            r"^(?:search(?:\s+the\s+web)?(?:\s+for)?|look\s+up|google|find(?:\s+information)?\s+about)\s+(.+)$",
            r"^(?:what\s+is\s+the\s+latest|who\s+won|recent\s+news\s+on)\s+(.+)$",
        ]
        for pattern in search_patterns:
            m = re.match(pattern, lower)
            if m:
                query = m.group(1).strip().rstrip("?.!")
                if query:
                    return ("web_search", {"query": query})

        # 8. Filesystem read intent
        file_read_patterns = [
            r"^(?:read(?:\s+file)?|inspect(?:\s+file)?|view(?:\s+file)?|show(?:\s+file)?)\s+([a-zA-Z0-9_\-\.\/\\~]+)$",
        ]
        for pattern in file_read_patterns:
            m = re.match(pattern, cleaned)
            if m:
                filepath = m.group(1).strip()
                if "." in filepath or "/" in filepath or "\\" in filepath:
                    return ("filesystem", {"action": "read", "path": filepath})

        # 9. Filesystem list intent
        file_list_patterns = [
            r"^(?:list\s+files(?:\s+in)?|what\s+files\s+are\s+in|show\s+directory)\s+([a-zA-Z0-9_\-\.\/\\~]*)$",
        ]
        for pattern in file_list_patterns:
            m = re.match(pattern, cleaned)
            if m:
                dirpath = m.group(1).strip() or "."
                return ("filesystem", {"action": "list", "path": dirpath})

        return None

    async def chat(self, user_message: str) -> Dict[str, Any]:
        """Process user input with autonomous tool selection and hierarchical/recursive execution."""
        start_time = time.perf_counter()

        # Check for direct slash command
        direct_cmd = self.parse_direct_command(user_message)
        if direct_cmd:
            cmd, arg = direct_cmd
            return await self.handle_direct_command(cmd, arg)

        # Handle explicit memory commands
        lower_msg = user_message.strip().lower()
        if lower_msg.startswith(("remember that ", "remember ")):
            fact = user_message.strip()
            if lower_msg.startswith("remember that "):
                fact = fact[14:].strip()
            elif lower_msg.startswith("remember "):
                fact = fact[9:].strip()

            self.memory.add_fact(fact, category="user_preference")
            await self.event_bus.emit("mascot.state_changed", state="completed", expression="happy")
            await self.event_bus.emit("memory.created", fact=fact)
            resp_text = f"I have committed this to my long-term memory: \"{fact}\"."
            self.history.append(ChatMessage(role="assistant", content=resp_text))
            await self.event_bus.emit("agent.completed", duration=0.05)
            return {
                "type": "chat_response",
                "content": resp_text,
                "tool_executed": None,
                "duration": 0.05,
            }

        await self.event_bus.emit("agent.started", mode="chat", user_message=user_message)
        await self.event_bus.emit("mascot.state_changed", state="listening", expression="perked")
        self.history.append(ChatMessage(role="user", content=user_message))

        # 1. Autonomous intent identification
        auto_tool = self.classify_autonomous_intent(user_message)

        # Create autonomous task record
        task = self.tasks.create_task(goal=user_message)
        self.tasks.start_task(task.id)

        # 2. Emit Hierarchical Plan Tree
        plan_nodes = [
            {
                "id": "node_goal",
                "label": "User Directive",
                "type": "goal",
                "depth": 0,
                "status": "completed",
                "detail": user_message,
            },
            {
                "id": "node_intent",
                "label": f"Auto-Route: {auto_tool[0]}" if auto_tool else "Cognitive Route: LLM Inference",
                "type": "router",
                "depth": 1,
                "status": "completed",
                "detail": f"Auto-detected capability '{auto_tool[0]}'" if auto_tool else "Decomposing intent for reasoning",
            },
            {
                "id": "node_exec",
                "label": f"Execute: {auto_tool[0]}" if auto_tool else "Capability Formulation",
                "type": "action",
                "depth": 2,
                "status": "running",
                "detail": str(auto_tool[1]) if auto_tool else "Analyzing directive context",
            },
            {
                "id": "node_recursive",
                "label": "Recursive Reflection",
                "type": "recursive",
                "depth": 2,
                "status": "standby",
                "detail": "Verify observation and resolve branches",
            },
            {
                "id": "node_synthesis",
                "label": "Natural Synthesis",
                "type": "synthesis",
                "depth": 1,
                "status": "standby",
                "detail": "Formulate articulate, concise output",
            },
        ]
        await self.event_bus.emit("agent.hierarchical_plan", plan={"goal": user_message, "nodes": plan_nodes, "task_id": task.id})

        system_prompt = self.get_system_prompt()
        tool_executed_info = None
        final_content = ""

        # Case A: Tool was autonomously auto-selected
        if auto_tool:
            tool_name, parameters = auto_tool
            step = task.add_step(name=f"Execute {tool_name}", tool=tool_name)
            step.status = "running"

            await self.event_bus.emit("mascot.state_changed", state="working", expression="focused")
            await self.event_bus.emit("tool.started", tool=tool_name, parameters=parameters)
            result: ToolResult = await self.registry.execute_tool(tool_name, **parameters)

            step.duration = result.duration
            if result.success:
                step.status = "completed"
                step.output = str(result.output)[:200]
                await self.event_bus.emit("tool.completed", tool=tool_name, duration=result.duration, output=result.output)
            else:
                step.status = "failed"
                step.output = str(result.error)
                await self.event_bus.emit("tool.failed", tool=tool_name, error=result.error, output=result.output)

            tool_executed_info = {
                "name": tool_name,
                "parameters": parameters,
                "result": result.model_dump(),
            }

            # Recursive reflection step
            rec_step = task.add_step(name="Recursive Reflection", tool=None)
            rec_step.status = "completed"
            await self.event_bus.emit(
                "agent.recursive_step",
                step_id="node_recursive",
                depth=2,
                status="completed",
                detail=f"Validated observation from {tool_name}.",
            )

            # Synthesize answer using observation
            obs_formatted = format_tool_display(tool_name, result)
            observation_msg = (
                f"[AUTONOMOUS OBSERVATION: {tool_name.upper()}]\n"
                f"{obs_formatted}\n\n"
                f"User Directive: {user_message}\n"
                f"INSTRUCTIONS: Synthesize this observation directly for the user. "
                f"Keep your response natural, short, and focused (1 to 3 sentences maximum). "
                f"STRICT RULE: Absolutely NO emojis. Do not output raw JSON."
            )

            synthetic_history = list(self.history)
            synthetic_history.append(ChatMessage(role="user", content=observation_msg))

            await self.event_bus.emit("mascot.state_changed", state="thinking", expression="thoughtful")
            await self.event_bus.emit("agent.thinking", state="synthesizing")
            try:
                final_resp = await self.llm.generate(
                    messages=synthetic_history,
                    system_prompt=system_prompt,
                    temperature=self.config.model.temperature,
                    max_tokens=self.config.model.max_tokens,
                )
                if final_resp.content and not final_resp.content.startswith("[Ollama"):
                    final_content = strip_emojis(final_resp.content.strip())
                else:
                    final_content = obs_formatted
            except Exception:
                final_content = obs_formatted

            self.tasks.complete_task(task.id, outcome=final_content[:150])
            await self.event_bus.emit("mascot.state_changed", state="completed", expression="happy")

        # Case B: Model reasoning / LLM generation with potential tool calling
        else:
            await self.event_bus.emit("agent.thinking", state="planning")
            llm_resp = await self.llm.generate(
                messages=self.history,
                system_prompt=system_prompt,
                temperature=self.config.model.temperature,
                max_tokens=self.config.model.max_tokens,
            )

            initial_content = llm_resp.content
            tool_call = self.extract_tool_call(initial_content)

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

                await self.event_bus.emit(
                    "agent.recursive_step",
                    step_id="node_recursive",
                    depth=2,
                    status="completed",
                    detail=f"Resolved recursive tool call for {tool_name}.",
                )

                obs_formatted = format_tool_display(tool_name, result)
                observation_msg = (
                    f"[TOOL OBSERVATION: {tool_name.upper()}]\n"
                    f"{obs_formatted}\n\n"
                    f"INSTRUCTIONS: Synthesize this observation directly for the user. "
                    f"Keep your response short, articulate, and focused (1 to 3 sentences maximum). "
                    f"STRICT RULE: Absolutely NO emojis. Do not output raw JSON."
                )

                synthetic_history = list(self.history)
                synthetic_history.append(ChatMessage(role="assistant", content=initial_content))
                synthetic_history.append(ChatMessage(role="user", content=observation_msg))

                await self.event_bus.emit("agent.thinking", state="synthesizing")
                try:
                    final_resp = await self.llm.generate(
                        messages=synthetic_history,
                        system_prompt=system_prompt,
                        temperature=self.config.model.temperature,
                        max_tokens=self.config.model.max_tokens,
                    )
                    if final_resp.content and not final_resp.content.startswith("[Ollama"):
                        final_content = strip_emojis(final_resp.content.strip())
                    else:
                        final_content = obs_formatted
                except Exception:
                    final_content = obs_formatted
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

        res = await self.chat(user_message)
        yield {"type": "tool_executed", "tool": res.get("tool_executed")}
        yield {"type": "content", "delta": res["content"]}
        yield {"type": "done", "duration": res.get("duration")}
