"""Factory for creating ticket system adapters."""

from choo.adapters.base import TicketSystemAdapter
from choo.adapters.github import GitHubProjectAdapter
from choo.config import TicketSystemConfig


class AdapterError(Exception):
    """Raised when adapter creation fails."""

    pass


def create_adapter(config: TicketSystemConfig) -> TicketSystemAdapter:
    """Create a ticket system adapter from configuration.

    Args:
        config: Ticket system configuration

    Returns:
        Initialized adapter instance

    Raises:
        AdapterError: If adapter type is unknown or creation fails
    """
    if config.type == "github-project-gh":
        return GitHubProjectAdapter(config.config)

    raise AdapterError(f"Unknown adapter type: {config.type}")
