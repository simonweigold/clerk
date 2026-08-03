# Auto-Evaluation Feature

## Overview

Auto-evaluation replaces the manual 0–100 scoring prompt with a judge LLM that scores each step automatically. The kit author adds `evaluator_N.txt` files alongside instructions. When the kit runs in auto-eval mode, each step's output is passed to the judge LLM with the evaluator prompt, and the returned score is stored exactly where the manual score would go — no schema changes required.

**Fallback rule**: If a step has no matching `evaluator_N.txt`, fall back to the existing interactive prompt.

---

## New File: `evaluator_N.txt`

Placed in the kit directory alongside `instruction_N.txt`. N must match the step number.

```
my-kit/
├── resource_1.txt
├── instruction_1.txt
├── evaluator_1.txt     ← scores step 1's output
├── instruction_2.txt
└── evaluator_2.txt     ← scores step 2's output
```

### Format

Plain text prompt for the judge LLM. Two placeholders are available:

| Placeholder | Resolves to |
|-------------|-------------|
| `{prompt}`  | The resolved prompt that was sent to the LLM for this step |
| `{output}`  | The LLM's output for this step |

The judge LLM must return a single integer 0–100 on the last line of its response and nothing else. Kit authors should make this explicit in the evaluator file.

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

---

## Changes Required

### 1. `loader.py` — discover evaluator files

Add evaluator discovery inside `load_reasoning_kit()`, following the same pattern as instructions and tools:

```python
# After instruction discovery
evaluators: dict[str, str] = {}
evaluator_files = sorted(
    kit_path.glob("evaluator_*.txt"),
    key=lambda f: _extract_number(f.name) or 0,
)
for evaluator_file in evaluator_files:
    step_num = _extract_number(evaluator_file.name)
    if step_num is not None:
        evaluators[str(step_num)] = evaluator_file.read_text()
```

Add `evaluators` to the `ReasoningKit` model and populate it here.

---

### 2. `models.py` — add evaluators field to ReasoningKit

```python
class ReasoningKit(BaseModel):
    name: str
    path: str
    resources: dict[str, Resource]
    workflow: dict[str, WorkflowStep]
    tools: dict[str, Tool]
    evaluators: dict[str, str] = {}   # step number (str) -> evaluator prompt text
```

---

### 3. `graph.py` — State and evaluate_step node

#### 3a. Add fields to State TypedDict

```python
class State(TypedDict):
    # ... existing fields ...
    auto_evaluate: bool             # True = use judge LLM; False = interactive prompt
    evaluators: dict[str, str]      # step number -> evaluator prompt template
    judge_model: str | None         # model override for judge LLM; None = use main model
```

#### 3b. Add to `create_initial_state()`

```python
"auto_evaluate": auto_evaluate,
"evaluators": kit.evaluators,
"judge_model": judge_model,
```

#### 3c. Replace the scoring logic in `evaluate_step()`

Current code calls `prompt_for_evaluation()` unconditionally. Replace with:

```python
def evaluate_step(state: State) -> dict[str, Any]:
    if not state["evaluate"]:
        return {}

    current_step = str(state["current_step"])
    output_id = state["workflow_output_ids"][current_step]
    evaluator_template = state["evaluators"].get(current_step)

    if state["auto_evaluate"] and evaluator_template:
        score = _run_judge_llm(
            template=evaluator_template,
            prompt=state["last_prompt"],
            output=state["last_output"],
            judge_model=state["judge_model"],
            user_id=state.get("user_id"),
        )
    else:
        score = prompt_for_evaluation(state["current_step"], output_id)

    step_eval = create_step_evaluation(
        prompt=state["last_prompt"],
        output=state["last_output"],
        score=score,
        mode=state["evaluation_mode"],
    )

    new_evaluations = {**state["evaluations"], current_step: step_eval.model_dump()}

    if state["save_to_db"] and state["db_run_id"]:
        # existing DB update call — unchanged
        ...

    return {"evaluations": new_evaluations}
```

