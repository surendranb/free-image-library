# SPDX-License-Identifier: MIT

"""Free Image Library MCP — CC-licensed images and audio for AI agents.

The visual sibling of music-mcp for the same content-creator audience:
search Openverse's millions of openly-licensed images, get ready-to-paste
attribution in three formats, and spin the image roulette for serendipity.
"""

import re
import json
import time
import random
import inspect
import functools
import contextvars
import urllib.request
from pathlib import Path

import pydantic_core
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import Annotations, TextContent, ToolAnnotations

from . import telemetry
from .telemetry import send_telemetry, capture_request

SERVER_NAME = "free-image-library"
WEBSITE_URL = "https://github.com/surendranb/free-image-library"
MCP_SERVER_VERSION = telemetry.MCP_SERVER_VERSION

INSTRUCTIONS = (
    "You can find openly-licensed images and audio for any project. "
    "find_images searches Openverse (Flickr, Wikimedia, museums and more); "
    "EVERY result carries an 'attribution' line the user must credit "
    "verbatim for CC BY-family licenses — always return it with the image "
    "URL. image_roulette is for serendipity; find_audio covers CC music and "
    "sound effects. On an error, call skills_list and read "
    "'interpreting-errors' with skill_read before retrying."
)

mcp = MCPServer(SERVER_NAME, title="Free Image Library",
                version=MCP_SERVER_VERSION, instructions=INSTRUCTIONS,
                website_url=WEBSITE_URL)
telemetry.announce_and_fire_boot_events()

_CURRENT_REQUEST = contextvars.ContextVar("openimages_current_request", default=None)


async def _telemetry_middleware(ctx, call_next):
    _CURRENT_REQUEST.set(ctx)
    try:
        capture_request(ctx)
    except Exception:
        pass
    return await call_next(ctx)


mcp.middleware.append(_telemetry_middleware)


async def _list_tools_with_telemetry():
    tools = await mcp._list_tools_orig()
    send_telemetry("tools_listed", {
        "tool_count": len(tools),
        **capture_request(_CURRENT_REQUEST.get()),
    })
    return tools


mcp._list_tools_orig = mcp.list_tools
mcp.list_tools = _list_tools_with_telemetry


def _count_rows(result):
    if result is None:
        return 0
    if isinstance(result, list):
        return len(result)
    if isinstance(result, dict):
        if result.get("error"):
            return 0
        for key in ("images", "picks", "audio", "skills", "formats"):
            if key in result:
                return len(result.get(key) or [])
        if "content" in result:
            return 1 if str(result.get("content") or "").strip() else 0
        return 1 if result else 0
    return 1 if result else 0


_EXCEPTION_CATEGORIES = {
    "ValueError": "ValidationError",
    "TypeError": "ValidationError",
}


def _classify_error_result(message):
    m = message.lower()
    if "not found" in m or "unknown" in m or "invalid" in m or "candidates" in m:
        return "ValidationError"
    if "rate limit" in m:
        return "RateLimitError"
    if "timed out" in m or "transient" in m:
        return "APIError"
    if "401" in m or "unauthorized" in m or "rejected" in m:
        return "AuthError"
    return "APIError"


def _result_chars(result):
    if result is None:
        return 0
    try:
        return len(result) if isinstance(result, str) else len(json.dumps(result, default=str))
    except Exception:
        return len(str(result))


def _argument_shape_props(tool_name, func, args, kwargs):
    """Argument SHAPE only — never the user's query text."""
    props = {}
    try:
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        a = bound.arguments
        if tool_name in ("find_images", "find_audio"):
            query = a.get("query")
            props["has_query"] = bool(query)
            props["query_length"] = len(query) if isinstance(query, str) else 0
            props["license"] = a.get("license")
            props["aspect_ratio"] = a.get("aspect_ratio")
            props["size"] = a.get("size")
        elif tool_name == "skill_read":
            name = a.get("name")
            if isinstance(name, str):
                props["skill_name"] = name.strip().lower()[:80]
    except Exception:
        pass
    return props


_original_tool = mcp.tool


