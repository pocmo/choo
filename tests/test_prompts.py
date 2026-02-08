"""Tests for prompt loading."""

import tempfile
from pathlib import Path

import pytest

from choo.prompts import PromptError, load_combined_prompt


def test_load_combined_prompt():
    """Test loading and combining prompts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        choo_dir = Path(tmpdir)
        prompts_dir = choo_dir / "prompts"
        prompts_dir.mkdir()

        # Create system prompt
        system_prompt_path = choo_dir / "system-prompt.md"
        system_prompt_path.write_text("# System Prompt\n\nThis is the system prompt.")

        # Create train prompt
        train_prompt_path = prompts_dir / "test-train.md"
        train_prompt_path.write_text("# Train Prompt\n\nThis is the train prompt.")

        # Load combined prompt
        combined = load_combined_prompt("test-train", choo_dir)

        # Check that both prompts are included
        assert "System Prompt" in combined
        assert "This is the system prompt." in combined
        assert "Train Prompt" in combined
        assert "This is the train prompt." in combined

        # Check order (system first, then train)
        system_idx = combined.index("System Prompt")
        train_idx = combined.index("Train Prompt")
        assert system_idx < train_idx


def test_missing_system_prompt():
    """Test error when system prompt is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        choo_dir = Path(tmpdir)
        prompts_dir = choo_dir / "prompts"
        prompts_dir.mkdir()

        # Create only train prompt
        train_prompt_path = prompts_dir / "test-train.md"
        train_prompt_path.write_text("# Train Prompt")

        # Should raise error
        with pytest.raises(PromptError, match="System prompt not found"):
            load_combined_prompt("test-train", choo_dir)


def test_missing_train_prompt():
    """Test error when train prompt is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        choo_dir = Path(tmpdir)
        prompts_dir = choo_dir / "prompts"
        prompts_dir.mkdir()

        # Create only system prompt
        system_prompt_path = choo_dir / "system-prompt.md"
        system_prompt_path.write_text("# System Prompt")

        # Should raise error
        with pytest.raises(PromptError, match="Train prompt not found"):
            load_combined_prompt("test-train", choo_dir)


def test_prompt_whitespace_handling():
    """Test that prompts are properly trimmed and combined."""
    with tempfile.TemporaryDirectory() as tmpdir:
        choo_dir = Path(tmpdir)
        prompts_dir = choo_dir / "prompts"
        prompts_dir.mkdir()

        # Create prompts with extra whitespace
        system_prompt_path = choo_dir / "system-prompt.md"
        system_prompt_path.write_text("\n\n  System content  \n\n")

        train_prompt_path = prompts_dir / "test-train.md"
        train_prompt_path.write_text("\n  Train content  \n\n\n")

        combined = load_combined_prompt("test-train", choo_dir)

        # Should be trimmed and combined with double newline
        assert combined == "System content\n\nTrain content"
