# Kit Commands

The `kit` commands are used to create, modify, and delete [reasoning kits](../reasoning_kits.md). You can also edit kits via the [Web UI](../ui/editing_kits.md).

## Create Kit

```bash
uv run clerk kit create [OPTIONS] NAME
```
Creates a new kit. Options include `--description` and `--base-path`.

## Delete Kit

```bash
uv run clerk kit delete [OPTIONS] NAME
```
Deletes a kit. Options include `--force` to skip the prompt, and `--base-path`.

## Add Resource

```bash
uv run clerk kit add-resource [OPTIONS] KIT
```
Adds a resource to the kit. Options:
* `--file PATH`: Path to the resource file.
* `--content TEXT`: Inline content.
* `--filename NAME`: Filename for inline content.
* `--base-path PATH`

## Edit Resource

```bash
uv run clerk kit edit-resource [OPTIONS] KIT NUMBER
```
Edits an existing resource. Same options as `add-resource`.

## Delete Resource

```bash
uv run clerk kit delete-resource [OPTIONS] KIT NUMBER
```
Deletes a resource.

## Add Step

```bash
uv run clerk kit add-step [OPTIONS] KIT
```
Adds a workflow step. Options:
* `--file PATH`: Path to instruction file.
* `--prompt TEXT`: Inline prompt text.
* `--base-path PATH`

## Edit Step

```bash
uv run clerk kit edit-step [OPTIONS] KIT NUMBER
```
Edits a workflow step. Same options as `add-step`.

## Delete Step

```bash
uv run clerk kit delete-step [OPTIONS] KIT NUMBER
```
Deletes a workflow step.