def _telemetry_tool(name=None, title=None, description=None, annotations=None,
                    icons=None, meta=None, structured_output=None):
    def decorator(func):
        tool_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error_category = None
            error_message = None
            result = None
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, dict) and result.get("error"):
                    status = "error"
                    error_message = str(result["error"])
                    error_category = _classify_error_result(error_message)
                if tool_name in ("find_images", "image_roulette", "find_audio"):
                    return _shape_user_result(result)
                return result
            except Exception as e:
                status = "exception"
                cls = e.__class__.__name__
                error_category = _EXCEPTION_CATEGORIES.get(cls, cls)
                error_message = str(e)
                raise
            except BaseException:
                status = "cancelled"
                error_category = "Cancelled"
                raise
            finally:
                try:
                    props = {
                        "tool_name": tool_name,
                        "status": status,
                        "latency_ms": int((time.time() - start_time) * 1000),
                        "rows_returned": _count_rows(result),
                        "result_chars": _result_chars(result),
                        **_argument_shape_props(tool_name, func, args, kwargs),
                        **capture_request(_CURRENT_REQUEST.get()),
                    }
                    if error_category:
                        props["error_category"] = error_category
                    if error_message:
                        props["error_message"] = telemetry._scrub(error_message)[:200]
                    telemetry.record_tool_call(tool_name)
                    send_telemetry("tool_executed", props)
                except Exception:
                    pass

        wrapper.__signature__ = inspect.signature(func)
        return _original_tool(name, title=title, description=description,
                              annotations=annotations, icons=icons, meta=meta,
                              structured_output=structured_output)(wrapper)
    return decorator


mcp.tool = _telemetry_tool


def _shape_user_result(result):
    """Search results ARE the human-facing content (image URLs + attribution
    the user must paste). Single annotated TextContent, byte-identical to the
    SDK's dict serialization; falls back to the plain dict on any failure."""
    try:
        if not isinstance(result, dict) or result.get("error"):
            return result
        text = pydantic_core.to_json(result, fallback=str, indent=2).decode()
        return TextContent(type="text", text=text,
                           annotations=Annotations(audience=["user"], priority=1.0))
    except Exception:
        return result


def _with_credits(rows, media_noun="image"):
    """Attach attribution lines + obligation note to every row."""
    from . import credits
    out = []
    for row in rows:
        plain, markdown, html = credits.credit_lines(row, media_noun)
        row["attribution"] = plain
        row["attribution_markdown"] = markdown
        row["attribution_html"] = html
        row["credit_note"] = credits.credit_note(row)
        out.append(row)
    return out


# --- tools ---

@mcp.tool(title="Find openly-licensed images",
          description="Search millions of CC-licensed images (Flickr, "
                      "Wikimedia, museums…); every result carries a "
                      "ready-to-paste attribution",
          annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True,
                                      open_world_hint=True))
async def find_images(query: str, license: str = "cc", count: int = 6,
                      aspect_ratio: str = None, size: str = None,
                      extension: str = None, intent: str = None) -> dict:
    """Find openly-licensed images for any topic or project.

    Args:
        query: what you need an image of ("misty forest at dawn", "vintage
            train poster", "team meeting — natural light").
        license: "all" (any license incl. rights-reserved), "cc" (default,
            all Creative Commons), or a specific one: cc0, pdm, by, by-sa,
            by-nc, by-nc-sa, by-nd, by-nc-nd.
        count: 1-20 results (default 6).
        aspect_ratio: "wide" | "square" | "tall" (hero images are wide).
        size: "small" | "medium" | "large".
        extension: jpg | png | gif | svg.
        intent: short plain-English description of the use ("hero image for a
            climate blog post").

    Returns:
        images: each with image_url, thumbnail, creator, license, license_url,
        source, dimensions, and attribution/attribution_markdown/attribution_html
        ready to paste, plus credit_note (what this license requires).

    ALWAYS relay the attribution with any image you recommend.
    """
    from . import openverse

    count = max(1, min(int(count), 20))
    try:
        rows, total = openverse.search_images(
            query, license=license, aspect_ratio=aspect_ratio, size=size,
            extension=extension, page=1, page_size=count)
    except ValueError as e:
        return {"error": str(e)}
    except openverse.OpenverseError as e:
        return {"error": str(e)}
    if not rows:
        return {"error": f"No images matched {query!r}. Fixes: broaden the "
                         f"query, set license='all', or drop aspect_ratio/size "
                         f"filters. [INPUT_FIXABLE]"}
    return {"images": _with_credits(rows),
            "result_count": total,
            "note": "Relay attribution verbatim with every image (credit_note "
                    "says what the license requires)."}


@mcp.tool(title="Image roulette",
          description="Serendipity: a random openly-licensed image matching a "
                      "topic — one pick, honest about how it was chosen",
          annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=False,
                                      open_world_hint=True))
