# Architecture Principles & Decisions

This document records architectural decisions made for the choo project, the reasoning behind them, and open questions that still need resolution.

## Core Architectural Decisions

### 1. Choo is an Orchestrator, Not an Agent

**Decision**: Choo does not implement AI functionality. It orchestrates existing AI CLI tools.

**Reasoning**:
- Avoid rebuilding what exists (claude-code, opencode, etc.)
- Stay focused on workflow orchestration, not AI implementation
- Users can choose their preferred AI tools
- Simpler architecture - we're glue, not a platform

**Implications**:
- Must support configurable CLI tools with different interfaces
- System prompts tell agents how to use choo commands
- We don't manage LLM API keys or rate limits (tools do)

### 2. Ticket System as Source of Truth

**Decision**: Choo never stores ticket data. It reads from and writes to external ticket systems via adapters.

**Reasoning**:
- Users already have ticket systems they trust
- Avoid data synchronization problems
- Humans can interact naturally with their existing tools
- Simpler failure modes - if choo crashes, no state is lost

**Implications**:
- Adapters must handle all CRUD operations
- Performance depends on ticket system API/CLI speed
- No offline mode
- Must respect manual changes made by humans in ticket system

### 3. Adapter Architecture

**Decision**: Adapters use existing CLI tools (gh, jira, etc.) rather than direct API integration.

**Reasoning**:
- CLI tools handle auth, configuration, caching
- Users already have these tools configured
- Simpler to implement - just command execution and parsing
- Easier to add new adapters (just config + parsing)

**Implications**:
- Users must have relevant CLI tools installed
- Performance bounded by CLI tool speed
- Output parsing may be fragile if CLIs change
- Need good error messages when CLIs fail

**Adapter Interface**:
```
- ListTickets(station) → []Ticket
- ReadTicket(id) → TicketDetail
- MoveTicket(id, toStation) → error
- AddComment(id, comment) → error
- SetStatus(id, status) → error
```

### 4. One Issue Per Agent Instance

**Decision**: Each agent process works on exactly one issue, then exits. Choo restarts the agent with fresh context.

**Reasoning**:
- Clean isolation - no state pollution between issues
- Natural error recovery - crashed agent just gets restarted
- Simpler context management for LLMs
- Clear completion signal - process exit
- Easier to reason about and debug

**Implications**:
- Higher overhead (process spawn per issue)
- Agent startup time matters
- System prompts must be concise (repeated for each issue)
- Orchestrator must handle rapid process cycling

### 5. Long-Running Orchestrator Process

**Decision**: `choo choo` starts a long-running process that manages multiple agent instances.

**Reasoning**:
- User types one command and everything runs
- Central place for logging and monitoring
- Can maintain configured instance counts
- Handles agent lifecycle automatically

**Implications**:
- Need robust process management
- Must handle graceful shutdown
- Need health checking and restart logic
- Log aggregation from multiple agents

### 6. Agents Use Environment Variables for Identity

**Decision**: Train identity (name, from_station, to_station) passed via environment variables like `CHOO_TRAIN_NAME`.

**Reasoning**:
- Agents don't need to know workflow details
- Commands become simple: `choo work list` (no station args)
- Works across different agent CLIs
- Standard unix pattern

**Implementation**:
When spawning an agent, choo sets:
```bash
CHOO_TRAIN_NAME=code-writer
CHOO_CONFIG_PATH=/path/to/.choo/config.yml
```

Agent commands look up train config using the environment variable.

### 7. Claim-Based Work Assignment

**Decision**: Issues remain in their station while being worked on. Agents "claim" them using ticket system features (assignee, labels) to prevent concurrent work.

**Reasoning**:
- Simpler model - only two stations per train (`from_station` and `to_station`)
- Uses native ticket system concepts (assignee already exists)
- Humans can easily see claimed vs. waiting work in the same column
- No need for extra "in-progress" columns unless desired
- Adapter-specific implementation (GitHub uses assignee, others might use labels)

**Configuration**:
```yaml
ticket_system:
  adapter: github-gh
  config:
    claim_method: assignee  # or label:in-progress

trains:
  - name: code-writer
    from_station: backlog
    to_station: testing  # moves here on complete
```

**Implementation**:
- `choo work list` filters out claimed issues
- `choo work start <id>` claims the issue
- `choo work complete <id>` unclaims and moves to `to_station`

### 8. Train Metaphor

**Decision**: Use train/station/passenger terminology for high-level concepts, but use agent/issue/ticket for technical details.

