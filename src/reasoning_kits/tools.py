"""Global tool registry for reasoning kits.

Tools follow the OpenAI function-calling pattern:
- Each tool has a name, description, JSON Schema parameters, and an execute function.
- During execution, tools are passed to the LLM via the `tools=` parameter.
- The LLM decides when to invoke a tool; we handle the call loop.
"""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class ToolDefinition:
    """A globally registered tool definition."""

    name: str
    description: str
    parameters: dict[str, Any]
    execute: Callable[..., Awaitable[str]]
    source: str = "builtin"


TOOL_REGISTRY: dict[str, ToolDefinition] = {}


def register_tool(tool: ToolDefinition) -> None:
    """Register a tool in the global registry."""
    TOOL_REGISTRY[tool.name] = tool


def get_tool(name: str) -> ToolDefinition | None:
    """Look up a tool by name."""
    return TOOL_REGISTRY.get(name)


def list_tools() -> list[ToolDefinition]:
    """Return all registered tools."""
    return list(TOOL_REGISTRY.values())


def clear_mcp_tools() -> None:
    """Remove all non-builtin tools from the global registry."""
    for name in [n for n, t in TOOL_REGISTRY.items() if t.source != "builtin"]:
        del TOOL_REGISTRY[name]


def get_openai_tool_schema(name: str) -> dict[str, Any] | None:
    """Return the OpenAI-compatible tool schema for a registered tool.

    Returns:
        Dict like {"type": "function", "function": {...}} or None.
    """
    tool = get_tool(name)
    if tool is None:
        return None
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


# =============================================================================
# Built-in tools
# =============================================================================


async def _read_url(args: dict[str, Any]) -> str:
    """Fetch a URL and return its text content.

    Uses httpx for the HTTP request and BeautifulSoup for HTML text extraction.
    Falls back to raw text for non-HTML responses. If SSL verification fails,
    retries without verification.
    """
    import httpx
    from bs4 import BeautifulSoup

    url = args.get("url", "")
    if not url:
        return "Error: No URL provided."

    async def _fetch(verify: bool) -> Any:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, verify=verify) as client:
            resp = await client.get(url, headers={"User-Agent": "ReasoningKits/1.0"})
            resp.raise_for_status()
            return resp

    try:
        try:
            response = await _fetch(verify=True)
        except Exception as ssl_err:
            if "SSL" in str(ssl_err) or "certificate" in str(ssl_err).lower():
                response = await _fetch(verify=False)
            else:
                raise

        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [line for line in text.splitlines() if line.strip()]
            return "\n".join(lines)

        return response.text

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} when fetching {url}"
    except Exception as e:
        return f"Error: Could not fetch URL: {e}"


register_tool(
    ToolDefinition(
        name="read_url",
        description="Read the content of a website and return its text. "
        "Useful for fetching information from web pages.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the website to read.",
                },
            },
            "required": ["url"],
        },
        execute=_read_url,
    )
)


async def _jina_reader(args: dict[str, Any]) -> str:
    """Fetch a URL via Jina Reader to bypass bot protection, return Markdown."""
    import httpx

    url = args.get("url", "")
    if not url:
        return "Error: No URL provided."

    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0, verify=False) as client:
            resp = await client.get(
                jina_url,
                headers={"User-Agent": "ReasoningKits/1.0", "Accept": "text/markdown"},
            )
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as e:
        return f"Error: Jina Reader returned HTTP {e.response.status_code}. Response: {e.response.text[:200]}"
    except Exception as e:
        return f"Error: Could not fetch URL via Jina Reader: {e}"


register_tool(
    ToolDefinition(
        name="jina_reader",
        description="Read the content of a strict or JS-heavy website using Jina Reader API. "
        "Bypasses bot protections and returns clean Markdown. Use when read_url fails.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the website to read.",
                },
            },
            "required": ["url"],
        },
        execute=_jina_reader,
    )
)