# User Guide

Welcome to Clerk! This guide will help you get started with the Clerk framework for multi-step LLM reasoning workflows.

## Getting Started

### Installation

Install Clerk using pip:

```bash
pip install openclerk
```

Or using UV (recommended):

```bash
uv add openclerk
```

### Verify Installation

Check that Clerk is installed correctly:

```bash
clerk --version
```

### Your First Workflow

Let's run a simple reasoning kit to see Clerk in action:

```bash
# List available kits
clerk list

# Run a kit
clerk run example-kit
```

That's it! You've just executed your first multi-step LLM reasoning workflow.

---

## Quick Start Example

Here's a complete 5-line example:

```bash
# 1. Install Clerk
pip install openclerk

# 2. Create a new kit
clerk kit create my-first-kit --description "My first reasoning workflow"

# 3. Add a resource
clerk kit add-resource my-first-kit --file data.txt

# 4. Add a workflow step
clerk kit add-step my-first-kit --prompt "Analyze the data and summarize key findings"

# 5. Run the kit
clerk run my-first-kit
```

---

## Next Steps

Now that you've run your first workflow, explore these resources:

- **[Core Concepts](concepts.md)** — Learn about Reasoning Kits, Resources, Instructions, and Workflows
- **[FAQ](faq.md)** — Find answers to common questions
- **[Reasoning Kits](../reasoning_kits.md)** — Deep dive into kit structure and creation

---

## Common Commands

| Command                        | Description                   |
| ------------------------------ | ----------------------------- |
| `clerk list`                   | List available reasoning kits |
| `clerk run <kit>`              | Run a reasoning kit           |
| `clerk info <kit>`             | Show information about a kit  |
| `clerk kit create <name>`      | Create a new reasoning kit    |
| `clerk kit add-resource <kit>` | Add a resource to a kit       |
| `clerk kit add-step <kit>`     | Add a workflow step to a kit  |
| `clerk web`                    | Start the web UI server       |

---

## Getting Help

If you run into issues:

1. Check the [FAQ](faq.md) for common problems
2. Review the [Core Concepts](concepts.md) documentation
3. Visit our [GitHub Issues](https://github.com/your-org/clerk/issues) for community support

---

Happy reasoning!
