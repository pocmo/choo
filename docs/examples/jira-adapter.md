# Jira Adapter for Choo

The Jira adapter enables choo to orchestrate AI agents using Atlassian Jira as the ticket system backend.

## Prerequisites

1. **Install ACLI** - Atlassian's official command-line tool:
   ```bash
   # See https://developer.atlassian.com/cloud/acli/
   # Installation instructions vary by platform
   ```

2. **Authenticate with Jira**:
   ```bash
   # Interactive authentication (recommended)
   acli jira auth login --web
   
   # OR with API token
   acli jira auth login --site "mycompany.atlassian.net" --email "user@example.com" --token
   
   # Verify authentication
   acli jira auth status
   ```

3. **Create agent label** in your Jira project (e.g., "agent-ready")

## Configuration

### Minimal Configuration

```yaml
ticket_system:
  type: jira-acli
  config:
    project: PROJ              # Your Jira project key
    agent_label: agent-ready   # Label to mark agent-eligible issues

stations:
  - backlog
  - done

trains:
  - name: dev-agent
    from_station: backlog
    to_station: done
    cli: claude
```

### Complete Configuration

```yaml
ticket_system:
  type: jira-acli
  config:
    project: PROJ
    agent_label: agent-ready
    claim_method: assignee     # Optional: "assignee" (default) or "label"
    
    # Optional: Map choo station names to Jira status names
    status_mapping:
      backlog: "To Do"
      in-progress: "In Progress"
      done: "Done"

stations:
  - backlog
  - in-progress
  - done

trains:
  - name: code-writer
    from_station: backlog
    to_station: in-progress
    cli: claude
```

See [jira-config.yml](jira-config.yml) for a complete example.

## Configuration Options

### Required Fields

- **`project`** (string): Jira project key (e.g., "PROJ", "TEAM")
- **`agent_label`** (string): Label used to mark issues ready for agents

### Optional Fields

- **`claim_method`** (string): How agents claim work
  - `"assignee"` (default): Assign issue to agent user (@me)
  - `"label"`: Add "in-progress" label to issue

- **`status_mapping`** (dict): Map choo station names to Jira status names
  - Useful when your Jira statuses have different names than your stations
  - Example: `backlog: "To Do"` maps station "backlog" to status "To Do"

## How It Works

### Workflow Stages (Stations)

Choo stations map directly to Jira issue statuses:
- Station "backlog" → Jira status "Backlog" (or use `status_mapping` to customize)
- Station "done" → Jira status "Done"

### Agent Work Filtering

Agents only see issues that match ALL of:
1. **Project**: Issue belongs to configured project
2. **Status**: Issue status matches agent's `from_station`
3. **Label**: Issue has the `agent_label` label
4. **Unclaimed**: Issue is not already assigned (if using assignee claim method)

This allows humans and agents to coexist in the same Jira statuses!

### Example Workflow

1. **Human** creates Jira issue with status "Backlog"
2. **Human** adds "agent-ready" label when ready for AI
3. **Agent** sees issue in `choo work list` (matches project + status + label + unclaimed)
4. **Agent** runs `choo work start PROJ-123` (assigns to @me)
5. **Agent** works on the issue
6. **Agent** runs `choo work complete PROJ-123` (transitions to next status)
7. **Human** reviews and continues workflow

## JQL Query Examples

When listing issues, choo builds JQL queries like:

```jql
project = PROJ AND status = "Backlog" AND labels = "agent-ready" AND assignee is EMPTY
```

## Commands

Agents interact with Jira via choo commands:

```bash
# List available work at a station
choo work list backlog

# View issue details
choo work read PROJ-123

# Claim an issue
choo work start PROJ-123

# Complete work (move to next station)
choo work complete PROJ-123

# Add a comment
choo work comment PROJ-123 "Implemented feature X"
```

## Claim Methods

### Assignee (Default)

Issues are claimed by assigning them to the agent user:
- **Claim**: `acli jira workitem assign --key PROJ-123 --assignee @me`
- **Unclaim**: `acli jira workitem assign --key PROJ-123 --remove-assignee`
- **Filter**: JQL includes `AND assignee is EMPTY`

### Label

Issues are claimed by adding an "in-progress" label:
- **Claim**: `acli jira workitem edit --key PROJ-123 --add-label in-progress`
- **Unclaim**: `acli jira workitem edit --key PROJ-123 --remove-label in-progress`
- **Filter**: JQL includes `AND labels not in ("in-progress")`

## Status Mapping

If your Jira statuses don't match your station names, use `status_mapping`:

```yaml
ticket_system:
  type: jira-acli
  config:
    project: PROJ
    agent_label: agent-ready
    status_mapping:
      todo: "To Do"           # Station "todo" → Status "To Do"
      wip: "In Progress"      # Station "wip" → Status "In Progress"
      qa: "QA Testing"        # Station "qa" → Status "QA Testing"
      shipped: "Completed"    # Station "shipped" → Status "Completed"

stations:
  - todo
  - wip
  - qa
  - shipped
```

## Troubleshooting

### Authentication Issues

```bash
# Check authentication status
acli jira auth status

# Re-authenticate
acli jira auth login --web
```

### Test ACLI Connection

```bash
# List projects
acli jira project list --json

# Search for issues
acli jira workitem search --jql "project = MYPROJ" --limit 5

# View specific issue
acli jira workitem view PROJ-123
```

### Invalid Transitions

If an agent tries to transition an issue to an invalid status for its issue type:
- ACLI will return an error
- Check your Jira workflow configuration
- Ensure the transition is valid for the issue type (Story, Bug, Task, etc.)

### No Issues Found

If `choo work list` shows no issues:
1. Verify issues exist with the correct status in Jira
2. Confirm issues have the `agent_label` label
3. Check issues are not already assigned (if using assignee claim method)
4. Test the JQL query directly in Jira:
   ```jql
   project = MYPROJ AND status = "Backlog" AND labels = "agent-ready" AND assignee is EMPTY
   ```

## Limitations & Future Enhancements

### Current Limitations (Phase 1)

- Single Jira site support only (uses active ACLI session)
- Single project per configuration
- Label-based filtering only (no component/JQL filters)
- No workflow transition validation

### Future Enhancements (Phase 2+)

- Multi-site support with automatic switching
- Multi-project support
- Advanced filtering (components, custom JQL)
- Sprint integration
- Epic/hierarchy support
- Workflow transition validation
- Custom field mapping

## Architecture

The Jira adapter follows choo's adapter pattern:
- **Adapter**: `JiraAcliAdapter` - Implements `TicketSystemAdapter` interface
- **CLI Integration**: Uses `acli jira` commands via subprocess
- **Authentication**: Relies on ACLI's persistent authentication
- **State**: Stateless - Jira is the source of truth

## See Also

- [ACLI Documentation](https://developer.atlassian.com/cloud/acli/)
- [Jira JQL Reference](https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- [Example Configuration](jira-config.yml)