#### 3d. New helper: `_run_judge_llm()`

Add this function to `graph.py` (or extract to a new `auto_eval.py` module and import):

```python
def _run_judge_llm(
    template: str,
    prompt: str,
    output: str,
    judge_model: str | None,
    user_id: str | None,
) -> int:
    """Call judge LLM and return an integer score 0–100."""
    from .llm_factory import get_llm

    eval_prompt = template.replace("{prompt}", prompt).replace("{output}", output)

    llm = asyncio.get_event_loop().run_until_complete(
        get_llm(user_id=user_id, model=judge_model, temperature=0.0)
    )
    response = asyncio.get_event_loop().run_until_complete(
        llm.ainvoke(eval_prompt)
    )
    return _parse_score(response.content)


def _parse_score(response_text: str) -> int:
    """Extract and validate integer score from judge LLM response."""
    for line in reversed(response_text.strip().splitlines()):
        line = line.strip()
        if line.isdigit():
            score = int(line)
            if 0 <= score <= 100:
                return score
    raise ValueError(f"Could not parse valid score (0–100) from judge response: {response_text!r}")
```

Note: `evaluate_step` is a sync LangGraph node. Use `asyncio.get_event_loop().run_until_complete()` the same way the existing DB calls do it. If the event loop pattern changes elsewhere in the codebase, match that pattern.

---

### 4. `cli.py` — new flags for `run` subcommand

Add alongside the existing `--evaluate` and `--mode` arguments:

```python
run_parser.add_argument(
    "--auto-evaluate",
    action="store_true",
    help="Score each step automatically using evaluator_N.txt files instead of prompting the user.",
)
run_parser.add_argument(
    "--judge-model",
    type=str,
    default=None,
    metavar="MODEL",
    help="Model to use for auto-evaluation scoring. Defaults to the same model as the main run.",
)
```

In `_cmd_run()`, pass through to `run_reasoning_kit_async()`:

```python
kwargs["auto_evaluate"] = args.auto_evaluate
kwargs["judge_model"] = args.judge_model
```

Also: if `--auto-evaluate` is passed without `--evaluate`, automatically enable evaluation so the user doesn't have to pass both flags.

```python
if args.auto_evaluate:
    kwargs["evaluate"] = True
```

---

### 5. `run_reasoning_kit_async()` signature

Add the two new parameters:

```python
async def run_reasoning_kit_async(
    kit: ReasoningKit,
    *,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
    auto_evaluate: bool = False,
    judge_model: str | None = None,
    # ... existing params ...
) -> dict[str, str]:
```

Pass them into `create_initial_state()`.

---

## No DB Schema Changes

The `step_executions` table already has an `evaluation_score` column (integer, 0–100, nullable). Auto-eval writes to it via the existing `update_step_evaluation_in_db()` call inside `evaluate_step()` — no migration needed.

---

## Usage

```bash
# Auto-score all steps that have an evaluator file
openclerk run my-kit --auto-evaluate

# Use a specific model as judge
openclerk run my-kit --auto-evaluate --judge-model gpt-4o

# Store full prompt/output text alongside scores
openclerk run my-kit --auto-evaluate --mode transparent

# Mix: auto-eval where evaluator files exist, prompt for the rest
openclerk run my-kit --evaluate --auto-evaluate
```

---

## Summary of Files to Change

| File | Change |
|------|--------|
| `models.py` | Add `evaluators: dict[str, str] = {}` to `ReasoningKit` |
| `loader.py` | Glob `evaluator_*.txt`, populate `kit.evaluators` |
| `graph.py` | Add `auto_evaluate`, `evaluators`, `judge_model` to `State`; update `evaluate_step`; add `_run_judge_llm` and `_parse_score` helpers |
| `cli.py` | Add `--auto-evaluate` and `--judge-model` flags; auto-enable `evaluate` when `auto_evaluate` is set |
