"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest

from choo.config import ChooConfig, ConfigError


def test_load_valid_config():
    """Test loading a valid configuration."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1
    claim_method: assignee

stations:
  - backlog
  - done

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert config.ticket_system.type == "github-project-gh"
        assert config.ticket_system.config["owner"] == "testorg"
        assert config.ticket_system.config["repo"] == "testrepo"
        assert config.ticket_system.config["project_number"] == 1
        assert config.stations == ["backlog", "done"]
        assert len(config.trains) == 1
        assert config.trains[0].name == "dev"

        Path(f.name).unlink()


def test_missing_config_file():
    """Test error when config file doesn't exist."""
    with pytest.raises(ConfigError, match="not found"):
        ChooConfig.load("/nonexistent/config.yml")


def test_empty_config():
    """Test error on empty config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("")
        f.flush()

        with pytest.raises(ConfigError, match="empty"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_missing_ticket_system():
    """Test error when ticket_system section is missing."""
    config_content = """
some_other_key: value
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="ticket_system"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_missing_required_fields():
    """Test error when required fields are missing."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="repo"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_invalid_adapter_type():
    """Test error with unknown adapter type."""
    config_content = """
ticket_system:
  type: invalid-adapter
  config:
    foo: bar
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Unknown ticket system type"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_strict_validation():
    """Test that unknown top-level keys are rejected."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1
unknown_key: value
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Unknown configuration keys"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_invalid_claim_method():
    """Test error with invalid claim method."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1
    claim_method: invalid
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Invalid claim_method"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_load_valid_stations_and_trains():
    """Test loading valid stations and trains configuration."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - testing
  - done

trains:
  - name: code-writer
    from_station: backlog
    to_station: testing
    cli: claude
  - name: tester
    from_station: testing
    to_station: done
    cli: opencode
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert config.stations == ["backlog", "testing", "done"]
        assert len(config.trains) == 2
        assert config.trains[0].name == "code-writer"
        assert config.trains[0].from_station == "backlog"
        assert config.trains[0].to_station == "testing"
        assert config.trains[0].cli == "claude"
        assert config.trains[1].name == "tester"

        Path(f.name).unlink()


def test_missing_stations():
    """Test error when stations section is missing."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Missing required section: stations"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_missing_trains():
    """Test error when trains section is missing."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Missing required section: trains"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_empty_stations():
    """Test error when stations list is empty."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations: []

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="stations list cannot be empty"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_empty_trains():
    """Test error when trains list is empty."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains: []
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="trains list cannot be empty"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_duplicate_station_names():
    """Test error when station names are duplicated."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - testing
  - backlog

trains:
  - name: dev
    from_station: backlog
    to_station: testing
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Duplicate station names"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_duplicate_train_names():
    """Test error when train names are duplicated."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - testing
  - done

trains:
  - name: dev
    from_station: backlog
    to_station: testing
    cli: claude
  - name: dev
    from_station: testing
    to_station: done
    cli: opencode
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Duplicate train names"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_train_invalid_from_station():
    """Test error when train references non-existent from_station."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: dev
    from_station: nonexistent
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="unknown from_station: nonexistent"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_train_invalid_to_station():
    """Test error when train references non-existent to_station."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: dev
    from_station: backlog
    to_station: nonexistent
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="unknown to_station: nonexistent"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_train_missing_required_fields():
    """Test error when train is missing required fields."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: dev
    from_station: backlog
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Missing required field in train config: to_station"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_train_unknown_keys():
    """Test error when train has unknown configuration keys."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
    unknown_field: value
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Unknown train configuration keys"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_stations_not_a_list():
    """Test error when stations is not a list."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations: "not a list"

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="stations must be a list"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_trains_not_a_list():
    """Test error when trains is not a list."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains: "not a list"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="trains must be a list"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_load_valid_jira_config():
    """Test loading a valid Jira configuration."""
    config_content = """
ticket_system:
  type: jira-acli
  config:
    project: TEST
    agent_label: agent-ready
    claim_method: assignee

stations:
  - todo
  - done

trains:
  - name: dev
    from_station: todo
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert config.ticket_system.type == "jira-acli"
        assert config.ticket_system.config["project"] == "TEST"
        assert config.ticket_system.config["agent_label"] == "agent-ready"
        assert config.ticket_system.config["claim_method"] == "assignee"
        assert config.stations == ["todo", "done"]

        Path(f.name).unlink()


def test_jira_missing_project():
    """Test error when Jira config is missing project."""
    config_content = """
ticket_system:
  type: jira-acli
  config:
    agent_label: agent-ready
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="project"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_jira_missing_agent_label():
    """Test error when Jira config is missing agent_label."""
    config_content = """
ticket_system:
  type: jira-acli
  config:
    project: TEST
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="agent_label"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_jira_invalid_claim_method():
    """Test error when Jira config has invalid claim_method."""
    config_content = """
ticket_system:
  type: jira-acli
  config:
    project: TEST
    agent_label: agent-ready
    claim_method: invalid
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="Invalid claim_method"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()


def test_jira_with_status_mapping():
    """Test loading Jira config with status mapping."""
    config_content = """
ticket_system:
  type: jira-acli
  config:
    project: TEST
    agent_label: agent-ready
    status_mapping:
      backlog: To Do
      done: Completed

stations:
  - backlog
  - done

trains:
  - name: dev
    from_station: backlog
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert config.ticket_system.config["status_mapping"] == {
            "backlog": "To Do",
            "done": "Completed",
        }

        Path(f.name).unlink()


def test_train_with_binary_parameter():
    """Test loading train configuration with binary parameter."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: copilot-train
    from_station: backlog
    to_station: done
    cli: copilot
    binary: /opt/homebrew/bin/copilot
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert len(config.trains) == 1
        assert config.trains[0].name == "copilot-train"
        assert config.trains[0].cli == "copilot"
        assert config.trains[0].binary == "/opt/homebrew/bin/copilot"

        Path(f.name).unlink()


def test_train_binary_optional():
    """Test that binary parameter is optional."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: claude-train
    from_station: backlog
    to_station: done
    cli: claude
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert config.trains[0].binary is None

        Path(f.name).unlink()


def test_train_binary_must_be_string():
    """Test that binary parameter must be a string."""
    config_content = """
ticket_system:
  type: github-project-gh
  config:
    owner: testorg
    repo: testrepo
    project_number: 1

stations:
  - backlog
  - done

trains:
  - name: test-train
    from_station: backlog
    to_station: done
    cli: copilot
    binary: 123
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        with pytest.raises(ConfigError, match="train.binary must be a string"):
            ChooConfig.load(f.name)

        Path(f.name).unlink()
