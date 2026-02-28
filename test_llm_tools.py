import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from clerk.loader import load_reasoning_kit_from_db
from clerk.graph import run_reasoning_kit_async
from clerk.models import ReasoningKit, Resource, WorkflowStep, Tool

async def main():
    loaded = await load_reasoning_kit_from_db('tool-test-kit')
    base_kit = loaded.kit
    
    # Create an isolated mock kit with just 1 step to test tools
    step = base_kit.workflow["1"]
    
    # We must construct a valid ReasoningKit pydantic model for run_reasoning_kit_async
    kit = ReasoningKit(
        name="Mock Kit",
        schema_version="1.0",
        resources={},
        workflow={"1": step},
        tools=base_kit.tools,
    )
    
    print(f"Loaded tools: {kit.tools}")
    print(f"Step 1 prompt: {step.prompt}")
    
    print("\nExecuting step 1 via Async graph path...")
    
    # Hook stdout briefly to see the raw output
    import io
    sys.stdout = io.StringIO()
    try:
        result = await run_reasoning_kit_async(kit, evaluate=False, save_to_db=False)
    finally:
        output = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__
        
    print(output)
    
    print("\n" + "="*50)
    print("FINAL RESULT")
    print("="*50)
    print(result.get("outputs", {}).get(step.output_id))

if __name__ == "__main__":
    asyncio.run(main())
