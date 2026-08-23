# SPDX-License-Identifier: MIT

"""Attribution builders — the instant-credit pattern from music-mcp.

Every result row can be turned into ready-to-paste credit lines in three
formats. CC BY / BY-SA require credit; CC0/PDM don't (but crediting is good
practice and we say so rather than silently dropping it).
"""

_LICENSE_NAMES = {
    "CC0": "CC0 1.0 (public domain)",
    "PDM": "Public Domain Mark",
    "BY": "CC BY",
    "BY-SA": "CC BY-SA",
    "BY-NC": "CC BY-NC",
    "BY-NC-SA": "CC BY-NC-SA",
    "BY-ND": "CC BY-ND",
    "BY-NC-ND": "CC BY-NC-ND",
}


def _license_label(row):
    lic = (row.get("license") or "").upper()
    version = row.get("license_version")
    name = _LICENSE_NAMES.get(lic, lic or "unknown license")
    return f"{name} {version}".strip() if version else name


def _creator(row):
    creator = (row.get("creator") or "").strip()
    if not creator:
        return None, None
    source = row.get("source") or "the source"
    url = row.get("foreign_landing_url")
    return creator, f'by <a href="{url}">{creator}</a> ({source})' if url \
        else f"by {creator} ({source})"


def credit_lines(row, media_noun="image"):
    """(plaintext, markdown, html) attribution for one result row."""
    title = row.get("title") or "(untitled)"
    creator, creator_html = _creator(row)
    creator_plain = creator or "unknown creator"
    source = row.get("source") or "the source"
    license_label = _license_label(row)
    license_url = row.get("license_url")
    landing = row.get("foreign_landing_url") or row.get("image_url") \
        or row.get("audio_url") or ""

    lic_plain = f"{license_label} ({license_url})" if license_url else license_label
    lic_md = f"[{license_label}]({license_url})" if license_url else license_label
    lic_html = (f'<a href="{license_url}">{license_label}</a>'
                if license_url else license_label)

    title_md = f"[{title}]({landing})" if landing else title
    title_html = f'<a href="{landing}">{title}</a>' if landing else title

    plain = (f'"{title}" {media_noun} by {creator_plain} ({source}), '
             f"licensed {lic_plain}")
    if creator:
        markdown = (f'*"{title}"* {media_noun} '
                    f"{creator_md(creator, landing, source)} — {lic_md}")
    else:
        markdown = f'*"{title}"* {media_noun} from {source} — {lic_md}'
    html = (f"{title_html} {media_noun} {creator_html} — {lic_html}")

    return plain, markdown, html


def creator_md(creator, landing, source):
    if not creator:
        return f"from {source}"
    return f"by [{creator}]({landing}) ({source})" if landing else \
        f"by {creator} ({source})"


def credit_note(row):
    """One-line obligation note: what credit this license actually requires."""
    lic = (row.get("license") or "").upper()
    if lic in ("CC0", "PDM"):
        return ("No credit required — but including one is good practice "
                "and helps the creator.")
    if lic in ("BY-NC", "BY-NC-SA", "BY-NC-ND"):
        return ("Credit REQUIRED and commercial use NOT allowed — verify the "
                "use is non-commercial before shipping.")
    if lic:
        return "Credit REQUIRED — paste the attribution verbatim."
    return "License unknown — do not use without checking the source page."
