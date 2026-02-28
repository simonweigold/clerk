"""LangGraph workflow execution for reasoning kits."""

import asyncio
import re
import time
from pathlib import Path
from typing import Annotated, Any, TypedDict
from uuid import UUID

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import StateGraph, END

from .evaluation import (
    complete_execution_run,
    create_execution_run,
    create_step_evaluation,
    prompt_for_evaluation,
    save_evaluation,
    save_step_to_db,
    update_step_evaluation_in_db,
)
from .embeddings import CachedEmbeddings
from .db.config import get_async_session_factory
from .models import Evaluation, ReasoningKit
from .tools import get_openai_tool_schema, get_tool


DEFAULT_MODEL = "gpt-5-mini"


class State(TypedDict):
    """TypedDict state for LangGraph."""

    kit_name: str
    kit_path: str
    resources: dict[str, str]  # resource_id -> content
    workflow_prompts: dict[str, str]  # step number -> prompt template
    workflow_output_ids: dict[str, str]  # step number -> output_id
    outputs: Annotated[dict[str, str], lambda x, y: {**x, **y}]  # output_id -> result
    current_step: int
    total_steps: int
    completed: bool
    error: str | None
    # Evaluation fields
    evaluate: bool  # Whether evaluation is enabled
    evaluation_mode: str  # "transparent" or "anonymous"
    evaluations: dict[str, dict]  # step number -> {input, output, evaluation}
    last_prompt: str  # Store the last prompt for evaluation
    last_output: str  # Store the last output for evaluation
    # Database tracking fields
    db_run_id: str | None  # Execution run UUID (as string for TypedDict)
    db_version_id: str | None  # Kit version UUID (as string for TypedDict)
    save_to_db: bool  # Whether to save execution to database
    model_used: str  # LLM model being used
    # Tool fields
    tools: dict[str, dict]  # tool_number -> {tool_name, tool_id, ...}


def create_initial_state(
    kit: ReasoningKit,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
    db_run_id: UUID | None = None,
    db_version_id: UUID | None = None,
    save_to_db: bool = False,
    model: str = DEFAULT_MODEL,
) -> State:
    """Create initial state from a reasoning kit.

    Args:
        kit: The reasoning kit to execute
        evaluate: Whether to enable step-by-step evaluation
        evaluation_mode: Either "transparent" or "anonymous"
        db_run_id: Database execution run UUID (if saving to DB)
        db_version_id: Database kit version UUID (if saving to DB)
        save_to_db: Whether to save execution to database
        model: LLM model to use

    Returns:
        Initial state for the workflow
    """
    resources = {r.resource_id: r.content for r in kit.resources.values()}
    workflow_prompts = {k: v.prompt for k, v in kit.workflow.items()}
    workflow_output_ids = {k: v.output_id for k, v in kit.workflow.items()}
    tools_data = {
        k: {
            "tool_name": v.tool_name,
            "tool_id": v.tool_id,
            "display_name": v.display_name,
            "configuration": v.configuration,
        }
        for k, v in kit.tools.items()
    }

    return State(
        kit_name=kit.name,
        kit_path=kit.path,
        resources=resources,
        workflow_prompts=workflow_prompts,
        workflow_output_ids=workflow_output_ids,
        outputs={},
        current_step=1,
        total_steps=len(kit.workflow),
        completed=False,
        error=None,
        evaluate=evaluate,
        evaluation_mode=evaluation_mode,
        evaluations={},
        last_prompt="",
        last_output="",
        db_run_id=str(db_run_id) if db_run_id else None,
        db_version_id=str(db_version_id) if db_version_id else None,
        save_to_db=save_to_db,
        model_used=model,
        tools=tools_data,
    )