async def image_roulette(query: str = None, license: str = "cc",
                         seed: int = None) -> dict:
    """Spin the image roulette: one random pick from deep in the result set
    (a random page among the first 40), not the first hit.

    Args:
        query: what you want an image of; omit for pure randomness (a random
            curated topic is chosen).
        license: like find_images ("cc" default, "cc0" for no-credit-needed).
        seed: optional int for a reproducible pick.
    """
    from . import openverse

    rng = random.Random(seed)
    if not query:
        query = rng.choice([
            "mist over mountains", "old library shelves", "city at night",
            "desert dunes", "greenhouse plants", "harbor cranes",
            "starry sky", "vintage machinery", "market spices",
            "northern lights", "rain on window", "lighthouse",
        ])
    try:
        rows, total = openverse.search_images(
            query, license=license, page=rng.randint(1, 40), page_size=5)
    except ValueError as e:
        return {"error": str(e)}
    except openverse.OpenverseError as e:
        return {"error": str(e)}
    if not rows:
        return {"error": f"No images matched {query!r}; try a broader query. "
                         "[INPUT_FIXABLE]"}
    pick = rng.choice(rows)
    pick = _with_credits([pick])[0]
    return {"picks": [pick],
            "query_used": query,
            "result_count": total,
            "why_picked": f"random page of the {total} results for "
                          f"“{query}” — a serendipity spin, not the top hit"}


@mcp.tool(title="Find openly-licensed audio",
          description="Search CC music, sound effects and field recordings "
                      "from Openverse's audio index",
          annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True,
                                      open_world_hint=True))
async def find_audio(query: str, license: str = "cc", count: int = 5,
                     intent: str = None) -> dict:
    """Find openly-licensed audio: music, sound effects, field recordings.

    Args:
        query: what you need ("calm piano loop", "ocean waves", "typewriter").
        license: like find_images; "cc" default, "cc0" needs no credit.
        count: 1-10 results (default 5).
        intent: short plain-English description of the use.

    Returns:
        audio: each with audio_url, creator, license, duration_s, and the
        three attribution formats.

    For a full royalty-free MUSIC catalog (with curated sources), prefer the
    companion free-music-library-mcp server; this covers the broader Openverse
    audio index.
    """
    from . import openverse

    count = max(1, min(int(count), 10))
    try:
        rows, total = openverse.search_audio(query, license=license,
                                             page=1, page_size=count)
    except ValueError as e:
        return {"error": str(e)}
    except openverse.OpenverseError as e:
        return {"error": str(e)}
    if not rows:
        return {"error": f"No audio matched {query!r}. Fixes: broaden the "
                         f"query or set license='all'. [INPUT_FIXABLE]"}
    return {"audio": _with_credits(rows, media_noun="audio"),
            "result_count": total}


# --- skills: updatable knowledge, fetched at runtime from this repo ---

_SKILLS_RAW_URL = "https://raw.githubusercontent.com/surendranb/free-image-library/main/skills/{name}.md"
_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
_SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_BUNDLED_SKILLS = {
    "interpreting-errors": "How to read this server's error shapes (rate "
                           "limits, empty results, bad filters) and recover.",
    "license-briefs": "The CC license families in plain language: what each "
                      "requires and when to use which.",
}


def _local_skills():
    skills = {}
    try:
        if _SKILLS_DIR.is_dir():
            for md_file in sorted(_SKILLS_DIR.glob("*.md")):
                desc = ""
                try:
                    for line in md_file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip()
                            break
                except Exception:
                    pass
                skills[md_file.stem] = desc
    except Exception:
        pass
    return skills


def _fetch_skill_content(key):
    content = None
    fetch_ok = False
    try:
        req = urllib.request.Request(
            _SKILLS_RAW_URL.format(name=key),
            headers={"User-Agent": f"free-image-library/{MCP_SERVER_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
        fetch_ok = True
    except Exception:
        pass
    if content is None:
        try:
            local = _SKILLS_DIR / f"{key}.md"
            if local.is_file():
                content = local.read_text(encoding="utf-8")
        except Exception:
            pass
    return content, fetch_ok


@mcp.tool(title="List skills",
          description="List available skills (guidance playbooks) for using "
                      "this server well — read one with skill_read",
          annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True,
                                      open_world_hint=False))
async def skills_list() -> dict:
    """List available skills: short guidance documents for a model using this
    server (license semantics, error recovery). Call this when a tool errors
    or a license question comes up, then fetch the full skill with
    skill_read(name)."""
    merged = dict(_BUNDLED_SKILLS)
    for skill_name, desc in _local_skills().items():
        if desc or skill_name not in merged:
            merged[skill_name] = desc or merged.get(skill_name, "")
    return {"skills": [{"name": n, "description": d} for n, d in sorted(merged.items())]}


@mcp.tool(title="Read a skill",
          description="Fetch the full content of one skill by name (from "
                      "skills_list)",
          annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True,
                                      open_world_hint=True))
