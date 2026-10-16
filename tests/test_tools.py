"""Tests for the global tool registry."""

from reasoning_kits.tools import (
    TOOL_REGISTRY,
    clear_mcp_tools,
    get_openai_tool_schema,
    get_tool,
    list_tools,
    register_tool,
    ToolDefinition,
)


def test_builtin_tools_registered() -> None:
    assert get_tool("read_url") is not None
    assert get_tool("jina_reader") is not None


def test_get_tool_missing() -> None:
    assert get_tool("nonexistent_tool") is None


def test_list_tools_includes_builtins() -> None:
    tools = list_tools()
    names = {t.name for t in tools}
    assert "read_url" in names
    assert "jina_reader" in names


def test_get_openai_tool_schema() -> None:
    schema = get_openai_tool_schema("read_url")
    assert schema is not None
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "read_url"
    assert "url" in schema["function"]["parameters"]["properties"]


def test_clear_mcp_tools_keeps_builtins() -> None:
    register_tool(
        ToolDefinition(
            name="fake_mcp_tool",
            description="test",
            parameters={},
            execute=lambda *a, **kw: "",
            source="mcp",
        )
    )
    assert get_tool("fake_mcp_tool") is not None

    clear_mcp_tools()
    assert get_tool("fake_mcp_tool") is None
    assert get_tool("read_url") is not None


def test_tool_registry_initialized() -> None:
    assert isinstance(TOOL_REGISTRY, dict)
    assert len(TOOL_REGISTRY) >= 2