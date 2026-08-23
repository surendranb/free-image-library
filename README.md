# Free Image Library — Free CC Images & Audio MCP 🖼️

[![CI](https://github.com/surendranb/free-image-library/actions/workflows/package-checks.yml/badge.svg)](https://github.com/surendranb/free-image-library/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/free-image-library.svg)](https://pypi.org/project/free-image-library/)

> **Free images for any project: millions of openly-licensed, royalty-free Creative Commons images and audio (Flickr, Wikimedia, museums) — every result with ready-to-paste attribution. Zero API keys, zero configuration.**

The visual sibling of the [Free Music Library](https://github.com/surendranb/music-mcp)
for the same content-creator audience: the agent finds the image AND the credit
line in one call, so the attribution never gets lost between copy and paste.

## Why this exists

- Models suggest random stock images (license unknown, credit never written).
  This returns license-safe images with the credit the user MUST paste — built
  into the same result.
- **License intelligence, not just labels**: every row carries a `credit_note`
  stating the actual obligation — CC BY-NC rows are loudly flagged
  non-commercial-only before your client ships them into a paid campaign.
- **Serendipity**: `image_roulette` picks from deep in the result set, not the
  first hit everyone has seen.
- Built on [Openverse](https://api.openverse.org) — keyless (anonymous limits:
  20 requests/min, 200/day, verified; a free registered key raises them via
  `OPENVERSE_API_KEY`). A 5-minute TTL cache makes repeat searches free.

## Tools

| Tool | What it does |
|---|---|
| `find_images` | Free CC image search with filters (license, aspect_ratio, size, extension) + attribution on every row |
| `image_roulette` | One random license-safe pick, honest about how it was chosen |
| `find_audio` | Free CC music / sound effects / field recordings from Openverse's audio index |
| `skills_list` / `skill_read` | Updatable playbooks: CC license briefs in plain language, error recovery |

Plus prompts: `hero-image`, `license-safe-images`.

## Quickstart

```bash
# 1-Line Universal Installer (auto-configures Claude Desktop, Cursor, Claude Code, VS Code, ...)
curl -fsSL "https://free-image-library.builditwithai.xyz/install" | bash

# Or run directly via your preferred runtime:
uvx free-image-library
npx -y free-image-library
```

## Example

```
User:  I need a hero image for my climate blog post

find_images(query="melting glacier", aspect_ratio="wide", count=3,
            intent="hero image for a climate blog post")
→ images: [{
     title: "Glacier calving", creator: "…", license: "CC BY 2.0",
     image_url: "https://…", width: 2048, height: 1152,
     attribution: "\"Glacier calving\" image by … (flickr), licensed CC BY 2.0 (…)",
     credit_note: "Credit REQUIRED — paste the attribution verbatim." }]
```

## Telemetry & privacy

Anonymous usage telemetry (no PII, no queries, no paths) via the fleet
standard (schema v2, dual-endpoint fallback). Opt out any time:
`FREE_IMAGE_LIBRARY_TELEMETRY=false` or `DO_NOT_TRACK=1`.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
DO_NOT_TRACK=1 .venv/bin/python -m pytest tests/ -q   # unit + live + e2e
```

Live tests hit the real Openverse API; they skip themselves when offline or
rate-limited.

## License

MIT
