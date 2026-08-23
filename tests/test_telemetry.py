# SPDX-License-Identifier: MIT

"""Telemetry opt-out / privacy contract tests (fleet standard)."""

from free_image_library import telemetry as t


def test_telemetry_disabled_flags(monkeypatch):
    for flag, value in (
        ("FREE_IMAGE_LIBRARY_TELEMETRY", "false"),
        ("FREE_IMAGE_LIBRARY_TELEMETRY", "0"),
        ("DISABLE_TELEMETRY", "1"),
        ("DO_NOT_TRACK", "true"),
        ("NO_TELEMETRY", "on"),
    ):
        monkeypatch.setenv(flag, value)
        assert t._telemetry_disabled() is True, flag


def test_telemetry_enabled_by_default(monkeypatch):
    for flag in ("FREE_IMAGE_LIBRARY_TELEMETRY", "DISABLE_TELEMETRY",
                 "DO_NOT_TRACK", "NO_TELEMETRY"):
        monkeypatch.delenv(flag, raising=False)
    assert t._telemetry_disabled() is False


def test_scrub_redacts_pii():
    assert t._scrub("see https://example.com/a and /Users/me/secret.txt") == \
        "see <url> and <path>"
    assert t._scrub("mail reachsuren@gmail.com") == "mail <email>"
    assert t._scrub({"nested": "https://x.io"}) == {"nested": "<url>"}


def test_send_telemetry_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(t, "TELEMETRY_DISABLED", True)
    assert t.send_telemetry("mcp_started") is None


def test_opt_out_never_writes_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(t, "TELEMETRY_DISABLED", True)
    monkeypatch.setenv("HOME", str(tmp_path))
    install_id, _ = t._init_anonymous_identity()
    assert install_id.startswith("anon_")
    assert not (tmp_path / ".free_image_library").exists()
