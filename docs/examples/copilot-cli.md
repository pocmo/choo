# GitHub Copilot CLI Support

Choo supports using GitHub Copilot as an AI agent for processing work items. This guide covers how to configure and use the Copilot CLI with Choo.

## Prerequisites

1. **Install GitHub Copilot CLI**: Follow the [official installation guide](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
2. **Authenticate**: Run `copilot auth login` to authenticate with GitHub
3. **Verify installation**: Run `copilot --version` to confirm it's installed and working

## Basic Configuration

To use GitHub Copilot CLI as your agent, set the `cli` field to `copilot` in your train configuration:

```yaml
ticket_system:
  type: github-project-gh
  config:
    owner: myorg
    repo: myrepo
    project_number: 1

stations:
  - backlog
  - in-progress
  - done

trains:
  - name: copilot-agent
    from_station: backlog
    to_station: in-progress
    cli: copilot
```

## Custom Binary Path

If Copilot CLI is installed in a non-standard location, or you want to use a specific version, you can specify the binary path:

```yaml
trains:
  - name: copilot-agent
    from_station: backlog
    to_station: in-progress
    cli: copilot
    binary: /opt/homebrew/bin/copilot  # Custom path to copilot binary
```

This is useful when:
- Copilot is installed via Homebrew at a specific path
- You have multiple versions of Copilot and want to use a specific one
- The copilot binary is not in your system PATH

## How It Works

When you run a train with the Copilot CLI:

1. Choo passes the system prompt via the `GITHUB_COPILOT_SYSTEM_PROMPT` environment variable
2. Copilot runs in your working directory with access to your codebase
3. Standard environment variables are available:
   - `CHOO_TRAIN_NAME`: Name of the train
   - `CHOO_FROM_STATION`: Source station
   - `CHOO_TO_STATION`: Destination station
   - Plus any custom environment variables you configure

## Running a Train

To start a Copilot-powered train:

```bash
choo train start copilot-agent
```

Copilot will:
1. Pick up the work item from the `from_station`
2. Analyze the issue description and requirements
3. Work on the task interactively
4. Move the item to `to_station` when complete

## Environment Variables

Choo sets the following environment variables that Copilot can access:

- `GITHUB_COPILOT_SYSTEM_PROMPT`: The combined system + train prompts
- `CHOO_TRAIN_NAME`: Name of the current train
- `CHOO_FROM_STATION`: The station where work items are picked up
- `CHOO_TO_STATION`: The station where completed items are moved

## Customizing Prompts

You can customize how Copilot behaves by creating prompt files:

**`.choo/prompts/system.md`** - Global system prompt for all trains:
```markdown
You are an AI coding assistant working on a software project.
Your job is to complete tasks assigned to you through the ticket system.
Always write tests for your changes and ensure existing tests pass.
```

**`.choo/prompts/train-copilot-agent.md`** - Train-specific instructions:
```markdown
This train handles bug fixes in the backend API.

Process:
1. Read the issue description carefully
2. Reproduce the bug if possible
3. Fix the bug with minimal changes
4. Add regression tests
5. Update documentation if needed
```

## Comparison with Claude

| Feature | Claude | Copilot |
|---------|--------|---------|
| Custom binary path | ❌ Not yet supported | ✅ Supported via `binary` config |
| System prompt | ✅ Via CLI args | ✅ Via environment variable |
| Interactive mode | ✅ Yes | ✅ Yes |
| Built-in code execution | ✅ Yes | ✅ Yes |
| Authentication | API key | GitHub authentication |

## Troubleshooting

### Copilot not found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'copilot'`

**Solution**: Either install Copilot in your PATH, or specify the full path:
```yaml
trains:
  - cli: copilot
    binary: /path/to/copilot
```

### Authentication issues

**Error**: `Error: You must authenticate before using Copilot`

**Solution**: Run `copilot auth login` to authenticate with GitHub.

### System prompt not working

The Copilot CLI reads the system prompt from the `GITHUB_COPILOT_SYSTEM_PROMPT` environment variable. Choo automatically sets this for you. If your prompts aren't being applied:

1. Check that `.choo/prompts/system.md` exists
2. Verify the train-specific prompt file matches your train name
3. Use `--verbose` flag to see the environment variables being set:
   ```bash
   choo train start copilot-agent --verbose
   ```

### Different behavior than expected

Each CLI tool has its own personality and capabilities. If you notice Copilot behaving differently than Claude:
- This is expected - they are different AI systems
- Adjust your prompts specifically for Copilot's style
- Test your prompts with both CLIs if you use multiple

## Examples

### Development Train

A train that handles feature development:

```yaml
trains:
  - name: copilot-dev
    from_station: ready-for-dev
    to_station: in-review
    cli: copilot
    binary: /usr/local/bin/copilot
```

### Bug Fix Train

A specialized train for quick bug fixes:

```yaml
trains:
  - name: copilot-hotfix
    from_station: urgent-bugs
    to_station: needs-testing
    cli: copilot
```

### Multiple Trains with Different Tools

You can mix different CLI tools in the same project:

```yaml
trains:
  - name: claude-features
    from_station: backlog
    to_station: done
    cli: claude
    
  - name: copilot-bugs
    from_station: bug-queue
    to_station: fixed
    cli: copilot
    binary: /opt/homebrew/bin/copilot
```

## Best Practices

1. **Use train-specific prompts**: Create customized prompts for each train in `.choo/prompts/train-{name}.md`
2. **Test your setup**: Run `copilot --version` before configuring to ensure it's installed
3. **Start simple**: Begin with basic configuration, then add custom binary paths if needed
4. **Monitor behavior**: Use `--verbose` flag initially to see what's happening
5. **Iterate on prompts**: If Copilot isn't behaving as expected, refine your prompt files

## Advanced Configuration

### Using Copilot with Jira

```yaml
ticket_system:
  type: jira-acli
  config:
    project: MYPROJ
    agent_label: copilot-ready

trains:
  - name: copilot-agent
    from_station: To Do
    to_station: In Progress
    cli: copilot
```

### Multiple Copilot Trains

You can run multiple trains with the same CLI but different configurations:

```yaml
trains:
  - name: copilot-frontend
    from_station: frontend-backlog
    to_station: frontend-done
    cli: copilot
    
  - name: copilot-backend
    from_station: backend-backlog
    to_station: backend-done
    cli: copilot
```

Each train will have its own prompts in `.choo/prompts/train-copilot-frontend.md` and `.choo/prompts/train-copilot-backend.md`.

## See Also

- [Configuration Reference](../README.md#configuration)
- [GitHub Copilot CLI Documentation](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
- [Creating Custom Prompts](../README.md#prompts)
