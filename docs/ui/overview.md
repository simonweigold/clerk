# Web UI Overview

CLERK features a graphical user interface that can be launched using the [web command](../cli/web.md).

The web interface is a user-friendly wrapper around the Reasoning Kit definition layer, enabling you to visually build, manage, and test kits without using the command line.

## Key Features

1. **Dashboard:** View all available [Reasoning Kits](../reasoning_kits.md).
2. **Editor:** Visually [edit kits](editing_kits.md), manage resources, and sequence workflow steps.
3. **Runner:** [Execute kits](running_kits.md), input dynamic resources, and interact with evaluations.

## Getting Started

To launch the web interface:

```bash
uv run clerk web
```

By default, the UI will be available at `http://127.0.0.1:8000`. You can configure the port and host using the options described in the [web command documentation](../cli/web.md).
