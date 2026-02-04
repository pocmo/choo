# choo 🚂

An agent orchestration framework for AI-powered development workflows.

## What is choo?

Choo is a command-line tool that orchestrates AI agents through customizable development workflows. It acts as the glue between your ticket system (GitHub Issues, Jira, etc.) and AI coding assistants (Claude, OpenAI Codex, etc.), managing how work flows through different stages.

Think of it as a **lightweight workflow engine** where:
- **Stations** are workflow stages (Backlog, Testing, Review, Merge, etc.)
- **Trains** are AI agent instances that move work between stations
- **Passengers** are issues/tasks from your external ticket system

## Key Features

- **Ticket System Agnostic**: Works with GitHub Issues, Jira, or any ticket system via adapters
- **Agent Agnostic**: Orchestrates existing AI CLI tools (claude, opencode, etc.)
- **Flexible Workflows**: Define your own workflow stages and configure which agents handle what
- **Human-in-the-Loop**: Seamlessly mix AI automation with human review stages
- **Clean Separation**: Agents don't manage tickets directly - choo provides the abstraction layer

## Target Users

- **Individual developers** automating their personal projects
- **Development teams** setting up AI-powered development pipelines
- **Organizations** standardizing how AI agents contribute to codebases

## How It Works

### 1. Initialize a Project

```bash
choo init
```

This creates a `.choo/` directory with:
- `config.yml` - workflow and agent configuration
- `prompts/` - system prompts for each agent type

### 2. Configure Your Workflow

Edit `.choo/config.yml` to define stations (workflow stages) and trains (agents):

```yaml
ticket_system:
  adapter: github-gh
  config:
    repo: owner/repo
    project: 123
    claim_method: assignee  # How trains claim passengers (assignee, label, etc.)

stations:
  - draft
  - backlog
  - testing
  - review            # human-only station
  - merge
  - done

trains:
  - name: code-writer
    from_station: backlog
    to_station: testing
    cli: claude
    prompt_file: .choo/prompts/code-writer.md
    instances: 2
    timeout: 3600

  - name: test-runner
    from_station: testing
    to_station: merge
    cli: opencode
    prompt_file: .choo/prompts/test-runner.md
    instances: 1
```

### 3. Start the Orchestrator

```bash
choo choo
```

This starts the orchestration engine:
- Spawns configured agent instances (trains)
- Each agent picks up issues from their configured `from_station`
- Agents work on one issue at a time with fresh context
- When complete, issues move to `to_station`
- Process repeats continuously

### 4. Agents Use Choo Commands

Agents interact with issues through choo's CLI (commands are automatically available via environment):

```bash
# List available work (filtered by agent's from_station)
choo work list

# Read full issue details
choo work read <issue-id>

# Start working on an issue (claims it via assignee/label)
choo work start <issue-id>

# Complete work (moves issue to to_station)
choo work complete <issue-id>

# Mark issue as blocked
choo work blocked <issue-id> --reason "Missing API documentation"

# Add comment/handoff notes for next agent
choo work comment <issue-id> "Implemented feature X, tests passing"
```

## Architecture

```
┌─────────────────┐
│ Ticket System   │  (GitHub/Jira/etc)
│  (Source of     │
│   Truth)        │
└────────┬────────┘
         │
         │ Adapter (gh/jira CLI)
         │
    ┌────┴─────┐
    │   choo   │  Orchestrator
    │  Engine  │
    └────┬─────┘
         │
         │ Spawns & Manages
         │
    ┌────┴──────────────────┐
    │                       │
┌───┴────┐            ┌─────┴────┐
│ Train  │            │  Train   │
│ (Agent │            │  (Agent  │
│Instance│            │ Instance)│
└────────┘            └──────────┘
  Uses choo            Uses choo
  work commands        work commands
```

## Core Concepts

### Stations
In choo's metaphor, stations are workflow stages where issues wait. These map to columns in your ticket system (GitHub Project columns, Jira board columns, etc.). Some stations may have agents that pick up work, others are human-only review stages.

### Trains
In choo's metaphor, trains are agent instances that move passengers (issues) between stations (workflow stages). Each train:
- Picks up work from a specific `from_station`
- Claims the issue (via assignee, label, or other mechanism) to mark it as in-progress
- Moves it to a `to_station` when complete
- Works on one issue at a time with fresh context
- Runs an external AI CLI tool (claude, opencode, etc.)

Issues remain in their column while being worked on, but are marked as claimed so other agents don't pick them up. This allows humans viewing the ticket board to see both waiting and in-progress work in the same column.

### Passengers
In choo's metaphor, passengers represent issues or tasks from your external ticket system. Choo doesn't maintain its own copy of issues - it reads and updates them via adapters. Issues flow through workflow stages, moved by agents or humans.

### Adapters
Plugins that connect choo to different ticket systems. Adapters use existing CLI tools (like `gh` for GitHub) to fetch, update, and comment on issues. Each adapter implements a claim mechanism appropriate for that platform (GitHub uses assignee, others might use labels or custom fields). Choo ships with built-in adapters for common systems.

## Claiming Work

When an agent starts working on an issue, it needs to "claim" it to prevent other agents from picking up the same work. The claim mechanism is adapter-specific and configurable:

**GitHub (via assignee)**:
```yaml
ticket_system:
  adapter: github-gh
  config:
    claim_method: assignee
```
When `choo work start` is called, the issue gets assigned to a bot user. When viewing the board, assigned issues are in-transit, unassigned issues are waiting.

**GitHub (via label)**:
```yaml
ticket_system:
  adapter: github-gh
  config:
    claim_method: label:in-progress
```
Adds an `in-progress` label when claimed.

**Jira or other systems**:
Adapters implement claim mechanisms appropriate for their platform (assignee, status, custom fields, etc.).

The `choo work list` command automatically filters out claimed issues, showing only available work for that agent's configured station.

## Progressive Disclosure

Start simple:
- Define a basic linear workflow (backlog → done)
- Configure one train with sensible defaults
- Run `choo choo` locally

Scale up:
- Add specialized agents for different tasks (coding, testing, documentation)
- Configure parallel workflows and human review stages
- Add multiple agent instances for concurrent work
- Eventually run orchestrator as a service

## Example Use Cases

### Solo Developer Workflow
```yaml
stations: [backlog, done]
trains:
  - name: dev-agent
    from_station: backlog
    to_station: done
    cli: claude
    instances: 1
```

### Team Development Pipeline
```yaml
stations: [draft, backlog, testing, review, merge, done]
trains:
  - name: coder
    from_station: backlog
    to_station: testing
    instances: 2

  - name: tester
    from_station: testing
    to_station: review
    instances: 1
```
Human reviews happen at the `review` station, then manually move to `merge`. Issues at `testing` show as assigned while being worked on by the tester agent.

## Development Status

Choo is in early development. This README documents the vision and intended functionality.

## License

TBD
