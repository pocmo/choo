"""Tests for GitHub Copilot agent adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from choo.agent_adapters.copilot import CopilotAdapter


@pytest.fixture
def copilot_adapter():
    """Create a Copilot adapter with default binary."""
    return CopilotAdapter()


@pytest.fixture
def copilot_adapter_custom():
    """Create a Copilot adapter with custom binary path."""
    return CopilotAdapter(binary="/custom/path/to/copilot")


def test_init_default_binary():
    """Test initialization with default binary."""
    adapter = CopilotAdapter()
    assert adapter.binary == "copilot"


def test_init_custom_binary():
    """Test initialization with custom binary path."""
    adapter = CopilotAdapter(binary="/usr/local/bin/copilot")
    assert adapter.binary == "/usr/local/bin/copilot"


@patch("subprocess.run")
def test_run_basic(mock_run, copilot_adapter):
    """Test running copilot with basic parameters."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    system_prompt = "You are a helpful AI assistant."
    working_dir = Path("/tmp/test")
    env = {"KEY": "value"}

    exit_code = copilot_adapter.run(system_prompt, working_dir, env)

    assert exit_code == 0
    mock_run.assert_called_once()

    # Check command
    call_args = mock_run.call_args
    cmd = call_args[0][0]
    assert cmd == ["copilot"]

    # Check working directory
    assert call_args[1]["cwd"] == working_dir

    # Check environment includes system prompt
    process_env = call_args[1]["env"]
    assert "GITHUB_COPILOT_SYSTEM_PROMPT" in process_env
    assert process_env["GITHUB_COPILOT_SYSTEM_PROMPT"] == system_prompt
    assert process_env["KEY"] == "value"


@patch("subprocess.run")
def test_run_custom_binary(mock_run, copilot_adapter_custom):
    """Test running copilot with custom binary path."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    system_prompt = "Custom system prompt"
    working_dir = Path("/tmp/test")
    env = {}

    copilot_adapter_custom.run(system_prompt, working_dir, env)

    # Check custom binary is used
    call_args = mock_run.call_args
    cmd = call_args[0][0]
    assert cmd == ["/custom/path/to/copilot"]


@patch("subprocess.run")
def test_run_with_verbose(mock_run, copilot_adapter, capsys):
    """Test running copilot with verbose output."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    system_prompt = "Test prompt"
    working_dir = Path("/tmp/test")
    env = {"TEST_VAR": "test_value"}

    copilot_adapter.run(system_prompt, working_dir, env, verbose=True)

    # Check verbose output is printed to stderr
    captured = capsys.readouterr()
    assert "Verbose" in captured.err
    assert "Working directory" in captured.err
    assert "Environment" in captured.err
    assert "Command" in captured.err
    assert "System prompt length" in captured.err


@patch("subprocess.run")
def test_run_nonzero_exit(mock_run, copilot_adapter):
    """Test that non-zero exit codes are returned correctly."""
    mock_result = MagicMock()
    mock_result.returncode = 42
    mock_run.return_value = mock_result

    system_prompt = "Test"
    working_dir = Path("/tmp")
    env = {}

    exit_code = copilot_adapter.run(system_prompt, working_dir, env)

    assert exit_code == 42


@patch("subprocess.run")
def test_run_environment_merge(mock_run, copilot_adapter):
    """Test that environment variables are properly merged."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    system_prompt = "Test"
    working_dir = Path("/tmp")
    env = {"CUSTOM_VAR": "custom_value", "PATH": "/custom/path"}

    copilot_adapter.run(system_prompt, working_dir, env)

    # Check that both custom and system prompt env vars are set
    call_args = mock_run.call_args
    process_env = call_args[1]["env"]
    assert "GITHUB_COPILOT_SYSTEM_PROMPT" in process_env
    assert process_env["CUSTOM_VAR"] == "custom_value"
    assert process_env["PATH"] == "/custom/path"
