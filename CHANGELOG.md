# Changelog

## 0.1.5 — 2026-11-27

Discovery, no API change.

- **Registered in the official MCP registry.** The README now carries the
  `mcp-name` marker PyPI ownership validation requires, and the release
  workflow publishes `server.json` to the registry after PyPI, authenticating
  with GitHub OIDC so no long-lived token can expire.
- **Release gate reports npm failures.** A failed npm publish used to leave the
  workflow green. It now fails.

## 0.1.4 — 2026-11-24

Error classification fixes, no API change.

- **Zero-result searches are successes.** `find_images`, `image_roulette` and
  `find_audio` now return an empty list plus a `note` instead of an `error`
  object, so a real search with no matches is no longer reported as a failed
  call. The query-broadening hint is kept as guidance in `note`.
- **Upstream 5xx is transient.** Openverse HTTP 500/502/504 now reads
  `[TRANSIENT: retry once]` (not `[INPUT_FIXABLE]`); the argument advice is
  reserved for 4xx responses, where it belongs.
- `skills/interpreting-errors.md` updated to match both shapes.

## 0.1.3

Prior release. See git history for details.
