# Agent Instructions for Building Choo

## Project Vision

Choo is an **orchestration framework**, not another AI coding assistant. Our job is to coordinate existing tools cleanly. We provide:
- A unified CLI interface for ticket operations
- Process management for AI agent instances
- Adapters to abstract different ticket systems
- Configuration-driven workflow engine

We DO NOT:
- Implement LLM integrations (agents use external tools like `claude`)
- Maintain ticket state (ticket systems are source of truth)
- Make opinionated decisions about workflows (user-configurable)

## Development Setup

See `DEVELOPMENT.md` for instructions on setting up the development environment, running tests, and using the project tooling.

## Architecture Principles

See `docs/architecture-principles.md` for detailed architectural decisions and princles when needing to make decisions.