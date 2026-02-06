# Development Guide

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Initial Setup

```bash
# Install dependencies
uv pip install -e .

# Install dev dependencies
uv pip install --group dev
```

### Running Choo

```bash
# From the activated virtualenv
choo --help

# Or directly
.venv/bin/choo --help
```

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=choo tests/

# Run specific test
pytest tests/test_cli.py::test_version -v
```

### Code Quality

```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

