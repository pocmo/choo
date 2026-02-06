"""Tests for the CLI."""

from click.testing import CliRunner

from choo.cli import main


def test_version():
    """Test that version command works."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help():
    """Test that help command works."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Choo" in result.output
    assert "orchestration" in result.output


def test_init():
    """Test that init command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_work_list():
    """Test that work list command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["work", "list"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output
