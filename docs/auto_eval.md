# Auto-Evaluation

Auto-evaluation replaces the manual 0–100 scoring prompt with a judge LLM that scores each step automatically. Kit authors add `evaluator_N.txt` files alongside their instructions. When a kit runs in auto-eval mode, each step's output is sent to the judge LLM, and the returned score is stored in the same place a manual score would go — no schema changes required.

**Fallback rule**: steps without a matching `evaluator_N.txt` fall back to the interactive prompt (as long as `--evaluate` is also passed).

## Kit Structure

Place `evaluator_N.txt` files next to the corresponding `instruction_N.txt` files. N must match the step number:

```
my-kit/
├── resource_1.txt
├── instruction_1.txt
├── evaluator_1.txt     ← scores step 1's output
├── instruction_2.txt
└── evaluator_2.txt     ← scores step 2's output
```

### Evaluator file format

Plain text prompt for the judge LLM. Two placeholders are available:

| Placeholder | Resolves to                                        |
|-------------|---------------------------------------------------|
| `{prompt}`  | The resolved prompt sent to the LLM for this step |
| `{output}`  | The LLM's output for this step                    |

The judge LLM must return a single integer 0–100 on the last line of its response. Include this instruction explicitly in the evaluator file.

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
openclerk run my-kit --auto-evaluate

# Use a specific model as judge (defaults to the same model as the main run)
openclerk run my-kit --auto-evaluate --judge-model gpt-5-mini

# Store full prompt/output text alongside scores
openclerk run my-kit --auto-evaluate --mode transparent

# Mix: auto-eval where evaluator files exist, prompt for the rest
openclerk run my-kit --evaluate --auto-evaluate
```

Passing `--auto-evaluate` automatically enables evaluation — you do not need to also pass `--evaluate` unless you want the interactive fallback for steps that lack an evaluator file.

## CLI Options

| Option | Description |
|--------|-------------|
| `--auto-evaluate` | Score each step using `evaluator_N.txt` instead of prompting the user |
| `--judge-model MODEL` | Model to use for the judge LLM. Defaults to the same model as the main run |
| `--mode transparent\|anonymous` | Controls what is stored: full text (`transparent`) or character counts (`anonymous`) |

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
    judge_model="gpt-5-mini",       # optional; omit to use the default model
    evaluation_mode="transparent",
)
```

`kit.evaluators` is a `dict[str, str]` mapping step number strings to evaluator prompt text. It is populated automatically when the kit is loaded from the filesystem.

## How Scores Are Stored

Auto-eval writes integer scores (0–100) to the same column as manual scores (`evaluation_score` in `step_executions`). If the judge LLM response does not contain a parseable integer between 0 and 100 on its last line, execution raises a `ValueError`. No partial scores are written.

Local evaluation files are saved to `<kit-path>/evaluations/` in the same JSON format as manual evaluations.

## Design Notes

- The judge LLM is called with `temperature=0.0` for deterministic scoring.
- A separate `--judge-model` lets you use a cheaper or stronger model just for scoring without affecting the main workflow model.
- Steps without a matching `evaluator_N.txt` always fall back to the interactive prompt when `--evaluate` is set, and are silently skipped when only `--auto-evaluate` is set.
