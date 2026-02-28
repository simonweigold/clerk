import asyncio
import os
from dotenv import load_dotenv

# Load env before importing DB modules
load_dotenv()
if "SUPABASE_URL" not in os.environ:
    print("Error: SUPABASE_URL not found in environment!")
    exit(1)

from clerk.db import get_async_session, ReasoningKitRepository, KitVersionRepository

async def clean_and_create():
    async with get_async_session() as session:
        kits = ReasoningKitRepository(session)
        versions = KitVersionRepository(session)
        
        # 1. Delete if exists
        old_kit = await kits.get_by_slug('tool-test-kit')
        if old_kit:
            print(f"Deleting existing kit (ID: {old_kit.id})")
            await kits.delete(old_kit.id)
            
        # 2. Create fresh kit
        print("Creating fresh 'Tool Test Kit'")
        kit = await kits.create(
            slug='tool-test-kit',
            name='Tool Test Kit',
            description='Freshly created for CLI testing',
            is_public=True
        )
        
        print("Creating v1")
        version = await versions.create(kit.id, 'Initial clean version')
        
        print("Adding tool #1 (read_url)")
        await versions.add_tool(
            version.id,
            tool_number=1,
            tool_name='read_url',
            display_name='URL Reader'
        )
        
        print("Adding workflow step #1")
        await versions.add_workflow_step(
            version.id,
            step_number=1,
            prompt_template='Use {tool_1} to read the content of https://example.com and write a one-paragraph summary of what the page contains.'
        )
        
        print("Done!")

if __name__ == "__main__":
    asyncio.run(clean_and_create())
