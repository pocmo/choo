"""GitHub Projects adapter using gh CLI."""

import json
import subprocess
from typing import Any

from choo.adapters.base import IssueNotFoundError, TicketSystemAdapter
from choo.models import Issue


class GitHubProjectAdapter(TicketSystemAdapter):
    """Adapter for GitHub Projects V2 using the gh CLI."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the GitHub adapter.

        Args:
            config: Configuration dictionary with owner, repo, project_number
        """
        self.owner = config["owner"]
        self.repo = config["repo"]
        # Convert project_number to string for gh commands
        self.project_number = str(config["project_number"])
        self.claim_method = config.get("claim_method", "assignee")

        # Fetch the actual project ID (PVT_...) needed for item-edit
        self.project_id = self._get_project_id()

        # Fetch the Status field information for moving items
        self.status_field_id, self.status_options = self._get_status_field_info()

    def _get_project_id(self) -> str:
        """Get the actual project ID (not just the number).

        Returns:
            The project ID string (e.g., "PVT_...")

        Raises:
            RuntimeError: If project cannot be found
        """
        output = self._run_gh(
            ["project", "list", "--owner", self.owner, "--format", "json", "--limit", "100"]
        )
        data = json.loads(output)

        for project in data.get("projects", []):
            if str(project.get("number")) == self.project_number:
                return project.get("id")

        raise RuntimeError(
            f"Project {self.project_number} not found for owner {self.owner}"
        )

    def _get_status_field_info(self) -> tuple[str, dict[str, str]]:
        """Get the Status field ID and its option mappings.

        Returns:
            Tuple of (field_id, {option_name: option_id} dict)

        Raises:
            RuntimeError: If Status field cannot be found
        """
        output = self._run_gh(
            [
                "project",
                "field-list",
                self.project_number,
                "--owner",
                self.owner,
                "--format",
                "json",
            ]
        )
        data = json.loads(output)

        for field in data.get("fields", []):
            if field.get("name") == "Status":
                field_id = field.get("id")
                options = {}
                for option in field.get("options", []):
                    options[option.get("name")] = option.get("id")
                return field_id, options

        raise RuntimeError("Status field not found in project")

    def _run_gh(self, args: list[str]) -> str:
        """Run a gh CLI command and return output.

        Args:
            args: Command arguments to pass to gh

        Returns:
            Command output as string

        Raises:
            RuntimeError: If gh command fails
        """
        cmd = ["gh"] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"gh command failed: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"gh command timed out: {' '.join(cmd)}") from e

    def _parse_item(self, item_data: dict[str, Any]) -> Issue:
        """Parse a GitHub Project item into an Issue object.

        Args:
            item_data: Raw item data from gh API

        Returns:
            Issue object
        """
        # Extract content (the actual issue/PR)
        content = item_data.get("content", {})

        # Get status from the top-level status field
        status = item_data.get("status", "Unknown")

        # Get assignees from top-level (project item includes this)
        assignees = item_data.get("assignees", [])
        assignee = assignees[0] if assignees else None

        return Issue(
            id=str(content.get("number", "")),
            title=content.get("title", ""),
            body=content.get("body"),
            station=status,
            url=content.get("url"),
            assignee=assignee,
            labels=[label.get("name", "") for label in content.get("labels", [])],
        )

    def _get_assignee(self, content: dict[str, Any]) -> str | None:
        """Extract assignee from issue content.

        Args:
            content: Issue content data

        Returns:
            Assignee username or None
        """
        assignees = content.get("assignees", [])
        if assignees and len(assignees) > 0:
            return assignees[0].get("login")
        return None

    def list_stations(self) -> list[str]:
        """List all available workflow stations in the project.

        Returns:
            List of unique station names from all items
        """
        output = self._run_gh(
            [
                "project",
                "item-list",
                self.project_number,
                "--owner",
                self.owner,
                "--format",
                "json",
                "--limit",
                "100",
            ]
        )

        items = json.loads(output)
        stations = set()

        for item in items.get("items", []):
            status = item.get("status")
            if status:
                stations.add(status)

        return sorted(stations)

    def list_issues(self, station: str) -> list[Issue]:
        """List all issues at a specific workflow station.

        Args:
            station: The workflow stage (status field value)

        Returns:
            List of issues at that station
        """
        # Use gh project item-list to get items
        # We'll need to filter by status field value
        output = self._run_gh(
            [
                "project",
                "item-list",
                self.project_number,
                "--owner",
                self.owner,
                "--format",
                "json",
                "--limit",
                "100",
            ]
        )

        items = json.loads(output)
        issues = []

        for item in items.get("items", []):
            try:
                issue = self._parse_item(item)
                # Filter by station
                if issue.station == station:
                    issues.append(issue)
            except Exception as e:
                # Skip items that can't be parsed
                continue

        return issues

    def get_issue(self, issue_id: str) -> Issue:
        """Get full details of a specific issue.

        Args:
            issue_id: The issue number

        Returns:
            Issue object with full details

        Raises:
            IssueNotFoundError: If issue doesn't exist
        """
        try:
            # Get issue details from the repo
            output = self._run_gh(
                [
                    "issue",
                    "view",
                    issue_id,
                    "--repo",
                    f"{self.owner}/{self.repo}",
                    "--json",
                    "number,title,body,url,assignees,labels",
                ]
            )
            issue_data = json.loads(output)

            # Now get the project status
            # We need to query the project to find this item's status
            project_output = self._run_gh(
                [
                    "project",
                    "item-list",
                    self.project_number,
                    "--owner",
                    self.owner,
                    "--format",
                    "json",
                    "--limit",
                    "100",
                ]
            )
            project_data = json.loads(project_output)

            # Find the item in the project
            station = "Unknown"
            for item in project_data.get("items", []):
                content = item.get("content", {})
                if str(content.get("number")) == str(issue_id):
                    station = item.get("status", "Unknown")
                    break

            return Issue(
                id=str(issue_data.get("number", "")),
                title=issue_data.get("title", ""),
                body=issue_data.get("body"),
                station=station,
                url=issue_data.get("url"),
                assignee=self._get_assignee(issue_data),
                labels=[label.get("name", "") for label in issue_data.get("labels", [])],
            )

        except RuntimeError as e:
            if "Could not resolve to an Issue" in str(e):
                raise IssueNotFoundError(f"Issue {issue_id} not found")
            raise

    def claim_issue(self, issue_id: str) -> None:
        """Claim an issue by assigning it to the current user.

        Args:
            issue_id: The issue number
        """
        if self.claim_method == "assignee":
            # Assign to @me (current authenticated user)
            self._run_gh(
                [
                    "issue",
                    "edit",
                    issue_id,
                    "--repo",
                    f"{self.owner}/{self.repo}",
                    "--add-assignee",
                    "@me",
                ]
            )
        elif self.claim_method == "label":
            # Add "in-progress" label
            self._run_gh(
                [
                    "issue",
                    "edit",
                    issue_id,
                    "--repo",
                    f"{self.owner}/{self.repo}",
                    "--add-label",
                    "in-progress",
                ]
            )

    def unclaim_issue(self, issue_id: str) -> None:
        """Unclaim an issue by removing assignment.

        Args:
            issue_id: The issue number
        """
        if self.claim_method == "assignee":
            # Remove @me from assignees
            self._run_gh(
                [
                    "issue",
                    "edit",
                    issue_id,
                    "--repo",
                    f"{self.owner}/{self.repo}",
                    "--remove-assignee",
                    "@me",
                ]
            )
        elif self.claim_method == "label":
            # Remove "in-progress" label
            self._run_gh(
                [
                    "issue",
                    "edit",
                    issue_id,
                    "--repo",
                    f"{self.owner}/{self.repo}",
                    "--remove-label",
                    "in-progress",
                ]
            )

    def move_issue(self, issue_id: str, to_station: str) -> None:
        """Move an issue to a different workflow station.

        Args:
            issue_id: The issue number
            to_station: The target status value
        """
        # First, we need to find the item ID in the project
        project_output = self._run_gh(
            [
                "project",
                "item-list",
                self.project_number,
                "--owner",
                self.owner,
                "--format",
                "json",
                "--limit",
                "100",
            ]
        )
        project_data = json.loads(project_output)

        # Find the project item ID for this issue
        item_id = None
        for item in project_data.get("items", []):
            content = item.get("content", {})
            if str(content.get("number")) == str(issue_id):
                item_id = item.get("id")
                break

        if not item_id:
            raise RuntimeError(f"Issue {issue_id} not found in project")

        # Get the option ID for the target station
        if to_station not in self.status_options:
            available = ", ".join(self.status_options.keys())
            raise RuntimeError(
                f"Invalid station '{to_station}'. Available: {available}"
            )

        option_id = self.status_options[to_station]

        # Edit the Status field using the actual IDs
        self._run_gh(
            [
                "project",
                "item-edit",
                "--id",
                item_id,
                "--project-id",
                self.project_id,
                "--field-id",
                self.status_field_id,
                "--single-select-option-id",
                option_id,
            ]
        )

    def get_comments(self, issue_id: str) -> list[dict[str, str]]:
        """Get all comments for an issue.

        Args:
            issue_id: The issue number

        Returns:
            List of comments with author, body, and created_at
        """
        output = self._run_gh(
            [
                "issue",
                "view",
                issue_id,
                "--repo",
                f"{self.owner}/{self.repo}",
                "--json",
                "comments",
            ]
        )
        data = json.loads(output)
        comments = []

        for comment in data.get("comments", []):
            comments.append(
                {
                    "author": comment.get("author", {}).get("login", "unknown"),
                    "body": comment.get("body", ""),
                    "created_at": comment.get("createdAt", ""),
                }
            )

        return comments

    def add_comment(self, issue_id: str, message: str) -> None:
        """Add a comment to an issue.

        Args:
            issue_id: The issue number
            message: The comment text
        """
        self._run_gh(
            [
                "issue",
                "comment",
                issue_id,
                "--repo",
                f"{self.owner}/{self.repo}",
                "--body",
                message,
            ]
        )
