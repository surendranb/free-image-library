# SPDX-License-Identifier: MIT

"""Error-classification contract: zero rows is success, upstream 5xx is transient."""

import asyncio

import pytest

from free_image_library import openverse


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def captured(monkeypatch):
    import os
    os.environ["DO_NOT_TRACK"] = "1"
    from free_image_library import server
    events = []
    monkeypatch.setattr(server, "send_telemetry",
                        lambda ev, props: events.append((ev, props)))
    return server, events


def _payload(result):
    import json
    return json.loads(result.text) if hasattr(result, "text") else result


def test_zero_result_search_is_success(captured, monkeypatch):
    server, events = captured
    monkeypatch.setattr(openverse, "search_images", lambda *a, **k: ([], 0))
    result = _payload(_run(server.find_images("zzzz no such image zzzz")))
    assert "error" not in result
    assert result["images"] == [] and result["result_count"] == 0
    assert "broaden the query" in result["note"]
    props = [p for ev, p in events if ev == "tool_executed"][-1]
    assert props["status"] == "success"
    assert props["rows_returned"] == 0


def test_zero_result_audio_is_success(captured, monkeypatch):
    server, events = captured
    monkeypatch.setattr(openverse, "search_audio", lambda *a, **k: ([], 0))
    result = _payload(_run(server.find_audio("zzzz no such audio zzzz")))
    assert "error" not in result and result["audio"] == []
    props = [p for ev, p in events if ev == "tool_executed"][-1]
    assert props["status"] == "success"


def test_upstream_504_is_transient(monkeypatch):
    class Resp:
        status_code = 504
    monkeypatch.setattr(openverse.requests, "get", lambda *a, **k: Resp())
    with pytest.raises(openverse.OpenverseError) as exc:
        openverse._get("/images/", {"q": "x"})
    msg = str(exc.value)
    assert "[TRANSIENT: retry once]" in msg
    assert "INPUT_FIXABLE" not in msg


def test_upstream_400_stays_input_fixable(monkeypatch):
    class Resp:
        status_code = 400
    monkeypatch.setattr(openverse.requests, "get", lambda *a, **k: Resp())
    with pytest.raises(openverse.OpenverseError) as exc:
        openverse._get("/images/", {"q": "x"})
    assert "[INPUT_FIXABLE" in str(exc.value)
