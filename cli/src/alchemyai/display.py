"""Rich terminal display for AlchemyCLI AI."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme
THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "red bold",
    "safe": "green",
    "command": "bold white on grey23",
    "confidence.high": "green",
    "confidence.medium": "yellow",
    "confidence.low": "red",
    "technology": "cyan bold",
    "category": "dim",
})

console = Console(theme=THEME)


def display_banner() -> None:
    """Display the AlchemyCLI AI banner."""
    banner = Text()
    banner.append("ALCHEMYCLI AI", style="bold cyan")
    console.print(Panel(
        banner,
        subtitle="Ask your terminal. Find the right command.",
        border_style="cyan",
        padding=(1, 4),
    ))


def display_result(result: dict, index: int = 0, show_explanation: bool = False) -> None:
    """Display a single search result."""
    tech = result.get("technology", "")
    category = result.get("category", "")
    name = result.get("name", "")
    command = result.get("command", "")
    description = result.get("description", "")
    confidence = result.get("confidence", 0.0)
    risk = result.get("risk", "safe")
    doc_url = result.get("documentation_url", "")
    related = result.get("related_commands", [])

    # Header
    header = Text()
    header.append(f"{tech.title()}", style="technology")
    if category:
        header.append(f" › {category.replace('_', ' ').title()}", style="category")

    console.print(header)
    console.print(f"  {name}\n", style="bold")

    # Command
    console.print(f"  {command}\n", style="command")

    # Description
    if description:
        # Truncate long descriptions
        desc = description.strip()
        if len(desc) > 200:
            desc = desc[:197] + "..."
        console.print(f"  {desc}\n", style="dim")

    # Confidence
    conf_pct = f"{confidence:.0%}"
    if confidence >= 0.90:
        conf_style = "confidence.high"
    elif confidence >= 0.75:
        conf_style = "confidence.medium"
    else:
        conf_style = "confidence.low"
    console.print(f"  Confidence: ", end="")
    console.print(conf_pct, style=conf_style)

    # Risk
    risk_display = {
        "safe": ("SAFE", "safe"),
        "warning": ("⚠ WARNING", "warning"),
        "dangerous": ("🔴 DANGEROUS", "danger"),
    }
    label, style = risk_display.get(risk, ("SAFE", "safe"))
    console.print(f"  Risk: ", end="")
    console.print(label, style=style)

    # Related commands
    if related:
        console.print("\n  Related:", style="dim")
        for r in related[:3]:
            console.print(f"    {r}", style="dim")

    # Documentation
    if doc_url:
        console.print(f"\n  Docs: {doc_url}", style="dim underline")

    # Explanation
    if show_explanation and result.get("explanation"):
        exp = result["explanation"]
        console.print("\n  Why this matched:", style="dim")
        if exp.get("technology_detected"):
            console.print(f"    ✓ {exp['technology_detected']} detected", style="green")
        if exp.get("intent_detected"):
            console.print(f"    ✓ intent: {exp['intent_detected']}", style="green")
        if exp.get("matched_tags"):
            console.print(f"    ✓ tags: {', '.join(exp['matched_tags'])}", style="green")
        console.print(f"    ✓ semantic: {exp.get('semantic_score', 0):.2f}", style="dim")
        console.print(f"    ✓ keyword: {exp.get('keyword_score', 0):.2f}", style="dim")

    console.print()


def display_results(results: list[dict], show_explanation: bool = False) -> None:
    """Display multiple results."""
    if not results:
        console.print("  No results found.\n", style="warning")
        return

    if len(results) == 1:
        display_result(results[0], show_explanation=show_explanation)
        return

    console.print(f"\n  Top {len(results)} matches\n", style="bold")
    for i, result in enumerate(results, 1):
        console.print(f"  ─── Result {i} ───", style="dim")
        display_result(result, index=i, show_explanation=show_explanation)


def display_clarification(message: str, options: list[dict]) -> None:
    """Display a clarification request."""
    console.print(f"\n  {message}\n", style="warning")
    for i, opt in enumerate(options, 1):
        console.print(f"    {i}. {opt.get('label', '')}", style="bold")
        if opt.get("query"):
            console.print(f"       → {opt['query']}", style="dim")
    console.print()


def display_model_info(info: dict) -> None:
    """Display model information."""
    table = Table(title="AlchemyCLI AI — Model Info", show_header=False, border_style="cyan")
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Embedding model", info.get("embedding_model", ""))
    table.add_row("Embedding dimension", str(info.get("embedding_dimension", "")))
    table.add_row("Classifier", info.get("classifier_type", ""))
    table.add_row("Commands", str(info.get("num_commands", "")))
    table.add_row("Technologies", str(info.get("num_technologies", "")))
    table.add_row("Intents", str(info.get("num_intents", "")))
    table.add_row("Index type", info.get("index_type", ""))
    table.add_row("Model version", info.get("model_version", ""))
    table.add_row("Dataset version", info.get("dataset_version", ""))

    console.print(table)


def display_technologies(technologies: dict[str, int]) -> None:
    """Display technology list with command counts."""
    table = Table(title="Available Technologies", border_style="cyan")
    table.add_column("Technology", style="bold cyan")
    table.add_column("Commands", justify="right")

    for tech, count in sorted(technologies.items()):
        table.add_row(tech.title(), str(count))

    console.print(table)


def display_commands_list(commands: list[dict], technology: str) -> None:
    """Display commands for a technology."""
    table = Table(title=f"{technology.title()} Commands", border_style="cyan")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Command", style="white")
    table.add_column("Risk", justify="center")

    for i, cmd in enumerate(commands, 1):
        risk = cmd.get("risk", "safe")
        risk_display = {"safe": "🟢", "warning": "🟡", "dangerous": "🔴"}.get(risk, "🟢")
        table.add_row(str(i), cmd.get("name", ""), cmd.get("command", ""), risk_display)

    console.print(table)


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"\n  ✗ {message}\n", style="red bold")


def display_low_confidence_help(technologies: list[str]) -> None:
    """Display help when confidence is low."""
    console.print("\n  I couldn't confidently identify the command.\n", style="warning")
    console.print("  Try specifying the technology:\n", style="dim")
    for tech in technologies:
        console.print(f"    alchemyai {tech} ", style="dim")
    console.print()
