"""End-to-end tests for MCP integration with opencaselaw.ch."""

import asyncio
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables from project root .env
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from openclerk.graph import run_reasoning_kit, run_reasoning_kit_async  # noqa: E402
from openclerk.loader import load_reasoning_kit  # noqa: E402
from openclerk.mcp_client import close_mcp_servers, init_mcp_servers  # noqa: E402
from openclerk.tools import clear_mcp_tools, get_tool  # noqa: E402

KIT_PATH = Path(__file__).parent.parent.parent.parent / "reasoning_kits" / "test_swiss_legal"


@pytest.fixture(autouse=True)
def ensure_openai_key():
    """Skip tests if OPENAI_API_KEY is not available."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")


class TestMcpInitialization:
    """Tests for MCP server initialization and tool registration."""

    @pytest.mark.asyncio
    async def test_kit_mcp_config_loaded(self):
        """Kit-local mcp_servers.json should be loaded and tools registered."""
        kit_mcp = KIT_PATH / "mcp_servers.json"
        assert kit_mcp.exists(), "Kit MCP config file not found"

        clear_mcp_tools()
        await init_mcp_servers(
            config_path="mcp_servers.json",
            kit_config_path=str(kit_mcp),
        )
        try:
            # Verify opencaselaw tools are registered
            assert get_tool("get_law") is not None, "get_law tool not registered"
            assert get_tool("search_decisions") is not None, "search_decisions tool not registered"

            law_tool = get_tool("get_law")
            # SSE/HTTP transport tools are registered as "builtin" so they are
            # visible to all users without requiring DB activation.
            assert law_tool.source == "builtin", f"Expected source 'builtin', got {law_tool.source}"
        finally:
            await close_mcp_servers()

    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self):
        """MCP tools should be directly callable and return real data."""
        kit_mcp = KIT_PATH / "mcp_servers.json"
        clear_mcp_tools()
        await init_mcp_servers(
            config_path="mcp_servers.json",
            kit_config_path=str(kit_mcp),
        )
        try:
            law_tool = get_tool("get_law")
            assert law_tool is not None

            result = await law_tool.execute({"abbreviation": "OR", "article": "1"})
            assert isinstance(result, str)
            assert len(result) > 0
            # Should contain Swiss legal content
            assert (
                "Vertrag" in result
                or "contrat" in result
                or "contratto" in result
                or "Bundesgesetz" in result
            )
        finally:
            await close_mcp_servers()


class TestMcpReasoningKit:
    """End-to-end tests running a reasoning kit with MCP tools."""

    @pytest.mark.asyncio
    async def test_load_swiss_legal_kit(self):
        """The test Swiss legal kit should load correctly with MCP tools."""
        kit = load_reasoning_kit(KIT_PATH)
        assert kit.name == "test_swiss_legal"
        assert "1" in kit.tools
        assert kit.tools["1"].tool_name == "get_law"
        assert "2" in kit.tools
        assert kit.tools["2"].tool_name == "search_decisions"

    @pytest.mark.asyncio
    async def test_run_swiss_legal_kit_async(self):
        """Async kit execution should successfully call MCP tools and produce output."""
        kit = load_reasoning_kit(KIT_PATH)
        kit_mcp = KIT_PATH / "mcp_servers.json"

        clear_mcp_tools()
        await init_mcp_servers(
            config_path="mcp_servers.json",
            kit_config_path=str(kit_mcp),
        )
        try:
            outputs = await run_reasoning_kit_async(kit, evaluate=False, save_to_db=False)

            assert (
                "workflow_1" in outputs
            ), f"Expected workflow_1 in outputs, got {list(outputs.keys())}"
            result = outputs["workflow_1"]
            assert isinstance(result, str)
            # Retry once if the LLM returns empty content (transient issue)
            if len(result) < 50:
                outputs = await run_reasoning_kit_async(kit, evaluate=False, save_to_db=False)
                result = outputs["workflow_1"]
            assert len(result) > 50, f"Output too short: {result}"

            # The answer should mention something about contract requirements
            result_lower = result.lower()
            assert any(
                keyword in result_lower
                for keyword in [
                    "vertrag",
                    "contract",
                    "abschluss",
                    "willens",
                    "consent",
                    "art.",
                    "article",
                    "or",
                    "zgb",
                ]
            ), f"Result does not contain expected legal keywords: {result[:500]}"
        finally:
            await close_mcp_servers()


def test_run_swiss_legal_kit_sync():
    """Sync kit execution should work from a purely synchronous context."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    kit = load_reasoning_kit(KIT_PATH)
    kit_mcp = KIT_PATH / "mcp_servers.json"

    clear_mcp_tools()
    # Use a single persistent event loop for MCP init, kit execution, and cleanup
    # so that MCP sessions remain valid throughout.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            init_mcp_servers(
                config_path="mcp_servers.json",
                kit_config_path=str(kit_mcp),
            )
        )
        outputs = run_reasoning_kit(kit, evaluate=False, save_to_db=False, model="gpt-5.4-nano")

        assert (
            "workflow_1" in outputs
        ), f"Expected workflow_1 in outputs, got {list(outputs.keys())}"
        result = outputs["workflow_1"]
        assert isinstance(result, str)
        assert len(result) > 50, f"Output too short: {result}"

        # The answer should mention something about contract requirements
        result_lower = result.lower()
        assert any(
            keyword in result_lower
            for keyword in [
                "vertrag",
                "contract",
                "abschluss",
                "willens",
                "consent",
                "art.",
                "article",
                "or",
                "zgb",
            ]
        ), f"Result does not contain expected legal keywords: {result[:500]}"
    finally:
        loop.run_until_complete(close_mcp_servers())
        loop.close()
