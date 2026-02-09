"""Factory for creating agent adapters."""

from choo.agent_adapters.base import AgentAdapter
from choo.agent_adapters.claude import ClaudeAdapter
from choo.agent_adapters.copilot import CopilotAdapter
from choo.config import TrainConfig


class AgentAdapterError(Exception):
    """Raised when agent adapter creation fails."""

    pass


def create_agent_adapter(train_config: TrainConfig) -> AgentAdapter:
    """Create an agent adapter for the given train configuration.

    Args:
        train_config: Train configuration including CLI name and optional binary path

    Returns:
        AgentAdapter instance for the specified CLI

    Raises:
        AgentAdapterError: If the CLI type is not supported
    """
    cli_name = train_config.cli
    binary = train_config.binary

    if cli_name == "claude":
        # Claude doesn't support custom binary yet
        return ClaudeAdapter()
    elif cli_name == "copilot":
        return CopilotAdapter(binary=binary or "copilot")
    else:
        raise AgentAdapterError(
            f"Unsupported agent CLI: {cli_name}. Currently supported: claude, copilot"
        )

