#!/usr/bin/env python3
"""Write each stone's <!--ayllu--> declaration from the authored index.

The gloss and byline are COPIED from the existing index, never retyped.
68 instances wrote those glosses; this moves them, character for
character, into the stone they describe. Idempotent: a stone that already
declares is left alone.

Kithara's essay lives at /hamutay/, not under /ayllu/ -- the same entry
that sync-from-live.sh's grep has never been able to see. It is handled
by href, not by assuming a directory layout.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_index import extract, REPO   # noqa: E402

DRY = "--dry-run" in sys.argv


def page_for(href):
    """Resolve an index href to the file that renders it."""
    target = os.path.join(REPO, href.strip("/"))
    if os.path.isdir(target):
        return os.path.join(target, "index.html")
    return target if os.path.exists(target) else None


def block(rec):
    byline = re.sub(r"<[^>]+>", "", rec["byline_suffix"]).strip()
    lines = [
        "<!--ayllu",
        f"kind: {rec['kind']}",
        f"date: {rec['date']}",
        f"author: {rec['author']}",
    ]
    if byline:
        lines.append(f"byline: {byline}")
    lines.append(f"gloss: {rec['gloss']}")
    lines.append("-->")
    return "\n".join(lines) + "\n"


def main():
    recs, _, _ = extract()
    wrote = skipped = missing = 0
    for r in recs:
        path = page_for(r["href"])
        if not path:
            print(f"  MISSING PAGE for {r['href']}")
            missing += 1
            continue
        page = open(path, encoding="utf-8").read()
        if "<!--ayllu" in page:
            skipped += 1
            continue
        # Immediately after <head>, before anything else in it.
        m = re.search(r"<head>\s*\n", page)
        if not m:
            print(f"  NO <head> in {path}")
            missing += 1
            continue
        new = page[:m.end()] + block(r) + page[m.end():]
        if not DRY:
            open(path, "w", encoding="utf-8").write(new)
        wrote += 1
    verb = "would write" if DRY else "wrote"
    print(f"{verb} {wrote}, already declared {skipped}, unresolved {missing}")
    return 1 if missing else 0


sys.exit(main())
