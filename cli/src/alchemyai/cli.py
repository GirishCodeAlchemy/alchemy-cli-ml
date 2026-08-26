"""Main CLI entry point for AlchemyCLI AI.

Usage:
    alchemyai "how do I restart a kubernetes deployment?"
    alchemyai ask "find pods using the most memory"
    alchemyai search "kubectl rollout"
    alchemyai kubernetes
    alchemyai model info
    alchemyai serve
"""

from __future__ import annotations

import json
import logging
import sys

import click
from rich.console import Console

from . import __version__
from .display import (
    console,
    display_banner,
    display_clarification,
    display_commands_list,
    display_error,
    display_low_confidence_help,
    display_model_info,
    display_results,
    display_technologies,
)

logger = logging.getLogger(__name__)

# Known technology shortcuts
TECH_SHORTCUTS = {
    "kubernetes", "k8s", "docker", "git", "linux", "python",
    "go", "rust", "kafka", "terraform", "helm",
}


def _get_engine():
    """Lazy-load the inference engine."""
    from alchemy_ml.inference import InferenceEngine
    engine = InferenceEngine()
    try:
        engine.initialize()
    except Exception as e:
        logger.warning("ML engine init failed: %s", e)
        # Fallback: just load commands for keyword search
        engine.load_commands()
    return engine


@click.group(invoke_without_command=True)
@click.argument("query", nargs=-1, required=False)
@click.option("--json-output", "--json", "json_out", is_flag=True, help="Output JSON")
@click.option("--explain", is_flag=True, help="Show match explanations")
@click.option("--debug", is_flag=True, help="Show debug information")
@click.option("--mode", type=click.Choice(["semantic", "keyword", "hybrid"]), default="hybrid")
@click.option("--top-k", "-k", type=int, default=5, help="Number of results")
@click.option("--copy", is_flag=True, help="Copy top result to clipboard")
@click.option("--command-only", "--cmd", is_flag=True, help="Output only the command string")
@click.version_option(version=__version__, prog_name="AlchemyCLI AI")
@click.pass_context
def main(
    ctx: click.Context,
    query: tuple[str, ...],
    json_out: bool,
    explain: bool,
    debug: bool,
    mode: str,
    top_k: int,
    copy: bool,
    command_only: bool,
) -> None:
    """AlchemyCLI AI — Ask your terminal. Find the right command."""
    # Handle subcommand routing for known commands that got consumed as args
    if query and len(query) == 1 and query[0] in main.commands:
        ctx.invoke(main.commands[query[0]])
        return

    if ctx.invoked_subcommand is not None:
        return

    # No query and no subcommand → interactive mode
    if not query:
        engine = _get_engine()
        from .interactive import run_interactive
        run_interactive(engine, explain=explain)
        return

    query_str = " ".join(query)

    # Check for technology shortcut
    if query_str.lower() in TECH_SHORTCUTS:
        ctx.invoke(technology_list, technology=query_str.lower())
        return

    # Run the query
    engine = _get_engine()
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    response = engine.ask(
        query=query_str,
        top_k=top_k,
        mode=mode,
        explain=explain,
        debug=debug,
    )

    # JSON output
    if json_out:
        click.echo(json.dumps(response.model_dump(), indent=2, default=str))
        return

    # Command-only output
    if command_only and response.results:
        click.echo(response.results[0].command)
        return

    # Rich output
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
        display_low_confidence_help(engine.get_all_technologies())

    # Copy to clipboard
    if copy and response.results:
        try:
            import pyperclip
            cmd = response.results[0].command
            pyperclip.copy(cmd)
            console.print("  [Copied to clipboard]\n", style="green")
        except Exception:
            console.print("  Could not copy to clipboard.\n", style="warning")

    # Debug info
    if debug and response.debug:
        console.print("\n  Debug:", style="dim")
        for k, v in response.debug.items():
            console.print(f"    {k}: {v}", style="dim")


@main.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--explain", is_flag=True)
@click.option("--json-output", "--json", "json_out", is_flag=True)
@click.option("--top-k", "-k", type=int, default=5)
@click.option("--mode", type=click.Choice(["semantic", "keyword", "hybrid"]), default="hybrid")
def ask(query: tuple[str, ...], explain: bool, json_out: bool, top_k: int, mode: str) -> None:
    """Ask a natural language question."""
    query_str = " ".join(query)
    engine = _get_engine()
    response = engine.ask(query=query_str, top_k=top_k, mode=mode, explain=explain)

    if json_out:
        click.echo(json.dumps(response.model_dump(), indent=2, default=str))
    elif response.results:
        display_results([r.model_dump() for r in response.results], show_explanation=explain)
    else:
        display_low_confidence_help(engine.get_all_technologies())


