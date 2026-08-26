"""Interactive terminal mode for AlchemyCLI AI."""

from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console

from .display import (
    console,
    display_banner,
    display_clarification,
    display_results,
)

HELP_TEXT = """
  /help     Show this help
  /history  Show recent queries
  /clear    Clear conversation context
  /exit     Exit interactive mode
  /quit     Exit interactive mode
"""


def run_interactive(engine, explain: bool = False) -> None:
    """Run the interactive terminal session.

    Args:
        engine: Initialized InferenceEngine instance.
        explain: Whether to show match explanations.
    """
    import os
    from pathlib import Path

    display_banner()
    console.print()

    # Set up prompt history
    history_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "alchemyai"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "prompt_history"

    session: PromptSession = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
    )

    while True:
        try:
            query = session.prompt("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  Goodbye!\n", style="dim")
            break

        if not query:
            continue

        # Handle commands
        if query.startswith("/"):
            cmd = query.lower().strip()
            if cmd in ("/exit", "/quit"):
                console.print("\n  Goodbye!\n", style="dim")
                break
            elif cmd == "/help":
                console.print(HELP_TEXT, style="dim")
                continue
            elif cmd == "/clear":
                engine.clear_context()
                console.print("  Context cleared.\n", style="dim")
                continue
            elif cmd == "/history":
                # Show recent context
                ctx = engine._context
                if not ctx:
                    console.print("  No recent queries.\n", style="dim")
                else:
                    for entry in ctx[-5:]:
                        console.print(f"  • {entry.get('query', '')}", style="dim")
                    console.print()
                continue
            else:
                console.print(f"  Unknown command: {cmd}", style="warning")
                continue

        # Process query
        response = engine.ask(query=query, explain=explain)

        console.print()

        if response.clarification:
            display_clarification(
                response.clarification.message,
                [opt.model_dump() for opt in response.clarification.options],
            )

            if response.results:
                display_results(
                    [r.model_dump() for r in response.results],
                    show_explanation=explain,
                )
        elif response.results:
            display_results(
                [r.model_dump() for r in response.results],
                show_explanation=explain,
            )
        else:
            console.print("  No matching commands found.\n", style="warning")
