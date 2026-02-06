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
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config = ChooConfig.load(f.name)
        assert config.ticket_system.type == "github-project-gh"
        assert config.ticket_system.config["owner"] == "testorg"
        assert config.ticket_system.config["repo"] == "testrepo"
        assert config.ticket_system.config["project_number"] == 1

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
