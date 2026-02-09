"""Tests for Jira ACLI adapter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from choo.adapters.base import IssueNotFoundError
from choo.adapters.jira import JiraAcliAdapter


@pytest.fixture
def jira_config():
    """Minimal Jira configuration."""
    return {
        "project": "TEST",
        "agent_label": "agent-ready",
        "claim_method": "assignee",
    }


@pytest.fixture
def jira_adapter(jira_config):
    """Create a Jira adapter instance."""
    return JiraAcliAdapter(jira_config)


@pytest.fixture
def sample_jira_issue():
    """Sample Jira issue data from acli."""
    return {
        "key": "TEST-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/12345",
        "fields": {
            "summary": "Test issue",
            "description": "This is a test issue",
            "status": {"name": "To Do"},
            "assignee": None,
            "labels": ["agent-ready"],
        },
    }


@pytest.fixture
def sample_jira_issue_assigned():
    """Sample assigned Jira issue."""
    return {
        "key": "TEST-456",
        "self": "https://test.atlassian.net/rest/api/3/issue/12346",
        "fields": {
            "summary": "Assigned issue",
            "description": "This is assigned",
            "status": {"name": "In Progress"},
            "assignee": {
                "displayName": "Test User",
                "emailAddress": "test@example.com",
            },
            "labels": ["agent-ready"],
        },
    }


def test_init_minimal_config(jira_config):
    """Test initialization with minimal configuration."""
    adapter = JiraAcliAdapter(jira_config)
    assert adapter.project == "TEST"
    assert adapter.agent_label == "agent-ready"
    assert adapter.claim_method == "assignee"
    assert adapter.status_mapping == {}
    assert adapter.verbose is False


def test_init_with_status_mapping():
    """Test initialization with status mapping."""
    config = {
        "project": "TEST",
        "agent_label": "agent-ready",
        "status_mapping": {
            "backlog": "To Do",
            "done": "Done",
        },
    }
    adapter = JiraAcliAdapter(config)
    assert adapter.status_mapping == {"backlog": "To Do", "done": "Done"}


def test_parse_workitem(jira_adapter, sample_jira_issue):
    """Test parsing a Jira work item."""
    issue = jira_adapter._parse_workitem(sample_jira_issue)

    assert issue.id == "TEST-123"
    assert issue.title == "Test issue"
    assert issue.body == "This is a test issue"
    assert issue.station == "To Do"
    assert issue.assignee is None
    assert issue.labels == ["agent-ready"]


def test_parse_workitem_with_assignee(jira_adapter, sample_jira_issue_assigned):
    """Test parsing a Jira work item with assignee."""
    issue = jira_adapter._parse_workitem(sample_jira_issue_assigned)

    assert issue.id == "TEST-456"
    assert issue.assignee == "Test User"
    assert issue.station == "In Progress"


@patch("subprocess.run")
def test_list_stations(mock_run, jira_adapter):
    """Test listing workflow stations."""
    mock_result = MagicMock()
    # ACLI returns a list at top level, not wrapped in "issues"
    mock_result.stdout = json.dumps([
        {"fields": {"status": {"name": "To Do"}}},
        {"fields": {"status": {"name": "In Progress"}}},
        {"fields": {"status": {"name": "Done"}}},
        {"fields": {"status": {"name": "To Do"}}},  # Duplicate
    ])
    mock_run.return_value = mock_result

    stations = jira_adapter.list_stations()

    assert stations == ["Done", "In Progress", "To Do"]  # Sorted, unique
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "acli"
    assert "workitem" in args
    assert "search" in args
    assert "--jql" in args


@patch("subprocess.run")
def test_list_issues(mock_run, jira_adapter, sample_jira_issue):
    """Test listing issues at a station."""
    mock_result = MagicMock()
    # ACLI returns a list at top level
    mock_result.stdout = json.dumps([sample_jira_issue])
    mock_run.return_value = mock_result

    issues = jira_adapter.list_issues("To Do")

    assert len(issues) == 1
    assert issues[0].id == "TEST-123"
    assert issues[0].station == "To Do"

    # Check JQL query was built correctly
    args = mock_run.call_args[0][0]
    jql_index = args.index("--jql") + 1
    jql = args[jql_index]
    assert "project = TEST" in jql
    assert 'status = "To Do"' in jql
    assert 'labels = "agent-ready"' in jql
    assert "assignee is EMPTY" in jql


@patch("subprocess.run")
def test_list_issues_with_status_mapping(mock_run):
    """Test listing issues with status mapping."""
    config = {
        "project": "TEST",
        "agent_label": "agent-ready",
        "status_mapping": {"backlog": "To Do"},
    }
    adapter = JiraAcliAdapter(config)

    mock_result = MagicMock()
    mock_result.stdout = json.dumps([])  # ACLI returns list
    mock_run.return_value = mock_result

    adapter.list_issues("backlog")

    # Should use mapped status "To Do" in JQL
    args = mock_run.call_args[0][0]
    jql_index = args.index("--jql") + 1
    jql = args[jql_index]
    assert 'status = "To Do"' in jql


@patch("subprocess.run")
def test_get_issue(mock_run, jira_adapter, sample_jira_issue):
    """Test getting a specific issue."""
    mock_result = MagicMock()
    mock_result.stdout = json.dumps(sample_jira_issue)
    mock_run.return_value = mock_result

    issue = jira_adapter.get_issue("TEST-123")

    assert issue.id == "TEST-123"
    assert issue.title == "Test issue"

    args = mock_run.call_args[0][0]
    assert "workitem" in args
    assert "view" in args
    assert "TEST-123" in args


@patch("subprocess.run")
def test_get_issue_not_found(mock_run, jira_adapter):
    """Test getting a non-existent issue."""
    mock_run.side_effect = RuntimeError("Issue not found")

    with pytest.raises(IssueNotFoundError):
        jira_adapter.get_issue("TEST-999")


@patch("subprocess.run")
def test_claim_issue_assignee(mock_run, jira_adapter):
    """Test claiming an issue via assignee."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    jira_adapter.claim_issue("TEST-123")

    args = mock_run.call_args[0][0]
    assert "workitem" in args
    assert "assign" in args
    assert "--key" in args
    assert "TEST-123" in args
    assert "--assignee" in args
    assert "@me" in args