def chunk_text(text: str, max_size: int = 2000, overlap: int = 200) -> list[str]:
    """Split text into chunks of maximum size with some overlap.
    
    Tries to split by paragraphs (\\n\\n) first, then falls back to lines (\\n),
    and finally chunks by character count if necessary.
    """
    if len(text) <= max_size:
        return [text]
        
    chunks = []
    paragraphs = text.split("\n\n")
    
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 <= max_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + p + "\n\n"
            else:
                # Paragraph is larger than max_size, need to split by line or chars
                lines = p.split("\n")
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= max_size:
                        current_chunk += line + "\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                            current_chunk = overlap_text + line + "\n"
                        else:
                            # Line is larger than max_size, split by chars
                            for i in range(0, len(line), max_size - overlap):
                                chunk_part = line[i:i + max_size]
                                chunks.append(chunk_part)
                            # Handle overlap for the last part
                            if chunks:
                                current_chunk = chunks[-1][-overlap:] if len(chunks[-1]) > overlap else chunks[-1]
                            
    if current_chunk and current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks


def extract_search_query(text: str) -> str:
    """Remove all {placeholders} from text to create a clean search query."""
    return re.sub(r"\{(\w+)\}", "", text).strip()


def extract_tool_refs(text: str, kit_tools: dict[str, dict]) -> list[dict]:
    """Find {tool_N} references in text and return their OpenAI tool schemas.

    Args:
        text: Prompt template that may contain {tool_1}, {tool_2}, etc.
        kit_tools: Dict of tool_number -> {tool_name, tool_id, ...} from kit

    Returns:
        List of OpenAI-compatible tool schemas for referenced tools
    """
    placeholders = re.findall(r"\{(tool_\d+)\}", text)
    schemas = []
    seen = set()

    for placeholder in placeholders:
        # Extract number from "tool_1" -> "1"
        num = placeholder.replace("tool_", "")
        if num in kit_tools and placeholder not in seen:
            tool_name = kit_tools[num]["tool_name"]
            schema = get_openai_tool_schema(tool_name)
            if schema:
                schemas.append(schema)
                seen.add(placeholder)

    return schemas


def remove_tool_placeholders(text: str, kit_tools: dict[str, dict] | None = None) -> str:
    """Replace {tool_N} placeholders with the tool's name for a readable prompt.

    Instead of just stripping placeholders, we replace them with a readable
    reference like 'the read_url tool' so the LLM knows which tool to use.
    The actual tool definitions are passed separately via the tools parameter.
    """
    import re as _re

    def _replace_match(m: _re.Match) -> str:
        num = m.group(1)
        if kit_tools and num in kit_tools:
            name = kit_tools[num].get("display_name") or kit_tools[num].get("tool_name", "")
            return f"the {name} tool"
        return ""

    cleaned = _re.sub(r"\{tool_(\d+)\}", _replace_match, text)
    # Collapse any double spaces left behind
    cleaned = _re.sub(r"  +", " ", cleaned)
    return cleaned.strip()


def resolve_placeholders(
    text: str, resources: dict[str, str], outputs: dict[str, str],
    resource_size_threshold: int = 4000, max_chunks: int = 4
) -> str:
    """Resolve {placeholder} references in text, using RAG for large resources.

    Args:
        text: Text with placeholders like {resource_1} or {workflow_1}
        resources: Dict of resource_id -> content
        outputs: Dict of output_id -> result
        resource_size_threshold: Character threshold to trigger RAG
        max_chunks: Maximum number of chunks to retrieve for large resources

    Returns:
        Text with all placeholders resolved
    """
    placeholders = re.findall(r"\{(\w+)\}", text)
    if not placeholders:
        return text

    # Extract clean search query from prompt to use for RAG
    search_query = extract_search_query(text)
    
    # We load embeddings lazily to avoid unnecessary initialization
    embeddings = None

    for placeholder in placeholders:
        if placeholder in resources:
            content = resources[placeholder]
            
            # If resource is large, use simple RAG
            if len(content) > resource_size_threshold and search_query:
                try:
                    if embeddings is None:
                        embeddings = OpenAIEmbeddings()
                        
                    chunks = chunk_text(content)
                    vectorstore = InMemoryVectorStore.from_texts(chunks, embeddings)
                    results = vectorstore.similarity_search(search_query, k=max_chunks)
                    
                    # Combine relevant chunks
                    relevant_content = "\n\n... [Context skipped] ...\n\n".join([doc.page_content for doc in results])
                    text = text.replace(f"{{{placeholder}}}", relevant_content)
                    print(f"RAG triggered for {placeholder}: chunked {len(content)} chars into {len(chunks)} parts, retrieved {len(results)} chunks.")
                except Exception as e:
                    print(f"Warning: RAG failed for {placeholder}, falling back to full text. Error: {e}")
                    text = text.replace(f"{{{placeholder}}}", content)
            else:
                text = text.replace(f"{{{placeholder}}}", content)
                
        elif placeholder in outputs:
            text = text.replace(f"{{{placeholder}}}", outputs[placeholder])

    return text


