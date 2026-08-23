# SPDX-License-Identifier: MIT

"""E2E: a real MCP stdio session against the actual server binary.
Spawns `python -m free_image_library` as a host would, initializes, lists tools,
and calls the surface. DO_NOT_TRACK=1 keeps telemetry silent."""

import sys
import json

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.live]


async def test_stdio_session_full_surface():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "free_image_library"],
        env={"DO_NOT_TRACK": "1", "PATH": "/usr/bin:/bin"})
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # --- tools/list ---
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert {"find_images", "image_roulette", "find_audio",
                    "skills_list", "skill_read"} <= names

            # --- find_images (live Openverse) ---
            result = await session.call_tool(
                "find_images",
                {"query": "misty forest", "license": "cc", "count": 3,
                 "aspect_ratio": "wide"})
            payload = json.loads(result.content[0].text)
            assert len(payload["images"]) == 3
            img = payload["images"][0]
            assert img["image_url"].startswith("http")
            assert "attribution" in img and img["attribution"]
            assert "credit_note" in img

            # --- bad license -> error with candidates ---
            result = await session.call_tool(
                "find_images", {"query": "forest", "license": "wat"})
            payload = json.loads(result.content[0].text)
            assert "error" in payload
            assert "INPUT_FIXABLE" in payload["error"]
            assert "cc0" in payload["error"]


async def test_stdio_session_roulette_and_audio():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "free_image_library"],
        env={"DO_NOT_TRACK": "1", "PATH": "/usr/bin:/bin"})
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            result = await session.call_tool(
                "image_roulette", {"seed": 7})
            payload = json.loads(result.content[0].text)
            assert len(payload["picks"]) == 1
            assert payload["picks"][0]["attribution"]
            assert "why_picked" in payload and "serendipity" in payload["why_picked"]

            result = await session.call_tool(
                "find_audio", {"query": "ocean waves", "count": 2})
            payload = json.loads(result.content[0].text)
            assert 1 <= len(payload["audio"]) <= 2
            assert payload["audio"][0]["audio_url"].startswith("http")
