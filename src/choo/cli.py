"""Main CLI entry point for choo."""

import click
from rich.console import Console

from choo import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="choo")
@click.pass_context
def main(ctx):
    """Choo - An agent orchestration framework for AI-powered development workflows.

    🚂 Orchestrate AI agents through customizable development workflows.
    """
    ctx.ensure_object(dict)


@main.command()
def init():
    """Initialize a new choo project in the current directory."""
    console.print("[yellow]choo init - not yet implemented[/yellow]")


@main.command()
def choo():
    """Start the orchestration engine."""
    console.print("[yellow]choo choo - not yet implemented[/yellow]")


@main.group()
def work():
    """Commands for agents to interact with work items."""
    pass


@work.command("list")
def work_list():
    """List available work items."""
    console.print("[yellow]choo work list - not yet implemented[/yellow]")


@work.command("read")
@click.argument("issue_id")
def work_read(issue_id):
    """Read full issue details."""
    console.print(f"[yellow]choo work read {issue_id} - not yet implemented[/yellow]")


@work.command("start")
@click.argument("issue_id")
def work_start(issue_id):
    """Start working on an issue (claims it)."""
    console.print(f"[yellow]choo work start {issue_id} - not yet implemented[/yellow]")


@work.command("complete")
@click.argument("issue_id")
def work_complete(issue_id):
    """Complete work on an issue (moves it to next station)."""
    console.print(f"[yellow]choo work complete {issue_id} - not yet implemented[/yellow]")


@work.command("blocked")
@click.argument("issue_id")
@click.option("--reason", required=True, help="Reason for blocking")
def work_blocked(issue_id, reason):
    """Mark an issue as blocked."""
    console.print(f"[yellow]choo work blocked {issue_id} --reason '{reason}' - not yet implemented[/yellow]")


@work.command("comment")
@click.argument("issue_id")
@click.argument("message")
def work_comment(issue_id, message):
    """Add a comment to an issue."""
    console.print(f"[yellow]choo work comment {issue_id} '{message}' - not yet implemented[/yellow]")


if __name__ == "__main__":
    main()
