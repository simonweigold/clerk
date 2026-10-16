"""Prompt-chaining executor for reasoning kits.

The runner executes instructions sequentially. Each step:
1. Resolves {resource_N} and {workflow_N} placeholders in its prompt.
2. Optionally exposes {tool_N} references as OpenAI-format tools.
3. Calls the LLM; if tools are present, runs the tool-call loop.
4. Stores the response as workflow_N output for downstream steps.
5. Optionally runs evaluators (judge LLM or interactive).

No LangGraph, no database, no state machine. Just an async for-loop.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from .evaluator import (
    aggregate_scores,
    create_step_evaluation,
    prompt_for_evaluation,
    run_judge,
    save_evaluation,
)
from .llm import acompletion, get_default_model
from .models import Evaluation, ReasoningKit, StepEvaluation
from .tools import get_openai_tool_schema, get_tool

logger = logging.getLogger(__name__)

DEFAULT_MODEL = get_default_model()
TOOL_MAX_ROUNDS = 5
RAG_THRESHOLD_CHARS = 400_000
MAX_RAG_CHUNKS = 4


def _preview(text: str, max_len: int = 120) -> str:
    """Return a one-line preview of text."""
    if not text:
        return "<empty>"
    if text.startswith("Error"):
        return text[:max_len]
    single = text.replace("\n", " ")
    if len(single) > max_len:
        return single[:max_len - 3] + "..."
    return single


def extract_tool_refs(text: str, kit_tools: dict[str, dict]) -> list[dict]:
    """Find {tool_N} references and return their OpenAI tool schemas."""
    placeholders = re.findall(r"\{(tool_\d+)\}", text)
    schemas: list[dict] = []
    seen: set[str] = set()

    for placeholder in placeholders:
        num = placeholder.replace("tool_", "")
        if num in kit_tools and placeholder not in seen:
            tool_name = kit_tools[num]["tool_name"]
            schema = get_openai_tool_schema(tool_name)
            if schema:
                schemas.append(schema)
                seen.add(placeholder)

    return schemas


def remove_tool_placeholders(text: str, kit_tools: dict[str, dict]) -> str:
    """Replace {tool_N} placeholders with readable tool references."""

    def _replace_match(m: re.Match) -> str:
        num = m.group(1)
        if kit_tools and num in kit_tools:
            name = kit_tools[num].get("display_name") or kit_tools[num].get("tool_name", "")
            return f"the {name} tool"
        return ""

    cleaned = re.sub(r"\{tool_(\d+)\}", _replace_match, text)
    cleaned = re.sub(r"  +", " ", cleaned)
    return cleaned.strip()


def chunk_text(text: str, max_size: int = 2000, overlap: int = 200) -> list[str]:
    """Split text into chunks of maximum size with overlap."""
    if len(text) <= max_size:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 <= max_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + p + "\n\n"
            else:
                lines = p.split("\n")
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= max_size:
                        current_chunk += line + "\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            overlap_text = (
                                current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                            )
                            current_chunk = overlap_text + line + "\n"
                        else:
                            for i in range(0, len(line), max_size - overlap):
                                chunks.append(line[i : i + max_size])
                            if chunks:
                                current_chunk = (
                                    chunks[-1][-overlap:]
                                    if len(chunks[-1]) > overlap
                                    else chunks[-1]
                                )

    if current_chunk and current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def extract_search_query(text: str) -> str:
    """Remove all {placeholders} from text to create a clean search query."""
    return re.sub(r"\{(\w+)\}", "", text).strip()


def _lite_top_chunks(chunks: list[str], query: str, k: int) -> str:
    """Pick top-k chunks by keyword overlap (no embedding dep).

    Used as a fallback RAG when no embeddings are available.
    """
    query_words = set(re.findall(r"\w+", query.lower()))
    if not query_words:
        return "\n\n... [Context skipped] ...\n\n".join(chunks[:k])

    scored = []
    for chunk in chunks:
        chunk_words = set(re.findall(r"\w+", chunk.lower()))
        overlap = len(query_words & chunk_words)
        scored.append((overlap, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [chunk for _, chunk in scored[:k]]
    return "\n\n... [Context skipped] ...\n\n".join(top)


async def aresolve_placeholders(
    text: str,
    resources: dict[str, str],
    outputs: dict[str, str],
) -> str:
    """Resolve {placeholder} references in text, using lite RAG for large resources."""
    placeholders = re.findall(r"\{(\w+)\}", text)
    if not placeholders:
        return text

    search_query = extract_search_query(text)

    for placeholder in placeholders:
        if placeholder in resources:
            content = resources[placeholder]
            if not isinstance(content, str):
                content = str(content) if content else ""

            if len(content) > RAG_THRESHOLD_CHARS and search_query:
                try:
                    chunks = chunk_text(content)
                    relevant = _lite_top_chunks(chunks, search_query, MAX_RAG_CHUNKS)
                    text = text.replace(f"{{{placeholder}}}", relevant)
                except Exception as e:
                    logger.debug(f"RAG failed for {placeholder}, falling back: {e}")
                    text = text.replace(f"{{{placeholder}}}", content)
            else:
                text = text.replace(f"{{{placeholder}}}", content)

        elif placeholder in outputs:
            text = text.replace(f"{{{placeholder}}}", outputs[placeholder])

    return text


def _parse_tool_args(raw: Any) -> dict[str, Any]:
    """Tool call args may be a JSON string (OpenAI) or already a dict."""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    if isinstance(raw, dict):
        return raw
    return {}


async def run_kit_async(
    kit: ReasoningKit,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
    model: str = DEFAULT_MODEL,
    auto_evaluate: bool = False,
    judge_model: str | None = None,
    evaluator_aggregation: str = "average",
    verbose: bool = False,
    collected_prompts: dict[str, str] | None = None,
) -> dict[str, str]:
    """Run a reasoning kit via prompt-chaining.

    Args:
        kit: The reasoning kit to execute.
        evaluate: Whether to enable evaluation.
        evaluation_mode: 'transparent' or 'anonymous'.
        model: LLM model to use.
        auto_evaluate: Use judge LLM instead of user prompt.
        judge_model: Model for judge (defaults to main model).
        evaluator_aggregation: Score aggregation strategy.
        verbose: Print execution details.
        collected_prompts: Optional dict to populate with resolved prompts per step.

    Returns:
        Dict mapping output_id -> result text.
    """
    resources = {r.resource_id: r.content for r in kit.resources.values()}
    outputs: dict[str, str] = {}
    evaluations: dict[str, dict] = {}

    kit_tools = {
        k: {
            "tool_name": v.tool_name,
            "tool_id": v.tool_id,
            "display_name": v.display_name,
            "configuration": v.configuration,
        }
        for k, v in kit.tools.items()
    }

    if verbose:
        print(f"\n{'#' * 60}")
        print(f"Running Reasoning Kit: {kit.name}")
        print(f"{'#' * 60}")
        print(f"Resources: {list(resources.keys())}")
        print(f"Workflow Steps: {len(kit.workflow)}")
        print(f"Model: {model}")
        if evaluate:
            print(f"Evaluation: enabled ({evaluation_mode} mode)")
        print(f"{'#' * 60}\n")

    error_message: str | None = None

    for step_key in sorted(kit.workflow.keys(), key=int):
        step = kit.workflow[step_key]
        step_num = int(step_key)

        try:
            prompt = await aresolve_placeholders(step.prompt, resources, outputs)
            openai_tools = extract_tool_refs(step.prompt, kit_tools)
            clean_prompt = remove_tool_placeholders(prompt, kit_tools)

            if collected_prompts is not None:
                collected_prompts[step.output_id] = clean_prompt

            tool_schemas = [t["function"] for t in openai_tools]
            messages: list[dict[str, Any]] = [{"role": "user", "content": clean_prompt}]

            if tool_schemas:
                tool_names = [t["name"] for t in tool_schemas]
                if verbose:
                    print(f"\n{'=' * 60}")
                    print(f"Step {step_num} — Tools: {', '.join(tool_names)}")
                    print(f"{'=' * 60}")
                    print(f"[Prompt]\n{clean_prompt}\n")

                response = await acompletion(
                    model=model,
                    messages=messages,
                    tools=tool_schemas,
                    temperature=0.0,
                )

                for _ in range(TOOL_MAX_ROUNDS):
                    msg = response.choices[0].message
                    if not msg.tool_calls:
                        break
                    messages.append(msg.model_dump(exclude_none=True))

                    for tool_call in msg.tool_calls:
                        tool_def = get_tool(tool_call.function.name)
                        if tool_def:
                            args = _parse_tool_args(tool_call.function.arguments)
                            if verbose:
                                args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
                                print(f"  → {tool_call.function.name}({args_str})")
                            try:
                                tool_result = await tool_def.execute(args)
                            except Exception as te:
                                tool_result = f"Error executing tool: {te}"
                            if verbose:
                                print(f"  ← ({len(tool_result)} chars) {_preview(tool_result)}")
                        else:
                            tool_result = f"Unknown tool: {tool_call.function.name}"
                            if verbose:
                                print(f"  ← Unknown tool: {tool_call.function.name}")

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_result,
                            }
                        )

                    response = await acompletion(
                        model=model,
                        messages=messages,
                        tools=tool_schemas,
                        temperature=0.0,
                    )

                result = response.choices[0].message.content or ""

                if not result:
                    logger.info(f"Step {step_num} — Forcing final response after tool rounds")
                    if messages and isinstance(messages[-1], dict) and messages[-1].get("tool_calls"):
                        messages.pop()
                    final = await acompletion(
                        model=model,
                        messages=messages,
                        tools=tool_schemas,
                        tool_choice="none",
                        temperature=0.0,
                    )
                    result = final.choices[0].message.content or ""

                if verbose:
                    print(f"\n[Final Response]\n{result}")
                    print(f"{'=' * 60}\n")
            else:
                response = await acompletion(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                )
                result = response.choices[0].message.content or ""

                if verbose:
                    print(f"\n{'=' * 60}")
                    print(f"Step {step_num} — {step.output_id}")
                    print(f"{'=' * 60}")
                    print(f"[Prompt]\n{clean_prompt}\n")
                    print(f"[Response]\n{result}")
                    print(f"{'=' * 60}\n")

            outputs[step.output_id] = result

            if evaluate:
                evaluator_list = kit.evaluators.get(str(step_num), [])
                step_aggregation = kit.evaluator_aggregations.get(
                    str(step_num), evaluator_aggregation
                )
                if auto_evaluate and evaluator_list:
                    scores = await asyncio.gather(
                        *[
                            run_judge(
                                template=template,
                                prompt=clean_prompt,
                                output=result,
                                judge_model=judge_model or model,
                            )
                            for _, template in evaluator_list
                        ]
                    )
                    dimension_scores = [
                        {"label": label, "score": s}
                        for (label, _), s in zip(evaluator_list, scores)
                    ]
                    score = aggregate_scores(
                        [int(d["score"]) for d in dimension_scores], step_aggregation
                    )
                    if verbose:
                        if len(dimension_scores) > 1:
                            print(f"\nStep {step_num} — Evaluation")
                            for d in dimension_scores:
                                print(f"  {d['label']:<16} {d['score']:>3}/100")
                            print(f"  {'─' * 20}")
                            print(f"  {'Aggregate':<16} {score:>3}/100  ({step_aggregation})")
                        else:
                            print(f"\nStep {step_num} — Score: {score}/100")
                else:
                    score = await asyncio.to_thread(
                        prompt_for_evaluation, step_num, step.output_id
                    )
                    dimension_scores = [{"label": "default", "score": score}]

                step_eval = create_step_evaluation(
                    prompt=clean_prompt,
                    output=result,
                    score=score,
                    mode=evaluation_mode,
                    dimension_scores=dimension_scores,
                )
                evaluations[str(step_num)] = step_eval.model_dump()

        except Exception as e:
            error_message = str(e)
            if verbose:
                print(f"\nError during execution: {e}")
            break

    if verbose:
        print(f"\n{'#' * 60}")
        print("Workflow Completed!" if not error_message else "Workflow Failed!")
        print(f"{'#' * 60}")
        if not error_message:
            print("Final Outputs:")
            for output_id, result in outputs.items():
                print(f"\n{output_id}:")
                print(result)
        print(f"{'#' * 60}\n")

    if evaluate and evaluations:
        steps_eval = {
            str(k): StepEvaluation(**v) if isinstance(v, dict) else v
            for k, v in evaluations.items()
        }
        evaluation = Evaluation(mode=evaluation_mode, steps=steps_eval)
        eval_file = save_evaluation(Path(kit.path), evaluation)
        if verbose:
            print(f"Evaluation saved to: {eval_file}\n")

    if error_message:
        raise RuntimeError(error_message)

    return outputs