# OpenClerk

[![PyPI](https://img.shields.io/pypi/v/openclerk.svg)](https://pypi.org/project/openclerk/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Community Library of Executable Reasoning Kits

Clerk is a Python framework for multi-step LLM reasoning workflows with a React frontend. Define and execute modular, reusable reasoning workflows using Large Language Models.

## Quickstart

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

kit = load_reasoning_kit("reasoning_kits/demo")
outputs = run_reasoning_kit(kit)
```

## Installation

```bash
pip install openclerk
```

Or from source:
```bash
git clone https://github.com/simonweigold/clerk.git && cd clerk
just setup
```

## Usage

```bash
clerk list       # List reasoning kits
clerk run demo   # Run a kit
clerk web        # Start web UI
```

## Documentation

- [User Guide](docs/user-guide/) - Getting started
- [Integration Guide](docs/integration/) - Embedding Clerk
- [Contributing](CONTRIBUTING.md) - Development setup

## License

[MIT License](LICENSE)
