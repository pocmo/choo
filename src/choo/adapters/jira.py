"""Jira adapter using acli CLI."""

import json
import subprocess
import sys
from datetime import datetime
from typing import Any

from choo.adapters.base import IssueNotFoundError, TicketSystemAdapter
from choo.models import Issue


class JiraAcliAdapter(TicketSystemAdapter):
    """Adapter for Jira using the acli CLI."""

    def __init__(self, config: dict[str, Any], verbose: bool = False):
        """Initialize the Jira adapter.

        Args:
            config: Configuration dictionary with project, agent_label
            verbose: If True, print acli commands
        """
        self.project = config["project"]
        self.agent_label = config["agent_label"]
        self.claim_method = config.get("claim_method", "assignee")
        self.status_mapping = config.get("status_mapping", {})
        self.verbose = verbose

        # Lazy-loaded cached values
        self._statuses: list[str] | None = None

    def _run_acli(self, args: list[str]) -> str:
        """Run an acli CLI command and return output.

        Args:
            args: Command arguments to pass to acli

        Returns:
            Command output as string

        Raises:
            RuntimeError: If acli command fails
        """
        cmd = ["acli"] + args

        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] $ acli {' '.join(args)}", file=sys.stderr)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"acli command failed: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"acli command timed out: {' '.join(cmd)}") from e

    def _parse_workitem(self, item_data: dict[str, Any]) -> Issue:
        """Parse a Jira work item into an Issue object.

        Args:
            item_data: Raw item data from acli API

        Returns:
            Issue object
        """
        # Get status from fields
        status_field = item_data.get("fields", {}).get("status", {})
        status = status_field.get("name", "Unknown")

        # Get assignee
        assignee_field = item_data.get("fields", {}).get("assignee")
        assignee = None
        if assignee_field:
            assignee = assignee_field.get("displayName") or assignee_field.get("emailAddress")

        # Get labels
        labels = item_data.get("fields", {}).get("labels", [])

        return Issue(
            id=item_data.get("key", ""),
            title=item_data.get("fields", {}).get("summary", ""),
            body=item_data.get("fields", {}).get("description"),
            station=status,
            url=item_data.get("self"),
            assignee=assignee,
            labels=labels,
        )

    def list_stations(self) -> list[str]:
        """List all available workflow stations in the project.

        Returns:
            List of unique status names
        """
        if self._statuses is None:
            # Query all issues in project and extract unique statuses
            output = self._run_acli(
                [
                    "jira",
                    "workitem",
                    "search",
                    "--jql",
                    f"project = {self.project}",
                    "--fields",
                    "status",
                    "--limit",
                    "100",
                    "--json",
                ]
            )
            data = json.loads(output)

            # ACLI returns a list at top level, not a dict with "issues" key
            if not isinstance(data, list):
                data = []

            statuses = set()
            for item in data:
                status_field = item.get("fields", {}).get("status", {})
                status = status_field.get("name")
                if status:
                    statuses.add(status)

            self._statuses = sorted(statuses)

        return self._statuses

    def list_issues(self, station: str) -> list[Issue]:
        """List all issues at a specific workflow station.

        Args:
            station: The workflow stage (status field value)

        Returns:
            List of issues at that station that are agent-ready and unclaimed
        """
        # Map station to status if mapping exists
        status = self.status_mapping.get(station, station)

        # Build JQL: project + status + agent label + unclaimed
        jql = f'project = {self.project} AND status = "{status}" AND labels = "{self.agent_label}"'

        if self.claim_method == "assignee":
            jql += " AND assignee is EMPTY"
        elif self.claim_method == "label":
            jql += ' AND labels not in ("in-progress")'

        output = self._run_acli(
            [
                "jira",
                "workitem",
                "search",
                "--jql",
                jql,
                "--fields",
                "key,summary,description,status,assignee,labels",
                "--json",
            ]
        )
        data = json.loads(output)

        # ACLI returns a list at top level, not a dict with "issues" key
        if not isinstance(data, list):
            data = []

        issues = []
        for item in data:
            try:
                issue = self._parse_workitem(item)
                issues.append(issue)
            except Exception:
                # Skip items that can't be parsed
                continue

        return issues

    def get_issue(self, issue_id: str) -> Issue:
        """Get full details of a specific issue.

        Args:
            issue_id: The issue key (e.g., "PROJ-123")

        Returns:
            Issue object with full details

        Raises:
            IssueNotFoundError: If issue doesn't exist
        """
        try:
            output = self._run_acli(
                [
                    "jira",
                    "workitem",
                    "view",
                    issue_id,
                    "--fields",
                    "key,summary,description,status,assignee,labels",
                    "--json",
                ]
            )
            data = json.loads(output)
            return self._parse_workitem(data)

        except RuntimeError as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                raise IssueNotFoundError(f"Issue {issue_id} not found")
            raise

    def claim_issue(self, issue_id: str) -> None:
        """Claim an issue by assigning it to the current user.

        Args:
            issue_id: The issue key
        """
        if self.claim_method == "assignee":
            self._run_acli(
                [
                    "jira",
                    "workitem",
                    "assign",
                    "--key",
                    issue_id,
                    "--assignee",
                    "@me",
                ]
            )
        elif self.claim_method == "label":
            # Add "in-progress" label
            self._run_acli(
                [
                    "jira",
                    "workitem",
                    "edit",
                    "--key",
                    issue_id,
                    "--add-label",
                    "in-progress",
                ]
            )

    def unclaim_issue(self, issue_id: str) -> None:
        """Unclaim an issue by removing assignment.

        Args:
            issue_id: The issue key
        """
        if self.claim_method == "assignee":
            self._run_acli(
                [
                    "jira",
                    "workitem",
                    "assign",
                    "--key",
                    issue_id,
                    "--remove-assignee",
                ]
            )
        elif self.claim_method == "label":
            # Remove "in-progress" label
            self._run_acli(
                [
                    "jira",
                    "workitem",
                    "edit",
                    "--key",
                    issue_id,
                    "--remove-label",
                    "in-progress",
                ]
            )

    def move_issue(self, issue_id: str, to_station: str) -> None:
        """Move an issue to a different workflow station.

        Args:
            issue_id: The issue key
            to_station: The target status value
        """
        # Map station to status if mapping exists
        status = self.status_mapping.get(to_station, to_station)

        self._run_acli(
            [
                "jira",
                "workitem",
                "transition",
                "--key",
                issue_id,
                "--status",
                status,
                "--yes",
            ]
        )

    def get_comments(self, issue_id: str) -> list[dict[str, str]]:
        """Get all comments for an issue.

        Args:
            issue_id: The issue key

        Returns:
            List of comments with author, body, and created_at
        """
        output = self._run_acli(
            [
                "jira",
                "workitem",
                "comment",
                "list",
                issue_id,
                "--json",
            ]
        )
        data = json.loads(output)
        comments = []

        for comment in data.get("comments", []):
            author_field = comment.get("author", {})
            author = author_field.get("displayName") or author_field.get("emailAddress", "unknown")

            comments.append(
                {
                    "author": author,
                    "body": comment.get("body", ""),
                    "created_at": comment.get("created", ""),
                }
            )

        return comments

    def add_comment(self, issue_id: str, message: str) -> None:
        """Add a comment to an issue.

        Args:
            issue_id: The issue key
            message: The comment text
        """
        self._run_acli(
            [
                "jira",
                "workitem",
                "comment",
                "create",
                "--key",
                issue_id,
                "--body",
                message,
            ]
        )
