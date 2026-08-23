# SPDX-License-Identifier: MIT

"""Unit tests for attribution builders — pure logic, no network."""

from free_image_library import credits


def _row(**over):
    base = {
        "title": "Morning Fog", "creator": "davidyuweb",
        "license": "BY", "license_version": "2.0",
        "license_url": "https://creativecommons.org/licenses/by/2.0/",
        "source": "flickr", "foreign_landing_url": "https://flickr.com/x",
        "image_url": "https://live.staticflickr.com/x.jpg",
    }
    base.update(over)
    return base


def test_credit_lines_by():
    plain, md, html = credits.credit_lines(_row())
    assert '"Morning Fog" image by davidyuweb (flickr)' in plain
    assert "CC BY 2.0" in plain
    assert "creativecommons.org/licenses/by/2.0" in plain
    assert "[davidyuweb]" in md and "[CC BY 2.0]" in md
    assert '<a href="https://flickr.com/x">davidyuweb</a>' in html


def test_credit_lines_unknown_creator_and_no_urls():
    row = _row(creator=None, license_url=None, foreign_landing_url=None)
    plain, md, html = credits.credit_lines(row)
    assert "unknown creator" in plain
    assert "CC BY 2.0" in plain  # label still present without link
    assert "<a" not in html or "creativecommons" not in html


def test_credit_lines_cc0_label():
    _, _, _ = (None, None, None)
    plain, _, _ = credits.credit_lines(_row(license="CC0", license_version="1.0"))
    assert "CC0 1.0 (public domain)" in plain


def test_credit_notes_match_obligations():
    assert "No credit required" in credits.credit_note(_row(license="CC0"))
    assert "No credit required" in credits.credit_note(_row(license="PDM"))
    assert "Credit REQUIRED" in credits.credit_note(_row(license="BY"))
    assert "NOT allowed" in credits.credit_note(_row(license="BY-NC"))
    assert "License unknown" in credits.credit_note(_row(license=None))


def test_audio_media_noun():
    plain, _, _ = credits.credit_lines(_row(), media_noun="audio")
    assert '"Morning Fog" audio' in plain
