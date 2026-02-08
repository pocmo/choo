"""Factory for creating agent adapters."""

from choo.agent_adapters.base import AgentAdapter
from choo.agent_adapters.claude import ClaudeAdapter


class AgentAdapterError(Exception):
    """Raised when agent adapter creation fails."""

    pass


def create_agent_adapter(cli_name: str) -> AgentAdapter:
    """Create an agent adapter for the given CLI tool.

    Args:
        cli_name: Name of the CLI tool (e.g., "claude", "opencode")

    Returns:
        AgentAdapter instance for the specified CLI

    Raises:
        AgentAdapterError: If the CLI type is not supported
    """
    if cli_name == "claude":
        return ClaudeAdapter()
    else:
        raise AgentAdapterError(
            f"Unsupported agent CLI: {cli_name}. Currently supported: claude"
        )
