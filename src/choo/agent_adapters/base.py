"""Base class for agent adapters."""

from abc import ABC, abstractmethod
from pathlib import Path


class AgentAdapter(ABC):
    """Base class for agent adapters.

    Agent adapters handle spawning and managing different AI agent tools
    (claude, openai, etc.) with the appropriate command-line parameters.
    """

    @abstractmethod
    def run(
        self,
        system_prompt: str,
        working_dir: Path,
        env: dict[str, str],
    ) -> int:
        """Run the agent with the given system prompt.

        Args:
            system_prompt: Combined system prompt to pass to the agent
            working_dir: Working directory for the agent process
            env: Environment variables to set for the agent

        Returns:
            Exit code from the agent process
        """
        pass