async def aresolve_placeholders(
    text: str, resources: dict[str, str], outputs: dict[str, str],
    resource_size_threshold: int = 4000, max_chunks: int = 4
) -> str:
    """Async version of resolve_placeholders for non-blocking execution."""
    placeholders = re.findall(r"\{(\w+)\}", text)
    if not placeholders:
        return text

    search_query = extract_search_query(text)
    embeddings = None

    for placeholder in placeholders:
        if placeholder in resources:
            content = resources[placeholder]
            
            if len(content) > resource_size_threshold and search_query:
                try:
                    if embeddings is None:
                        base_embeddings = OpenAIEmbeddings()
                        session_factory = get_async_session_factory()
                        # Wrap the OpenAI embeddings with our database cache handler
                        embeddings = CachedEmbeddings(
                            underlying_embeddings=base_embeddings, 
                            session_factory=session_factory
                        )
                        
                    chunks = chunk_text(content)
                    vectorstore = await InMemoryVectorStore.afrom_texts(chunks, embeddings)
                    results = await vectorstore.asimilarity_search(search_query, k=max_chunks)
                    
                    relevant_content = "\n\n... [Context skipped] ...\n\n".join([doc.page_content for doc in results])
                    text = text.replace(f"{{{placeholder}}}", relevant_content)
                except Exception as e:
                    print(f"Warning: async RAG failed for {placeholder}, falling back to full text. Error: {e}")
                    text = text.replace(f"{{{placeholder}}}", content)
            else:
                text = text.replace(f"{{{placeholder}}}", content)
                
        elif placeholder in outputs:
            text = text.replace(f"{{{placeholder}}}", outputs[placeholder])

    return text


