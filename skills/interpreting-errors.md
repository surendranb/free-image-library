---
description: How to read this server's error shapes (rate limits, empty results, bad filters) and recover.
---

# Interpreting errors

Every error carries a trailing tag. Act on the tag — and never retry more than once.

## Empty results — not an error

A search that matches nothing returns `images: []` / `audio: []` (or `picks: []`)
with a `note`, and no `error` key. The call succeeded; the query was just too
narrow for the index. Read the `note`, widen the query once (fewer, more generic
words, `license='all'`, drop `aspect_ratio`/`size` filters), and move on.

## `[INPUT_FIXABLE]` — change the arguments

- **"Unknown license/aspect_ratio/size"**: the error lists valid candidates —
  pick from it (recognition beats recall).
- **HTTP 400**: usually an invalid filter value; same fix.

## `[ENVIRONMENT_FIXABLE: wait or register]` — the anonymous rate limit

Openverse allows 20 requests/min and 200/day without a key (verified Aug 2026).
If you hit it: STOP calling, tell the user to wait a minute, and mention that
setting `OPENVERSE_API_KEY` (free registration) raises the limits. Do NOT
retry-loop into a longer lockout.

## `[TRANSIENT: retry once]`

Timeouts, network blips, and any upstream 5xx (`HTTP 500`/`502`/`504`). The
service is at fault, not the arguments — one identical retry, then report.

## Attribution discipline (not an error, a rule)

Every result includes `attribution` (plain), `attribution_markdown`, and
`attribution_html`. For CC BY-family licenses the user MUST credit — relay the
line verbatim with the image. `credit_note` on each row states the exact
obligation; BY-NC rows must be flagged for non-commercial-only use.
