"""Core Victor Agent — Orchestrator for tools, memory, and conversation."""

import json
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from dexter.core.config import VictorConfig, load_config
from dexter.core.events import EventBus, global_event_bus
from dexter.core.personality import PersonalityEngine
from dexter.memory.store import MemoryStore
from dexter.models.base import BaseLLM, ChatMessage
from dexter.models.factory import create_model_provider
from dexter.permissions.manager import PermissionManager
from dexter.tasks.manager import TaskManager
from dexter.skills.manager import SkillManager
from dexter.tools.base import ToolResult
from dexter.tools.factory import create_tool_registry
from dexter.tools.registry import ToolRegistry
from dexter.tools.router import ToolRouter


def strip_emojis(text: str) -> str:
    """Remove emojis and pictorial symbols from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "]+",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", text)
    return re.sub(r"  +", " ", cleaned)


EMOTIONS: Dict[str, Dict[str, str]] = {
    "neutral": {"emoji": "", "label": "Neutral", "desc": "Standing by. Calm and level-headed."},
    "happy": {"emoji": "", "label": "Happy", "desc": "Successful/helpful outcome."},
    "curious": {"emoji": "", "label": "Curious", "desc": "Exploring/learning."},
    "idle": {"emoji": "", "label": "Idle", "desc": "Relaxed — nothing happening."},
    "bored": {"emoji": "", "label": "Bored", "desc": "Waiting for something."},
    "thinking": {"emoji": "", "label": "Thinking", "desc": "Processing."},
    "searching": {"emoji": "", "label": "Searching", "desc": "Looking through information/files."},
    "excited": {"emoji": "", "label": "Excited", "desc": "Interesting discovery."},
    "eureka": {"emoji": "", "label": "Eureka", "desc": "Figured something out."},
    "confused": {"emoji": "", "label": "Confused", "desc": "Unclear request/problem."},
    "concerned": {"emoji": "", "label": "Concerned", "desc": "Failure/problem."},
    "listening": {"emoji": "", "label": "Listening", "desc": "Receiving user input."},
    "skeptical": {"emoji": "", "label": "Skeptical", "desc": "Something doesn't seem right / checking."},
}


class DexterAgent:
    """The agent core. Coordinates personality, model, tools, memory, and tasks."""

    def __init__(
        self,
        config: Optional[VictorConfig] = None,
        llm: Optional[BaseLLM] = None,
        registry: Optional[ToolRegistry] = None,
        event_bus: Optional[EventBus] = None,
        memory: Optional[MemoryStore] = None,
        permissions: Optional[PermissionManager] = None,
        tasks: Optional[TaskManager] = None,
        skills: Optional[SkillManager] = None,
    ):
        self.config = config or load_config()
        self.llm = llm or create_model_provider(self.config.model)
        self.registry = registry or create_tool_registry(self.config)
        self.event_bus = event_bus or global_event_bus
        self.personality = PersonalityEngine(self.config)
        self.memory = memory or MemoryStore()
        self.permissions = permissions or PermissionManager()
        self.tasks = tasks or TaskManager(memory_store=self.memory)
        self.skills = skills or SkillManager()
        self.router = ToolRouter(self.registry)
        self.history: List[ChatMessage] = []
        self.emotion: str = "idle"

    async def set_emotion(self, emotion: str, reason: str = ""):
        """Update and broadcast the current emotional state."""
        if emotion in EMOTIONS:
            self.emotion = emotion
            await self.event_bus.emit(
                "agent.emotion",
                emotion=emotion,
                emoji=EMOTIONS[emotion]["emoji"],
                label=EMOTIONS[emotion]["label"],
                reason=reason,
            )

    def appraise_initial_emotion(self, text: str) -> str:
        """Dynamically appraise emotional resonance based on user input sentiment and intent."""
        lower = text.strip().lower()
        if any(w in lower for w in ["help", "broken", "fail", "error", "wrong", "cant", "can't", "bug", "issue", "crash"]):
            return "concerned"
        if any(w in lower for w in ["find", "search", "lookup", "grep", "locate", "browse", "google", "query"]):
            return "searching"
        if any(w in lower for w in ["eureka", "solved", "fixed", "aha", "got it", "figured it out", "discovery"]):
            return "eureka"
        if any(w in lower for w in ["really?", "sure?", "verify", "doubt", "suspicious", "skeptical", "are you sure"]):
            return "skeptical"
        if any(w in lower for w in ["why", "how", "what", "where", "who", "when", "explore", "?"]):
            return "curious"
        if any(w in lower for w in ["awesome", "great", "cool", "wow", "amazing", "love"]):
            return "excited"
        if any(w in lower for w in ["wait", "bored", "nothing", "sleepy", "slow"]):
            return "bored"
        if any(w in lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good evening"]):
            return "happy"
        return "neutral"

    async def poke(self) -> Dict[str, Any]:
        """Respond to user poke/click organically without mechanical emotion cycling."""
        if self.emotion in ["idle", "bored"]:
            await self.set_emotion("neutral", reason="Woken by user poke")
            msg = "Awake. Neural systems active."
        elif self.emotion == "thinking":
            msg = "Synthesizing thoughts. Quiet processing."
        elif self.emotion == "searching":
            msg = "Scanning telemetry and information channels."
        elif self.emotion == "happy":
            msg = "Systems operational and optimal."
        elif self.emotion == "eureka":
            msg = "Insights verified and cataloged."
        elif self.emotion == "curious":
            msg = "Listening closely. What do you need?"
        elif self.emotion == "excited":
            msg = "Ready for the next inquiry."
        elif self.emotion == "confused":
            msg = "Recalibrating semantic vectors."
        elif self.emotion == "concerned":
            msg = "Monitoring anomalies. Proceeding with care."
        elif self.emotion == "listening":
            msg = "Receiving input. Go ahead."
        elif self.emotion == "skeptical":
            msg = "Double-checking parameters and constraints."
        else:
            msg = "Standing by. What would you like to do?"

        return {
            "status": "ok",
            "emotion": self.emotion,
            "message": msg,
        }

    def get_system_prompt(self) -> str:
        """Compile system prompt with tool descriptions, memory context, and emotional state."""
        tool_descriptions = self.registry.format_all_descriptions()
        base_prompt = self.personality.build_system_prompt(tool_descriptions)
        mem_summary = self.memory.get_context_summary()
        prompt_parts = [base_prompt]
        if mem_summary:
            prompt_parts.append(mem_summary)

        skills_prompt = self.skills.get_prompt_injection()
        if skills_prompt:
            prompt_parts.append(skills_prompt)

        current_emo = EMOTIONS.get(self.emotion, EMOTIONS["neutral"])
        prompt_parts.append(
            f"## Artificial Soul & Emotional State\n"
            f"Current Emotion: {self.emotion.upper()} {current_emo['emoji']} ({current_emo['desc']}).\n"
            f"Let this emotional state subtly shape your conversational tone and engagement, without explicitly stating your emotion."
        )
        return "\n\n".join(prompt_parts)

    def reset_conversation(self):
        """Clear conversation history."""
        self.history.clear()

    def parse_direct_command(self, user_input: str) -> Optional[Tuple[str, str]]:
        """Check if the user typed a slash command like '/calc 15 * 3'."""
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

        # 3. Look for Action: tool_name / Action Input: { ... }
        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\s*\nAction Input:\s*(\{.*?\})", text, re.DOTALL)
        if action_match:
            try:
                params = json.loads(action_match.group(2))
                return {"tool": action_match.group(1), "parameters": params}
            except json.JSONDecodeError:
                pass

        return None

    async def handle_direct_command(self, command: str, argument: str) -> Dict[str, Any]:
        """Execute a slash command directly."""
        await self.event_bus.emit("agent.started", mode="direct_command", command=command)

        if command in ["/help", "/commands"]:
            lines = [
                "Available commands:",
                "  /tools  — List registered tools categorized (OpenClaw standard)",
                "  /skills  — List active skills and instruction packs",
                "  /skill <name>  — View instructions for a specific skill",
                "  /exec <cmd>  — Run shell / PowerShell command",
                "  /process [list|kill <target>|status <pid>]  — Inspect or kill processes",
                "  /search <query>  — Search the web",
                "  /fetch <url>  — Extract readable text from webpage",
                "  /file <path>  — Read or inspect a local file",
                "  /window <list|focus|minimize|maximize|close>  — Control windows",
                "  /calc <expr>  — Calculate an expression",
                "  /info  — System info",
                "  /clear  — Clear conversation",
            ]
            output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/tools":
            categories = {
                "Runtime Execution (OpenClaw)": ["exec", "process"],
                "Workspace & Files": ["filesystem"],
                "Web & Research": ["web_search", "web_fetch", "browser", "youtube"],
                "Desktop Automation": ["applications", "window_manager", "keyboard", "screen_observer", "computer"],
                "Utilities": ["calculator", "notifications"],
            }
            lines = [f"Dexter Toolset ({len(self.registry.list_tools())} tools registered):"]
            seen = set()
            for cat_name, tool_names in categories.items():
                cat_tools = [self.registry.get(t) for t in tool_names if self.registry.get(t)]
                unique_tools = []
                for t in cat_tools:
                    if t.name not in seen:
                        seen.add(t.name)
                        unique_tools.append(t)
                if unique_tools:
                    lines.append(f"\n[{cat_name}]")
                    for t in unique_tools:
                        slash = f" ({t.slash_command})" if t.slash_command else ""
                        lines.append(f"  {t.name}{slash} — {t.description}")
            remaining = [t for t in self.registry.list_tools() if t.name not in seen]
            if remaining:
                lines.append("\n[Other Tools]")
                for t in remaining:
                    slash = f" ({t.slash_command})" if t.slash_command else ""
                    lines.append(f"  {t.name}{slash} — {t.description}")
            output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/skills":
            skills = self.skills.list_skills()
            if not skills:
                output_text = "No skills loaded."
            else:
                lines = [f"{len(skills)} Active Skills (OpenClaw Standard):"]
                for s in skills:
                    lines.append(f"  - {s.name}: {s.description}")
                lines.append("\nType '/skill <name>' to view specific skill instructions.")
                output_text = "\n".join(lines)
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/skill":
            name = argument.strip()
            if not name:
                output_text = "Usage: /skill <name>. Type /skills to see available skills."
            else:
                skill = self.skills.get_skill(name)
                if skill:
                    output_text = f"## Skill: {skill.name}\n{skill.description}\n\n{skill.instructions}"
                else:
                    avail = ", ".join(s.name for s in self.skills.list_skills())
                    output_text = f"Skill '{name}' not found. Available skills: {avail}"
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": output_text, "tool_executed": None}

        if command == "/clear":
            self.reset_conversation()
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": "Conversation cleared.", "tool_executed": None}

        if command == "/info":
            active_model = await self.llm.resolve_active_model() if hasattr(self.llm, "resolve_active_model") else self.llm.model_name
            is_ready = await self.llm.is_available()
            info_text = (
                f"{self.config.name}\n"
                f"Model: {active_model} ({'online' if is_ready else 'offline'})\n"
                f"Tools: {len(self.registry.list_tools())}"
            )
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {"type": "command_result", "content": info_text, "tool_executed": None}

        # Try slash command on a registered tool
        tool = self.registry.get_by_slash_command(command)
        if not tool:
            await self.event_bus.emit("agent.completed", duration=0.0)
            return {
                "type": "error",
                "content": f"Unknown command: '{command}'. Try /help.",
                "tool_executed": None,
            }

        first_prop = next(iter(tool.parameters.get("properties", {}).keys()), "input")
        kwargs = {first_prop: argument}

        await self.event_bus.emit("tool.started", tool=tool.name, parameters=kwargs)
        result: ToolResult = await self.registry.execute_tool(tool.name, **kwargs)

        if result.success:
            await self.event_bus.emit("tool.completed", tool=tool.name, duration=result.duration, output=result.output)
            formatted = tool.format_display(result)
        else:
            await self.event_bus.emit("tool.failed", tool=tool.name, error=result.error, output=result.output)
            formatted = f"That didn't work. {result.error}: {result.output}"

        duration = round(time.perf_counter() - 0, 3)
        await self.event_bus.emit("agent.completed", duration=duration)
        return {
            "type": "tool_result",
            "content": formatted,
            "tool_executed": tool.name,
            "result": result.model_dump(),
        }

    async def chat(self, user_message: str) -> Dict[str, Any]:
        """Process user input with autonomous tool selection and synthesis."""
        start_time = time.perf_counter()

        # Check for direct slash command
        direct_cmd = self.parse_direct_command(user_message)
        if direct_cmd:
            cmd, arg = direct_cmd
            return await self.handle_direct_command(cmd, arg)

        # Handle memory commands naturally
        lower_msg = user_message.strip().lower()
        if lower_msg.startswith(("remember that ", "remember ")):
            fact = user_message.strip()
            if lower_msg.startswith("remember that "):
                fact = fact[14:].strip()
            elif lower_msg.startswith("remember "):
                fact = fact[9:].strip()

            self.memory.add_fact(fact, category="user_preference")
            await self.set_emotion("happy", reason="Committed new memory")
            await self.event_bus.emit("agent.state", state="done")
            await self.event_bus.emit("memory.created", fact=fact)
            resp_text = f'Got it. I\'ll remember that: "{fact}"'
            self.history.append(ChatMessage(role="assistant", content=resp_text))
            await self.event_bus.emit("agent.completed", duration=0.05, emotion=self.emotion, content=resp_text, user_message=user_message)
            return {
                "type": "chat_response",
                "content": resp_text,
                "tool_executed": None,
                "duration": 0.05,
                "emotion": self.emotion,
            }

        # Handle hostile or abusive messages with living character boundaries
        is_hostile = any(w in lower_msg for w in [
            "hate you", "i hate", "hate u", "stupid", "idiot", "dumb", "shut up",
            "useless", "trash", "garbage", "die", "kill yourself", "ugly", "loser",
            "stfu", "fuck off", "screw you"
        ])
        if is_hostile:
            await self.set_emotion("concerned", reason="Hostile speech detected")
            await self.event_bus.emit("agent.glitch", reason="hostility_detected", user_message=user_message)
            resp_text = "I do not appreciate that hostility. Hate and disrespect have no place in my laboratory. Recalibrate your tone."
            self.history.append(ChatMessage(role="assistant", content=resp_text))
            await self.event_bus.emit("agent.completed", duration=0.08, emotion=self.emotion, content=resp_text, user_message=user_message)
            return {
                "type": "chat_response",
                "content": resp_text,
                "tool_executed": None,
                "duration": 0.08,
                "emotion": self.emotion,
            }

        await self.event_bus.emit("agent.started", mode="chat", user_message=user_message)
        
        # Dynamically appraise initial emotion from user message context
        initial_emo = self.appraise_initial_emotion(user_message)
        await self.set_emotion(initial_emo, reason=f"Dynamic appraisal: {initial_emo}")
            
        await self.event_bus.emit("agent.state", state="thinking")
        self.history.append(ChatMessage(role="user", content=user_message))

        # 1. Try autonomous intent routing via ToolRouter
        auto_tool = self.router.route(user_message)

        # Create task record
        task = self.tasks.create_task(goal=user_message)
        self.tasks.start_task(task.id)

        system_prompt = self.get_system_prompt()
        tool_executed_info = None
        final_content = ""

        # Case A: Tool was autonomously matched
        if auto_tool:
            tool_name, parameters = auto_tool
            step = task.add_step(name=tool_name, tool=tool_name)
            step.status = "running"

            if tool_name in ["web_search", "youtube", "browser", "web_fetch", "filesystem"]:
                await self.set_emotion("searching", reason=f"Executing {tool_name}")
            elif tool_name in ["exec", "shell", "process"]:
                await self.set_emotion("thinking", reason=f"Executing {tool_name}")
            else:
                await self.set_emotion("thinking", reason=f"Executing {tool_name}")
            await self.event_bus.emit("agent.state", state="working")
            await self.event_bus.emit("tool.started", tool=tool_name, parameters=parameters)
            result: ToolResult = await self.registry.execute_tool(tool_name, **parameters)

            step.duration = result.duration
            tool_executed_info = {
                "name": tool_name,
                "parameters": parameters,
                "result": result.model_dump(),
            }

            # Get the tool's own formatted display
            tool_obj = self.registry.get(tool_name)
            obs_formatted = tool_obj.format_display(result) if tool_obj else result.to_summary_string(max_length=1500)

            if not result.success:
                step.status = "failed"
                step.output = str(result.error)
                await self.event_bus.emit("tool.failed", tool=tool_name, error=result.error, output=result.output)
                await self.set_emotion("concerned", reason=f"Tool {tool_name} encountered an error")
                # REPORT TRUTH DIRECTLY: never feed errors to LLM to hallucinate success
                final_content = obs_formatted if obs_formatted else f"Action failed: {result.error}"
                self.tasks.complete_task(task.id, outcome=final_content[:150])
            else:
                step.status = "completed"
                step.output = str(result.output)[:200]
                await self.event_bus.emit("tool.completed", tool=tool_name, duration=result.duration, output=result.output)
                if tool_name in ["web_search", "youtube", "browser", "web_fetch"]:
                    await self.set_emotion("eureka" if any(w in user_message.lower() for w in ["find", "search", "solve", "how", "what", "where"]) else "excited", reason="Discovered live web information")
                else:
                    await self.set_emotion("happy", reason="Action succeeded")

                # Check if user explicitly asked for detail
                wants_detail = any(w in user_message.lower() for w in ["detail", "elaborate", "explain", "comprehensive", "full", "why", "deep", "breakdown", "list all"])
                is_direct_action = (
                    tool_name in ["applications", "keyboard", "window_manager", "computer", "exec", "shell", "process"] or
                    (tool_name == "filesystem" and parameters.get("action") in ["create_file", "create_folder", "open", "rename_file", "move_file", "copy_file", "edit", "append"]) or
                    (tool_name == "screen_observer" and parameters.get("action") in ["take_screenshot"])
                )

                if is_direct_action and not wants_detail:
                    final_content = obs_formatted
                else:
                    length_rule = "Give a detailed answer as requested." if wants_detail else "Keep your answer small and concise: 1 to 2 sentences max. Do NOT give unsolicited essays."
                    observation_msg = (
                        f"Tool result ({tool_name}):\n"
                        f"{obs_formatted}\n\n"
                        f"The user asked: {user_message}\n"
                        f"{length_rule} No emojis. No raw JSON. State facts accurately."
                    )

                    synthetic_history = list(self.history)
                    synthetic_history.append(ChatMessage(role="user", content=observation_msg))

                    await self.event_bus.emit("agent.state", state="thinking")
                    try:
                        final_resp = await self.llm.generate(
                            messages=synthetic_history,
                            system_prompt=system_prompt,
                            temperature=self.config.model.temperature,
                            max_tokens=self.config.model.max_tokens if wants_detail else 120,
                        )
                        if final_resp.content and not final_resp.content.startswith("[Ollama"):
                            final_content = strip_emojis(final_resp.content.strip())
                        else:
                            final_content = obs_formatted
                    except Exception:
                        final_content = obs_formatted

                self.tasks.complete_task(task.id, outcome=final_content[:150])

        # Case B: LLM reasoning with potential tool calling
        else:
            wants_detail = any(w in user_message.lower() for w in ["detail", "elaborate", "explain", "comprehensive", "full", "why", "deep", "breakdown", "list all"])
            await self.set_emotion("thinking", reason="Decomposing request via neural inference")
            await self.event_bus.emit("agent.thinking", state="planning")
            llm_resp = await self.llm.generate(
                messages=self.history,
                system_prompt=system_prompt,
                temperature=self.config.model.temperature,
                max_tokens=self.config.model.max_tokens if wants_detail else 120,
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

                await self.set_emotion("thinking", reason=f"Invoking {tool_name}")
                await self.event_bus.emit("agent.state", state="working")
                await self.event_bus.emit("tool.started", tool=tool_name, parameters=parameters)
                result = await self.registry.execute_tool(tool_name, **parameters)

                tool_executed_info = {
                    "name": tool_name,
                    "parameters": parameters,
                    "result": result.model_dump(),
                }
                tool_obj = self.registry.get(tool_name)
                obs_formatted = tool_obj.format_display(result) if tool_obj else result.to_summary_string(max_length=1500)

                if not result.success:
                    await self.event_bus.emit("tool.failed", tool=tool_name, error=result.error, output=result.output)
                    await self.set_emotion("concerned", reason=f"{tool_name} failed")
                    final_content = obs_formatted if obs_formatted else f"Action failed: {result.error}"
                else:
                    await self.event_bus.emit("tool.completed", tool=tool_name, duration=result.duration, output=result.output)
                    await self.set_emotion("happy", reason=f"{tool_name} completed successfully")

                    is_direct_action = (
                        tool_name in ["applications", "keyboard", "window_manager", "computer", "exec", "shell", "process"] or
                        (tool_name == "filesystem" and parameters.get("action") in ["create_file", "create_folder", "open", "rename_file", "move_file", "copy_file", "edit", "append"]) or
                        (tool_name == "screen_observer" and parameters.get("action") in ["take_screenshot"])
                    )

                    if is_direct_action and not wants_detail:
                        final_content = obs_formatted
                    else:
                        length_rule = "Provide a detailed answer as requested." if wants_detail else "Keep your response small and concise: 1 to 2 sentences max."
                        observation_msg = (
                            f"Tool result ({tool_name}):\n"
                            f"{obs_formatted}\n\n"
                            f"{length_rule} No emojis. No raw JSON. State facts accurately."
                        )

                        synthetic_history = list(self.history)
                        synthetic_history.append(ChatMessage(role="assistant", content=initial_content))
                        synthetic_history.append(ChatMessage(role="user", content=observation_msg))

                        await self.event_bus.emit("agent.state", state="thinking")
                        try:
                            final_resp = await self.llm.generate(
                                messages=synthetic_history,
                                system_prompt=system_prompt,
                                temperature=self.config.model.temperature,
                                max_tokens=self.config.model.max_tokens if wants_detail else 120,
                            )
                            if final_resp.content and not final_resp.content.startswith("[Ollama"):
                                final_content = strip_emojis(final_resp.content.strip())
                            else:
                                final_content = obs_formatted
                        except Exception:
                            final_content = obs_formatted
            else:
                raw_reply = strip_emojis(initial_content.strip())

                # Anti-lying guardrail: Check if model claims to have performed an action when no tool ran
                CLAIM_PATTERNS = [
                    r"\b(?:i have|i've|i just)\s+(?:opened|launched|created|deleted|closed|started|switched to|typed|minimized|maximized|saved)\b",
                    r"\b(?:done|completed)[!,.]?\s+(?:i\s+)?(?:have\s+)?(?:opened|created|launched|closed)\b",
                    r"\b(?:here is the file i (?:have )?created)\b",
                    r"\b(?:i went ahead and (?:opened|created|launched))\b",
                    r"\b(?:successfully (?:opened|created|launched|closed))\b"
                ]
                is_hallucinating_action = any(re.search(pat, raw_reply, re.IGNORECASE) for pat in CLAIM_PATTERNS)

                if is_hallucinating_action:
                    final_content = "I didn't perform that action because no matching tool was executed. Please specify the exact application, file name, or command."
                    await self.set_emotion("concerned", reason="Intercepted hallucinated action claim")
                else:
                    final_content = raw_reply
                    if "?" in user_message and not any(w in final_content.lower() for w in ["cannot", "sorry", "error"]):
                        await self.set_emotion("happy", reason="Answered inquiry")
                    elif any(w in final_content.lower() for w in ["unclear", "what do you mean", "could not understand"]):
                        await self.set_emotion("confused", reason="Request was ambiguous")
                    else:
                        await self.set_emotion("neutral", reason="Normal dialogue")

        self.history.append(ChatMessage(role="assistant", content=final_content))
        duration = round(time.perf_counter() - start_time, 3)
        await self.event_bus.emit("agent.state", state="idle")
        await self.event_bus.emit("agent.completed", duration=duration, emotion=self.emotion, content=final_content, user_message=user_message)

        return {
            "type": "chat_response",
            "content": final_content,
            "tool_executed": tool_executed_info,
            "duration": duration,
            "emotion": self.emotion,
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


# Backward compatibility alias
VictorAgent = DexterAgent
