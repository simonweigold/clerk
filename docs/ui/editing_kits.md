# Editing Kits

The Web UI allows you to easily edit [Reasoning Kits](../reasoning_kits.md).

## Interface

When you launch the [Web UI](overview.md), you will see an overview of available kits. Clicking a kit brings you to the editor.

## Features

1. **Resources:** Upload files, add inline content, or manage existing resources. The UI will automatically generate `{resource_X}` tags for your workflow prompts.
2. **Workflow Steps:** You can add, remove, and reorder workflow steps. The UI allows you to insert prompts and reference previous `{workflow_N}` outputs and `{resource_X}` files.

## Saving

Changes are automatically saved to your local `reasoning_kits` directory, keeping your files consistent with the database. You can also sync these changes to a database using the [sync command](../cli/sync.md).
