"""Configuration loading and validation for choo."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""

    pass


@dataclass
class TicketSystemConfig:
    """Configuration for the ticket system adapter."""

    type: str
    config: dict[str, Any]

    def validate(self) -> None:
        """Validate ticket system configuration."""
        if self.type == "github-project-gh":
            self._validate_github_config()
        else:
            raise ConfigError(f"Unknown ticket system type: {self.type}")

    def _validate_github_config(self) -> None:
        """Validate GitHub-specific configuration."""
        required = ["owner", "repo", "project_number"]
        for field in required:
            if field not in self.config:
                raise ConfigError(f"Missing required field in ticket_system.config: {field}")

        # Validate types
        if not isinstance(self.config["owner"], str):
            raise ConfigError("ticket_system.config.owner must be a string")
        if not isinstance(self.config["repo"], str):
            raise ConfigError("ticket_system.config.repo must be a string")
        if not isinstance(self.config["project_number"], int):
            raise ConfigError("ticket_system.config.project_number must be an integer")

        # Validate claim_method if present
        if "claim_method" in self.config:
            valid_methods = ["assignee", "label"]
            if self.config["claim_method"] not in valid_methods:
                raise ConfigError(
                    f"Invalid claim_method: {self.config['claim_method']}. "
                    f"Must be one of: {valid_methods}"
                )


@dataclass
class ChooConfig:
    """Main configuration for choo."""

    ticket_system: TicketSystemConfig

    @classmethod
    def load(cls, path: Path | str = ".choo/config.yml") -> "ChooConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the configuration file

        Returns:
            Loaded and validated configuration

        Raises:
            ConfigError: If configuration is invalid or file doesn't exist
        """
        path = Path(path)

        if not path.exists():
            raise ConfigError(f"Configuration file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML: {e}")

        if not data:
            raise ConfigError("Configuration file is empty")

        # Validate structure
        if "ticket_system" not in data:
            raise ConfigError("Missing required section: ticket_system")

        ticket_data = data["ticket_system"]
        if "type" not in ticket_data:
            raise ConfigError("Missing required field: ticket_system.type")
        if "config" not in ticket_data:
            raise ConfigError("Missing required field: ticket_system.config")

        # Check for unknown top-level keys (strict validation)
        known_keys = {"ticket_system", "stations", "trains"}
        unknown = set(data.keys()) - known_keys
        if unknown:
            raise ConfigError(f"Unknown configuration keys: {', '.join(unknown)}")

        # Create config object
        ticket_config = TicketSystemConfig(
            type=ticket_data["type"], config=ticket_data["config"]
        )

        # Validate
        ticket_config.validate()

        return cls(ticket_system=ticket_config)
