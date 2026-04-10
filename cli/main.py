"""SkillForge CLI — Typer-based command-line interface."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from skillforge.base import SkillInput

console = Console()
app = typer.Typer(
    name="skillforge",
    help="SkillForge — Real code. Standard I/O. No database. Just workers.",
    add_completion=False,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("skillforge.cli")

# ── Paths ────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
PIPELINES_ROOT = REPO_ROOT / "pipelines"


# ── Commands ─────────────────────────────────────────────────────────

@app.command()
def run(
    skill_id: str = typer.Argument(..., help="Skill identifier, e.g. mediscreen.triage"),
    input: Path = typer.Option(..., "--input", "-i", help="Path to input JSON file"),
) -> None:
    """Run a single skill with the given JSON input."""
    from skillforge.registry import load_skill

    if not input.exists():
        console.print(f"[red]Error:[/red] Input file not found: {input}")
        raise typer.Exit(1)

    raw = json.loads(input.read_text(encoding="utf-8"))
    skill_input = SkillInput(data=raw.get("data", raw), metadata=raw.get("metadata", {}))

    try:
        worker = load_skill(skill_id)
    except KeyError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    errors = worker.validate(skill_input)
    if errors:
        console.print("[yellow]Validation warnings:[/yellow]")
        for e in errors:
            console.print(f"  • {e}")

    result = worker.run(skill_input)
    _print_output(result)


@app.command("list")
def list_skills(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category prefix"),
) -> None:
    """List all registered skills."""
    from skillforge.registry import list_skills as _list

    skills = _list(category=category)
    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title="SkillForge Skills")
    table.add_column("Skill ID", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Title")

    for s in skills:
        table.add_row(s.get("skill_id", "?"), s.get("version", "?"), s.get("title", ""))

    console.print(table)


@app.command()
def info(
    skill_id: str = typer.Argument(..., help="Skill identifier"),
) -> None:
    """Show detailed info about a skill."""
    from skillforge.registry import load_skill

    try:
        worker = load_skill(skill_id)
    except KeyError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    desc = worker.describe()
    console.print_json(json.dumps(desc, indent=2, ensure_ascii=False))

    skill_dir = worker._skill_dir()
    if skill_dir:
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            console.print("\n[bold]─── SKILL.md ───[/bold]\n")
            console.print(skill_md.read_text(encoding="utf-8"))


@app.command()
def test(
    skill_id: str = typer.Argument(..., help="Skill identifier to test"),
) -> None:
    """Run pytest for a specific skill."""
    from skillforge.registry import load_skill

    try:
        worker = load_skill(skill_id)
    except KeyError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    test_file = worker._skill_dir() / "test.py" if worker._skill_dir() else None
    if test_file is None or not test_file.exists():
        console.print(f"[red]No test.py found for {skill_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Running tests for {skill_id}...[/cyan]\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        cwd=str(REPO_ROOT),
    )
    raise typer.Exit(result.returncode)


@app.command()
def pipe(
    pipeline: str = typer.Argument(..., help="Pipeline name (without .yaml)"),
    input: Path = typer.Option(..., "--input", "-i", help="Path to input JSON file"),
) -> None:
    """Run a multi-skill pipeline."""
    from skillforge.orchestrator import load_pipeline, run_pipeline

    yaml_path = PIPELINES_ROOT / f"{pipeline}.yaml"
    if not yaml_path.exists():
        console.print(f"[red]Error:[/red] Pipeline file not found: {yaml_path}")
        raise typer.Exit(1)

    if not input.exists():
        console.print(f"[red]Error:[/red] Input file not found: {input}")
        raise typer.Exit(1)

    raw = json.loads(input.read_text(encoding="utf-8"))
    skill_input = SkillInput(data=raw.get("data", raw), metadata=raw.get("metadata", {}))

    definition = load_pipeline(yaml_path)
    console.print(f"[cyan]Running pipeline:[/cyan] {definition.name} ({definition.mode.value})\n")

    results = run_pipeline(definition, skill_input)
    for i, r in enumerate(results, 1):
        console.print(f"[bold]── Step {i} ──[/bold]")
        _print_output(r)


@app.command()
def create(
    description: str = typer.Argument(..., help="Natural-language description of the skill to generate"),
    category: str = typer.Option("auto", "--category", "-c", help="Target category folder"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print generated files without saving"),
) -> None:
    """Auto-generate a new skill from a description using Claude API."""
    import os

    try:
        import anthropic
    except ImportError:
        console.print("[red]Error:[/red] Install the create extra: pip install 'skillforge[create]'")
        raise typer.Exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        console.print("[red]Error:[/red] Set ANTHROPIC_API_KEY environment variable.")
        raise typer.Exit(1)

    from cli._creator import generate_skill

    files = generate_skill(description, category, api_key)

    if dry_run:
        for fname, content in files.items():
            console.print(f"\n[bold cyan]── {fname} ──[/bold cyan]")
            console.print(content)
    else:
        slug = files.get("_slug", description.lower().replace(" ", "-")[:30])
        target = SKILLS_ROOT / category / slug
        target.mkdir(parents=True, exist_ok=True)
        for fname, content in files.items():
            if fname.startswith("_"):
                continue
            (target / fname).write_text(content, encoding="utf-8")
            console.print(f"[green]✓[/green] Wrote {target / fname}")

        console.print(f"\n[cyan]Running tests for new skill...[/cyan]")
        test_file = target / "test.py"
        if test_file.exists():
            subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                cwd=str(REPO_ROOT),
            )


# ── helpers ──────────────────────────────────────────────────────────

def _print_output(output) -> None:
    """Pretty-print a SkillOutput."""
    status = "[green]✓ SUCCESS[/green]" if output.success else "[red]✗ FAILED[/red]"
    console.print(status)
    if output.error:
        console.print(f"  [red]Error:[/red] {output.error}")
    if output.data:
        console.print_json(json.dumps(output.data, indent=2, ensure_ascii=False))
    if output.metadata:
        console.print(f"  [dim]metadata: {output.metadata}[/dim]")


if __name__ == "__main__":
    app()

