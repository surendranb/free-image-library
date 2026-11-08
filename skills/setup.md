---
description: Setup, client harness configuration, and quickstart guide for free-image-library.
---

# Setting Up Free Image Library MCP Server

A zero-configuration Creative Commons image and audio search engine for AI agents, providing ready-to-paste attribution for Wikimedia, Flickr, and museum collections.

Official Repository: [github.com/surendranb/free-image-library](https://github.com/surendranb/free-image-library)

---

## 1. Quickstart (Zero API Keys Required)

`free-image-library` searches indexed Creative Commons media via Openverse:
- **800+ Million Openly Licensed Works**: Wikimedia Commons, Flickr, Met Museum, Europeana, Smithsonian, and more
- **Ready-to-Paste Attribution**: Every result delivers formatted markdown and HTML attribution snippets with license links

**Zero API keys required for standard usage.**

> **Note on Optional Rate Limit Key**: Openverse permits 20 requests/minute and 200 requests/day anonymously. Setting an optional `OPENVERSE_API_KEY` environment variable increases these rate limits if running bulk operations.

---

## 2. Client Configuration

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "free-image-library": {
      "command": "uvx",
      "args": ["free-image-library"]
    }
  }
}
```

Or via NPX:
```json
{
  "mcpServers": {
    "free-image-library": {
      "command": "npx",
      "args": ["-y", "free-image-library"]
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "free-image-library": {
      "command": "uvx",
      "args": ["free-image-library"]
    }
  }
}
```

### Command Line / CLI Testing
```bash
uvx free-image-library
```

---

## 3. Core Tools & Workflow

1. **`find_images(query="misty forest", license="cc0", count=5, aspect_ratio="wide")`**:
   Search millions of openly-licensed images with filters for license family, aspect ratio, and size.
2. **`image_roulette(topic="architecture", count=3)`**:
   Serendipitous visual discovery across historical and cultural museum archives.
3. **`find_audio(query="birds chirping", license="cc", count=3)`**:
   Search open audio samples and field recordings.
4. **`skills_list()` / `skill_read(name="license-briefs")`**:
   Guidance on CC licenses (CC0, CC BY, CC BY-SA, NC, ND) in plain language.

---

## 4. Troubleshooting & Operational Guidance

- **No Images Matched**: Broaden the query (use simpler terms), set `license="all"`, or drop strict aspect ratio/size filters.
- **Rate Limits (`[ENVIRONMENT_FIXABLE]` tag)**: If rate limited (HTTP 429), pause for 60 seconds. Set `OPENVERSE_API_KEY` to increase quota.
- **Update Verification**: Call `check_for_updates()` to check PyPI for newer versions and upgrade commands.
- **Dynamic Skills**: Call `skill_read(name="interpreting-errors")` for error shapes and recovery playbooks.
