# Contributing to choo 🚂

Thank you for your interest in contributing to choo! This document provides guidelines and instructions for contributing to the project.

## Project Philosophy

Before contributing, please understand choo's core philosophy:

- **Choo is an orchestration framework**, not another AI coding assistant
- We coordinate existing tools cleanly rather than reimplementing functionality
- We provide a unified CLI interface, process management, and adapters
- We remain agnostic to both ticket systems and AI agent implementations
- Configuration drives behavior; we avoid opinionated workflow decisions

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management

### Setting Up Your Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/pocmo/choo.git
   cd choo
   ```

2. **Install dependencies**
   ```bash
   # Install core dependencies
   uv pip install -e .

   # Install development dependencies
   uv pip install --group dev
   ```

3. **Verify the installation**
   ```bash
   uv run choo --help
   ```

## Development Workflow

### Running Tests

We use pytest for testing. Always ensure tests pass before submitting a pull request.

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=choo tests/

# Run specific test
uv run pytest tests/test_cli.py::test_version -v
```

### Code Quality

We maintain high code quality standards using ruff for linting and formatting.

```bash
# Run linter
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

**Before submitting a PR, ensure:**
- All tests pass
- Code is properly formatted (`ruff format`)
- No linting errors (`ruff check`)
- New code includes appropriate tests

## How to Contribute

### Reporting Bugs

- Use GitHub Issues to report bugs
- Include a clear description of the issue
- Provide steps to reproduce
- Include your environment details (OS, Python version, etc.)
- If applicable, include relevant configuration files (sanitized)

### Suggesting Features

- Open a GitHub Issue with the "enhancement" label
- Clearly describe the use case and problem being solved
- Consider whether the feature aligns with choo's philosophy as an orchestration framework
- Be open to discussion about implementation approaches

### Contributing Code

1. **Find or create an issue**
   - Check existing issues or create a new one
   - Discuss your approach before starting significant work

2. **Fork and create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Write clear, descriptive commit messages
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format .
   ```

5. **Submit a pull request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure CI checks pass

### Contributing Documentation

Documentation improvements are always welcome! This includes:
- README updates
- Code comments and docstrings
- Usage examples
- Architecture documentation
- Tutorial content

## Architecture Guidelines

### Core Principles

1. **Separation of Concerns**
   - Ticket systems are the source of truth
   - Choo orchestrates; it doesn't implement LLM integrations
   - Adapters abstract ticket system differences

2. **Extensibility**
   - New ticket system adapters should be straightforward to implement
   - Configuration drives behavior
   - Avoid hardcoding workflow assumptions

3. **Simplicity**
   - Prefer simple, clear solutions
   - Use existing tools (gh CLI, etc.) rather than reimplementing
   - Progressive disclosure: simple cases should be simple

### Adding a New Adapter

If you're adding support for a new ticket system:
1. Study existing adapters (e.g., `github-gh`)
2. Implement the core adapter interface
3. Use existing CLI tools where possible
4. Document configuration options
5. Add tests covering the adapter functionality

## Pull Request Process

1. Update documentation to reflect any changes
2. Add tests for new functionality
3. Ensure all tests pass and code is formatted
4. Update the README.md if needed
5. Request review from maintainers
6. Address any feedback
7. Once approved, a maintainer will merge your PR

## Code Review Guidelines

When reviewing PRs, we look for:
- Alignment with project philosophy
- Code quality and style
- Test coverage
- Documentation completeness
- Backward compatibility considerations

## Questions?

- Open a GitHub Discussion for general questions
- Join the conversation on existing issues
- Check the README.md and documentation first

## License

By contributing to choo, you agree that your contributions will be licensed under the same license as the project (TBD).

---

Thank you for contributing to choo! 🚂
