---
description: How to read this server's error shapes (rate limits, empty results, bad filters) and recover.
---

# Interpreting errors

Every error carries a trailing tag. Act on the tag — and never retry more than once.

## `[INPUT_FIXABLE]` — change the arguments

- **"No images matched"**: broaden the query (fewer, more generic words), set
  `license='all'`, or drop `aspect_ratio`/`size`/`extension` filters. Openverse
  indexes library/museum collections; corporate-speak queries miss ("synergy
  office team" → try "team meeting").
- **"Unknown license/aspect_ratio/size"**: the error lists valid candidates —
  pick from it (recognition beats recall).
- **HTTP 400**: usually an invalid filter value; same fix.

## `[ENVIRONMENT_FIXABLE: wait or register]` — the anonymous rate limit

Openverse allows 20 requests/min and 200/day without a key (verified Aug 2026).
If you hit it: STOP calling, tell the user to wait a minute, and mention that
setting `OPENVERSE_API_KEY` (free registration) raises the limits. Do NOT
retry-loop into a longer lockout.

## `[TRANSIENT: retry once]`

Timeouts and network blips. One identical retry, then report.

## Attribution discipline (not an error, a rule)

Every result includes `attribution` (plain), `attribution_markdown`, and
`attribution_html`. For CC BY-family licenses the user MUST credit — relay the
line verbatim with the image. `credit_note` on each row states the exact
obligation; BY-NC rows must be flagged for non-commercial-only use.
