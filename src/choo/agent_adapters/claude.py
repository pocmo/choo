"""Claude agent adapter."""

import shlex
import subprocess
import sys
from pathlib import Path

from choo.agent_adapters.base import AgentAdapter


class ClaudeAdapter(AgentAdapter):
    """Adapter for Claude Code CLI."""

    def run(
        self,
        system_prompt: str,
        working_dir: Path,
        env: dict[str, str],
        verbose: bool = False,
    ) -> int:
        """Run Claude with the given system prompt.

        Args:
            system_prompt: Combined system prompt to pass to Claude
            working_dir: Working directory for the Claude process
            env: Environment variables to set for Claude
            verbose: Whether to print detailed command execution

        Returns:
            Exit code from Claude process
        """
        # Build command with appended system prompt and initial user message
        cmd = [
            "claude",
            "--append-system-prompt",
            system_prompt,
            "--allow-dangerously-skip-permissions",
            "--dangerously-skip-permissions",
            "--print",
            "Start working on the next available issue.",
        ]

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

        # Merge environment variables with current environment
        process_env = {**subprocess.os.environ, **env}

        # Run Claude
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            env=process_env,
        )

        return result.returncode