def execute_step(state: State) -> dict[str, Any]:
    """Execute the current workflow step."""
    current_step = str(state["current_step"])

    if current_step not in state["workflow_prompts"]:
        return {
            "completed": True,
            "error": f"Step {current_step} not found in workflow",
        }

    prompt_template = state["workflow_prompts"][current_step]
    output_id = state["workflow_output_ids"][current_step]

    # Resolve placeholders in prompt
    prompt = resolve_placeholders(prompt_template, state["resources"], state["outputs"])

    # Extract tool references and clean prompt
    kit_tools = state.get("tools", {})
    openai_tools = extract_tool_refs(prompt_template, kit_tools)
    clean_prompt = remove_tool_placeholders(prompt, kit_tools)

    # Track execution time
    start_time = time.time()

    # Execute with LLM
    llm = ChatOpenAI(model=state["model_used"], temperature=0)

    if openai_tools:
        # Tool-aware execution
        from langchain_core.messages import HumanMessage, ToolMessage

        llm_with_tools = llm.bind_tools(
            [t["function"] for t in openai_tools]
        )
        messages = [HumanMessage(content=clean_prompt)]
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # Tool-call loop
        max_rounds = 5
        for _ in range(max_rounds):
            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool_def = get_tool(tool_call["name"])
                if tool_def:
                    try:
                        tool_result = asyncio.run(tool_def.execute(tool_call["args"]))
                    except Exception as te:
                        tool_result = f"Error executing tool: {te}"
                else:
                    tool_result = f"Unknown tool: {tool_call['name']}"

                messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                    )
                )

            response = llm_with_tools.invoke(messages)
            messages.append(response)

        result = str(response.content)
    else:
        # Standard execution without tools
        response = llm.invoke(clean_prompt)
        result = str(response.content)

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Get token usage if available
    tokens_used = None
    if hasattr(response, "response_metadata"):
        metadata = response.response_metadata
        if "token_usage" in metadata:
            usage = metadata["token_usage"]
            tokens_used = usage.get("total_tokens")

    # Update outputs
    new_outputs = {**state["outputs"], output_id: result}

    print(f"\n{'=' * 60}")
    print(f"Step {current_step} - Output ID: {output_id}")
    print(f"{'=' * 60}")
    print(f"Prompt:\n{clean_prompt[:200]}..." if len(clean_prompt) > 200 else f"Prompt:\n{clean_prompt}")
    print(f"\nResult:\n{result}")
    print(f"{'=' * 60}\n")

    # Save to database if enabled (run in event loop)
    if state["save_to_db"] and state["db_run_id"]:
        try:
            asyncio.get_event_loop().run_until_complete(
                save_step_to_db(
                    run_id=UUID(state["db_run_id"]),
                    step_number=int(current_step),
                    prompt=clean_prompt,
                    output=result,
                    mode=state["evaluation_mode"],
                    model_used=state["model_used"],
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                )
            )
        except RuntimeError:
            # No event loop running, create a new one
            asyncio.run(
                save_step_to_db(
                    run_id=UUID(state["db_run_id"]),
                    step_number=int(current_step),
                    prompt=clean_prompt,
                    output=result,
                    mode=state["evaluation_mode"],
                    model_used=state["model_used"],
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                )
            )

    return {
        "outputs": new_outputs,
        "last_prompt": clean_prompt,
        "last_output": result,
    }


def advance_step(state: State) -> dict[str, Any]:
    """Advance to the next step or mark as completed."""
    next_step = state["current_step"] + 1

    if next_step > state["total_steps"]:
        return {
            "completed": True,
            "current_step": next_step,
        }

    return {
        "current_step": next_step,
    }


def evaluate_step(state: State) -> dict[str, Any]:
    """Prompt user for evaluation of the current step if evaluation is enabled."""
    if not state["evaluate"]:
        return {}

    current_step = str(state["current_step"])
    output_id = state["workflow_output_ids"][current_step]

    # Prompt user for evaluation score
    score = prompt_for_evaluation(state["current_step"], output_id)

    # Create step evaluation based on mode
    step_eval = create_step_evaluation(
        prompt=state["last_prompt"],
        output=state["last_output"],
        score=score,
        mode=state["evaluation_mode"],
    )

    # Update evaluations dict
    new_evaluations = {
        **state["evaluations"],
        current_step: step_eval.model_dump(),
    }

    # Update evaluation in database if enabled
    if state["save_to_db"] and state["db_run_id"]:
        try:
            asyncio.get_event_loop().run_until_complete(
                update_step_evaluation_in_db(
                    run_id=UUID(state["db_run_id"]),
                    step_number=int(current_step),
                    score=score,
                )
            )
        except RuntimeError:
            # No event loop running, create a new one
            asyncio.run(
                update_step_evaluation_in_db(
                    run_id=UUID(state["db_run_id"]),
                    step_number=int(current_step),
                    score=score,
                )
            )

    return {
        "evaluations": new_evaluations,
    }


def should_continue(state: State) -> str:
    """Determine next node based on state."""
    if state["completed"]:
        return "end"
    if state["error"]:
        return "end"
    return "execute"


