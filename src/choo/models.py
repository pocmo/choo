"""Data models for choo."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Issue:
    """Represents a work item (issue/ticket)."""

    id: str
    title: str
    body: Optional[str]
    station: str  # Current workflow stage (e.g., "Backlog", "In Progress")
    url: Optional[str] = None
    assignee: Optional[str] = None
    labels: list[str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