@patch("subprocess.run")
def test_claim_issue_label(mock_run):
    """Test claiming an issue via label."""
    config = {
        "project": "TEST",
        "agent_label": "agent-ready",
        "claim_method": "label",
    }
    adapter = JiraAcliAdapter(config)

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    adapter.claim_issue("TEST-123")

    args = mock_run.call_args[0][0]
    assert "workitem" in args
    assert "edit" in args
    assert "--add-label" in args
    assert "in-progress" in args


@patch("subprocess.run")
def test_unclaim_issue(mock_run, jira_adapter):
    """Test unclaiming an issue."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    jira_adapter.unclaim_issue("TEST-123")

    args = mock_run.call_args[0][0]
    assert "workitem" in args
    assert "assign" in args
    assert "--remove-assignee" in args


@patch("subprocess.run")
def test_move_issue(mock_run, jira_adapter):
    """Test moving an issue to a different status."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    jira_adapter.move_issue("TEST-123", "Done")

    args = mock_run.call_args[0][0]
    assert "workitem" in args
    assert "transition" in args
    assert "--key" in args
    assert "TEST-123" in args
    assert "--status" in args
    assert "Done" in args
    assert "--yes" in args


@patch("subprocess.run")
def test_move_issue_with_mapping(mock_run):
    """Test moving an issue with status mapping."""
    config = {
        "project": "TEST",
        "agent_label": "agent-ready",
        "status_mapping": {"done": "Completed"},
    }
    adapter = JiraAcliAdapter(config)

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    adapter.move_issue("TEST-123", "done")

    args = mock_run.call_args[0][0]
    status_index = args.index("--status") + 1
    assert args[status_index] == "Completed"


@patch("subprocess.run")
def test_get_comments(mock_run, jira_adapter):
    """Test getting comments for an issue."""
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({
        "comments": [
            {
                "author": {"displayName": "Alice"},
                "body": "First comment",
                "created": "2024-01-01T10:00:00.000Z",
            },
            {
                "author": {"emailAddress": "bob@example.com"},
                "body": "Second comment",
                "created": "2024-01-02T11:00:00.000Z",
            },
        ]
    })
    mock_run.return_value = mock_result

    comments = jira_adapter.get_comments("TEST-123")

    assert len(comments) == 2
    assert comments[0]["author"] == "Alice"
    assert comments[0]["body"] == "First comment"
    assert comments[1]["author"] == "bob@example.com"


@patch("subprocess.run")
def test_add_comment(mock_run, jira_adapter):
    """Test adding a comment to an issue."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    jira_adapter.add_comment("TEST-123", "This is a comment")

    args = mock_run.call_args[0][0]
    assert "workitem" in args
    assert "comment" in args
    assert "create" in args
    assert "--key" in args
    assert "TEST-123" in args
    assert "--body" in args
    assert "This is a comment" in args


@patch("subprocess.run")
def test_verbose_mode(mock_run, jira_config):
    """Test verbose mode prints commands."""
    adapter = JiraAcliAdapter(jira_config, verbose=True)

    mock_result = MagicMock()
    mock_result.stdout = json.dumps([])  # ACLI returns list
    mock_run.return_value = mock_result

    with patch("sys.stderr"):
        adapter.list_issues("To Do")
        # Verbose mode should print to stderr
        # We're just checking it doesn't crash


def test_command_timeout(jira_adapter):
    """Test that commands have a timeout."""
    with patch("subprocess.run") as mock_run:
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("acli", 30)

        with pytest.raises(RuntimeError, match="timed out"):
            jira_adapter.list_stations()