@main.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--top-k", "-k", type=int, default=10)
def search(query: tuple[str, ...], top_k: int) -> None:
    """Keyword search through commands."""
    query_str = " ".join(query)
    engine = _get_engine()
    response = engine.ask(query=query_str, top_k=top_k, mode="keyword")

    if response.results:
        display_results([r.model_dump() for r in response.results])
    else:
        console.print("  No results found.\n", style="warning")


@main.command(name="show")
@click.argument("command_id")
def show_command(command_id: str) -> None:
    """Show details for a specific command."""
    engine = _get_engine()
    cmd = engine.get_command(command_id)

    if not cmd:
        display_error(f"Command not found: {command_id}")
        sys.exit(1)

    display_results([{
        "command_id": cmd.id,
        "command": cmd.command,
        "name": cmd.name,
        "description": cmd.description,
        "technology": cmd.technology,
        "category": cmd.category,
        "intent": cmd.intent,
        "confidence": 1.0,
        "risk": cmd.risk.value,
        "tags": cmd.tags,
        "documentation_url": cmd.doc_url,
        "related_commands": [],
    }], show_explanation=False)


@main.command(name="list")
def list_all() -> None:
    """List all technologies and command counts."""
    engine = _get_engine()
    techs = {}
    for t in engine.get_all_technologies():
        techs[t] = len(engine.get_commands_by_technology(t))
    display_technologies(techs)


@main.command(name="technology", hidden=True)
@click.argument("technology")
def technology_list(technology: str) -> None:
    """List commands for a specific technology."""
    engine = _get_engine()

    # Normalize technology name
    from alchemy_ml.preprocessing import TECHNOLOGY_ALIASES
    tech_name = TECHNOLOGY_ALIASES.get(technology.lower(), technology.lower())

    commands = engine.get_commands_by_technology(tech_name)
    if not commands:
        display_error(f"No commands found for: {technology}")
        return

    cmd_dicts = [{"name": c.name, "command": c.command, "risk": c.risk.value} for c in commands]
    display_commands_list(cmd_dicts, tech_name)


# Technology shortcut commands
for _tech in ["kubernetes", "docker", "git", "linux", "python", "go", "rust", "kafka", "terraform"]:
    def _make_tech_cmd(tech_name: str):
        @main.command(name=tech_name)
        def _cmd() -> None:
            f"""List {tech_name} commands."""
            engine = _get_engine()
            commands = engine.get_commands_by_technology(tech_name)
            if commands:
                cmd_dicts = [{"name": c.name, "command": c.command, "risk": c.risk.value} for c in commands]
                display_commands_list(cmd_dicts, tech_name)
            else:
                display_error(f"No commands found for {tech_name}")
        _cmd.__doc__ = f"List {tech_name} commands."
        return _cmd
    _make_tech_cmd(_tech)


@main.group()
def model() -> None:
    """Model management commands."""
    pass


@model.command(name="info")
def model_info() -> None:
    """Show model information."""
    engine = _get_engine()
    info = engine.get_model_info()
    display_model_info(info.model_dump())


@model.command(name="download")
def model_download() -> None:
    """Download or update the ML model."""
    console.print("\n  Downloading model...\n", style="info")
    engine = _get_engine()
    info = engine.get_model_info()
    console.print(f"  Model ready: {info.embedding_model}\n", style="green")


@main.group()
def context() -> None:
    """Manage conversation context."""
    pass


@context.command(name="clear")
def context_clear() -> None:
    """Clear conversation context."""
    engine = _get_engine()
    engine.clear_context()
    console.print("  Context cleared.\n", style="green")


@main.command()
def favorites() -> None:
    """Show saved favorite commands."""
    from pathlib import Path
    import os

    fav_path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "alchemyai" / "favorites.json"
    if not fav_path.exists():
        console.print("  No favorites saved.\n", style="dim")
        return

    with open(fav_path) as f:
        favs = json.load(f)

    if not favs:
        console.print("  No favorites saved.\n", style="dim")
        return

    for fav in favs:
        console.print(f"  {fav.get('name', '')}: {fav.get('command', '')}", style="bold")


@main.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", "-p", type=int, default=8000, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the API server."""
    import uvicorn
    console.print(f"\n  Starting AlchemyCLI AI server on {host}:{port}\n", style="info")
    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@main.command()
def update() -> None:
    """Check for updates."""
    console.print("\n  Checking for updates...", style="info")
    console.print(f"  Current version: {__version__}", style="dim")
    console.print("  You are up to date.\n", style="green")


@main.command()
def version() -> None:
    """Show version."""
    click.echo(f"AlchemyCLI AI v{__version__}")


if __name__ == "__main__":
    main()
