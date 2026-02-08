"""Claude agent adapter."""

import subprocess
from pathlib import Path

from choo.agent_adapters.base import AgentAdapter


class ClaudeAdapter(AgentAdapter):
    """Adapter for Claude Code CLI."""

    def run(
        self,
        system_prompt: str,
        working_dir: Path,
        env: dict[str, str],
    ) -> int:
        """Run Claude with the given system prompt.

        Args:
            system_prompt: Combined system prompt to pass to Claude
            working_dir: Working directory for the Claude process
            env: Environment variables to set for Claude

        Returns:
            Exit code from Claude process
        """
        # Build command
        cmd = ["claude", "--system-prompt", system_prompt]

        # Merge environment variables with current environment
        process_env = {**subprocess.os.environ, **env}

        # Run Claude in interactive mode
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            env=process_env,
        )

        return result.returncode
