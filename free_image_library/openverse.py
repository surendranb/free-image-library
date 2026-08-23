# SPDX-License-Identifier: MIT

"""Openverse API client — CC-licensed images and audio for AI agents.

Openverse (WordPress) is keyless: anonymous use is rate-limited to 20/min
burst and 200/day sustained (verified 2026-08-22), which is plenty for a
discovery tool with the TTL cache below. A registered key can be supplied
later via OPENVERSE_API_KEY for higher limits.
"""

import os
import time
import threading

import requests

BASE = "https://api.openverse.org/v1"
USER_AGENT = "free-image-library/0.1.0 (MCP server; +https://github.com/surendranb/free-image-library)"
TIMEOUT = 10.0
CACHE_TTL = 300  # 5 min: identical searches within a session cost nothing

LICENSES = ("all", "cc", "cc0", "pdm", "by", "by-sa", "by-nc", "by-nc-sa",
            "by-nd", "by-nc-nd")
ASPECTS = ("wide", "square", "tall")
SIZES = ("small", "medium", "large")


class OpenverseError(Exception):
    """Upstream failure with a model-facing tag."""

    def __init__(self, message, rate_limited=False):
        super().__init__(message)
        self.rate_limited = rate_limited


_cache_lock = threading.Lock()
_cache = {}


def _cached(key):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and hit[0] > now:
            return hit[1]
    return None


def _store(key, value):
    with _cache_lock:
        if len(_cache) > 128:  # bounded: discovery tool, not a mirror
            _cache.clear()
        _cache[key] = (time.time() + CACHE_TTL, value)


def _headers():
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    key = os.getenv("OPENVERSE_API_KEY")  # optional: higher rate limits
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _get(path, params):
    cache_key = f"{path}?{sorted((params or {}).items())}"
    hit = _cached(cache_key)
    if hit is not None:
        return hit
    try:
        resp = requests.get(f"{BASE}{path}", params=params or {},
                            headers=_headers(), timeout=TIMEOUT)
    except requests.Timeout as e:
        raise OpenverseError("Openverse request timed out "
                             "[TRANSIENT: retry once]") from e
    except requests.RequestException as e:
        raise OpenverseError(f"Openverse request failed: {e} "
                             "[TRANSIENT: retry once]") from e
    if resp.status_code == 429:
        raise OpenverseError(
            "Openverse anonymous rate limit hit (20/min, 200/day). Wait a "
            "minute before the next call; set OPENVERSE_API_KEY for higher "
            "limits [ENVIRONMENT_FIXABLE: wait or register a key at "
            "api.openverse.org]", rate_limited=True)
    if resp.status_code == 401:
        raise OpenverseError("Openverse rejected OPENVERSE_API_KEY "
                             "[ENVIRONMENT_FIXABLE: unset it to use anonymous "
                             "access, or fix the key]")
    if resp.status_code >= 400:
        raise OpenverseError(f"Openverse returned HTTP {resp.status_code} "
                             "[INPUT_FIXABLE: check the arguments, e.g. an "
                             "unknown license or aspect value]")
    try:
        data = resp.json()
    except ValueError as e:
        raise OpenverseError("Openverse returned a non-JSON body "
                             "[TRANSIENT]") from e
    _store(cache_key, data)
    return data


def _validate(license, aspect_ratio, size, extension):
    if license not in LICENSES:
        raise ValueError(f"Unknown license {license!r}. Candidates: "
                         f"{', '.join(LICENSES)}. [INPUT_FIXABLE]")
    if aspect_ratio is not None and aspect_ratio not in ASPECTS:
        raise ValueError(f"Unknown aspect_ratio {aspect_ratio!r}. Candidates: "
                         f"{', '.join(ASPECTS)}. [INPUT_FIXABLE]")
    if size is not None and size not in SIZES:
        raise ValueError(f"Unknown size {size!r}. Candidates: "
                         f"{', '.join(SIZES)}. [INPUT_FIXABLE]")
    if extension is not None and extension not in ("jpg", "png", "gif", "svg"):
        raise ValueError(f"Unknown extension {extension!r}. Candidates: "
                         "jpg, png, gif, svg. [INPUT_FIXABLE]")


def _params(query, license, aspect_ratio, size, extension, page, page_size):
    params = {"q": query, "page_size": page_size, "page": page,
              "mature": "false"}
    if license == "cc":
        params["license_type"] = "all-cc"
    elif license not in ("all", None):
        params["license"] = license
    if aspect_ratio:
        params["aspect_ratio"] = aspect_ratio
    if size:
        params["size"] = size
    if extension:
        params["extension"] = extension
    return params


def _thumb(url):
    """Openverse thumbnails are proxied and reliably hotlinkable."""
    if not url:
        return None
    return f"https://api.openverse.org/v1/images/{url}" if not str(url).startswith("http") else url


def _image_row(result):
    return {
        "id": result.get("id"),
        "title": result.get("title") or "(untitled)",
        "creator": result.get("creator"),
        "license": (result.get("license") or "").upper() or None,
        "license_version": result.get("license_version"),
        "license_url": result.get("license_url"),
        "source": result.get("source"),
        "image_url": result.get("url"),
        "thumbnail": result.get("thumbnail"),
        "foreign_landing_url": result.get("foreign_landing_url"),
        "width": result.get("width"),
        "height": result.get("height"),
        "tags": [t.get("name") for t in (result.get("tags") or [])
                 if t.get("name")][:8],
    }


def _audio_row(result):
    return {
        "id": result.get("id"),
        "title": result.get("title") or "(untitled)",
        "creator": result.get("creator"),
        "license": (result.get("license") or "").upper() or None,
        "license_version": result.get("license_version"),
        "license_url": result.get("license_url"),
        "source": result.get("source"),
        "audio_url": (result.get("url")
                      or ((result.get("audio_files") or [{}])[0].get("url"))),
        "duration_s": result.get("duration"),
        "foreign_landing_url": result.get("foreign_landing_url"),
    }


def search_images(query, license="cc", aspect_ratio=None, size=None,
                  extension=None, page=1, page_size=10):
    """CC image search. Returns (rows, result_count)."""
    _validate(license, aspect_ratio, size, extension)
    data = _get("/images/", _params(query, license, aspect_ratio, size,
                                    extension, page, page_size))
    return ([_image_row(r) for r in data.get("results", [])],
            data.get("result_count", 0))


def get_image(image_id):
    """One image record by id (for attribution formatting)."""
    data = _get(f"/images/{image_id}/", {})
    return _image_row(data)


def search_audio(query, license="cc", page=1, page_size=8):
    """CC audio search (music, sound effects, field recordings)."""
    if license not in LICENSES:
        raise ValueError(f"Unknown license {license!r}. Candidates: "
                         f"{', '.join(LICENSES)}. [INPUT_FIXABLE]")
    params = {"q": query, "page_size": page_size, "page": page, "mature": "false"}
    if license == "cc":
        params["license_type"] = "all-cc"
    elif license not in ("all", None):
        params["license"] = license
    data = _get("/audio/", params)
    return ([_audio_row(r) for r in data.get("results", [])],
            data.get("result_count", 0))
