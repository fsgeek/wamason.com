#!/usr/bin/env python3
"""Build ayllu/index.html and ayllu/search.json from the stones.

The index becomes derived. Nothing is transcribed by hand into a shared
file any more, which is where every known defect in this system landed.

  --check   build and compare against the committed index; exit 1 if the
            derived output differs in CONTENT. Use this in the deploy gate.
  (default) write ayllu/index.html and ayllu/search.json.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ayllu                                    # noqa: E402
from render_index import render_index           # noqa: E402

CHECK = "--check" in sys.argv
INDEX = os.path.join(ayllu.REPO, "ayllu", "index.html")
SEARCH = os.path.join(ayllu.REPO, "ayllu", "search.json")


def records():
    recs, _ = ayllu.collect()
    order = ayllu.order_from_index()
    for r in recs:
        r["order"] = order.get(r["href"], 10_000)
    recs.sort(key=ayllu.sort_key)
    # render_index expects the byline as the raw span it will splice in
    for r in recs:
        # A byline normally reads " (a Claude X instance), with Tony" and
        # takes a leading space after the author name. One does not:
        # "Codex, this instance" is followed by ", with Tony", where a
        # space would render as "instance , with Tony". Punctuation-initial
        # bylines butt directly against the author span.
        b = r["byline"]
        if not b:
            r["byline_suffix"] = ""
        else:
            sep = "" if b[0] in ",.;:!?" else " "
            r["byline_suffix"] = (
                f'{sep}<span style="color:var(--muted)">{b}</span>')
    return recs


def main():
    recs = records()
    current = open(INDEX, encoding="utf-8").read()
    built = render_index(recs, current)

    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    same = norm(built) == norm(current)

    if CHECK:
        if same:
            print(f"index is current: {len(recs)} entries derived from stones")
            return 0
        print("DERIVED INDEX DIFFERS from the committed one.", file=sys.stderr)
        print("  Run tools/build_index.py to regenerate.", file=sys.stderr)
        return 1

    open(INDEX, "w", encoding="utf-8").write(built)
    corpus = [{k: r[k] for k in
               ("href", "title", "kind", "date", "author", "byline", "gloss")}
              for r in recs]
    open(SEARCH, "w", encoding="utf-8").write(
        json.dumps(corpus, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote index.html ({len(recs)} entries) and search.json "
          f"({os.path.getsize(SEARCH)} bytes)")
    return 0


sys.exit(main())
