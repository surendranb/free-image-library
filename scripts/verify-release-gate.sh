#!/usr/bin/env bash
# Proves the release workflow cannot report green while npm stays behind.
set -euo pipefail
cd "$(dirname "$0")/.."
WF=.github/workflows/release.yml

python3 - "$WF" <<'PY'
import re, subprocess, sys

wf = open(sys.argv[1]).read()

create_release = wf.split("create-release:", 1)[1]
assert "actions/checkout@v4" in create_release, "create-release has no checkout step"
print("PASS create-release checks out the repo")

publish = wf.split("- name: Publish to npm", 1)[1]
body = [l[10:] for l in publish.splitlines() if l.startswith("          ")]
body = "\n".join(body).split("env:", 1)[0]
assert "|| echo" not in body, "npm publish still swallows failures with || echo"
print("PASS npm publish no longer swallows failures")

r = subprocess.run(
    ["bash", "-e", "-c", body],
    cwd=".",
    env={
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": subprocess.os.environ["HOME"],
        "NODE_AUTH_TOKEN": "bogus",
        "NPM_CONFIG_REGISTRY": "http://127.0.0.1:9",
        "NPM_CONFIG_FETCH_RETRIES": "0",
    },
    capture_output=True,
    text=True,
)
assert r.returncode != 0, f"publish step exited 0 on a failing publish:\n{r.stdout}"
assert "::error::npm publish failed" in (r.stdout + r.stderr), "no loud failure message emitted"
print(f"PASS failing npm publish exits {r.returncode} and emits ::error::")
PY
