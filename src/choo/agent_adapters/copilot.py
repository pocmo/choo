"""GitHub Copilot CLI agent adapter."""

import shlex
import subprocess
import sys
from pathlib import Path

from choo.agent_adapters.base import AgentAdapter


class CopilotAdapter(AgentAdapter):
    """Adapter for GitHub Copilot CLI."""

    def __init__(self, binary: str = "copilot"):
        """Initialize the Copilot adapter.

        Args:
            binary: Path to the copilot binary (default: "copilot")
        """
        self.binary = binary

    def run(
        self,
        system_prompt: str,
        working_dir: Path,
        env: dict[str, str],
        verbose: bool = False,
    ) -> int:
        """Run GitHub Copilot CLI with the given system prompt.

        Args:
            system_prompt: Combined system prompt to pass to Copilot
            working_dir: Working directory for the Copilot process
            env: Environment variables to set for Copilot
            verbose: Whether to print detailed command execution

        Returns:
            Exit code from Copilot process
        """
        # Build command with system prompt and allow all tools
        # --allow-all-tools is required for non-interactive mode
        cmd = [self.binary, "-p", system_prompt, "--allow-all-tools"]

        # Print command if verbose
        if verbose:
            # Format environment variables for display
            env_display = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())
            # Format command for display
            cmd_display = " ".join(shlex.quote(arg) for arg in cmd)
            print("\n[Verbose] Running command:", file=sys.stderr)
            print(f"  Working directory: {working_dir}", file=sys.stderr)
            print(f"  Environment: {env_display}", file=sys.stderr)
            print(f"  Command: {cmd_display}\n", file=sys.stderr)
            print(f"  System prompt length: {len(system_prompt)} chars\n", file=sys.stderr)

        # Merge environment variables with current environment
        process_env = {
            **subprocess.os.environ,
            **env,
        }

        # Run Copilot
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            env=process_env,
        )

        return result.returncode
