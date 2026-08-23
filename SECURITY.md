# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately via GitHub security advisories
(Report a vulnerability button on this repo) or email reachsuren@gmail.com.

This server is read-only over the public Openverse API: it accepts no
required secrets, writes no files outside its own anonymous telemetry id,
and executes no shell commands. Telemetry is opt-out via
`FREE_IMAGE_LIBRARY_TELEMETRY=false` / `DO_NOT_TRACK=1`.
