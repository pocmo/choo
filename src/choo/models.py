"""Data models for choo."""

from dataclasses import dataclass


@dataclass
class Issue:
    """Represents a work item (issue/ticket)."""

    id: str
    title: str
    body: str | None
    station: str  # Current workflow stage (e.g., "Backlog", "In Progress")
    url: str | None = None
    assignee: str | None = None
    labels: list[str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
