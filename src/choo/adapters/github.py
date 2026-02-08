"""GitHub Projects adapter using gh CLI."""

import json
import subprocess
import sys
from datetime import datetime
from typing import Any

from choo.adapters.base import IssueNotFoundError, TicketSystemAdapter
from choo.models import Issue


class GitHubProjectAdapter(TicketSystemAdapter):
    """Adapter for GitHub Projects V2 using the gh CLI."""

    def __init__(self, config: dict[str, Any], verbose: bool = False):
        """Initialize the GitHub adapter.

        Args:
            config: Configuration dictionary with owner, repo, project_number
            verbose: If True, print gh commands and rate limit info
        """
        self.owner = config["owner"]
        self.repo = config["repo"]
        # Convert project_number to string for gh commands
        self.project_number = str(config["project_number"])
        self.claim_method = config.get("claim_method", "assignee")
        self.verbose = verbose

        # Lazy-loaded cached values
        self._project_id: str | None = None
        self._status_field_id: str | None = None
        self._status_options: dict[str, str] | None = None
        self._project_items_cache: list[dict[str, Any]] | None = None

    @property
    def project_id(self) -> str:
        """Get the actual project ID (not just the number), cached after first call.

        Returns:
            The project ID string (e.g., "PVT_...")

        Raises:
            RuntimeError: If project cannot be found
        """
        if self._project_id is None:
            output = self._run_gh(
                ["project", "list", "--owner", self.owner, "--format", "json", "--limit", "100"]
            )
            data = json.loads(output)

            for project in data.get("projects", []):
                if str(project.get("number")) == self.project_number:
                    self._project_id = project.get("id")
                    return self._project_id

            raise RuntimeError(
                f"Project {self.project_number} not found for owner {self.owner}"
            )
        return self._project_id

    def _ensure_status_field_info(self) -> None:
        """Ensure Status field ID and options are loaded, cached after first call.

        Raises:
            RuntimeError: If Status field cannot be found
        """
        if self._status_field_id is None or self._status_options is None:
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
                    self._status_field_id = field.get("id")
                    self._status_options = {}
                    for option in field.get("options", []):
                        self._status_options[option.get("name")] = option.get("id")
                    return

            raise RuntimeError("Status field not found in project")

    @property
    def status_field_id(self) -> str:
        """Get the Status field ID, cached after first call."""
        self._ensure_status_field_info()
        return self._status_field_id  # type: ignore

    @property
    def status_options(self) -> dict[str, str]:
        """Get the Status field options mapping, cached after first call."""
        self._ensure_status_field_info()
        return self._status_options  # type: ignore

    def _get_project_items(self) -> list[dict[str, Any]]:
        """Fetch all project items, cached for the adapter instance.

        Returns:
            List of project item dictionaries

        Note:
            This method caches the result on first call. All methods that need
            to access project items should use this instead of calling _run_gh directly.
        """
        if self._project_items_cache is None:
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
            data = json.loads(output)
            self._project_items_cache = data.get("items", [])

        return self._project_items_cache

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

        if self.verbose:
            # Print the command being executed
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] $ gh {' '.join(args)}", file=sys.stderr)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )

            if self.verbose:
                # Show rate limit info after the command
                self._print_rate_limit_info()

            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"gh command failed: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"gh command timed out: {' '.join(cmd)}") from e

    def _print_rate_limit_info(self) -> None:
        """Print current GraphQL API rate limit information."""
        try:
            result = subprocess.run(
                ["gh", "api", "rate_limit", "--jq", ".resources.graphql"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            data = json.loads(result.stdout)
            limit = data.get("limit", "?")
            remaining = data.get("remaining", "?")
            used = data.get("used", "?")
            reset_ts = data.get("reset", 0)

            # Convert reset timestamp to readable time
            if reset_ts:
                reset_time = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S")
            else:
                reset_time = "?"

            print(
                f"[Rate Limit] {remaining}/{limit} remaining (used: {used}, resets at {reset_time})",
                file=sys.stderr,
            )
        except Exception:
            # Silently ignore rate limit check failures
            pass

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
        items = self._get_project_items()
        stations = set()

        for item in items:
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
        items = self._get_project_items()
        issues = []

        for item in items:
            try:
                issue = self._parse_item(item)
                # Filter by station
                if issue.station == station:
                    issues.append(issue)
            except Exception:
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
            items = self._get_project_items()

            # Find the item in the project
            station = "Unknown"
            for item in items:
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
        items = self._get_project_items()

        # Find the project item ID for this issue
        item_id = None
        for item in items:
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