**Metaphor**:
- **Stations** = workflow stages (columns in ticket board)
- **Trains** = agent instances that move work between stations
- **Passengers** = issues/tasks from the ticket system

**Application**:
- Config uses train/station terms (memorable, intuitive)
- Documentation introduces concepts via metaphor
- Technical details use practical terms (agent, issue, claim)
- Don't force metaphor where it sounds awkward ("when a train starts work on a passenger" → "when an agent starts working on an issue")

**Reasoning**:
- Metaphor helps understanding the architecture
- Makes it memorable and distinctive
- Fun branding with "choo choo" command
- But clarity trumps cuteness in technical contexts

### 9. Ticket Ordering and Selection

**Decision**:
- `choo work list` returns ordered list (respects ticket system order)
- Agent sees just IDs and titles (lightweight)
- Agent chooses which to work on
- System prompt suggests "prefer top ones"

**Reasoning**:
- Respect existing prioritization in ticket system
- Let AI use judgment (may skip tickets it can't handle)
- Efficient - don't fetch full details until needed
- Users can reorder in their ticket system naturally

**Flow**:
1. `choo work list` → ordered list with id + title
2. Agent chooses (typically first/top one)
3. `choo work read <id>` → fetch full details
4. `choo work start <id>` → claim it

### 10. Self-Healing Through Restart

**Decision**: When agents fail, crash, or timeout, choo restarts fresh instance. Ticket becomes available again.

**Reasoning**:
- Simple recovery mechanism
- Stateless agents mean restarts are safe
- Previous agent's comments provide context
- No complex retry logic needed

**Mechanism**:
- Agent crashes → ticket unlocks (returns to from_station or stays visible)
- New agent sees ticket in list
- Can read previous attempt's comments
- Decides whether to retry or skip

### 11. Human Intervention Design

**Decision**:
- Stations without trains are implicitly human-only
- Humans use ticket system UI (not forced to use choo)
- Humans can intervene anywhere, anytime
- Choo observes and respects manual changes

**Reasoning**:
- Don't force tools on humans
- Ticket system UI is often better for humans than CLI
- Flexibility - humans can jump in when needed
- Choo isn't gatekeeping or controlling - just facilitating

**Examples**:
- Human moves ticket manually in GitHub → choo sees new state
- Human comments on ticket → agent sees comment
- Human reorders backlog → `choo work list` reflects new order

### 12. Progressive Disclosure

**Decision**: Simple things should be simple, complex things should be possible.

**Application**:
- Default config works for basic case (one train, linear workflow)
- Power users can configure multiple trains, complex workflows, filters
- Documentation shows simple examples first
- Advanced features discoverable but not required

**Minimal Config**:
```yaml
ticket_system:
  adapter: github-gh
  config:
    repo: owner/repo
    project: 123

stations: [backlog, done]

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
```

---

## Design Patterns

### Delegation Over Implementation
When facing a choice between implementing something or delegating to existing tools, prefer delegation:
- Ticket operations → CLI tools (gh, jira)
- AI work → External AI CLIs (claude, opencode)
- Authentication → CLI tool's auth
- Caching → CLI tool's caching

### Fail Fast, Fail Clear
- Validate configuration on startup
- Clear error messages (not just stack traces)
- Don't start orchestrator if config is invalid
- Guide users to fix issues

### Observable System
- Log all state transitions (ticket moves, agent starts/exits)
- Capture agent stdout/stderr
- Structured logs for easy parsing
- Make it easy to understand what choo is doing

---

## Open Questions

These are unresolved design questions that need decisions:

### 1. Train Configuration Details

**Question**: What else should be configurable per train?
- Max retries before giving up on a ticket?
- Filters (labels, assignees, etc.)?
- Ticket selection strategy (random, round-robin vs. top-to-bottom)?
- Resource limits (CPU, memory)?
- Different behavior for blocked tickets?

**Impact**: Affects config schema and feature complexity

---

### 2. Blocked Ticket Handling

**Question**: When an agent calls `choo work blocked <id>`, what happens?
- Move to special "blocked" station?
- Add label/tag in ticket system?
- Remove from available work but stay in current station?
- Require explicit configuration of blocked handling?

**Impact**: Adapter implementation, config schema

---

### 3. Concurrent Work Prevention

**Question**: How do we prevent two agents from working on the same issue?

**Decision**: Use ticket system's native claim mechanisms (assignee, labels, etc.). Adapter-specific implementation.

**Implementation**:
- GitHub adapter: Uses assignee field (assign to bot user account)
- Alternative: Use labels like `in-progress` or `claimed-by-X`
- Configurable via `claim_method` in ticket system config

**How it works**:
- `choo work list` filters out claimed issues
- `choo work start <id>` atomically claims the issue
- If claim fails (race condition), command fails and agent picks another
- Timeout/crash unclaims the issue automatically or via orchestrator cleanup

**Status**: RESOLVED - using claim-based approach

**Impact**: Adapter implementation must support claiming/unclaiming

---

### 4. Multiple Trains Per Transition

**Question**: Can multiple trains work on the same from_station → to_station route?

**Example**:
```yaml
trains:
  - name: backend-dev
    from_station: backlog
    to_station: testing
    cli: claude
    instances: 2

  - name: frontend-dev
    from_station: backlog
    to_station: testing
    cli: opencode
    instances: 1
```

Would need filters to distinguish which tickets each train picks up (e.g., labels).

**Current thinking**: Support this, require filters to disambiguate.

**Impact**: Ticket selection logic, config validation

---

### 5. Adapter Discovery & Configuration

**Question**: How do users specify adapters?

**Current thinking**:
```yaml
ticket_system:
  adapter: github-gh  # built-in adapter name
  config:
    repo: owner/repo
    project: 123
```

**But what about**:
- Custom adapters (user-provided)?
- Adapter-specific configuration schema validation?
- Listing available adapters?
- Adapter versioning?

**Impact**: Plugin architecture, extensibility

---

### 6. Agent CLI Interface Variability

**Question**: Different AI CLIs have different interfaces. How do we pass system prompts?

**Examples**:
- claude: `claude --system-prompt-file prompt.md`
- openai: might use `--instructions`
- Custom tools: could be anything

**Options**:
A. Train config specifies the full command template:
```yaml
trains:
  - name: dev
    command: "claude --system-prompt-file {prompt_file}"
```

B. Built-in "CLI profiles" for common tools:
```yaml
trains:
  - name: dev
    cli: claude  # choo knows how to invoke claude
    prompt_file: prompts/dev.md
```

C. Mix - built-in profiles with override capability

**Current thinking**: Option C for flexibility

**Impact**: Train spawning logic, config schema

---

### 7. Logging & Observability

**Question**: What should choo log? Where should logs go?

**Needs**:
- Orchestrator activity (train starts, exits, restarts)
- Agent stdout/stderr (capture for debugging)
- Ticket state transitions
- Errors and warnings

**Questions**:
- Separate log file per train instance?
- Aggregated log with train ID tags?
- Structured JSON logs vs. human-readable?
- Log rotation strategy?
- Real-time log streaming to terminal?

**Impact**: Developer experience, debugging capability

---

### 8. Testing Individual Trains

**Question**: How does a user test a single train without running the full orchestrator?

**Desired**: Something like `choo train run code-writer` that:
- Spawns one instance of the train
- Runs once (picks one ticket, works, exits)
- Useful for debugging train configuration and prompts

**Implementation**: Separate command or flag on `choo choo`?

**Impact**: CLI design, developer experience

---

### 9. Configuration Validation

**Question**: What should we validate at config load time?

**Should check**:
- All referenced stations exist
- from_station, to_station are valid station names
- Prompt files exist
- Adapter config is valid for that adapter type
- No circular dependencies?
- CLI executables exist and are executable?

**How strict**?
- Fail on missing executable or just warn (might not be installed yet)?
- Validate adapter config against schema?

**Impact**: User experience, error handling

---

### 10. Initial Priority / Scope

**Question**: What's the MVP? What should we build first vs. later?

**MVP candidates**:
1. Core: Config parsing, orchestrator, train management
2. GitHub adapter (github-gh using `gh` CLI)
3. Basic work commands (list, read, start, complete, comment)
4. Simple error recovery (restart on exit)
5. Init command with templates

**Later**:
- Additional adapters (Jira, Linear, etc.)
- Advanced filtering and ticket selection
- Blocked ticket handling
- Metrics and monitoring
- Distributed orchestrator

**Impact**: Development roadmap, what agents should focus on

---

### 11. Language Choice

**Question**: What language should we implement choo in?

**Current thinking**: Go
- Single binary distribution (easy for users)
- Excellent CLI tooling (cobra)
- Strong concurrency (goroutines for multiple trains)
- Good process management (os/exec)
- Fast compile, small binaries

**Alternatives**:
- Python: Easier for some, but distribution harder
- Rust: More complex, but great for this use case
- Node.js: Good CLI tools, but runtime dependency

**Impact**: Everything

---

### 12. Config File Location & Discovery

**Question**: Where does `.choo/config.yml` live and how do we find it?

**Options**:
A. Must be in current directory (like `.git/`)
B. Walk up directory tree to find it (like git does)
C. Can specify with `--config` flag
D. All of the above

**Current thinking**: B & C (walk up + override flag)

**Impact**: User experience, how choo gets invoked

---

### 13. Graceful Shutdown

**Question**: What happens when user hits Ctrl-C on `choo choo`?

**Should**:
- Send SIGTERM to all agent processes
- Wait for in-progress work to complete (with timeout)?
- Or kill immediately?
- Save state about interrupted tickets?

**Current thinking**:
- SIGTERM to agents, 30s grace period
- If agents don't exit, SIGKILL
- Tickets remain in their current station
- Next `choo choo` will pick them up

**Impact**: Orchestrator implementation, user experience

---

### 14. Agent Environment

**Question**: What environment variables and context should we provide to agents?

**Definite**:
- `CHOO_TRAIN_NAME=code-writer`
- `CHOO_CONFIG_PATH=/path/to/.choo/config.yml`

**Maybe**:
- `CHOO_TICKET_ID` - if we auto-assign next ticket
- `CHOO_WORKING_DIR` - project root
- `CHOO_LOG_FILE` - where to write logs

**Current thinking**: Minimal - just train name and config path. Let agents discover what they need.

**Impact**: Agent implementation, system prompt design

---

### 15. Error States

**Question**: How do we handle persistent failures?

**Scenarios**:
- Ticket fails 3 times in a row (different agents)
- Adapter CLI is broken (gh auth expired)
- Agent CLI is missing
- Network failure to ticket system

**Should we**:
- Track retry counts per ticket?
- Auto-mark tickets as blocked after N failures?
- Pause train when adapter fails repeatedly?
- Alert user somehow?

**Impact**: Reliability, user experience

---

### 16. Metadata & Extensions

**Question**: Should we support custom metadata or extensions?

**Use cases**:
- Track agent attempts per ticket
- Store timing metrics
- Custom labels or tags
- Integration with other tools

**Where would this live**?
- In ticket system (as comments or custom fields)?
- Local file (`.choo/metadata.json`)?
- Nowhere - keep it simple?

**Current thinking**: Keep simple initially. If needed, use ticket comments with structured format.

**Impact**: Scope creep vs. extensibility

---

### 17. Config Schema Version

**Question**: Should config file have a version field?

```yaml
version: 1
ticket_system:
  ...
```

**Reasoning**: Allows breaking changes to config format in future.

**Impact**: Future-proofing vs. complexity

---

### 18. Multiple Projects

**Question**: Can one choo instance manage multiple projects/repos?

**Current thinking**: No. One `.choo/` per project. Run separate `choo choo` for each.

**Impact**: Scope, complexity

---

### 19. Dry Run Mode

**Question**: Should we support `choo choo --dry-run` that simulates without actually moving tickets?

**Use case**: Testing configuration without affecting real tickets.

**Impact**: Testing UX, implementation complexity

---

### 20. Security & Credentials

**Question**: How do we handle credentials for ticket systems and AI CLIs?

**Current thinking**:
- Delegate entirely to CLI tools (gh, claude handle their own auth)
- Support environment variable interpolation in config:
```yaml
ticket_system:
  config:
    auth_token: ${GITHUB_TOKEN}
```

**Questions**:
- Should choo validate credentials before starting?
- How to handle expired credentials?

**Impact**: User experience, security

---

## Decision Log

Record of when key decisions were made:

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-02-04 | Pure orchestration architecture | Focus on coordination, not implementation |
| 2026-02-04 | One ticket per agent instance | Clean isolation and error recovery |
| 2026-02-04 | Adapter pattern using CLI tools | Leverage existing tools, simpler implementation |
| 2026-02-04 | Long-running orchestrator process | Better UX, central management |
| 2026-02-04 | Train environment variables | Clean abstraction for agents |
| 2026-02-04 | Claim-based work assignment | Simpler than working_station, uses native ticket features |
| 2026-02-04 | Metaphor usage guidelines | Use train/station/passenger for concepts, agent/issue for technical details |

---

## Principles Summary

When making decisions, prioritize:

1. **Simplicity** - Can this be simpler?
2. **Delegation** - Can an existing tool do this?
3. **Flexibility** - Does this work for multiple use cases?
4. **Clarity** - Will users understand this?
5. **Reliability** - What happens when it fails?

The best architecture is one that solves the problem without being clever.