def build_graph():
    """Build the LangGraph workflow."""
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("execute", execute_step)
    graph.add_node("evaluate", evaluate_step)
    graph.add_node("advance", advance_step)

    # Set entry point
    graph.set_entry_point("execute")

    # Add edges: execute -> evaluate -> advance -> (loop or end)
    graph.add_edge("execute", "evaluate")
    graph.add_edge("evaluate", "advance")
    graph.add_conditional_edges(
        "advance",
        should_continue,
        {
            "execute": "execute",
            "end": END,
        },
    )

    return graph.compile()


def run_reasoning_kit(
    kit: ReasoningKit,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
    save_to_db: bool = False,
    db_version_id: UUID | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    """Run a reasoning kit through the workflow.

    Args:
        kit: The reasoning kit to execute
        evaluate: Whether to enable step-by-step evaluation
        evaluation_mode: Either "transparent" or "anonymous"
        save_to_db: Whether to save execution to database
        db_version_id: Database kit version UUID (required if save_to_db=True)
        model: LLM model to use

    Returns:
        Dict of all outputs from the workflow
    """
    # Create database execution run if enabled
    db_run_id: UUID | None = None
    if save_to_db:
        if db_version_id is None:
            print(
                "Warning: save_to_db=True but no db_version_id provided, skipping DB tracking"
            )
            save_to_db = False
        else:
            try:
                db_run_id = asyncio.run(
                    create_execution_run(
                        version_id=db_version_id,
                        storage_mode=evaluation_mode,
                    )
                )
                print(f"Created execution run: {db_run_id}")
            except Exception as e:
                print(f"Warning: Could not create execution run: {e}")
                save_to_db = False

    graph = build_graph()
    initial_state = create_initial_state(
        kit,
        evaluate,
        evaluation_mode,
        db_run_id=db_run_id,
        db_version_id=db_version_id,
        save_to_db=save_to_db,
        model=model,
    )

    print(f"\n{'#' * 60}")
    print(f"Running Reasoning Kit: {kit.name}")
    print(f"{'#' * 60}")
    print(f"Resources: {list(initial_state['resources'].keys())}")
    print(f"Workflow Steps: {initial_state['total_steps']}")
    print(f"Model: {model}")
    if evaluate:
        print(f"Evaluation: enabled ({evaluation_mode} mode)")
    if save_to_db:
        print(f"Database tracking: enabled")
    print(f"{'#' * 60}\n")

    error_message: str | None = None
    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        error_message = str(e)
        print(f"\nError during execution: {e}")
        final_state = initial_state
        final_state["error"] = error_message

    print(f"\n{'#' * 60}")
    print("Workflow Completed!" if not error_message else "Workflow Failed!")
    print(f"{'#' * 60}")

    if not error_message:
        print("Final Outputs:")
        for output_id, result in final_state["outputs"].items():
            print(f"\n{output_id}:")
            print(result)
    print(f"{'#' * 60}\n")

    # Save evaluation if enabled (to local file)
    if evaluate and final_state["evaluations"] and not kit.path.startswith("db://"):
        # Convert dict representations back to StepEvaluation objects
        from .models import StepEvaluation

        steps: dict[str, StepEvaluation] = {
            str(k): StepEvaluation(**v) if isinstance(v, dict) else v
            for k, v in final_state["evaluations"].items()
        }
        evaluation = Evaluation(
            mode=evaluation_mode,
            steps=steps,
        )
        eval_file = save_evaluation(Path(kit.path), evaluation)
        print(f"Evaluation saved to: {eval_file}\n")

    # Complete database execution run
    if save_to_db and db_run_id:
        try:
            asyncio.run(complete_execution_run(db_run_id, error=error_message))
            status = "failed" if error_message else "completed"
            print(f"Execution run {status}: {db_run_id}\n")
        except Exception as e:
            print(f"Warning: Could not complete execution run: {e}")

    return final_state["outputs"]


async def run_reasoning_kit_async(
    kit: ReasoningKit,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
    save_to_db: bool = False,
    db_version_id: UUID | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    """Async version of run_reasoning_kit for use in async contexts.

    Executes each workflow step using async LLM calls (ainvoke) and
    native async database operations, avoiding event loop blocking.

    Args:
        kit: The reasoning kit to execute
        evaluate: Whether to enable step-by-step evaluation
        evaluation_mode: Either "transparent" or "anonymous"
        save_to_db: Whether to save execution to database
        db_version_id: Database kit version UUID (required if save_to_db=True)
        model: LLM model to use

    Returns:
        Dict of all outputs from the workflow
    """
    # Create database execution run if enabled
    db_run_id: UUID | None = None
    if save_to_db:
        if db_version_id is None:
            save_to_db = False
        else:
            try:
                db_run_id = await create_execution_run(
                    version_id=db_version_id,
                    storage_mode=evaluation_mode,
                )
            except Exception:
                save_to_db = False

    resources = {r.resource_id: r.content for r in kit.resources.values()}
    outputs: dict[str, str] = {}
    llm = ChatOpenAI(model=model, temperature=0)
    error_message: str | None = None

    # Build tool data from kit
    kit_tools = {
        k: {
            "tool_name": v.tool_name,
            "tool_id": v.tool_id,
            "display_name": v.display_name,
            "configuration": v.configuration,
        }
        for k, v in kit.tools.items()
    }

    for step_key in sorted(kit.workflow.keys(), key=int):
        step = kit.workflow[step_key]
        step_num = int(step_key)

        prompt = await aresolve_placeholders(step.prompt, resources, outputs)

        # Extract tool references and clean prompt
        openai_tools = extract_tool_refs(step.prompt, kit_tools)
        clean_prompt = remove_tool_placeholders(prompt, kit_tools)

        start_time = time.time()

        try:
            if openai_tools:
                # Tool-aware execution
                from langchain_core.messages import HumanMessage, ToolMessage

                llm_with_tools = llm.bind_tools(
                    [t["function"] for t in openai_tools]
                )
                messages = [HumanMessage(content=clean_prompt)]
                response = await llm_with_tools.ainvoke(messages)
                messages.append(response)

                # Tool-call loop
                max_rounds = 5
                for _ in range(max_rounds):
                    if not response.tool_calls:
                        break

                    for tool_call in response.tool_calls:
                        tool_def = get_tool(tool_call["name"])
                        if tool_def:
                            try:
                                tool_result = await tool_def.execute(tool_call["args"])
                            except Exception as te:
                                tool_result = f"Error executing tool: {te}"
                        else:
                            tool_result = f"Unknown tool: {tool_call['name']}"

                        messages.append(
                            ToolMessage(
                                content=tool_result,
                                tool_call_id=tool_call["id"],
                            )
                        )

                    response = await llm_with_tools.ainvoke(messages)
                    messages.append(response)

                result = str(response.content)
            else:
                # Standard execution without tools
                response = await llm.ainvoke(clean_prompt)
                result = str(response.content)

            latency_ms = int((time.time() - start_time) * 1000)

            tokens_used = None
            if hasattr(response, "response_metadata"):
                metadata = response.response_metadata
                if "token_usage" in metadata:
                    tokens_used = metadata["token_usage"].get("total_tokens")

            outputs[step.output_id] = result

            # Save step to database
            if save_to_db and db_run_id:
                try:
                    await save_step_to_db(
                        run_id=db_run_id,
                        step_number=step_num,
                        prompt=clean_prompt,
                        output=result,
                        mode=evaluation_mode,
                        model_used=model,
                        tokens_used=tokens_used,
                        latency_ms=latency_ms,
                    )
                except Exception:
                    pass

        except Exception as e:
            error_message = str(e)
            break

    # Complete database execution run
    if save_to_db and db_run_id:
        try:
            await complete_execution_run(db_run_id, error=error_message)
        except Exception:
            pass

    if error_message:
        raise RuntimeError(error_message)

    return outputs
