# Running Kits

The Web UI allows you to execute [Reasoning Kits](../reasoning_kits.md).

## Interface

When you launch the [Web UI](overview.md) and select a kit, you can run the kit via the built-in runner interface.

## Features

1. **Dynamic Inputs:** If a kit has dynamic resources requiring user input, the UI will prompt you to provide text, file paths, or content before executing.
2. **Evaluations:** You can choose to run kits with the `--evaluate` option, allowing you to provide step-by-step evaluations as the workflow runs.

## Output

Once executed, all workflow steps and their outputs `{workflow_N}` will be presented clearly, allowing you to review the reasoning kit's results.

If you are using the database layer, you can also view past executions. See the [database documentation](../cli/db.md) for more details.
