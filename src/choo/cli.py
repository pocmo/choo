"""Main CLI entry point for choo."""

import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from choo import __version__
from choo.adapters.base import IssueNotFoundError
from choo.adapters.factory import AdapterError, create_adapter
from choo.agent_adapters.factory import AgentAdapterError, create_agent_adapter
from choo.config import ChooConfig, ConfigError
from choo.prompts import PromptError, load_combined_prompt

console = Console()


def load_config() -> ChooConfig:
    """Load choo configuration from .choo/config.yml.

    Returns:
        Loaded configuration

    Raises:
        click.ClickException: If config loading fails
    """
    try:
        return ChooConfig.load()
    except ConfigError as e:
        raise click.ClickException(str(e))


@click.group()
@click.version_option(version=__version__, prog_name="choo")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed command execution and rate limits")
@click.pass_context
def main(ctx, verbose):
    """Choo - An agent orchestration framework for AI-powered development workflows.

    🚂 Orchestrate AI agents through customizable development workflows.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
def init():
    """Initialize a new choo project in the current directory."""
    console.print("[yellow]choo init - not yet implemented[/yellow]")


@main.command()
def choo():
    """Start the orchestration engine."""
    console.print("[yellow]choo choo - not yet implemented[/yellow]")


@main.group()
def train():
    """Commands for managing trains."""
    pass


@train.command("run")
@click.argument("train_name", required=False)
@click.pass_context
def train_run(ctx, train_name):
    """Run a train once.

    TRAIN_NAME: Name of the train to run. If not provided, uses
    CHOO_TRAIN_NAME environment variable.
    """
    try:
        # Get train name from argument or environment variable
        if train_name is None:
            train_name = os.environ.get("CHOO_TRAIN_NAME")
            if train_name is None:
                raise click.ClickException(
                    "No train name specified. Provide a train name argument "
                    "or set CHOO_TRAIN_NAME environment variable."
                )
            console.print(f"[dim]Using train from CHOO_TRAIN_NAME: {train_name}[/dim]\n")

        # Load configuration
        config = load_config()

        # Find the train configuration
        train_config = None
        for t in config.trains:
            if t.name == train_name:
                train_config = t
                break

        if train_config is None:
            available = ", ".join(t.name for t in config.trains)
            raise click.ClickException(
                f"Train '{train_name}' not found in configuration. "
                f"Available trains: {available}"
            )

        # Find project root (where .choo directory is)
        choo_dir = Path(".choo")
        if not choo_dir.exists():
            raise click.ClickException(
                "No .choo directory found in current directory. "
                "Run this command from the project root."
            )
        project_root = Path.cwd()

        # Load and combine prompts
        console.print(f"[cyan]Loading prompts for train '{train_name}'...[/cyan]")
        try:
            combined_prompt = load_combined_prompt(train_name, choo_dir)
        except PromptError as e:
            raise click.ClickException(str(e))

        # Set up environment variables for the agent
        agent_env = {
            "CHOO_TRAIN_NAME": train_config.name,
            "CHOO_FROM_STATION": train_config.from_station,
            "CHOO_TO_STATION": train_config.to_station,
        }

        # Create agent adapter
        try:
            agent_adapter = create_agent_adapter(train_config)
        except AgentAdapterError as e:
            raise click.ClickException(str(e))

        # Run the agent
        console.print(f"[green]Starting train '{train_name}' ({train_config.cli})...[/green]")
        console.print(f"[dim]From station: {train_config.from_station}[/dim]")
        console.print(f"[dim]To station: {train_config.to_station}[/dim]")
        console.print()
        
        # Add visual separator before agent output
        console.rule(f"[cyan]Agent Output[/cyan]")
        console.print()

        verbose = ctx.obj.get("verbose", False)
        exit_code = agent_adapter.run(
            system_prompt=combined_prompt,
            working_dir=project_root,
            env=agent_env,
            verbose=verbose,
        )

        # Add visual separator after agent output
        console.print()
        console.rule(f"[cyan]End Agent Output[/cyan]")
        console.print()

        if exit_code == 0:
            console.print(f"[green]✓ Train '{train_name}' completed successfully[/green]")
        else:
            console.print(f"[red]✗ Train '{train_name}' exited with code {exit_code}[/red]")
            raise SystemExit(exit_code)

    except (ConfigError, AgentAdapterError) as e:
        raise click.ClickException(str(e))


@main.group()
def work():
    """Commands for agents to interact with work items."""
    pass


@work.command("list")
@click.argument("station", required=False)
@click.pass_context
def work_list(ctx, station):
    """List available work items at a station.

    STATION: The workflow stage to list issues from (e.g., "Backlog", "Todo").
             If not provided, uses CHOO_FROM_STATION environment variable.
    """
    try:
        # If no station provided, try environment variable
        if station is None:
            station = os.environ.get("CHOO_FROM_STATION")
            if station is None:
                raise click.ClickException(
                    "No station specified. Provide a station argument or set CHOO_FROM_STATION environment variable."
                )
            console.print(f"[dim]Using station from CHOO_FROM_STATION: {station}[/dim]\n")

        config = load_config()
        adapter = create_adapter(config.ticket_system, verbose=ctx.obj.get("verbose", False))

        # Get all available stations
        available_stations = adapter.list_stations()

        # Check if the requested station exists
        if station not in available_stations:
            console.print(f"[red]✗[/red] Station '{station}' not found in project")
            if available_stations:
                console.print("\n[bold]Available stations:[/bold]")
                for s in available_stations:
                    console.print(f"  • {s}")
            else:
                console.print("[yellow]No stations found in project (project may be empty)[/yellow]")
            return

        # List issues at the station
        issues = adapter.list_issues(station)

        if not issues:
            console.print(f"[yellow]No issues found at station: {station}[/yellow]")
            console.print("[dim](Station exists but contains no issues)[/dim]")
            return

        # Create a table to display issues
        table = Table(title=f"Issues at {station}")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Assignee", style="green")
        table.add_column("Labels", style="magenta")

        for issue in issues:
            table.add_row(
                issue.id,
                issue.title[:60] + "..." if len(issue.title) > 60 else issue.title,
                issue.assignee or "-",
                ", ".join(issue.labels) if issue.labels else "-",
            )

        console.print(table)
        console.print(f"\n[green]Found {len(issues)} issue(s)[/green]")

    except (ConfigError, AdapterError) as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to list issues: {e}")


@work.command("read")
@click.argument("issue_id")
@click.pass_context
def work_read(ctx, issue_id):
    """Read full issue details.

    ISSUE_ID: The issue number to read
    """
    try:
        config = load_config()
        adapter = create_adapter(config.ticket_system, verbose=ctx.obj.get("verbose", False))
        issue = adapter.get_issue(issue_id)

        # Display issue details
        console.print(f"\n[bold cyan]Issue #{issue.id}[/bold cyan]")
        console.print(f"[bold]Title:[/bold] {issue.title}")
        console.print(f"[bold]Station:[/bold] {issue.station}")
        console.print(f"[bold]Assignee:[/bold] {issue.assignee or 'Unassigned'}")
        if issue.labels:
            console.print(f"[bold]Labels:[/bold] {', '.join(issue.labels)}")
        if issue.url:
            console.print(f"[bold]URL:[/bold] {issue.url}")

        if issue.body:
            console.print("\n[bold]Description:[/bold]")
            console.print(issue.body)

        # Display comments
        comments = adapter.get_comments(issue_id)
        if comments:
            console.print(f"\n[bold]Comments ({len(comments)}):[/bold]")
            for i, comment in enumerate(comments, 1):
                console.print(f"\n[cyan]Comment #{i} by {comment['author']}[/cyan]")
                if comment.get("created_at"):
                    console.print(f"[dim]{comment['created_at']}[/dim]")
                console.print(comment["body"])
        else:
            console.print("\n[dim]No comments[/dim]")

    except IssueNotFoundError as e:
        raise click.ClickException(str(e))
    except (ConfigError, AdapterError) as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to read issue: {e}")


@work.command("start")
@click.argument("issue_id")
@click.pass_context
def work_start(ctx, issue_id):
    """Start working on an issue (claims it).

    ISSUE_ID: The issue number to claim
    """
    try:
        config = load_config()
        adapter = create_adapter(config.ticket_system, verbose=ctx.obj.get("verbose", False))
        adapter.claim_issue(issue_id)
        console.print(f"[green]✓[/green] Claimed issue #{issue_id}")

    except (ConfigError, AdapterError) as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to claim issue: {e}")


@work.command("complete")
@click.argument("issue_id")
@click.argument("to_station", required=False)
@click.pass_context
def work_complete(ctx, issue_id, to_station):
    """Complete work on an issue (moves it to next station).

    ISSUE_ID: The issue number to complete
    TO_STATION: The target workflow stage (e.g., "Done", "Review").
                If not provided, uses CHOO_TO_STATION environment variable.
    """
    try:
        # If no station provided, try environment variable
        if to_station is None:
            to_station = os.environ.get("CHOO_TO_STATION")
            if to_station is None:
                raise click.ClickException(
                    "No station specified. Provide a TO_STATION argument or set CHOO_TO_STATION environment variable."
                )
            console.print(f"[dim]Using station from CHOO_TO_STATION: {to_station}[/dim]\n")

        config = load_config()
        adapter = create_adapter(config.ticket_system, verbose=ctx.obj.get("verbose", False))
        adapter.move_issue(issue_id, to_station)
        console.print(f"[green]✓[/green] Moved issue #{issue_id} to {to_station}")

    except (ConfigError, AdapterError) as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to complete issue: {e}")


@work.command("blocked")
@click.argument("issue_id")
@click.option("--reason", required=True, help="Reason for blocking")
def work_blocked(issue_id, reason):
    """Mark an issue as blocked."""
    console.print(f"[yellow]choo work blocked {issue_id} --reason '{reason}' - not yet implemented[/yellow]")


@work.command("comment")
@click.argument("issue_id")
@click.argument("message")
@click.pass_context
def work_comment(ctx, issue_id, message):
    """Add a comment to an issue.

    ISSUE_ID: The issue number to comment on
    MESSAGE: The comment text
    """
    try:
        config = load_config()
        adapter = create_adapter(config.ticket_system, verbose=ctx.obj.get("verbose", False))
        adapter.add_comment(issue_id, message)
        console.print(f"[green]✓[/green] Added comment to issue #{issue_id}")

    except (ConfigError, AdapterError) as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to add comment: {e}")


if __name__ == "__main__":
    main()
