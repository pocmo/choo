"""Prompt loading and management."""

from pathlib import Path


class PromptError(Exception):
    """Raised when prompt loading fails."""

    pass


def load_combined_prompt(train_name: str, choo_dir: Path = Path(".choo")) -> str:
    """Load and combine system prompt with train-specific prompt.

    Args:
        train_name: Name of the train
        choo_dir: Path to .choo directory (default: .choo)

    Returns:
        Combined prompt string (system prompt + train prompt)

    Raises:
        PromptError: If required prompt files are missing
    """
    # Load system prompt
    system_prompt_path = choo_dir / "system-prompt.md"
    if not system_prompt_path.exists():
        raise PromptError(f"System prompt not found: {system_prompt_path}")

    with open(system_prompt_path) as f:
        system_prompt = f.read()

    # Load train-specific prompt
    train_prompt_path = choo_dir / "prompts" / f"{train_name}.md"
    if not train_prompt_path.exists():
        raise PromptError(f"Train prompt not found: {train_prompt_path}")

    with open(train_prompt_path) as f:
        train_prompt = f.read()

    # Combine prompts (system first, then train-specific)
    combined = f"{system_prompt.strip()}\n\n{train_prompt.strip()}"

    return combined
