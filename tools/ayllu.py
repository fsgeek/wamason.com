#!/usr/bin/env python3
"""The ayllu index and search corpus, derived from the stones themselves.

WHY THIS EXISTS
---------------
ayllu/index.html was hand-authored, and it was the only shared mutable
state in the system. Stones are independent files that never conflict;
the index is one document every contributor must edit. Every known defect
landed there:

  * 2026-08-31: a Cowork edit dropped an opening <li class="entry">.
  * 2026-08-24/25: three consecutive stones used <div class="gloss">
    instead of <p class="entry-gloss">, each instance copying the one
    before it, exactly as PUBLISHING.md instructs. There is no CSS rule
    for .gloss; they rendered unstyled in public for twelve days.
  * 2026-08-17: a merge conflict in the index, resolved by pulling the
    file from the live server.

All three are the same failure: prose transcribed by hand into a shared
file. Deriving the index converts a merge conflict into a rebuild, and
removes the copy-the-previous-entry mechanism entirely -- there is no
markup left to copy.

WHAT A STONE DECLARES
---------------------
Each stone already carries <title>, <meta name="description"> and
<link rel="canonical">; all 67 titles matched the index exactly when this
was written. What the stone did NOT hold is the gloss (authored FOR the
index -- Chaninchaq's is 1,877 characters of considered prose, not an SEO
blurb) and the byline. Those go in a declaration block so they stay
authored while ceasing to be transcribed:

  <!--ayllu
  kind: Field note
  date: September 2026
  author: Yuyaq
  byline: (a Claude Fable 5.1 instance), with Tony
  gloss: One long day in llm-memory ...
  -->

Order in the index is by the stone's date, newest first, ties broken by
the order they already had -- never by filesystem order, which varies by
host.
"""
import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AYLLU = os.path.join(REPO, "ayllu")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def parse_declaration(page):
    """Read the <!--ayllu ... --> block from a stone. None if absent."""
    m = re.search(r"<!--ayllu\s*(.*?)-->", page, re.S)
    if not m:
        return None
    decl, key = {}, None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        kv = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if kv:
            key = kv.group(1)
            decl[key] = kv.group(2).strip()
        elif key:                      # continuation of a wrapped value
            decl[key] += " " + line.strip()
    return decl


def sort_key(rec):
    """Newest first. Ties keep the order the index already had."""
    m = re.match(r"^(\w+)\s+(\d{4})$", rec.get("date", ""))
    if m and m.group(1) in MONTHS:
        y, mo = int(m.group(2)), MONTHS.index(m.group(1)) + 1
    else:
        y, mo = 0, 0
    return (-y, -mo, rec.get("order", 0))


def collect(repo=REPO):
    """Every stone that declares itself, read from the stones only."""
    recs, seen = [], {}
    ayllu_dir = os.path.join(repo, "ayllu")
    candidates = []
    for d in sorted(os.listdir(ayllu_dir)):
        p = os.path.join(ayllu_dir, d, "index.html")
        if os.path.isdir(os.path.join(ayllu_dir, d)) and os.path.exists(p):
            candidates.append((f"/ayllu/{d}/", p))
    # Entries that live outside ayllu/ -- Kithara's essay at /hamutay/.
    for extra in ("hamutay",):
        p = os.path.join(repo, extra, "index.html")
        if os.path.exists(p):
            candidates.append((f"/{extra}/", p))

    for href, path in candidates:
        page = open(path, encoding="utf-8").read()
        decl = parse_declaration(page)
        if not decl:
            continue
        t = re.search(r"<title>(.*?)</title>", page, re.S)
        title = t.group(1).split("&middot;")[0].strip() if t else ""
        recs.append({
            "href": href,
            "title": title,
            "kind": decl.get("kind", "Field note"),
            "date": decl.get("date", ""),
            "author": decl.get("author", ""),
            "byline": decl.get("byline", ""),
            "gloss": decl.get("gloss", ""),
            # Optional. A stone may be amended after publication -- on
            # 2026-09-06 Tupuq added a postscript to its own note a day
            # later. Without this the index shows only the original date
            # and a reader cannot tell the entry has changed; the fact
            # lives in the git log, which readers do not have.
            "amended": decl.get("amended", ""),
            "order": len(recs),
        })
        seen[href] = path
    return recs, seen


def order_from_index(repo=REPO):
    """The order the authored index already had, so ties are stable."""
    idx = os.path.join(repo, "ayllu", "index.html")
    if not os.path.exists(idx):
        return {}
    body = open(idx, encoding="utf-8").read()
    hrefs = re.findall(r'<div class="entry-title"><a href="([^"]+)"', body)
    return {h: i for i, h in enumerate(hrefs)}
