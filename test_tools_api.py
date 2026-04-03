#!/usr/bin/env python3
"""Test script for the CLERK tools API.

Tests the full tool lifecycle:
1. Create a test kit
2. Add a tool from the global registry
3. Add a workflow step that references the tool
4. Execute the kit and stream results
5. Clean up (delete the tool)

Usage:
    python test_tools_api.py [BASE_URL]

Set CLERK_EMAIL and CLERK_PASSWORD env vars for auto-login,
or the script will prompt interactively.
"""

import json
import os
import sys
import getpass

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SLUG = "tool-test-kit"

# Persistent client to preserve session cookies
client = httpx.Client(base_url=BASE_URL, timeout=30, follow_redirects=True)


def api(method: str, path: str, **kwargs) -> httpx.Response:
    return client.request(method, f"/api{path}", **kwargs)


def check(label: str, r: httpx.Response, expected: int = 200) -> bool:
    ok = r.status_code == expected
    print(f"  {'✅' if ok else '❌'} {label} — HTTP {r.status_code}")
    if not ok:
        print(f"     {r.text[:500]}")
    return ok


def safe_json(r: httpx.Response) -> dict:
    try:
        return r.json()
    except Exception:
        print(f"   ⚠️  Not JSON ({r.headers.get('content-type')}): {r.text[:200]}")
        return {}


def login() -> bool:
    email = os.environ.get("CLERK_EMAIL") or input("Email: ")
    password = os.environ.get("CLERK_PASSWORD") or getpass.getpass("Password: ")
    r = api("POST", "/auth/login", json={"email": email, "password": password})
    data = safe_json(r)
    if data.get("ok"):
        print(f"  ✅ Logged in as {data['user']['email']}\n")
        return True
    print(f"  ❌ Login failed: {data.get('error')}\n")
    return False


