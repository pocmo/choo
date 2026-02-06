"""Abstract base class for ticket system adapters."""

from abc import ABC, abstractmethod

from choo.models import Issue


class TicketSystemAdapter(ABC):
    """Abstract interface for ticket system backends."""

    @abstractmethod
    def list_stations(self) -> list[str]:
        """List all available workflow stations in the project.

        Returns:
            List of station names (status values)
        """
        pass

    @abstractmethod
    def list_issues(self, station: str) -> list[Issue]:
        """List all issues at a specific workflow station.

        Args:
            station: The workflow stage (e.g., "Backlog", "In Progress")

        Returns:
            List of issues at that station
        """
        pass

    @abstractmethod
    def get_issue(self, issue_id: str) -> Issue:
        """Get full details of a specific issue.

        Args:
            issue_id: The issue identifier

        Returns:
            Issue object with full details

        Raises:
            IssueNotFoundError: If issue doesn't exist
        """
        pass

    @abstractmethod
    def claim_issue(self, issue_id: str) -> None:
        """Claim an issue (mark as being worked on).

        Args:
            issue_id: The issue identifier
        """
        pass

    @abstractmethod
    def unclaim_issue(self, issue_id: str) -> None:
        """Unclaim an issue (release it back to available work).

        Args:
            issue_id: The issue identifier
        """
        pass

    @abstractmethod
    def move_issue(self, issue_id: str, to_station: str) -> None:
        """Move an issue to a different workflow station.

        Args:
            issue_id: The issue identifier
            to_station: The target workflow stage
        """
        pass

    @abstractmethod
    def get_comments(self, issue_id: str) -> list[dict[str, str]]:
        """Get all comments for an issue.

        Args:
            issue_id: The issue identifier

        Returns:
            List of comments, each with 'author', 'body', and 'created_at' keys
        """
        pass

    @abstractmethod
    def add_comment(self, issue_id: str, message: str) -> None:
        """Add a comment to an issue.

        Args:
            issue_id: The issue identifier
            message: The comment text
        """
        pass


class IssueNotFoundError(Exception):
    """Raised when an issue cannot be found."""

    pass
