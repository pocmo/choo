"""Ticket system adapters for choo."""

from choo.adapters.base import TicketSystemAdapter
from choo.adapters.github import GitHubProjectAdapter

__all__ = ["TicketSystemAdapter", "GitHubProjectAdapter"]
