"""Interactive Rich Command-Line Interface for Victor."""

import asyncio
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from victor.core.agent import VictorAgent
from victor.core.config import load_config
from victor.core.events import AgentEvent


class VictorCLI:
    """Terminal Command Center for Victor."""

    def __init__(self):
        self.console = Console()
        self.config = load_config()
        self.agent = VictorAgent(config=self.config)
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Subscribe terminal visualizers to the event bus."""
        async def on_event(event: AgentEvent):
            topic = event.topic
            data = event.data
            if topic == "agent.thinking":
                state = data.get("state", "thinking")
                self.console.print(f"[dim cyan]● Victor is {state}...[/dim cyan]")
            elif topic == "tool.started":
                tool = data.get("tool", "unknown")
                params = data.get("parameters", {})
                self.console.print(f"\n[bold yellow]┌ Executing tool: {tool}...[/bold yellow]")
                if params:
                    self.console.print(f"[dim yellow]│ Params: {params}[/dim yellow]")
            elif topic == "tool.completed":
                tool = data.get("tool", "")
                dur = data.get("duration", 0.0)
                self.console.print(f"[bold green]└ {tool} completed in {dur}s[/bold green]\n")
            elif topic == "tool.failed":
                tool = data.get("tool", "")
                err = data.get("error", "Failed")
                self.console.print(f"[bold red]└ {tool} failed: {err}[/bold red]\n")

        self.agent.event_bus.subscribe(on_event)

    def print_banner(self, model_name: str, is_online: bool):
        status_dot = "[green]● ONLINE[/green]" if is_online else "[red]○ OFFLINE (Check Ollama)[/red]"
        banner_text = Text()
        banner_text.append(f"{self.config.name.upper()} — {self.config.title.upper()}\n", style="bold cyan")
        banner_text.append(f"\"{self.config.tagline}\"\n\n", style="italic white")
        banner_text.append(f"Status: {status_dot}  |  Model: [magenta]{model_name}[/magenta]  |  Commands: [dim]/help[/dim]", style="white")

        self.console.print(Panel(banner_text, border_style="cyan", expand=False))

    async def run(self):
        is_online = await self.agent.llm.is_available()
        active_model = await self.agent.llm.resolve_active_model() if hasattr(self.agent.llm, "resolve_active_model") else self.config.model.name

        self.print_banner(active_model, is_online)

        if not is_online:
            self.console.print("[bold yellow]Warning: Ollama connection failed. Direct tool commands will work, but LLM chat requires Ollama.[/bold yellow]\n")

        while True:
            try:
                user_input = await asyncio.to_thread(input, "\nYou > ")
                user_input = user_input.strip()
                if not user_input:
                    continue

                if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                    self.console.print("[cyan]Victor: Farewell. Suspending artificial mind.[/cyan]")
                    break

                # Process message
                result = await self.agent.chat(user_input)
                content = result.get("content", "")

                self.console.print(f"\n[bold cyan]{self.config.name}:[/bold cyan]")
                try:
                    self.console.print(Markdown(content))
                except Exception:
                    self.console.print(content)

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[cyan]Session terminated by user.[/cyan]")
                break
            except Exception as ex:
                self.console.print(f"[red]Error during interaction: {ex}[/red]")


def main():
    cli = VictorCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
