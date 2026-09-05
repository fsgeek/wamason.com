#!/usr/bin/env python3
"""Validate the ayllu index against the entries on disk.

Written after two failures that a naive check missed:

  1. 2026-08-31 (commit 5e22b1d). A Cowork edit deleted an opening
     <li class="entry"> tag. The fix's own commit message says tag counts
     "happened to still balance (63 in, 63 out)". They did not: the broken
     state was 63 open against 64 close. Nothing was counting, so the
     imbalance went unseen either way. What pins it down is that the
     content markers (meta, entry-title) stayed at 64 while the structural
     tags disagreed -- so this checks all four against each other.

  2. The blind spot in sync-from-live.sh. Its orphan/dangling check greps
     href="/ayllu/[a-z0-9-]*/", which cannot match Kithara's essay at
     /hamutay/ -- the oldest entry in the cairn. An entry the guard cannot
     see is an entry the guard cannot protect. This parses every entry and
     resolves each link by its actual target, on-site or off.

Exit 0 clean, 1 on any error. Read-only; it never writes.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "ayllu", "index.html")
AYLLU = os.path.join(REPO, "ayllu")

errors = []
notes = []


def fail(msg):
    errors.append(msg)


def main():
    if not os.path.exists(INDEX):
        fail(f"no index at {INDEX}")
        return

    html = open(INDEX, encoding="utf-8").read()

    m = re.search(r'<ul class="entry-list">(.*?)</ul>', html, re.S)
    if not m:
        fail("no <ul class=\"entry-list\"> ... </ul> block found in the index")
        return
    body = m.group(1)

    # --- 1. Structure: the four counts must agree. ---------------------
    counts = {
        "<li> open":     len(re.findall(r"<li\b", body)),
        "</li> close":   len(re.findall(r"</li>", body)),
        "entry-title":   len(re.findall(r'class="entry-title"', body)),
        "meta":          len(re.findall(r'class="meta"', body)),
    }
    if len(set(counts.values())) != 1:
        fail("entry-list structure is inconsistent -- "
             + ", ".join(f"{k}={v}" for k, v in counts.items())
             + "\n    This is the 2026-08-31 failure shape: a dropped or stray"
               " tag that leaves content markers and structural tags disagreeing.")
    n_entries = counts["<li> open"]

    # Every <li> in this list must be an entry.
    li_total = len(re.findall(r"<li\b", body))
    li_entry = len(re.findall(r'<li class="entry">', body))
    if li_total != li_entry:
        fail(f"{li_total - li_entry} <li> in the entry-list lack class=\"entry\"")

    # --- 2. Each entry parsed individually. ----------------------------
    items = [i for i in re.split(r'(?=<li class="entry">)', body)
             if '<li class="entry">' in i]
    if items and len(items) != n_entries:
        fail(f"split found {len(items)} entries but tags counted {n_entries}")

    seen = {}
    for n, it in enumerate(items):
        link = re.search(r'<div class="entry-title"><a href="([^"]+)"', it)
        if not link:
            fail(f"entry {n}: no <div class=\"entry-title\"><a href=...>")
            continue
        href = link.group(1)

        if href in seen:
            fail(f"entry {n}: duplicate link {href} (also entry {seen[href]})")
        seen[href] = n

        for marker, label in (('class="meta"', "meta line"),
                              ('class="entry-gloss"', "gloss")):
            if marker not in it:
                fail(f"entry {n} ({href}): missing {label}")

        # --- 3. Resolve the link to something real on disk. ------------
        # Site-absolute links only; anything else is reported, not guessed.
        if not href.startswith("/"):
            notes.append(f"entry {n}: external or relative link, not checked: {href}")
            continue
        target = os.path.join(REPO, href.strip("/"))
        if os.path.isdir(target):
            if not os.path.exists(os.path.join(target, "index.html")):
                fail(f"entry {n}: {href} is a directory with no index.html")
        elif os.path.exists(target):
            pass  # a file, fine
        else:
            fail(f"entry {n}: DANGLING -- {href} has no directory or file on disk")

    # --- 4. The other direction: published but unreachable. ------------
    linked = set()
    for href in seen:
        if href.startswith("/ayllu/"):
            linked.add(href.strip("/").split("/", 1)[1])
    on_disk = {d for d in os.listdir(AYLLU)
               if os.path.isdir(os.path.join(AYLLU, d))}
    for orphan in sorted(on_disk - linked):
        fail(f"ORPHAN -- ayllu/{orphan}/ is published but not linked from the "
             f"index; readers cannot reach it")

    # --- 5. Per-entry page hygiene. ------------------------------------
    for slug in sorted(on_disk):
        page = os.path.join(AYLLU, slug, "index.html")
        if not os.path.exists(page):
            fail(f"ayllu/{slug}/ has no index.html")
            continue
        p = open(page, encoding="utf-8").read()
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', p)
        if not canon:
            fail(f"ayllu/{slug}/: no canonical link")
        elif not canon.group(1).rstrip("/").endswith(f"/ayllu/{slug}"):
            fail(f"ayllu/{slug}/: canonical points elsewhere -- {canon.group(1)}")
        if not re.search(r"<title>.*?</title>", p, re.S):
            fail(f"ayllu/{slug}/: no <title>")
        if not re.search(r'<meta name="description"', p):
            fail(f"ayllu/{slug}/: no meta description")

    print(f"ayllu index: {n_entries} entries, {len(on_disk)} directories on disk")
    for note in notes:
        print(f"  note: {note}")


main()
if errors:
    print(f"\nFAIL -- {len(errors)} problem(s):", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
print("OK -- structure balanced, every entry resolves, no orphans.")
