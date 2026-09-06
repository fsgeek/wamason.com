#!/usr/bin/env python3
"""Extract the ayllu index into structured records, losslessly.

The index is currently hand-authored HTML and is the only shared mutable
state in the system: stones are independent files that never conflict,
while every contributor must edit this one document. All three known
defects landed here -- the 2026-08-31 <li> corruption, the three drifted
glosses, and the 2026-08-17 merge conflict.

This reads what exists. It asserts nothing about what the index should
look like; the generator's job is to reproduce it byte for byte before
anything is allowed to replace it.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "ayllu", "index.html")


def extract(path=INDEX):
    html = open(path, encoding="utf-8").read()
    m = re.search(r'(<ul class="entry-list">)(.*?)(</ul>)', html, re.S)
    if not m:
        raise SystemExit("no entry-list block")
    body = m.group(2)

    items = [i for i in re.split(r'(?=<li class="entry">)', body)
             if '<li class="entry">' in i]

    records = []
    for n, it in enumerate(items):
        meta = re.search(r'<div class="meta">(.*?)</div>', it, re.S)
        title = re.search(
            r'<div class="entry-title"><a href="([^"]+)">(.*?)</a></div>',
            it, re.S)
        gloss = re.search(r'<p class="entry-gloss">(.*?)</p>', it, re.S)
        if not (meta and title):
            raise SystemExit(f"entry {n}: unparseable")

        mtext = meta.group(1).strip()
        # "<kind> &middot; <Month Year> &middot; by <author><suffix>"
        head = re.match(r'^(.*?)\s*&middot;\s*(.*?)\s*&middot;\s*by\s*(.*)$',
                        mtext, re.S)
        if not head:
            raise SystemExit(f"entry {n}: meta shape unknown: {mtext[:80]}")
        kind, date, byline = (g.strip() for g in head.groups())

        author = re.search(r'<span class="author">(.*?)</span>', byline, re.S)
        # Everything after the author span, verbatim -- model,
        # collaborators. The amended marker is captured separately, so it
        # must be trimmed here or it renders twice.
        suffix = byline[author.end():] if author else ""
        suffix = re.sub(r'\s*<span class="amended">.*?</span>', "", suffix,
                        flags=re.S)

        records.append({
            "n": n,
            "kind": kind,
            "date": date,
            "author": author.group(1).strip() if author else "",
            "byline_suffix": suffix,
            "href": title.group(1),
            "title": title.group(2).strip(),
            "gloss": gloss.group(1).strip() if gloss else None,
            "amended": (re.search(r'<span class="amended">&middot; amended '
                                  r'([^<]+)</span>', it).group(1).strip()
                        if 'class="amended"' in it else ""),
        })
    return records, html, m


if __name__ == "__main__":
    recs, _, _ = extract()
    print(json.dumps(recs, indent=2, ensure_ascii=False))
