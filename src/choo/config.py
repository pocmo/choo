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
        elif self.type == "jira-acli":
            self._validate_jira_config()
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

    def _validate_jira_config(self) -> None:
        """Validate Jira-specific configuration."""
        required = ["project", "agent_label"]
        for field in required:
            if field not in self.config:
                raise ConfigError(f"Missing required field in ticket_system.config: {field}")

        # Validate types
        if not isinstance(self.config["project"], str):
            raise ConfigError("ticket_system.config.project must be a string")
        if not isinstance(self.config["agent_label"], str):
            raise ConfigError("ticket_system.config.agent_label must be a string")

        # Validate claim_method if present
        if "claim_method" in self.config:
            valid_methods = ["assignee", "label"]
            if self.config["claim_method"] not in valid_methods:
                raise ConfigError(
                    f"Invalid claim_method: {self.config['claim_method']}. "
                    f"Must be one of: {valid_methods}"
                )


@dataclass
class TrainConfig:
    """Configuration for a train (agent instance)."""

    name: str
    from_station: str
    to_station: str
    cli: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainConfig":
        """Create TrainConfig from dictionary.

        Args:
            data: Dictionary containing train configuration

        Returns:
            TrainConfig instance

        Raises:
            ConfigError: If required fields are missing or invalid
        """
        # Check for required fields
        required = ["name", "from_station", "to_station", "cli"]
        for field in required:
            if field not in data:
                raise ConfigError(f"Missing required field in train config: {field}")

        # Check for unknown keys (strict validation)
        known_keys = {"name", "from_station", "to_station", "cli"}
        unknown = set(data.keys()) - known_keys
        if unknown:
            raise ConfigError(f"Unknown train configuration keys: {', '.join(unknown)}")

        # Validate types
        if not isinstance(data["name"], str):
            raise ConfigError("train.name must be a string")
        if not isinstance(data["from_station"], str):
            raise ConfigError("train.from_station must be a string")
        if not isinstance(data["to_station"], str):
            raise ConfigError("train.to_station must be a string")
        if not isinstance(data["cli"], str):
            raise ConfigError("train.cli must be a string")

        return cls(
            name=data["name"],
            from_station=data["from_station"],
            to_station=data["to_station"],
            cli=data["cli"],
        )


@dataclass
class ChooConfig:
    """Main configuration for choo."""

    ticket_system: TicketSystemConfig
    stations: list[str]
    trains: list[TrainConfig]

    def validate(self) -> None:
        """Validate the entire configuration.

        Raises:
            ConfigError: If configuration is invalid
        """
        # Validate stations
        if not self.stations:
            raise ConfigError("stations list cannot be empty")

        # Check for duplicate station names
        if len(self.stations) != len(set(self.stations)):
            raise ConfigError("Duplicate station names found")

        # Validate each station is a string
        for station in self.stations:
            if not isinstance(station, str):
                raise ConfigError(f"Station names must be strings, got: {type(station)}")

        # Validate trains
        if not self.trains:
            raise ConfigError("trains list cannot be empty")

        # Check for duplicate train names
        train_names = [train.name for train in self.trains]
        if len(train_names) != len(set(train_names)):
            raise ConfigError("Duplicate train names found")

        # Validate train station references
        station_set = set(self.stations)
        for train in self.trains:
            if train.from_station not in station_set:
                raise ConfigError(
                    f"Train '{train.name}' references unknown from_station: {train.from_station}"
                )
            if train.to_station not in station_set:
                raise ConfigError(
                    f"Train '{train.name}' references unknown to_station: {train.to_station}"
                )

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

        # Create ticket system config
        ticket_config = TicketSystemConfig(
            type=ticket_data["type"], config=ticket_data["config"]
        )
        ticket_config.validate()

        # Load stations
        if "stations" not in data:
            raise ConfigError("Missing required section: stations")

        stations_data = data["stations"]
        if not isinstance(stations_data, list):
            raise ConfigError("stations must be a list")

        stations = stations_data

        # Load trains
        if "trains" not in data:
            raise ConfigError("Missing required section: trains")

        trains_data = data["trains"]
        if not isinstance(trains_data, list):
            raise ConfigError("trains must be a list")

        trains = [TrainConfig.from_dict(train_data) for train_data in trains_data]

        # Create and validate config
        config = cls(ticket_system=ticket_config, stations=stations, trains=trains)
        config.validate()

        return config
