#!/usr/bin/env python3
"""Prove the generator reproduces the hand-authored index exactly.

This is the gate on the whole generation change. Until it passes, nothing
generated is allowed to overwrite anything authored.
"""
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_index import extract          # noqa: E402
from render_index import render_index      # noqa: E402

import re

recs, original, _ = extract()
regenerated = render_index(recs, original)

# The bar is CONTENT identity, not byte identity. On 2026-09-06 the
# authored index differed from the generated one by 15 bytes, all of it
# stray indentation on four entries -- three of them the same entries that
# carried the gloss drift. Byte equality would have meant reproducing
# those defects. Content equality is the property worth enforcing: every
# gloss, title, href, author and meta line survives verbatim.
norm = lambda s: re.sub(r"\s+", " ", s).strip()

# str.format() silently ignores keyword arguments the template does not
# use, so a half-applied edit to ENTRY renders clean output with a field
# missing and raises nothing.
#
# This must read the STONES' declarations, not the index. An earlier
# version of this check re-extracted from the index itself, so when the
# template dropped a field both sides lost it together and the test
# passed. A check whose expected value is derived from the thing under
# test proves nothing.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ayllu as _ayllu                          # noqa: E402

_declared, _ = _ayllu.collect()
for _d in _declared:
    for field in ("amended",):
        val = _d.get(field)
        if val and str(val) not in regenerated:
            print(f"FIELD DROPPED: {field}={val!r} is declared by "
                  f"{_d['href']} but never reached the rendered index -- "
                  f"the template probably does not reference it.",
                  file=sys.stderr)
            sys.exit(1)

lost = [r for r in recs if r["gloss"] and r["gloss"] not in regenerated]
lost += [r for r in recs if r["title"] not in regenerated]
lost += [r for r in recs if r["href"] not in regenerated]

if norm(regenerated) == norm(original) and not lost:
    delta = len(original) - len(regenerated)
    print(f"ROUND-TRIP CONTENT-EXACT: {len(recs)} entries reproduced; "
          f"every gloss, title and href verbatim.")
    if delta:
        print(f"  ({delta} bytes of inconsistent whitespace normalized away)")
    sys.exit(0)

if lost:
    print(f"CONTENT LOST -- {len(lost)} field(s) did not survive:", file=sys.stderr)
    for r in lost[:10]:
        print(f"  - entry {r['n']}: {r['href']}", file=sys.stderr)
    sys.exit(1)

o, r = original.splitlines(True), regenerated.splitlines(True)
diff = list(difflib.unified_diff(o, r, "authored", "generated", n=1))
print(f"ROUND-TRIP MISMATCH: {len(diff)} diff lines", file=sys.stderr)
for line in diff[:60]:
    sys.stderr.write(line if line.endswith("\n") else line + "\n")
sys.exit(1)