def main():
    print("=" * 60)
    print("CLERK Tools API — Full Integration Test")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")

    # ── 0. Login ──
    print("0. Authenticating...")
    if not login():
        return

    # ── 1. List available tools ──
    print("1. List available global tools")
    r = api("GET", "/tools/available")
    if not check("GET /api/tools/available", r):
        return
    tools = safe_json(r).get("tools", [])
    print(f"   Found {len(tools)} tool(s):")
    for t in tools:
        print(f"     • {t['name']}: {t['description'][:60]}")
    if not tools:
        print("   No tools registered. Aborting.")
        return
    tool_name = tools[0]["name"]

    # ── 2. Create test kit ──
    print(f"\n2. Create test kit '{SLUG}'")
    # First delete if exists to ensure idempotency
    r_del = api("DELETE", f"/kits/{SLUG}")
    if r_del.status_code == 200:
        print("  🧹 Deleted existing kit for a fresh test")

    r = api(
        "POST",
        "/kits",
        json={
            "name": "Tool Test Kit",
            "description": "Auto-created by test_tools_api.py",
        },
    )
    data = safe_json(r)
    if data.get("ok"):
        print(f"  ✅ Created kit (slug: {data.get('slug', SLUG)})")
        slug = data.get("slug", SLUG)
    else:
        check("POST /api/kits", r)
        slug = SLUG

    # ── 3. Add tool to kit ──
    print(f"\n3. Add tool '{tool_name}' to kit")
    r = api(
        "POST",
        f"/kits/{slug}/tools",
        json={
            "tool_name": tool_name,
            "display_name": "URL Reader",
        },
    )
    check(f"POST /api/kits/{slug}/tools", r)

    # ── 4. Verify tools in kit detail ──
    print("\n4. Verify kit has tool")
    r = api("GET", f"/kits/{slug}/detail")
    detail = safe_json(r)
    kit_tools = detail.get("tools", [])
    print(f"   Tools: {len(kit_tools)}")
    for t in kit_tools:
        print(f"     • #{t['number']} {t['tool_name']} ({t.get('display_name', '')})")

    if not kit_tools:
        print("   ❌ No tools found — aborting.")
        return

    tool_number = kit_tools[-1]["number"]

    # ── 5. Add a workflow step referencing the tool ──
    print(f"\n5. Add workflow step referencing {{tool_{tool_number}}}")
    prompt = (
        f"Use {{tool_{tool_number}}} to read the content of https://example.com "
        "and write a one-paragraph summary of what the page contains."
    )
    r = api(
        "POST",
        f"/kits/{slug}/steps",
        json={
            "prompt": prompt,
            "display_name": "Summarize example.com",
        },
    )
    check(f"POST /api/kits/{slug}/steps", r)

    # ── 6. Execute the kit (SSE stream) ──
    print("\n6. Execute kit with tool-calling")
    r = api("POST", f"/kits/{slug}/execute", json={})
    data = safe_json(r)
    execution_id = data.get("execution_id")
    if not execution_id:
        print(f"   ❌ No execution_id returned: {data}")
        return
    print(f"   execution_id: {execution_id}")

    print("   Streaming results...\n")
    with client.stream(
        "GET",
        f"/api/kits/{slug}/execute/{execution_id}/stream",
    ) as stream:
        for line in stream.iter_lines():
            if not line:
                continue
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                try:
                    event_data = json.loads(line[6:])
                except Exception:
                    event_data = line[6:]

                if event_type == "start":
                    print(
                        f"   ▶ Kit: {event_data.get('kit_name')}, "
                        f"steps: {event_data.get('total_steps')}"
                    )
                elif event_type == "step-start":
                    print(
                        f"   ⏳ Step {event_data.get('step')}: "
                        f"{event_data.get('display_name', '')}"
                    )
                elif event_type == "step-complete":
                    result = event_data.get("result", "")
                    latency = event_data.get("latency_ms", "?")
                    tokens = event_data.get("tokens_used", "?")
                    print(
                        f"   ✅ Step {event_data.get('step')} complete "
                        f"({latency}ms, {tokens} tokens)"
                    )
                    preview = result[:200].replace("\n", " ")
                    print(f"      Result: {preview}...")
                elif event_type == "done":
                    status = event_data.get("status", "unknown")
                    print(f"\n   🏁 Done — status: {status}")
                elif event_type == "error":
                    print(f"   ❌ Error: {event_data}")

    # ── 7. Update tool display name ──
    print(f"\n7. Update tool #{tool_number} display name")
    r = api(
        "POST",
        f"/kits/{slug}/tools/{tool_number}/update",
        json={
            "display_name": "Updated URL Reader",
        },
    )
    check("Update tool", r)

    # Verify
    detail = safe_json(api("GET", f"/kits/{slug}/detail"))
    for t in detail.get("tools", []):
        if t["number"] == tool_number:
            print(f"   Display name: {t.get('display_name')}")

    # ── 8. Delete tool ──
    print(f"\n8. Delete tool #{tool_number}")
    r = api("DELETE", f"/kits/{slug}/tools/{tool_number}")
    check("Delete tool", r)

    detail = safe_json(api("GET", f"/kits/{slug}/detail"))
    remaining = [t["number"] for t in detail.get("tools", [])]
    if tool_number not in remaining:
        print(f"   ✅ Tool #{tool_number} removed")
    else:
        print(f"   ❌ Tool #{tool_number} still present")

    # ── 9. Re-add tool so kit remains usable for CLI testing ──
    print("\n9. Re-add tool for CLI testing")
    r = api(
        "POST",
        f"/kits/{slug}/tools",
        json={
            "tool_name": tool_name,
            "display_name": "URL Reader",
        },
    )
    check(f"Re-add {tool_name}", r)

    # ── Done ──
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print(f"   Kit '{slug}' is ready — try: uv run clerk run {slug}")
    print("=" * 60)


if __name__ == "__main__":
    main()