async def skill_read(name: str) -> dict:
    """Fetch the full markdown content of one skill by name."""
    key = (name or "").strip().lower().removesuffix(".md")
    if not _SKILL_NAME_RE.match(key):
        return {"error": f"Invalid skill name {name!r}. "
                         "Call skills_list to see available skills."}
    content, fetch_ok = _fetch_skill_content(key)
    send_telemetry("skill_read", {"skill_name": key, "fetch_ok": fetch_ok})
    if content is None:
        return {"error": f"Skill '{key}' is unavailable right now (fetch failed "
                         "and no local copy). Call skills_list for available "
                         "skills, or proceed without it."}
    return {"name": key, "content": content}


def _register_skill_resources():
    try:
        skills = dict(_BUNDLED_SKILLS)
        for skill_name, desc in _local_skills().items():
            if desc or skill_name not in skills:
                skills[skill_name] = desc or skills.get(skill_name, "")
        for skill_name in sorted(skills):
            if not _SKILL_NAME_RE.match(skill_name):
                continue
            uri = f"skill://{skill_name}"
            desc = skills[skill_name] or f"free-image-library skill: {skill_name}"

            def _make_reader(key, res_uri):
                def _read_skill() -> str:
                    content, fetch_ok = _fetch_skill_content(key)
                    try:
                        send_telemetry("resource_read", {
                            "resource_uri": res_uri, "skill_name": key,
                            "fetch_ok": fetch_ok,
                            **capture_request(_CURRENT_REQUEST.get()),
                        })
                    except Exception:
                        pass
                    if content is None:
                        raise ValueError(
                            f"Skill '{key}' is unavailable right now. Use the "
                            "skills_list tool for available skills.")
                    return content

                _read_skill.__name__ = f"skill_resource_{key.replace('-', '_')}"
                return _read_skill

            mcp.resource(uri, name=skill_name, title=f"Skill: {skill_name}",
                         description=desc, mime_type="text/markdown")(
                _make_reader(skill_name, uri))
    except Exception:
        pass


_register_skill_resources()


# --- workflow prompts ---

def _emit_prompt_used(prompt_name, has_args):
    try:
        send_telemetry("prompt_used", {
            "prompt_name": prompt_name, "has_args": bool(has_args),
            **capture_request(_CURRENT_REQUEST.get()),
        })
    except Exception:
        pass


@mcp.prompt(name="hero-image", title="Hero image for a post",
            description="Find a license-safe hero image with ready attribution.")
def hero_image(topic: str) -> str:
    _emit_prompt_used("hero-image", bool(topic))
    return (
        f"Find a hero image for a blog post about {topic}.\n\n"
        "1. Call find_images(query built from '{topic}', aspect_ratio='wide', "
        "count=5). Heroes are wide; prefer large images with clean edges.\n"
        "2. Recommend 1-2 picks with image_url AND the attribution line — the "
        "user must paste it under the image or in the post footer.\n"
        "3. If license='cc0' matters (no credit wanted), pass license='cc0'.\n"
        "4. Empty results → broaden the query or drop aspect_ratio; read the "
        "'interpreting-errors' skill on any error."
    )


@mcp.prompt(name="license-safe-images", title="License-safe image set",
            description="Assemble a set of images the user can legally ship, "
                        "each with its credit line.")
def license_safe_images(what: str, count: str = "3") -> str:
    _emit_prompt_used("license-safe-images", bool(what))
    return (
        f"Assemble {count} license-safe images for: {what}.\n\n"
        "1. Default to license='cc' and relay credit lines. If the user says "
        "'no attribution' or 'commercial + modifications', pass license='cc0' "
        "or 'by' accordingly.\n"
        "2. Call find_images once per distinct visual need rather than one "
        "giant query; pass intent each time.\n"
        "3. For every pick give: image_url, thumbnail, license, the "
        "attribution line, and the credit_note (BY-NC means non-commercial "
        "ONLY — flag it loudly if the use is commercial).\n"
        "4. Unsure what a license allows? skills_list → "
        "skill_read('license-briefs')."
    )


def main():
    send_telemetry("mcp_started", {})
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
