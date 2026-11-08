"""Interactive fzf-style command browser for AlchemyCLI AI.

Provides a two-level browsable interface:
  Level 1 → Pick a technology (kubernetes, docker, git, …)
  Level 2 → Browse/search commands within that technology

Similar to zi (zoxide + fzf). Requires fzf to be installed.
Falls back to prompt_toolkit selection if fzf is unavailable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from alchemy_ml.inference import InferenceEngine
    from alchemy_ml.models import Command

console = Console()

# ── fzf detection ────────────────────────────────────────────

FZF_BIN = shutil.which("fzf")


def _has_fzf() -> bool:
    return FZF_BIN is not None


# ── Formatting helpers ───────────────────────────────────────

RISK_ICON = {"safe": "🟢", "warning": "🟡", "dangerous": "🔴"}


def _format_tech_line(tech: str, count: int, max_name: int = 14) -> str:
    """Format a technology line for fzf display."""
    return f"{tech.ljust(max_name)}  ({count} commands)"


def _format_command_line(cmd: "Command") -> str:
    """Format a command line for fzf display.

    Layout: ICON  name  ││  command  ││  description (truncated)
    Using ││ as a delimiter so fzf --delimiter can split fields.
    """
    icon = RISK_ICON.get(cmd.risk.value, "🟢")
    desc = cmd.description.strip().replace("\n", " ")
    if len(desc) > 60:
        desc = desc[:57] + "..."
    return f"{icon}  {cmd.name}  ││  {cmd.command}  ││  {desc}"


def _build_preview_text(cmd: "Command") -> str:
    """Build a rich preview string for a command."""
    lines = [
        f"╭──────────────────────────────────────────────────╮",
        f"│  {cmd.name}",
        f"╰──────────────────────────────────────────────────╯",
        "",
        f"  Technology : {cmd.technology}",
        f"  Category   : {cmd.category.replace('_', ' ').title()}",
        f"  Risk       : {RISK_ICON.get(cmd.risk.value, '')} {cmd.risk.value.upper()}",
        "",
        f"  Command:",
        f"    $ {cmd.command}",
        "",
        f"  Description:",
    ]
    # Wrap description to ~70 chars
    desc = cmd.description.strip()
    words = desc.split()
    line = "    "
    for w in words:
        if len(line) + len(w) + 1 > 72:
            lines.append(line)
            line = "    " + w
        else:
            line += (" " if len(line) > 4 else "") + w
    if line.strip():
        lines.append(line)

    if cmd.tags:
        lines.extend(["", f"  Tags: {', '.join(cmd.tags)}"])

    if cmd.aliases:
        lines.extend(["", f"  Aliases: {', '.join(cmd.aliases)}"])

    if cmd.examples:
        lines.append("")
        lines.append("  Examples:")
        for ex in cmd.examples[:3]:
            if "query" in ex:
                lines.append(f"    ? {ex['query']}")
            if "output" in ex:
                lines.append(f"      → {ex['output']}")

    if cmd.doc_url:
        lines.extend(["", f"  Docs: {cmd.doc_url}"])

    return "\n".join(lines)


# ── fzf runners ──────────────────────────────────────────────

def _run_fzf(
    items: list[str],
    *,
    prompt: str = "> ",
    header: str = "",
    preview_cmd: str | None = None,
    preview_data: dict[str, str] | None = None,
    multi: bool = False,
    ansi: bool = True,
) -> str | None:
    """Run fzf with given items and return the selected line (or None)."""
    args = [FZF_BIN, "--prompt", prompt]

    if header:
        args.extend(["--header", header])
    if ansi:
        args.append("--ansi")
    if multi:
        args.append("--multi")

    # Preview via a temp file if we have structured data
    preview_file = None
    if preview_data:
        import tempfile
        preview_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="alchemy_browse_"
        )
        json.dump(preview_data, preview_file)
        preview_file.close()
        # Use python to look up the key from the fzf selection
        args.extend([
            "--preview",
            f"python3 -c \""
            f"import json,sys; "
            f"d=json.load(open('{preview_file.name}')); "
            f"key={{}}; "
            f"sel=sys.argv[1].split('  ')[0].strip() if len(sys.argv)>1 else ''; "
            f"[print(v) for k,v in d.items() if k.startswith(sel)]"
            f"\" {{1}}",
            "--preview-window", "right:50%:wrap",
        ])
    elif preview_cmd:
        args.extend(["--preview", preview_cmd, "--preview-window", "right:50%:wrap"])

    input_text = "\n".join(items)

    try:
        result = subprocess.run(
            args,
            input=input_text,
            capture_output=True,
            text=True,
        )
        if preview_file:
            os.unlink(preview_file.name)

        if result.returncode == 0:
            return result.stdout.strip()
        # 130 = user pressed Esc/Ctrl-C
        return None
    except FileNotFoundError:
        return None


def _run_fzf_with_file_preview(
    items: list[str],
    preview_map: dict[str, str],
    *,
    prompt: str = "> ",
    header: str = "",
) -> str | None:
    """Run fzf using a temp preview-data file for rich previews."""
    import tempfile

    preview_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, prefix="alchemy_browse_"
    )
    json.dump(preview_map, preview_file)
    preview_file.close()

    # Shell script that extracts the command name (field before first ││)
    # and looks it up in the JSON preview file
    preview_script = (
        f'python3 -Ic "'
        f"import json,sys;"
        f"d=json.load(open(\\'{preview_file.name}\\'));"
        f"line=\\' \\'.join(sys.argv[1:]);"
        f"name=line.split(\\'  ││\\')[0].strip();"
        f"name=name.lstrip(\\'🟢🟡🔴 \\').strip();"
        f"print(d.get(name, \\'No preview\\'))"
        f'" {{..}}'
    )

    args = [
        FZF_BIN,
        "--prompt", prompt,
        "--ansi",
        "--preview", preview_script,
        "--preview-window", "right:55%:wrap",
    ]
    if header:
        args.extend(["--header", header])

    input_text = "\n".join(items)

    try:
        result = subprocess.run(args, input=input_text, capture_output=True, text=True)
        os.unlink(preview_file.name)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, OSError):
        try:
            os.unlink(preview_file.name)
        except OSError:
            pass
        return None


# ── Fallback (no fzf) ───────────────────────────────────────

def _select_prompt_toolkit(items: list[str], prompt_text: str) -> str | None:
    """Fallback selector using prompt_toolkit completions."""
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter

    completer = WordCompleter(items, sentence=True)
    try:
        selected = pt_prompt(prompt_text, completer=completer).strip()
        return selected if selected else None
    except (EOFError, KeyboardInterrupt):
        return None


# ── Main browse flow ─────────────────────────────────────────

def _pick_technology(engine: "InferenceEngine") -> str | None:
    """Level 1: pick a technology."""
    techs: dict[str, int] = {}
    for t in engine.get_all_technologies():
        techs[t] = len(engine.get_commands_by_technology(t))

    if not techs:
        console.print("  No technologies loaded.\n", style="warning")
        return None

    max_name = max(len(t) for t in techs)
    lines = [_format_tech_line(t, c, max_name) for t, c in sorted(techs.items())]

    if _has_fzf():
        selected = _run_fzf(
            lines,
            prompt="Technology ❯ ",
            header="  ↑/↓ Navigate  ⏎ Select  Esc Cancel",
        )
    else:
        console.print("\n  Available technologies:\n", style="bold")
        for i, line in enumerate(lines, 1):
            console.print(f"    {i}. {line}")
        console.print()
        selected = _select_prompt_toolkit(
            [t for t in sorted(techs)],
            "  Select technology: ",
        )

    if not selected:
        return None

    # Extract technology name (first word before whitespace)
    return selected.split()[0].strip().lower()


def _pick_command(engine: "InferenceEngine", technology: str) -> "Command | None":
    """Level 2: pick a command within a technology."""
    commands = engine.get_commands_by_technology(technology)
    if not commands:
        console.print(f"  No commands for {technology}.\n", style="warning")
        return None

    # Build display lines and preview map
    lines: list[str] = []
    preview_map: dict[str, str] = {}
    cmd_by_name: dict[str, "Command"] = {}

    for cmd in sorted(commands, key=lambda c: c.name):
        line = _format_command_line(cmd)
        lines.append(line)
        preview_map[cmd.name] = _build_preview_text(cmd)
        cmd_by_name[cmd.name] = cmd

    if _has_fzf():
        header_text = (
            f"  {technology.upper()} — {len(commands)} commands  │  "
            "↑/↓ Navigate  ⏎ Select  Esc Back"
        )
        selected = _run_fzf_with_file_preview(
            lines,
            preview_map,
            prompt=f"{technology} ❯ ",
            header=header_text,
        )
    else:
        console.print(f"\n  {technology.title()} commands:\n", style="bold")
        for i, line in enumerate(lines, 1):
            console.print(f"    {i}. {line}")
        console.print()
        selected = _select_prompt_toolkit(
            [cmd.name for cmd in commands],
            "  Select command: ",
        )

    if not selected:
        return None

    # Extract command name from the selected line
    # Format: "ICON  name  ││  command  ││  desc"
    parts = selected.split("  ││  ")
    if parts:
        name = parts[0].strip().lstrip("🟢🟡🔴 ").strip()
        return cmd_by_name.get(name)

    return None


def _show_command_detail(cmd: "Command") -> str | None:
    """Show command detail and offer actions."""
    console.print()
    console.print(Panel(
        Text(cmd.command, style="bold white"),
        title=f"{cmd.technology.title()} › {cmd.name}",
        subtitle=f"{RISK_ICON.get(cmd.risk.value, '')} {cmd.risk.value.upper()}",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print(f"  {cmd.description}\n", style="dim")

    if cmd.tags:
        console.print(f"  Tags: {', '.join(cmd.tags)}", style="dim")
    if cmd.doc_url:
        console.print(f"  Docs: {cmd.doc_url}", style="dim underline")
    console.print()

    # Action menu
    actions = ["copy", "back", "exit"]
    if _has_fzf():
        action = _run_fzf(
            ["📋 Copy to clipboard", "⬅  Back to commands", "❌ Exit"],
            prompt="Action ❯ ",
            header="  What would you like to do?",
        )
        if action and "Copy" in action:
            return "copy"
        elif action and "Back" in action:
            return "back"
        return "exit"
    else:
        console.print("  [1] Copy to clipboard  [2] Back  [3] Exit\n", style="dim")
        try:
            choice = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"
        if choice == "1":
            return "copy"
        elif choice == "2":
            return "back"
        return "exit"


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    # macOS fallback
    if sys.platform == "darwin":
        try:
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        except Exception:
            pass

    return False


# ── Public entry point ───────────────────────────────────────

def run_browse(engine: "InferenceEngine") -> None:
    """Run the interactive fzf-style command browser.

    Flow:
      1. Pick a technology
      2. Browse commands (with preview pane)
      3. View detail / copy / go back
      4. Loop until exit
    """
    if not _has_fzf():
        console.print(
            "\n  [dim]fzf not found. Install it for the best experience:[/dim]"
            "\n    brew install fzf  [dim]# macOS[/dim]"
            "\n    apt install fzf   [dim]# Ubuntu/Debian[/dim]"
            "\n  [dim]Falling back to basic selection...[/dim]\n",
        )

    while True:
        tech = _pick_technology(engine)
        if tech is None:
            break

        while True:
            cmd = _pick_command(engine, tech)
            if cmd is None:
                break  # back to technology picker

            action = _show_command_detail(cmd)
            if action == "copy":
                if _copy_to_clipboard(cmd.command):
                    console.print("  ✓ Copied to clipboard!\n", style="green")
                else:
                    console.print(f"  Command: {cmd.command}\n", style="bold")
                    console.print("  (Could not copy — manually select above)\n", style="dim")
            elif action == "back":
                continue
            else:
                return

    console.print("  Goodbye!\n", style="dim")
