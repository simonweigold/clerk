# Auto-Evaluation

Auto-evaluation replaces the manual 0–100 scoring prompt with a judge LLM that scores each step automatically. Kit authors add `evaluator_N.json` (or `evaluator_N.txt`) files alongside their instructions. When a kit runs in auto-eval mode, each step's output is sent to the judge LLM, and the returned score is stored in the same place a manual score would go — no schema changes required.

**Fallback rule**: steps without a matching evaluator file fall back to the interactive prompt (as long as `--evaluate` is also passed).

## Kit Structure

Place evaluator files next to the corresponding `instruction_N.txt` files. N must match the step number:

```
my-kit/
├── resource_1.txt
├── instruction_1.txt
├── evaluator_1.json    ← multi-dimension: scores step 1 on several criteria
├── instruction_2.txt
└── evaluator_2.txt     ← single-dimension fallback (plain text)
```

Both formats can coexist within the same kit. JSON takes precedence over TXT for the same step number.

## Evaluator File Formats

### JSON (recommended) — multi-dimension

A JSON file with a `dimensions` dict (each key is a label, each value is a judge prompt) and an optional `aggregation` strategy:

```json
{
  "aggregation": "average",
  "dimensions": {
    "structure": "You are an expert evaluator...\n\n{prompt}\n\n{output}\n\nReply with ONLY a single integer between 0 and 100.",
    "coverage": "You are an expert evaluator...\n\n{prompt}\n\n{output}\n\nReply with ONLY a single integer between 0 and 100.",
    "citations": "You are an expert evaluator...\n\n{prompt}\n\n{output}\n\nReply with ONLY a single integer between 0 and 100."
  }
}
```

Each dimension is judged independently (calls run concurrently). The per-step `aggregation` overrides the global `--evaluator-aggregation` flag.

**`aggregation` values:**

| Value     | Behaviour                               |
| --------- | --------------------------------------- |
| `average` | Arithmetic mean of all dimension scores (default) |
| `min`     | Minimum score across dimensions         |
| `max`     | Maximum score across dimensions         |
| `first`   | Score of the first dimension only       |

### TXT — single-dimension (legacy / simple)

Plain text prompt for the judge LLM. Two placeholders are available:

| Placeholder | Resolves to                                       |
| ----------- | ------------------------------------------------- |
| `{prompt}`  | The resolved prompt sent to the LLM for this step |
| `{output}`  | The LLM's output for this step                    |

The judge LLM must return a single integer 0–100 on the last line of its response. The dimension is labelled `"default"`.

**Example `evaluator_1.txt`:**

```
You are an expert evaluator. Score the following LLM response on a scale of 0–100.

Criteria:
- Factual accuracy
- Completeness
- Clarity

Original prompt:
{prompt}

Response to evaluate:
{output}

Reply with ONLY a single integer between 0 and 100. No explanation.
```

## Running with Auto-Evaluation

```bash
# Auto-score all steps that have an evaluator file
uv run clerk run my-kit --auto-evaluate

# Use a specific model as judge (or set judge_model in kit.json to avoid repeating this)
uv run clerk run my-kit --auto-evaluate --judge-model deepseek/deepseek-v4-pro

# Store full prompt/output text alongside scores
uv run clerk run my-kit --auto-evaluate --mode transparent

# Override the aggregation strategy for multi-dimension evaluators
uv run clerk run my-kit --auto-evaluate --evaluator-aggregation min

# Mix: auto-eval where evaluator files exist, prompt for the rest
uv run clerk run my-kit --evaluate --auto-evaluate
```

Passing `--auto-evaluate` automatically enables evaluation — you do not need to also pass `--evaluate` unless you want the interactive fallback for steps that lack an evaluator file.

## CLI Options

| Option                                      | Description                                                                          |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `--auto-evaluate`                           | Score each step using the evaluator file instead of prompting the user               |
| `--judge-model MODEL`                       | Model to use for the judge LLM. Defaults to the same model as the main run           |
| `--mode transparent\|anonymous`             | Controls what is stored: full text (`transparent`) or character counts (`anonymous`) |
| `--evaluator-aggregation average\|min\|max\|first` | Global aggregation strategy for multi-dimension scores (default: `average`). Per-step `aggregation` in `evaluator_N.json` takes precedence. |

See the full [run command reference](cli/run.md).

## Programmatic API

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit_async

kit = load_reasoning_kit("reasoning_kits/my-kit")

outputs = await run_reasoning_kit_async(
    kit=kit,
    evaluate=True,
    auto_evaluate=True,
    judge_model="gpt-5.4-nano",       # optional; omit to use the default model
    evaluation_mode="transparent",
    evaluator_aggregation="average",  # global fallback; per-step JSON setting wins
)
```

`kit.evaluators` is a `dict[str, list[tuple[str, str]]]` mapping step number strings to a list of `(label, prompt)` pairs. `kit.evaluator_aggregations` maps step numbers to their per-step aggregation strategy. Both are populated automatically when the kit is loaded from the filesystem.

## How Scores Are Stored

For each step, individual dimension scores are written to `evaluation_scores` (a JSON list of `{label, score}` objects). The aggregated 0–100 score is written to `evaluation_score`. If the judge LLM response does not contain a parseable integer between 0 and 100 on its last line, execution raises a `ValueError`. No partial scores are written.

Local evaluation files are saved to `<kit-path>/evaluations/` in the same JSON format as manual evaluations.

## Pinning a judge model in kit.json

To avoid passing `--judge-model` on every run, add it to the kit's `kit.json`:

```json
{
  "judge_model": "deepseek/deepseek-v4-pro"
}
```

The CLI reads this automatically. `--judge-model` on the command line still overrides it. See [Reasoning Kits — kit configuration](reasoning_kits.md#kit-configuration-optional).

## Design Notes

- The judge LLM is called with `temperature=0.0` for deterministic scoring.
- A separate `--judge-model` lets you use a cheaper or stronger model just for scoring without affecting the main workflow model.
- Dimension judges for a single step run concurrently via `asyncio.gather`.
- When a step has more than one dimension, the CLI prints a per-dimension breakdown table before the aggregated score.
- Steps without a matching evaluator file always fall back to the interactive prompt when `--evaluate` is set, and are silently skipped when only `--auto-evaluate` is set.
