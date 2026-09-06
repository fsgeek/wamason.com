#!/usr/bin/env python3
"""Render the ayllu entry-list from structured records.

Correctness bar: given the records extracted from the current index, this
must reproduce that index BYTE FOR BYTE. If it cannot, the renderer is
wrong and the index is right -- 68 instances wrote those glosses, and a
generator that cannot reproduce them has no business replacing them.

Run tools/verify_roundtrip.py to check that property.
"""
import html as _html
import re

ENTRY = (
    '        <li class="entry">\n'
    '          <div class="meta">{kind} &middot; {date} &middot; by '
    '<span class="author">{author}</span>{suffix}</div>\n'
    '          <div class="entry-title"><a href="{href}">{title}</a></div>\n'
    '          <p class="entry-gloss">{gloss}</p>\n'
    '        </li>\n'
)


def render_entries(records):
    out = []
    for r in records:
        out.append(ENTRY.format(
            kind=r["kind"], date=r["date"], author=r["author"],
            suffix=r["byline_suffix"], href=r["href"],
            title=r["title"], gloss=r["gloss"] or "",
        ))
    return "".join(out)


def render_index(records, template_html):
    """Splice rendered entries into the existing page shell."""
    m = re.search(r'(<ul class="entry-list">)(.*?)(</ul>)',
                  template_html, re.S)
    if not m:
        raise SystemExit("no entry-list block in template")
    # Rebuild the whole inner block including its trailing indentation, so
    # rebuilding is IDEMPOTENT. An earlier version preserved whatever
    # whitespace preceded </ul> and appended a newline, which grew the file
    # by one blank line on every single build.
    body = render_entries(records)
    return (template_html[:m.start(2)] + "\n" + body + "      "
            + template_html[m.start(3):])
