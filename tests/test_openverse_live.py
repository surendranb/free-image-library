# SPDX-License-Identifier: MIT

"""Live tests against the real keyless Openverse API. Marked `live`:
self-skipping on network failure or rate-limit exhaustion."""

import pytest

from free_image_library import openverse

pytestmark = pytest.mark.live


def _reachable():
    try:
        rows, _ = openverse.search_images("forest", page_size=3)
        return bool(rows)
    except Exception:
        return False


if not _reachable():
    pytest.skip("Openverse unreachable or rate-limited from this network",
                allow_module_level=True)


def test_search_images_normalized_rows():
    rows, total = openverse.search_images("misty forest", page_size=5)
    assert total > 100
    row = rows[0]
    assert row["id"] and row["title"]
    assert row["license"] in ("BY", "BY-SA", "BY-NC", "BY-NC-SA", "CC0",
                              "PDM", "BY-ND", "BY-NC-ND")
    assert row["image_url"].startswith("http")
    assert row["source"]


def test_search_images_cc0_filter_and_aspect():
    rows, _ = openverse.search_images("lighthouse", license="cc0", page_size=5)
    assert rows and all(r["license"] == "CC0" for r in rows)
    wide, _ = openverse.search_images("sunset", aspect_ratio="wide", page_size=5)
    assert all((r["width"] or 0) >= (r["height"] or 0) for r in wide if r["width"])


def test_cache_returns_second_call_without_network(monkeypatch):
    rows, _ = openverse.search_images("mountain river", page_size=3)
    assert rows

    def _boom(*a, **kw):
        raise AssertionError("network hit — should have been served from cache")

    monkeypatch.setattr(openverse.requests, "get", _boom)
    again, _ = openverse.search_images("mountain river", page_size=3)
    assert again == rows


def test_search_audio():
    rows, total = openverse.search_audio("ocean waves", page_size=3)
    assert total > 10
    assert rows[0]["audio_url"].startswith("http")


def test_get_image_roundtrip():
    rows, _ = openverse.search_images("harbor", page_size=1)
    single = openverse.get_image(rows[0]["id"])
    assert single["id"] == rows[0]["id"]
    assert single["license"]
