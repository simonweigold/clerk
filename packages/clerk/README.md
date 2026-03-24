# OpenClerk

A Python framework for multi-step LLM reasoning workflows with structured execution.

## Overview

OpenClerk (formerly CLERK) provides a declarative way to define and execute multi-step reasoning workflows using Large Language Models (LLMs). It supports:

- **Reasoning Kits**: Modular, reusable workflow definitions
- **Multiple LLM Providers**: OpenAI, Anthropic, Mistral, Google, and more
- **Database Storage**: Persistent kit storage and execution tracking
- **Web Interface**: FastAPI-based web UI for executing kits
- **MCP Integration**: Model Context Protocol support for external tools

## Installation

```bash
pip install openclerk
```

## Quick Start

```python
from openclerk import load_reasoning_kit, run_reasoning_kit

# Load a reasoning kit
kit = load_reasoning_kit("path/to/kit")

# Run it
result = run_reasoning_kit(kit)
```

## CLI Usage

```bash
# List available kits
clerk list

# Run a kit
clerk run my-kit

# Start web UI
clerk web
```

## Documentation

For full documentation, visit [https://openclerk.dev/docs](https://openclerk.dev/docs)

## License

MIT License
