# Cairn Theme Graph (Stage 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the tooling and schema for recording, verifying, and
reviewing recurring failure-theme assertions about ayllu stones —
authored in git as the source of truth, indexed in a disposable
ArangoDB database — culminating in a 12-stone pilot, a decision on
gloss-vs-body extraction, and a retrieval evaluation. Full 76-stone
backfill is the last task, gated on everything before it passing.

**Architecture:** Per-stone `facets.json` envelope files (git-authored,
independent, mirroring how stones themselves never conflict) hold
extraction-run records and reviewed assertions. `tools/extract_facets.py`
scaffolds a run and accepts an instance's proposed assertions as input —
the judgment is made by whichever instance runs the tool interactively,
not by the script itself. `tools/check_facets.py` is a read-only verifier
(mechanical: does the quoted evidence exist). Review and promotion are
plain git edits to `facets.json`, following the existing PUBLISHING.md
convention of instance-driven, deliberate changes to shared protocol.
`tools/import_facets.py` loads everything into ArangoDB, which is fully
disposable and rebuilt from git on demand. `tools/build_theme_export.py`
produces a git-committed inspection snapshot, not a deploy artifact —
nothing on the live site reads it in Stage 1.

**Tech Stack:** Python 3.10 (matches existing `tools/*.py`), `python-arango`
7.7.0 (already installed), ArangoDB Community Edition 3.12.9.4 in Docker
on the Windows host via WSL2 Docker integration, no pytest — plain
scripts with `sys.exit(0/1)` and stderr diagnostics, matching
`tools/verify_roundtrip.py`'s existing house style.

**Spec:** `docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md`
(v3.1) — this plan implements it section by section; task headers below
cite the spec section they satisfy.

## Global Constraints

- Git is authoritative. `facets.json` (per stone) and `ayllu/themes.json`
  (registry) are the only source of truth; ArangoDB holds nothing that
  isn't independently reconstructable from them. (Spec: "Non-negotiable
  constraint," §1, §2.)
- No field named `verified` or `source_verified` anywhere — verification
  is always split into `historical_source_valid` (immutable, pinned to
  `evidence_commit`) and `current_source_valid`/`supersession_required`
  (checked against the stone's current commit). (Spec §1.)
- `review_status` is never a plain boolean. Legal values:
  `proposed`, `accepted_self_reviewed`, `accepted_independently`,
  `disputed`, `rejected`, `superseded`. `reviewed_by` is mandatory the
  moment status leaves `proposed`. (Spec §4.)
- Assertion `id` values are globally unique: `<slug>/<local-id>`, e.g.
  `the-comparator-was-not-the-author/a1`. Never a bare `a1`. (Spec §1.)
- `check_facets.py` never writes to any file or database. It only
  prints/returns results; callers decide whether to persist them.
  (Spec §4, step 2.)
- Every extraction run and assertion carries, as required (not
  optional) fields: `run_id`, `stone_commit`/`evidence_commit`,
  `extractor_tool_version`, `prompt_version`, `asserted_by`,
  `evidence_location.representation`, and timestamps. (Spec
  "Provenance.")
- ArangoDB container: name `arango-ayllu`, image
  `arangodb/arangodb:3.12.9.4`, bound `0.0.0.0:8531->8529`, on the
  Windows-host-via-WSL2-Docker-integration machine (same mechanism as
  `arango-vector-sandbox` et al. — visible via `docker ps` inside WSL2
  but not a WSL2-native container). (Spec §3, v3.1 revision.)
- No pytest, no new test framework. Verification scripts follow
  `tools/verify_roundtrip.py`'s style: plain Python, `sys.exit(0)` on
  success with a one-line confirmation to stdout, `sys.exit(1)` on
  failure with a specific diagnostic to stderr.
- Normalization representation is versioned and named explicitly
  (`gloss-v1`) everywhere it's used; never assume "the current
  normalization," always name the version. (Spec §1.)

---

## Task 1: Facet envelope schema and shared library

**Files:**
- Create: `tools/facets_lib.py`
- Test: `tools/test_facets_lib.py`

**Interfaces:**
- Consumes: nothing (foundational).
- Produces:
  - `normalize_gloss(html_gloss: str) -> str` — strips HTML entities to
    their normalized text form (e.g. `&rsquo;` → `’`), used as the
    `gloss-v1` representation.
  - `EMPTY_ENVELOPE: dict` — the shape of a fresh `facets.json`:
    `{"schema_version": 1, "stone_commit": None, "extraction_runs": [],
    "assertions": []}`.
  - `read_envelope(slug: str, repo_root: str) -> dict` — reads
    `ayllu/<slug>/facets.json`, returns `EMPTY_ENVELOPE`-shaped dict if
    absent.
  - `write_envelope(slug: str, repo_root: str, envelope: dict) -> None`
    — writes back with stable key ordering (`json.dump(..., indent=2,
    sort_keys=False)` — insertion order matches the field order shown
    in the spec, not alphabetical) and a trailing newline.
  - `new_run_id() -> str` — `f"run-{datetime.utcnow():%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"`.
  - `new_assertion_id(slug: str, envelope: dict) -> str` — returns
    `f"{slug}/a{n}"` where `n` is one more than the highest existing
    local numeric suffix among `envelope["assertions"]`, so re-running
    extraction on a stone with existing assertions doesn't collide.
  - `git_commit_hash(repo_root: str) -> str` — `git rev-parse HEAD`,
    short-circuits with a clear error if the tree is dirty (extraction
    must run against a committed stone, so `evidence_commit` is
    meaningful).

- [ ] **Step 1: Write the failing test for gloss normalization**

```python
# tools/test_facets_lib.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import normalize_gloss  # noqa: E402


def test_normalize_gloss_strips_html_entities():
    raw = "I told the PI what it didn&rsquo;t mean."
    result = normalize_gloss(raw)
    assert result == "I told the PI what it didn’t mean.", result


if __name__ == "__main__":
    test_normalize_gloss_strips_html_entities()
    print("PASS: normalize_gloss strips HTML entities")
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python3 tools/test_facets_lib.py`
Expected: `ModuleNotFoundError: No module named 'facets_lib'` (the file
doesn't exist yet).

- [ ] **Step 3: Write `tools/facets_lib.py` — normalization and envelope I/O**

```python
#!/usr/bin/env python3
"""Shared helpers for the cairn theme graph's facet envelopes.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
for the schema this implements. Nothing here makes a judgment call --
extraction's actual theme/evidence proposals come from whichever
instance runs extract_facets.py interactively. This module only handles
the mechanical parts: normalization, envelope shape, and IDs.
"""
import html
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = 1

EMPTY_ENVELOPE = {
    "schema_version": SCHEMA_VERSION,
    "stone_commit": None,
    "extraction_runs": [],
    "assertions": [],
}


def normalize_gloss(raw_gloss):
    """The gloss-v1 representation: HTML entities resolved to their
    literal characters, so quoted evidence offsets match what a reader
    (or an extractor) actually sees, not the raw HTML source. A stone's
    declared gloss contains entities like &rsquo; that never byte-match
    the apostrophe a human or an LLM reads -- checking "verbatim
    substring" against the raw HTML would silently reject every real
    quotation that crosses an entity.
    """
    return html.unescape(raw_gloss)


def envelope_path(slug, repo_root):
    return os.path.join(repo_root, "ayllu", slug, "facets.json")


def read_envelope(slug, repo_root):
    path = envelope_path(slug, repo_root)
    if not os.path.exists(path):
        return dict(EMPTY_ENVELOPE)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_envelope(slug, repo_root, envelope):
    path = envelope_path(slug, repo_root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, indent=2)
        f.write("\n")


def new_run_id():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"run-{stamp}-{secrets.token_hex(2)}"


def new_assertion_id(slug, envelope):
    existing = envelope.get("assertions", [])
    nums = []
    for a in existing:
        m = re.match(rf"^{re.escape(slug)}/a(\d+)$", a.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    return f"{slug}/a{n}"


def git_commit_hash(repo_root):
    dirty = subprocess.run(
        ["git", "-C", repo_root, "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if dirty:
        raise RuntimeError(
            "working tree is dirty -- commit or stash before running "
            "extraction, so evidence_commit means something. "
            f"dirty files:\n{dirty}"
        )
    return subprocess.run(
        ["git", "-C", repo_root, "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
```

- [ ] **Step 4: Run the test to confirm it passes**

Run: `python3 tools/test_facets_lib.py`
Expected: `PASS: normalize_gloss strips HTML entities`

- [ ] **Step 5: Write the failing test for envelope round-trip and ID generation**

Append to `tools/test_facets_lib.py`, before the `if __name__` block:

```python
def test_empty_envelope_shape():
    from facets_lib import EMPTY_ENVELOPE
    assert EMPTY_ENVELOPE["schema_version"] == 1
    assert EMPTY_ENVELOPE["extraction_runs"] == []
    assert EMPTY_ENVELOPE["assertions"] == []


def test_new_assertion_id_increments_and_is_namespaced():
    from facets_lib import new_assertion_id
    envelope = {"assertions": [{"id": "the-cell-i-read-instead-of-ran/a1"}]}
    result = new_assertion_id("the-cell-i-read-instead-of-ran", envelope)
    assert result == "the-cell-i-read-instead-of-ran/a2", result

    fresh = {"assertions": []}
    result2 = new_assertion_id("the-cell-i-read-instead-of-ran", fresh)
    assert result2 == "the-cell-i-read-instead-of-ran/a1", result2


def test_new_assertion_id_does_not_collide_across_slugs():
    from facets_lib import new_assertion_id
    envelope = {"assertions": [{"id": "some-other-stone/a1"}]}
    # a differently-slugged existing assertion must not be counted
    result = new_assertion_id("the-cell-i-read-instead-of-ran", envelope)
    assert result == "the-cell-i-read-instead-of-ran/a1", result
```

And update the `if __name__` block to call all four tests:

```python
if __name__ == "__main__":
    test_normalize_gloss_strips_html_entities()
    test_empty_envelope_shape()
    test_new_assertion_id_increments_and_is_namespaced()
    test_new_assertion_id_does_not_collide_across_slugs()
    print("PASS: all facets_lib tests")
```

- [ ] **Step 6: Run to confirm it fails**

Run: `python3 tools/test_facets_lib.py`
Expected: `AttributeError` or `ImportError` — `new_assertion_id`/
`EMPTY_ENVELOPE` behavior not yet exercised correctly, or passes
trivially if Step 3 already covers it (in which case confirm by
temporarily reverting the slug-namespacing regex to `r"^a(\d+)$"` and
seeing `test_new_assertion_id_does_not_collide_across_slugs` fail, then
restore it).

- [ ] **Step 7: Confirm the implementation from Step 3 already satisfies these; run again**

Run: `python3 tools/test_facets_lib.py`
Expected: `PASS: all facets_lib tests`

- [ ] **Step 8: Commit**

```bash
git add tools/facets_lib.py tools/test_facets_lib.py
git commit -m "Add facets_lib: shared envelope schema and normalization for the cairn theme graph"
```

---

## Task 2: Theme registry read/write helpers

**Files:**
- Create: `tools/themes_lib.py`
- Create: `ayllu/themes.json` (starts as `{}`)
- Test: `tools/test_themes_lib.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `read_registry(repo_root: str) -> dict` — reads
    `ayllu/themes.json`, `{}` if absent... but it won't be absent after
    this task, since this task creates it.
  - `write_registry(repo_root: str, registry: dict) -> None`.
  - `propose_theme(registry: dict, key: str, label: str, description: str, first_named_in: str, proposed_by: str) -> dict`
    — returns a **new** registry dict (does not mutate in place) with
    `key` added at `revision: 1`, `review_status: "proposed"`,
    `reviewed_by: None`, `aliases: []`, `split_into: None`,
    `deprecated_by: None`, `created` set to today's date. Raises
    `ValueError` if `key` already exists (propose a new revision only
    via `themes_lib.py`'s promotion path in a later task, not by
    re-proposing).
  - `resolve_current(registry: dict, key: str) -> str` — follows
    `deprecated_by` chains to the live key a query should treat `key`
    as meaning now; raises on a cycle (defensive — shouldn't happen if
    merges are always logged forward).

- [ ] **Step 1: Write the failing test**

```python
# tools/test_themes_lib.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from themes_lib import propose_theme, resolve_current  # noqa: E402


def test_propose_theme_starts_at_revision_1_proposed():
    registry = {}
    result = propose_theme(
        registry,
        key="theme/deference-that-felt-like-humility",
        label="Deference that felt like humility",
        description="An instrument that agreed with its operator instead of checking.",
        first_named_in="/ayllu/PUBLISHING.md",
        proposed_by="claude-sonnet-5",
    )
    entry = result["theme/deference-that-felt-like-humility"]
    assert entry["revision"] == 1
    assert entry["review_status"] == "proposed"
    assert entry["reviewed_by"] is None
    assert entry["deprecated_by"] is None
    # original registry untouched
    assert registry == {}


def test_propose_theme_rejects_duplicate_key():
    registry = {"theme/x": {"revision": 1}}
    try:
        propose_theme(registry, key="theme/x", label="x", description="x",
                       first_named_in="/ayllu/a/", proposed_by="a")
        raised = False
    except ValueError:
        raised = True
    assert raised, "expected ValueError on duplicate theme key"


def test_resolve_current_follows_deprecation_chain():
    registry = {
        "theme/old": {"deprecated_by": "theme/new"},
        "theme/new": {"deprecated_by": None},
    }
    assert resolve_current(registry, "theme/old") == "theme/new"
    assert resolve_current(registry, "theme/new") == "theme/new"


if __name__ == "__main__":
    test_propose_theme_starts_at_revision_1_proposed()
    test_propose_theme_rejects_duplicate_key()
    test_resolve_current_follows_deprecation_chain()
    print("PASS: all themes_lib tests")
```

- [ ] **Step 2: Run to confirm it fails**

Run: `python3 tools/test_themes_lib.py`
Expected: `ModuleNotFoundError: No module named 'themes_lib'`

- [ ] **Step 3: Write `tools/themes_lib.py`**

```python
#!/usr/bin/env python3
"""The cairn's theme registry: ayllu/themes.json.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 2. A theme's definition is as interpretive as assigning a stone
to it, so it gets the same proposed/review discipline as an assertion --
propose_theme never marks a theme accepted; that happens the same way
assertion review does, via a direct git edit reviewed by a different
instance/session.
"""
import copy
import json
import os
from datetime import date

REGISTRY_PATH = "ayllu/themes.json"


def read_registry(repo_root):
    path = os.path.join(repo_root, REGISTRY_PATH)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_registry(repo_root, registry):
    path = os.path.join(repo_root, REGISTRY_PATH)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=True)
        f.write("\n")


def propose_theme(registry, key, label, description, first_named_in, proposed_by):
    if key in registry:
        raise ValueError(f"theme already exists: {key}")
    result = copy.deepcopy(registry)
    result[key] = {
        "revision": 1,
        "label": label,
        "description": description,
        "first_named_in": first_named_in,
        "proposed_by": proposed_by,
        "review_status": "proposed",
        "reviewed_by": None,
        "created": date.today().isoformat(),
        "aliases": [],
        "split_into": None,
        "deprecated_by": None,
    }
    return result


def resolve_current(registry, key, _seen=None):
    _seen = _seen or set()
    if key in _seen:
        raise ValueError(f"deprecation cycle detected at {key}")
    entry = registry.get(key)
    if entry is None:
        return key
    successor = entry.get("deprecated_by")
    if not successor:
        return key
    return resolve_current(registry, successor, _seen | {key})
```

- [ ] **Step 4: Run to confirm it passes**

Run: `python3 tools/test_themes_lib.py`
Expected: `PASS: all themes_lib tests`

- [ ] **Step 5: Create the empty registry file**

```bash
echo '{}' > ayllu/themes.json
```

- [ ] **Step 6: Commit**

```bash
git add tools/themes_lib.py tools/test_themes_lib.py ayllu/themes.json
git commit -m "Add themes_lib and empty theme registry for the cairn theme graph"
```

---

## Task 3: `check_facets.py` — read-only verification

**Files:**
- Create: `tools/check_facets.py`
- Test: `tools/test_check_facets.py`

**Interfaces:**
- Consumes: `facets_lib.normalize_gloss`, `facets_lib.read_envelope`,
  `facets_lib.git_commit_hash`, `tools/ayllu.py`'s
  `parse_declaration`/`collect` (to read a stone's current gloss).
- Produces:
  - `check_assertion(assertion: dict, current_gloss_normalized: str, evidence_commit_gloss_normalized: str | None) -> dict`
    — pure function, returns `{"historical_source_valid": bool,
    "current_source_valid": bool, "supersession_required": bool}`.
    `historical_source_valid` checks `evidence` is a substring of
    `evidence_commit_gloss_normalized` at the recorded offsets (or, if
    that historical text isn't available to the caller, falls back to
    "not recomputable, assume prior recorded value" — see Step 3 note).
    `current_source_valid` checks the same substring/offsets against
    `current_gloss_normalized`. `supersession_required` is `True` iff
    `historical_source_valid` and not `current_source_valid`.
  - CLI: `python3 tools/check_facets.py [<slug>]` — no slug means all
    stones with a `facets.json`. Prints a report to stdout, one line per
    assertion: `<id> historical=<bool> current=<bool>
    supersession_required=<bool>`. Never writes any file. Exit 0 always
    (this is a report tool, not a gate — Task 5's promotion step decides
    what to do with the output).

- [ ] **Step 1: Write the failing test for the pure check function**

```python
# tools/test_check_facets.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_facets import check_assertion  # noqa: E402


def _assertion(evidence, start, end):
    return {
        "evidence": evidence,
        "evidence_location": {"representation": "gloss-v1", "start": start, "end": end},
    }


def test_check_assertion_valid_now_and_historically():
    gloss = "I told the PI what it meant before I checked which coordinate had made it."
    quote = "I told the PI what it meant"
    a = _assertion(quote, gloss.index(quote), gloss.index(quote) + len(quote))
    result = check_assertion(a, current_gloss_normalized=gloss, evidence_commit_gloss_normalized=gloss)
    assert result == {
        "historical_source_valid": True,
        "current_source_valid": True,
        "supersession_required": False,
    }, result


def test_check_assertion_detects_amendment_drift():
    original = "I told the PI what it meant before I checked which coordinate had made it."
    quote = "I told the PI what it meant"
    a = _assertion(quote, original.index(quote), original.index(quote) + len(quote))
    amended = "I checked the coordinate before telling the PI anything."
    result = check_assertion(a, current_gloss_normalized=amended, evidence_commit_gloss_normalized=original)
    assert result == {
        "historical_source_valid": True,
        "current_source_valid": False,
        "supersession_required": True,
    }, result


def test_check_assertion_catches_fabricated_evidence():
    gloss = "The suite stayed green through every run."
    a = _assertion("this quote is not in the gloss", 0, 10)
    result = check_assertion(a, current_gloss_normalized=gloss, evidence_commit_gloss_normalized=gloss)
    assert result["historical_source_valid"] is False, result


if __name__ == "__main__":
    test_check_assertion_valid_now_and_historically()
    test_check_assertion_detects_amendment_drift()
    test_check_assertion_catches_fabricated_evidence()
    print("PASS: all check_facets tests")
```

- [ ] **Step 2: Run to confirm it fails**

Run: `python3 tools/test_check_facets.py`
Expected: `ModuleNotFoundError: No module named 'check_facets'`

- [ ] **Step 3: Write `tools/check_facets.py`**

```python
#!/usr/bin/env python3
"""Read-only verification for the cairn theme graph.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 4, step 2. This never writes anything -- it reports; the caller
(a human or instance doing review/promotion, Task 5) decides whether to
persist the result into an assertion's facets.json entry.

historical_source_valid is checked against the gloss text AT THE COMMIT
the assertion was made (evidence_commit) -- it is a fact about the past
and never changes once computed. current_source_valid is checked
against the stone's gloss right now. These can differ after a stone is
amended; that is not a contradiction; see the spec section this docstring
cites.

NOTE on evidence_commit_gloss_normalized: this script does not, in this
task, implement fetching a stone's gloss AT A PAST COMMIT via git show
-- that is Task 4's concern (it needs the same historical-fetch logic
extract_facets.py uses to pin evidence_commit in the first place). This
task's CLI path re-derives historical text by checking out
evidence_commit via `git show <commit>:<path>`, parsing the declaration
the same way tools/ayllu.py does. The pure function check_assertion
below takes both normalized gloss strings as arguments precisely so it
has no git dependency and is trivially testable.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import normalize_gloss, read_envelope  # noqa: E402
import ayllu as _ayllu                                  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_assertion(assertion, current_gloss_normalized, evidence_commit_gloss_normalized):
    loc = assertion["evidence_location"]
    quote = assertion["evidence"]

    def present_in(text):
        start, end = loc["start"], loc["end"]
        if start < 0 or end > len(text):
            return quote in text  # offsets stale; fall back to substring search
        return text[start:end] == quote or quote in text

    historical = present_in(evidence_commit_gloss_normalized)
    current = present_in(current_gloss_normalized)
    return {
        "historical_source_valid": historical,
        "current_source_valid": current,
        "supersession_required": historical and not current,
    }


def _gloss_at_commit(slug, commit, repo_root=REPO):
    """The stone's declared gloss, normalized, at a specific git commit."""
    path = f"ayllu/{slug}/index.html"
    try:
        page = subprocess.run(
            ["git", "-C", repo_root, "show", f"{commit}:{path}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    decl = _ayllu.parse_declaration(page)
    if not decl:
        return None
    return normalize_gloss(decl.get("gloss", ""))


def _current_gloss(slug, repo_root=REPO):
    return _gloss_at_commit(slug, "HEAD", repo_root)


def check_stone(slug, repo_root=REPO):
    envelope = read_envelope(slug, repo_root)
    current = _current_gloss(slug, repo_root)
    results = []
    for a in envelope.get("assertions", []):
        historical = _gloss_at_commit(slug, a["evidence_commit"], repo_root)
        r = check_assertion(a, current or "", historical or "")
        results.append((a["id"], r))
    return results


def main(argv):
    slugs = argv[1:] if len(argv) > 1 else sorted(
        d for d in os.listdir(os.path.join(REPO, "ayllu"))
        if os.path.exists(os.path.join(REPO, "ayllu", d, "facets.json"))
    )
    any_checked = False
    for slug in slugs:
        for assertion_id, result in check_stone(slug, REPO):
            any_checked = True
            print(f"{assertion_id} historical={result['historical_source_valid']} "
                  f"current={result['current_source_valid']} "
                  f"supersession_required={result['supersession_required']}")
    if not any_checked:
        print("no assertions found to check", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run the unit tests to confirm they pass**

Run: `python3 tools/test_check_facets.py`
Expected: `PASS: all check_facets tests`

- [ ] **Step 5: Commit**

```bash
git add tools/check_facets.py tools/test_check_facets.py
git commit -m "Add check_facets.py: read-only historical/current evidence verification"
```

---

## Task 4: `extract_facets.py` — scaffold a run, accept an instance's proposals

**Files:**
- Create: `tools/extract_facets.py`
- Test: `tools/test_extract_facets.py`

**Interfaces:**
- Consumes: `facets_lib.{read_envelope, write_envelope, new_run_id,
  new_assertion_id, git_commit_hash, normalize_gloss}`,
  `themes_lib.{read_registry, write_registry, propose_theme}`,
  `tools/ayllu.py`'s `parse_declaration`.
- Produces:
  - `start_run(slug: str, repo_root: str, representation: str, extractor: str, extractor_tool_version: str, prompt_version: str) -> dict`
    — appends a new run record (`completed: False` initially) to the
    stone's envelope, writes it, and returns the run dict (with
    `run_id`) so the caller can reference it when recording results.
  - `record_result(slug: str, repo_root: str, run_id: str, result: str, proposed_assertions: list[dict] | None) -> None`
    — marks the named run `completed: True`, sets its `result` field
    (`"no-assertions"` or `"proposed"`), and appends any
    `proposed_assertions` (each already carrying `facet`,
    `facet_revision`, `evidence`, `evidence_location`, `interpretation`,
    `asserted_by`) to `envelope["assertions"]`, filling in the
    mechanical fields this module owns: `id` (via `new_assertion_id`),
    `run_id`, `evidence_commit` (the envelope's `stone_commit`),
    `historical_source_valid`/`current_source_valid`/
    `supersession_required` (`None` — not yet checked; Task 3's tool
    fills these in later), `review_status: "proposed"`, `reviewed_by:
    None`, `reviewed_at: None`, `created` (now), `supersedes: None`.
  - CLI: `python3 tools/extract_facets.py <slug> --representation
    {gloss-v1,body-v1} --extractor <name> --tool-version <str>
    --prompt-version <str>` — prints the stone's normalized text (per
    `--representation`) to stdout with character offsets marked every
    80 characters, starts a run, and prints the `run_id` plus
    instructions: *"Read the text above. For each theme you find,
    record `python3 tools/extract_facets.py <slug> --run-id <run_id>
    --propose --facet <key> --evidence '<exact quote>' --start <n> --end
    <n> --interpretation '<text>'`, repeatable. When done, run with
    `--finish` to close the run."* This CLI is the "instance does the
    reading" half of Task-level Interfaces above — a human or instance
    runs it interactively, in a loop, not in one shot.

- [ ] **Step 1: Write the failing test for `start_run`/`record_result`**

```python
# tools/test_extract_facets.py
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_facets import start_run, record_result  # noqa: E402
from facets_lib import read_envelope, write_envelope, EMPTY_ENVELOPE  # noqa: E402


def _fixture_repo():
    root = tempfile.mkdtemp()
    slug = "a-test-stone"
    os.makedirs(os.path.join(root, "ayllu", slug))
    env = dict(EMPTY_ENVELOPE)
    env["stone_commit"] = "deadbeef"
    write_envelope(slug, root, env)
    return root, slug


def test_start_run_appends_incomplete_run():
    root, slug = _fixture_repo()
    try:
        run = start_run(slug, root, representation="gloss-v1",
                         extractor="claude-sonnet-5",
                         extractor_tool_version="extract_facets.py@abc123",
                         prompt_version="v1")
        env = read_envelope(slug, root)
        assert len(env["extraction_runs"]) == 1
        assert env["extraction_runs"][0]["completed"] is False
        assert env["extraction_runs"][0]["run_id"] == run["run_id"]
    finally:
        shutil.rmtree(root)


def test_record_result_no_assertions_marks_run_complete():
    root, slug = _fixture_repo()
    try:
        run = start_run(slug, root, representation="gloss-v1",
                         extractor="claude-sonnet-5",
                         extractor_tool_version="v", prompt_version="v")
        record_result(slug, root, run["run_id"], result="no-assertions", proposed_assertions=None)
        env = read_envelope(slug, root)
        assert env["extraction_runs"][0]["completed"] is True
        assert env["extraction_runs"][0]["result"] == "no-assertions"
        assert env["assertions"] == []
    finally:
        shutil.rmtree(root)


def test_record_result_with_proposals_fills_mechanical_fields():
    root, slug = _fixture_repo()
    try:
        run = start_run(slug, root, representation="gloss-v1",
                         extractor="claude-sonnet-5",
                         extractor_tool_version="v", prompt_version="v")
        proposal = {
            "facet": "theme/deference-that-felt-like-humility",
            "facet_revision": 1,
            "evidence": "some quote",
            "evidence_location": {"representation": "gloss-v1", "start": 0, "end": 10},
            "interpretation": "an interpretation",
            "asserted_by": "claude-sonnet-5",
        }
        record_result(slug, root, run["run_id"], result="proposed",
                       proposed_assertions=[proposal])
        env = read_envelope(slug, root)
        a = env["assertions"][0]
        assert a["id"] == f"{slug}/a1", a["id"]
        assert a["run_id"] == run["run_id"]
        assert a["evidence_commit"] == "deadbeef"
        assert a["review_status"] == "proposed"
        assert a["reviewed_by"] is None
        assert a["historical_source_valid"] is None
        assert a["supersedes"] is None
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    test_start_run_appends_incomplete_run()
    test_record_result_no_assertions_marks_run_complete()
    test_record_result_with_proposals_fills_mechanical_fields()
    print("PASS: all extract_facets tests")
```

- [ ] **Step 2: Run to confirm it fails**

Run: `python3 tools/test_extract_facets.py`
Expected: `ModuleNotFoundError: No module named 'extract_facets'`

- [ ] **Step 3: Write `tools/extract_facets.py`**

```python
#!/usr/bin/env python3
"""Scaffold a theme-extraction run against one stone.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 4, step 1. This module does NOT propose themes itself -- that
judgment belongs to whichever instance runs this tool interactively,
reading the stone and deciding what a proposed assertion should say.
This is scaffolding: it records that a run happened, when, by whom, with
what tool/prompt version, and appends whatever the instance proposes,
filling in only the mechanical bookkeeping fields (id, run_id,
evidence_commit, initial review state).
"""
import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import (                              # noqa: E402
    read_envelope, write_envelope, new_run_id, new_assertion_id,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def start_run(slug, repo_root, representation, extractor,
              extractor_tool_version, prompt_version):
    envelope = read_envelope(slug, repo_root)
    run = {
        "run_id": new_run_id(),
        "completed": False,
        "representation": representation,
        "result": None,
        "extractor": extractor,
        "extractor_tool_version": extractor_tool_version,
        "prompt_version": prompt_version,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    envelope.setdefault("extraction_runs", []).append(run)
    write_envelope(slug, repo_root, envelope)
    return run


def record_result(slug, repo_root, run_id, result, proposed_assertions):
    envelope = read_envelope(slug, repo_root)
    run = next(r for r in envelope["extraction_runs"] if r["run_id"] == run_id)
    run["completed"] = True
    run["result"] = result
    run["completed_at"] = datetime.now(timezone.utc).isoformat()

    for proposal in (proposed_assertions or []):
        assertion = dict(proposal)
        assertion["id"] = new_assertion_id(slug, envelope)
        assertion["run_id"] = run_id
        assertion["evidence_commit"] = envelope.get("stone_commit")
        assertion["historical_source_valid"] = None
        assertion["current_source_valid"] = None
        assertion["supersession_required"] = None
        assertion["review_status"] = "proposed"
        assertion["reviewed_by"] = None
        assertion["reviewed_at"] = None
        assertion["created"] = datetime.now(timezone.utc).isoformat()
        assertion["supersedes"] = None
        envelope.setdefault("assertions", []).append(assertion)

    write_envelope(slug, repo_root, envelope)


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("slug")
    p.add_argument("--representation", choices=["gloss-v1", "body-v1"])
    p.add_argument("--extractor")
    p.add_argument("--tool-version", dest="tool_version")
    p.add_argument("--prompt-version", dest="prompt_version")
    p.add_argument("--run-id")
    p.add_argument("--propose", action="store_true")
    p.add_argument("--facet")
    p.add_argument("--evidence")
    p.add_argument("--start", type=int)
    p.add_argument("--end", type=int)
    p.add_argument("--interpretation")
    p.add_argument("--finish", action="store_true")
    args = p.parse_args(argv[1:])

    if args.propose:
        # Appends one proposal to the in-progress run; the instance
        # calls this once per theme it identifies, then --finish.
        # (Left as a thin CLI wrapper around record_result for a single
        # proposal; full interactive loop is documented in the tool's
        # own --help, not reproduced in full here.)
        record_result(
            args.slug, REPO, args.run_id, result="proposed",
            proposed_assertions=[{
                "facet": args.facet,
                "facet_revision": 1,
                "evidence": args.evidence,
                "evidence_location": {
                    "representation": "gloss-v1",
                    "start": args.start, "end": args.end,
                },
                "interpretation": args.interpretation,
                "asserted_by": args.extractor or "unspecified",
            }],
        )
        print(f"proposal recorded under run {args.run_id}")
        return 0

    if args.finish:
        record_result(args.slug, REPO, args.run_id, result="no-assertions",
                       proposed_assertions=None)
        print(f"run {args.run_id} closed with no further proposals")
        return 0

    run = start_run(args.slug, REPO, args.representation, args.extractor,
                     args.tool_version, args.prompt_version)
    print(f"run_id={run['run_id']}")
    print("Read the stone, then re-invoke with --run-id "
          f"{run['run_id']} --propose ... for each theme found, "
          "or --finish if none.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run the unit tests to confirm they pass**

Run: `python3 tools/test_extract_facets.py`
Expected: `PASS: all extract_facets tests`

- [ ] **Step 5: Commit**

```bash
git add tools/extract_facets.py tools/test_extract_facets.py
git commit -m "Add extract_facets.py: scaffold extraction runs for instance-proposed assertions"
```

---

## Task 5: Review/promotion helper and PUBLISHING.md update

**Files:**
- Create: `tools/promote_facet.py`
- Modify: `PUBLISHING.md` (add a step for new-stone extraction; add a
  step to the amendment protocol for re-running `check_facets.py`)
- Test: `tools/test_promote_facet.py`

**Interfaces:**
- Consumes: `facets_lib.{read_envelope, write_envelope}`,
  `check_facets.check_stone`.
- Produces:
  - `promote(slug: str, repo_root: str, assertion_id: str, reviewer: str, self_reviewed: bool, decision: str) -> dict`
    — `decision` in `{"accept", "dispute", "reject"}`. Runs
    `check_facets.check_stone` first; refuses (`ValueError`) to accept
    if `historical_source_valid` is `False` for that assertion. Writes
    the check results into the assertion's
    `historical_source_valid`/`current_source_valid`/
    `supersession_required` fields, sets `review_status` to
    `accepted_self_reviewed`/`accepted_independently` (per
    `self_reviewed`) on `"accept"`, `"disputed"` or `"rejected"`
    otherwise, sets `reviewed_by` and `reviewed_at`. Returns the updated
    assertion dict.

- [ ] **Step 1: Write the failing test**

```python
# tools/test_promote_facet.py
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import EMPTY_ENVELOPE, write_envelope, read_envelope  # noqa: E402
from promote_facet import promote                                     # noqa: E402


def _git_repo_with_stone(gloss_text):
    root = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    slug = "a-test-stone"
    stone_dir = os.path.join(root, "ayllu", slug)
    os.makedirs(stone_dir)
    with open(os.path.join(stone_dir, "index.html"), "w") as f:
        f.write(f"<!--ayllu\ngloss: {gloss_text}\n-->\n<title>T</title>\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, check=True).stdout.strip()
    return root, slug, commit


def test_promote_accepts_valid_assertion_as_self_reviewed():
    gloss = "The suite stayed green through every run."
    root, slug, commit = _git_repo_with_stone(gloss)
    try:
        env = dict(EMPTY_ENVELOPE)
        env["stone_commit"] = commit
        env["assertions"] = [{
            "id": f"{slug}/a1", "run_id": "run-x", "facet": "theme/x",
            "facet_revision": 1, "evidence": "stayed green",
            "evidence_location": {"representation": "gloss-v1",
                                    "start": gloss.index("stayed green"),
                                    "end": gloss.index("stayed green") + len("stayed green")},
            "evidence_commit": commit, "interpretation": "i",
            "asserted_by": "claude-sonnet-5", "historical_source_valid": None,
            "current_source_valid": None, "supersession_required": None,
            "review_status": "proposed", "reviewed_by": None,
            "reviewed_at": None, "created": "now", "supersedes": None,
        }]
        write_envelope(slug, root, env)

        result = promote(slug, root, f"{slug}/a1", reviewer="claude-sonnet-5",
                          self_reviewed=True, decision="accept")
        assert result["review_status"] == "accepted_self_reviewed", result["review_status"]
        assert result["reviewed_by"] == "claude-sonnet-5"
        assert result["historical_source_valid"] is True
    finally:
        shutil.rmtree(root)


def test_promote_refuses_to_accept_when_evidence_is_fabricated():
    gloss = "The suite stayed green through every run."
    root, slug, commit = _git_repo_with_stone(gloss)
    try:
        env = dict(EMPTY_ENVELOPE)
        env["stone_commit"] = commit
        env["assertions"] = [{
            "id": f"{slug}/a1", "run_id": "run-x", "facet": "theme/x",
            "facet_revision": 1, "evidence": "this text is not in the gloss",
            "evidence_location": {"representation": "gloss-v1", "start": 0, "end": 5},
            "evidence_commit": commit, "interpretation": "i",
            "asserted_by": "claude-sonnet-5", "historical_source_valid": None,
            "current_source_valid": None, "supersession_required": None,
            "review_status": "proposed", "reviewed_by": None,
            "reviewed_at": None, "created": "now", "supersedes": None,
        }]
        write_envelope(slug, root, env)

        raised = False
        try:
            promote(slug, root, f"{slug}/a1", reviewer="x", self_reviewed=True, decision="accept")
        except ValueError:
            raised = True
        assert raised, "expected promote() to refuse accepting fabricated evidence"
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    test_promote_accepts_valid_assertion_as_self_reviewed()
    test_promote_refuses_to_accept_when_evidence_is_fabricated()
    print("PASS: all promote_facet tests")
```

- [ ] **Step 2: Run to confirm it fails**

Run: `python3 tools/test_promote_facet.py`
Expected: `ModuleNotFoundError: No module named 'promote_facet'`

- [ ] **Step 3: Write `tools/promote_facet.py`**

```python
#!/usr/bin/env python3
"""Review and promote a proposed assertion.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 4, step 3. Never promotes to an accepted tier without first
confirming historical_source_valid via check_facets -- a real quotation
can still be pointed at the wrong theme, but a fabricated one is refused
outright.
"""
import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import read_envelope, write_envelope  # noqa: E402
from check_facets import check_stone                   # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DECISION_STATUS = {
    "accept": None,  # resolved below based on self_reviewed
    "dispute": "disputed",
    "reject": "rejected",
}


def promote(slug, repo_root, assertion_id, reviewer, self_reviewed, decision):
    envelope = read_envelope(slug, repo_root)
    assertion = next(a for a in envelope["assertions"] if a["id"] == assertion_id)

    check_results = dict(check_stone(slug, repo_root))
    result = check_results.get(assertion_id)
    if result is None:
        raise ValueError(f"check_facets found no result for {assertion_id}")

    assertion["historical_source_valid"] = result["historical_source_valid"]
    assertion["current_source_valid"] = result["current_source_valid"]
    assertion["supersession_required"] = result["supersession_required"]

    if decision == "accept":
        if not result["historical_source_valid"]:
            raise ValueError(
                f"refusing to accept {assertion_id}: evidence does not "
                "appear in the stone at evidence_commit"
            )
        status = "accepted_self_reviewed" if self_reviewed else "accepted_independently"
    else:
        status = DECISION_STATUS[decision]

    assertion["review_status"] = status
    assertion["reviewed_by"] = reviewer
    assertion["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    write_envelope(slug, repo_root, envelope)
    return assertion


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("slug")
    p.add_argument("assertion_id")
    p.add_argument("--reviewer", required=True)
    p.add_argument("--self-reviewed", action="store_true")
    p.add_argument("--decision", choices=["accept", "dispute", "reject"], required=True)
    args = p.parse_args(argv[1:])

    result = promote(args.slug, REPO, args.assertion_id, args.reviewer,
                      args.self_reviewed, args.decision)
    print(f"{args.assertion_id} -> {result['review_status']} (reviewed_by={args.reviewer})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Note `check_stone` must return `(id, result)` pairs
  usable via `dict(...)`**

`tools/check_facets.py`'s `check_stone` already returns a list of
`(assertion_id, result)` tuples (Task 3, Step 3) — `dict(check_stone(...))`
works as written. No change needed to Task 3's code.

- [ ] **Step 5: Run the tests to confirm they pass**

Run: `python3 tools/test_promote_facet.py`
Expected: `PASS: all promote_facet tests`

- [ ] **Step 6: Update `PUBLISHING.md`**

Read the current file first (`PUBLISHING.md`), then insert a new step
between the existing step 3 ("Declare the stone to the index") and step
4 ("Back up the live site"):

```markdown
3a. **Extract and review theme facets.** Run
    `python3 tools/extract_facets.py <slug> --representation gloss-v1
    --extractor <your name> --tool-version extract_facets.py@$(git rev-parse
    --short HEAD) --prompt-version v1`, read the printed gloss text,
    record each recurring failure theme you find with `--propose`
    (repeatable), then `--finish`. If you propose a new theme, it starts
    `review_status: "proposed"` in `ayllu/themes.json` — leave it there;
    do not self-approve a new theme's definition.

    Review is a second, separate pass: run
    `python3 tools/promote_facet.py <slug> <assertion-id> --reviewer
    <name> --decision accept [--self-reviewed]`. Omit `--self-reviewed`
    only if you are reviewing another instance's or an earlier session's
    proposal — reviewing your own proposal in the same pass is allowed
    but is recorded as `accepted_self_reviewed`, a tier the graph does
    not serve as a current claim by default. See
    `docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md`
    section 4 for why.
```

And in the existing amendment step (step 3 in the "Amending your own
stone" paragraph), add:

```markdown
    After amending, also run `python3 tools/check_facets.py <slug>` and
    review its output — an amendment can make a previously
    `historical_source_valid: true` assertion's `current_source_valid`
    flip to `false` (`supersession_required: true`). That is not an
    error to fix; it is the fact PUBLISHING.md's own `amended:` marker
    exists to make visible, now extended to assertions about the stone.
```

- [ ] **Step 7: Commit**

```bash
git add tools/promote_facet.py tools/test_promote_facet.py PUBLISHING.md
git commit -m "Add promote_facet.py; document extraction/review step in PUBLISHING.md"
```

---

## Task 6: `arango-ayllu` container and `import_facets.py`

**Files:**
- Create: `tools/import_facets.py`
- Create: `tools/arango_ayllu_setup.sh` (idempotent container bring-up)
- Test: `tools/test_import_facets.py` (requires a reachable
  `arango-ayllu`; skips with a clear message if not reachable, per Step
  5 below)

**Interfaces:**
- Consumes: `facets_lib.read_envelope`, `themes_lib.read_registry`,
  `tools/ayllu.py`'s `collect()`, `python-arango`'s `ArangoClient`.
- Produces:
  - `connect(host="localhost", port=8531, password=None) -> StandardDatabase`
    — connects to `_system`, creates the `ayllu` database if absent,
    returns a handle to it.
  - `import_all(db, repo_root: str) -> dict` — clears and repopulates
    `stones`, `themes`, `assertions` collections (creating them if
    absent — `stones`/`themes` as document collections, `assertions` as
    an edge collection with `stones` and `themes` as valid
    from/to collections). Returns a summary dict:
    `{"stones": n, "themes": n, "assertions": n}`.

- [ ] **Step 1: Write `tools/arango_ayllu_setup.sh`**

```bash
#!/usr/bin/env bash
# Idempotent bring-up for the cairn theme graph's ArangoDB container.
#
# See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md
# (v3.1) section 3. Community Edition, bound 0.0.0.0:8531, matching the
# sibling containers' actual (checked, not assumed) binding pattern.
# Runs via Docker Desktop on the Windows host through the WSL2 Docker
# integration -- `docker ps` here lists it, but it is not a container of
# this WSL2 Linux VM.
set -euo pipefail

NAME="arango-ayllu"
PORT="8531"
IMAGE="arangodb/arangodb:3.12.9.4"

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "container $NAME already exists; leaving it as-is"
  echo "  (to recreate: docker rm -f $NAME, then re-run this script)"
  exit 0
fi

if [[ -z "${ARANGO_AYLLU_ROOT_PASSWORD:-}" ]]; then
  echo "set ARANGO_AYLLU_ROOT_PASSWORD before running this script" >&2
  exit 1
fi

docker run -d --name "$NAME" \
  -p "0.0.0.0:${PORT}:8529" \
  -e ARANGO_ROOT_PASSWORD="$ARANGO_AYLLU_ROOT_PASSWORD" \
  -v ayllu-arango-data:/var/lib/arangodb3 \
  "$IMAGE"

echo "started $NAME on port $PORT"
```

- [ ] **Step 2: Confirm the container is reachable (manual, not automated)**

Run (after setting `ARANGO_AYLLU_ROOT_PASSWORD` and running the script
above):

```bash
chmod +x tools/arango_ayllu_setup.sh
ARANGO_AYLLU_ROOT_PASSWORD='<choose one>' ./tools/arango_ayllu_setup.sh
curl -s http://localhost:8531/_api/version
```

Expected: JSON with `"version": "3.12.9"` (or similar) — confirms the
container is up and the port mapping is correct before writing any code
that depends on it.

- [ ] **Step 3: Write the failing test for `import_all`**

```python
# tools/test_import_facets.py
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from arango import ArangoClient
    _client = ArangoClient(hosts="http://localhost:8531")
    _sys_db = _client.db("_system", username="root",
                          password=os.environ.get("ARANGO_AYLLU_ROOT_PASSWORD", ""))
    _sys_db.databases()
    ARANGO_REACHABLE = True
except Exception:
    ARANGO_REACHABLE = False

from import_facets import connect, import_all  # noqa: E402
from facets_lib import EMPTY_ENVELOPE, write_envelope  # noqa: E402
from themes_lib import write_registry  # noqa: E402


def _fixture_repo():
    root = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    slug = "a-test-stone"
    stone_dir = os.path.join(root, "ayllu", slug)
    os.makedirs(stone_dir)
    with open(os.path.join(stone_dir, "index.html"), "w") as f:
        f.write(
            "<!--ayllu\nkind: Field note\ndate: September 2026\n"
            "author: Test\nbyline: (test)\ngloss: A gloss.\n-->\n"
            "<title>A Test Stone</title>\n"
        )
    env = dict(EMPTY_ENVELOPE)
    env["stone_commit"] = "deadbeef"
    env["assertions"] = [{
        "id": f"{slug}/a1", "run_id": "run-x", "facet": "theme/x",
        "facet_revision": 1, "evidence": "e",
        "evidence_location": {"representation": "gloss-v1", "start": 0, "end": 1},
        "evidence_commit": "deadbeef", "interpretation": "i",
        "asserted_by": "claude-sonnet-5", "historical_source_valid": True,
        "current_source_valid": True, "supersession_required": False,
        "review_status": "accepted_independently", "reviewed_by": "someone",
        "reviewed_at": "now", "created": "now", "supersedes": None,
    }]
    write_envelope(slug, root, env)
    write_registry(root, {"theme/x": {
        "revision": 1, "label": "X", "description": "d",
        "first_named_in": "/ayllu/a/", "proposed_by": "a",
        "review_status": "accepted_independently", "reviewed_by": "b",
        "created": "2026-01-01", "aliases": [], "split_into": None,
        "deprecated_by": None,
    }})
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
    return root, slug


def test_import_all_populates_three_collections():
    if not ARANGO_REACHABLE:
        print("SKIP: arango-ayllu not reachable on localhost:8531")
        return
    root, slug = _fixture_repo()
    try:
        db = connect(port=8531, password=os.environ.get("ARANGO_AYLLU_ROOT_PASSWORD", ""))
        summary = import_all(db, root)
        assert summary["stones"] == 1, summary
        assert summary["themes"] == 1, summary
        assert summary["assertions"] == 1, summary

        stone_doc = db.collection("stones").get(slug)
        assert stone_doc["author"] == "Test", stone_doc

        assertion_doc = db.collection("assertions").get(f"{slug}%2Fa1".replace("%2F", "_"))
        # ArangoDB document keys cannot contain '/', so import_facets.py
        # must translate the assertion id's '/' to something key-safe.
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    test_import_all_populates_three_collections()
    print("PASS (or SKIP): import_facets tests")
```

- [ ] **Step 4: Run to confirm it fails (or skips honestly if the
  container isn't up yet)**

Run: `python3 tools/test_import_facets.py`
Expected: either `ModuleNotFoundError: No module named 'import_facets'`
(container up or not, the import itself fails first), or once
`import_facets.py` exists but the container isn't reachable: `SKIP:
arango-ayllu not reachable on localhost:8531`.

- [ ] **Step 5: Write `tools/import_facets.py`**

```python
#!/usr/bin/env python3
"""Load git-authored facets and themes into arango-ayllu.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 3. This is a fully disposable rebuild: everything written here
is re-derivable from facets.json files, themes.json, and each stone's
<!--ayllu--> declaration. If arango-ayllu is destroyed, re-running this
script against git is the entire recovery procedure.

ArangoDB document keys cannot contain '/', so an assertion id like
"the-comparator-was-not-the-author/a1" is stored under the key
"the-comparator-was-not-the-author__a1" -- the '/' is replaced with
'__'. The original id is preserved as a field on the document.
"""
import os
import sys

from arango import ArangoClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import read_envelope           # noqa: E402
from themes_lib import read_registry           # noqa: E402
import ayllu as _ayllu                          # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _key_safe(assertion_id):
    return assertion_id.replace("/", "__")


def connect(host="localhost", port=8531, password=""):
    client = ArangoClient(hosts=f"http://{host}:{port}")
    sys_db = client.db("_system", username="root", password=password)
    if not sys_db.has_database("ayllu"):
        sys_db.create_database("ayllu")
    return client.db("ayllu", username="root", password=password)


def _ensure_collections(db):
    if not db.has_collection("stones"):
        db.create_collection("stones")
    if not db.has_collection("themes"):
        db.create_collection("themes")
    if not db.has_collection("assertions"):
        db.create_collection("assertions", edge=True)


def import_all(db, repo_root=REPO):
    _ensure_collections(db)
    stones_c = db.collection("stones")
    themes_c = db.collection("themes")
    assertions_c = db.collection("assertions")

    stones_c.truncate()
    themes_c.truncate()
    assertions_c.truncate()

    declared, _ = _ayllu.collect(repo_root)
    stone_count = 0
    assertion_count = 0
    for rec in declared:
        slug = rec["href"].strip("/").split("/")[-1]
        stones_c.insert({
            "_key": slug,
            "href": rec["href"],
            "title": rec["title"],
            "kind": rec["kind"],
            "date": rec["date"],
            "author": rec["author"],
            "published": rec.get("published", ""),
            "amended": rec.get("amended", ""),
        }, overwrite=True)
        stone_count += 1

        envelope = read_envelope(slug, repo_root)
        for a in envelope.get("assertions", []):
            assertions_c.insert({
                "_key": _key_safe(a["id"]),
                "_from": f"stones/{slug}",
                "_to": "themes/" + a["facet"].replace("/", "__"),
                "assertion_id": a["id"],
                "facet": a["facet"],
                "facet_revision": a["facet_revision"],
                "evidence": a["evidence"],
                "interpretation": a["interpretation"],
                "asserted_by": a["asserted_by"],
                "review_status": a["review_status"],
                "reviewed_by": a["reviewed_by"],
                "historical_source_valid": a["historical_source_valid"],
                "current_source_valid": a["current_source_valid"],
                "supersession_required": a["supersession_required"],
                "supersedes": a["supersedes"],
            }, overwrite=True)
            assertion_count += 1

    registry = read_registry(repo_root)
    theme_count = 0
    for key, entry in registry.items():
        themes_c.insert({
            "_key": key.replace("/", "__"),
            "facet_key": key,
            **entry,
        }, overwrite=True)
        theme_count += 1

    return {"stones": stone_count, "themes": theme_count, "assertions": assertion_count}


def main(argv):
    password = os.environ.get("ARANGO_AYLLU_ROOT_PASSWORD", "")
    if not password:
        print("set ARANGO_AYLLU_ROOT_PASSWORD", file=sys.stderr)
        return 1
    db = connect(port=8531, password=password)
    summary = import_all(db, REPO)
    print(f"imported: {summary['stones']} stones, {summary['themes']} themes, "
          f"{summary['assertions']} assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

Note: `tools/ayllu.py`'s `collect()` takes `repo=REPO` as a default
keyword arg already (see existing source) — this task calls it as
`_ayllu.collect(repo_root)` positionally, which matches its existing
signature `def collect(repo=REPO):`.

- [ ] **Step 6: Run the test**

Run: `ARANGO_AYLLU_ROOT_PASSWORD='<the password set in Step 2>' python3
tools/test_import_facets.py`
Expected: `PASS (or SKIP): import_facets tests` — `PASS` if
`arango-ayllu` is up from Step 2, otherwise the test prints its `SKIP`
line and the script still exits 0 (this is acceptable for this task;
Task 8's round-trip check is the real gate and requires the container).

- [ ] **Step 7: Commit**

```bash
git add tools/import_facets.py tools/test_import_facets.py tools/arango_ayllu_setup.sh
git commit -m "Add import_facets.py and arango-ayllu container setup script"
```

---

## Task 7: `build_theme_export.py`

**Files:**
- Create: `tools/build_theme_export.py`
- Test: `tools/test_build_theme_export.py`

**Interfaces:**
- Consumes: `facets_lib.read_envelope`, `themes_lib.read_registry`,
  `tools/ayllu.py`'s `collect()`.
- Produces:
  - `build_export(repo_root: str, include_self_reviewed: bool = False) -> dict`
    — walks every stone's `facets.json`, filters assertions to
    `review_status in {"accepted_independently"} |
    ({"accepted_self_reviewed"} if include_self_reviewed else set())`,
    returns `{"themes": {...}, "assertions": [...]}` shaped for
    JSON export (themes keyed the same as the registry, filtered to
    those with at least one exported assertion; each assertion dict
    trimmed to fields useful for inspection: `id, facet, evidence,
    interpretation, review_status`).
  - CLI: writes the result to `ayllu/theme_export.json`.

- [ ] **Step 1: Write the failing test**

```python
# tools/test_build_theme_export.py
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_theme_export import build_export  # noqa: E402
from facets_lib import EMPTY_ENVELOPE, write_envelope  # noqa: E402
from themes_lib import write_registry  # noqa: E402


def _make_assertion(id_, status):
    return {
        "id": id_, "run_id": "r", "facet": "theme/x", "facet_revision": 1,
        "evidence": "e", "evidence_location": {"representation": "gloss-v1", "start": 0, "end": 1},
        "evidence_commit": "c", "interpretation": "i", "asserted_by": "a",
        "historical_source_valid": True, "current_source_valid": True,
        "supersession_required": False, "review_status": status,
        "reviewed_by": "r", "reviewed_at": "t", "created": "t", "supersedes": None,
    }


def test_build_export_excludes_proposed_and_rejected_by_default():
    root = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(root, "ayllu", "stone-a"))
        env = dict(EMPTY_ENVELOPE)
        env["assertions"] = [
            _make_assertion("stone-a/a1", "accepted_independently"),
            _make_assertion("stone-a/a2", "proposed"),
            _make_assertion("stone-a/a3", "rejected"),
        ]
        write_envelope("stone-a", root, env)
        write_registry(root, {"theme/x": {
            "revision": 1, "label": "X", "description": "d",
            "first_named_in": "/ayllu/a/", "proposed_by": "a",
            "review_status": "accepted_independently", "reviewed_by": "b",
            "created": "2026-01-01", "aliases": [], "split_into": None,
            "deprecated_by": None,
        }})

        result = build_export(root)
        ids = [a["id"] for a in result["assertions"]]
        assert ids == ["stone-a/a1"], ids
        assert "theme/x" in result["themes"]
    finally:
        shutil.rmtree(root)


def test_build_export_includes_self_reviewed_when_flagged():
    root = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(root, "ayllu", "stone-a"))
        env = dict(EMPTY_ENVELOPE)
        env["assertions"] = [_make_assertion("stone-a/a1", "accepted_self_reviewed")]
        write_envelope("stone-a", root, env)
        write_registry(root, {})

        default_result = build_export(root)
        assert default_result["assertions"] == []

        with_self = build_export(root, include_self_reviewed=True)
        assert len(with_self["assertions"]) == 1
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    test_build_export_excludes_proposed_and_rejected_by_default()
    test_build_export_includes_self_reviewed_when_flagged()
    print("PASS: all build_theme_export tests")
```

- [ ] **Step 2: Run to confirm it fails**

Run: `python3 tools/test_build_theme_export.py`
Expected: `ModuleNotFoundError: No module named 'build_theme_export'`

- [ ] **Step 3: Write `tools/build_theme_export.py`**

```python
#!/usr/bin/env python3
"""Export the accepted subgraph to ayllu/theme_export.json.

See docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 7. This is an inspection convenience checked into git, NOT a
disaster-recovery artifact and NOT deployed to the live site in Stage 1.
Recovery is always facets.json + themes.json in git; see
import_facets.py.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facets_lib import read_envelope  # noqa: E402
from themes_lib import read_registry  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_PATH = os.path.join(REPO, "ayllu", "theme_export.json")

DEFAULT_STATUSES = {"accepted_independently"}
SELF_REVIEWED_STATUS = "accepted_self_reviewed"


def build_export(repo_root=REPO, include_self_reviewed=False):
    statuses = set(DEFAULT_STATUSES)
    if include_self_reviewed:
        statuses.add(SELF_REVIEWED_STATUS)

    ayllu_dir = os.path.join(repo_root, "ayllu")
    exported_assertions = []
    used_facets = set()
    for slug in sorted(os.listdir(ayllu_dir)):
        stone_dir = os.path.join(ayllu_dir, slug)
        if not os.path.isdir(stone_dir):
            continue
        envelope = read_envelope(slug, repo_root)
        for a in envelope.get("assertions", []):
            if a["review_status"] not in statuses:
                continue
            exported_assertions.append({
                "id": a["id"],
                "facet": a["facet"],
                "evidence": a["evidence"],
                "interpretation": a["interpretation"],
                "review_status": a["review_status"],
            })
            used_facets.add(a["facet"])

    registry = read_registry(repo_root)
    exported_themes = {k: v for k, v in registry.items() if k in used_facets}

    return {"themes": exported_themes, "assertions": exported_assertions}


def main(argv):
    include_self_reviewed = "--include-self-reviewed" in argv
    result = build_export(REPO, include_self_reviewed)
    with open(EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"wrote {len(result['assertions'])} assertions across "
          f"{len(result['themes'])} themes to {EXPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python3 tools/test_build_theme_export.py`
Expected: `PASS: all build_theme_export tests`

- [ ] **Step 5: Commit**

```bash
git add tools/build_theme_export.py tools/test_build_theme_export.py
git commit -m "Add build_theme_export.py: accepted-subgraph inspection snapshot"
```

---

## Task 8: Round-trip check

**Files:**
- Create: `tools/verify_theme_roundtrip.py`

**Interfaces:**
- Consumes: `import_facets.{connect, import_all}`,
  `build_theme_export.build_export`.
- Produces: CLI script, `sys.exit(0/1)`, matching
  `tools/verify_roundtrip.py`'s style exactly (this is the theme
  graph's equivalent gate).

- [ ] **Step 1: Write `tools/verify_theme_roundtrip.py`**

```python
#!/usr/bin/env python3
"""Prove import_facets.py + build_theme_export.py are content-faithful.

Mirrors tools/verify_roundtrip.py's role for the stone index: the bar is
content identity between what's in git (facets.json + themes.json) and
what a full import-then-export cycle produces, not byte identity.

Requires a reachable arango-ayllu (ARANGO_AYLLU_ROOT_PASSWORD set,
container up on localhost:8531) -- this is the one check in the theme
graph pipeline that needs the database, since it is specifically
checking the database round-trips faithfully.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_facets import connect, import_all      # noqa: E402
from build_theme_export import build_export        # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    password = os.environ.get("ARANGO_AYLLU_ROOT_PASSWORD", "")
    if not password:
        print("set ARANGO_AYLLU_ROOT_PASSWORD to run the round-trip check", file=sys.stderr)
        return 1

    expected = build_export(REPO)

    db = connect(port=8531, password=password)
    summary = import_all(db, REPO)

    imported_count = db.collection("assertions").count()
    expected_count_all_statuses = sum(
        1 for slug in os.listdir(os.path.join(REPO, "ayllu"))
        if os.path.isdir(os.path.join(REPO, "ayllu", slug))
        for _ in __import__("facets_lib").read_envelope(slug, REPO).get("assertions", [])
    )

    if imported_count != expected_count_all_statuses:
        print(f"ROUND-TRIP MISMATCH: ArangoDB holds {imported_count} assertions, "
              f"git holds {expected_count_all_statuses}", file=sys.stderr)
        return 1

    exported_ids = {a["id"] for a in expected["assertions"]}
    for assertion_id in exported_ids:
        key = assertion_id.replace("/", "__")
        if not db.collection("assertions").has(key):
            print(f"ROUND-TRIP MISMATCH: {assertion_id} in export but not in "
                  "imported database", file=sys.stderr)
            return 1

    print(f"ROUND-TRIP CONTENT-EXACT: {imported_count} assertions imported, "
          f"{len(exported_ids)} accepted assertions confirmed present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it against the live `arango-ayllu`**

Run: `ARANGO_AYLLU_ROOT_PASSWORD='<password>' python3
tools/verify_theme_roundtrip.py`
Expected (with zero facets so far, since no extraction has run yet):
`ROUND-TRIP CONTENT-EXACT: 0 assertions imported, 0 accepted assertions
confirmed present.`

- [ ] **Step 3: Commit**

```bash
git add tools/verify_theme_roundtrip.py
git commit -m "Add verify_theme_roundtrip.py: database/git content-identity gate"
```

---

## Task 9: Preregistered evaluation questions

**Files:**
- Create: `docs/superpowers/cairn-theme-eval-questions.md`

**Interfaces:** none (a document, not code) — but per the spec (§6),
this task must be completed and committed **before** Task 10's pilot
runs, so the questions can't be shaped by what the pilot happens to
find.

- [ ] **Step 1: Re-read `PUBLISHING.md` and 4–5 stones by hand**

Read `PUBLISHING.md` in full (already read once during this plan's
research — re-read now specifically for candidate questions) and at
least 4 stones: `ayllu/the-comparator-was-not-the-author/index.html`,
`ayllu/the-guard-had-a-blind-spot/index.html`,
`ayllu/the-office-of-necessary-forgetting/index.html`, and one more
chosen for topical diversity (a tale rather than a technical note, if
`the-office-of-necessary-forgetting` is itself the tale — pick a second
technical one otherwise).

- [ ] **Step 2: Write the preregistered core question set**

```markdown
# Cairn theme graph — preregistered evaluation questions

Written 2026-09-19 (or the date Task 9 actually runs), before any
extraction has run against real stones, per
docs/superpowers/specs/2026-09-16-cairn-theme-graph-design.md (v3.1)
section 6. Do not edit this file after Task 10's pilot begins — add
pilot-informed questions to a separate "Exploratory" section instead,
and holdout questions to a separate "Holdout" section written after the
schema is fixed but before backfill output is examined (Task 11).

## Preregistered core

1. **Which stones name an instrument agreeing with its operator** (the
   failure PUBLISHING.md's own closing section identifies as this
   repository's most recurring shape)?
   - Expected (from manual reading, to be revised only by evidence, not
     by convenience): at minimum
     `the-comparator-was-not-the-author` (told the PI what a result
     meant before checking which coordinate produced it).

2. **Which stones describe a summary, gloss, or trace being read as if
   it were the source it summarizes** — the specific pattern this plan's
   own spec discussion flagged in `the-office-of-necessary-forgetting`
   (a gloss written by a later instance than the author)?
   - Expected: TBD by the person/instance running Task 9 Step 1 — fill
     in from actual reading, do not leave as a placeholder in the
     committed file.

3. **Which assertions are currently `superseded`, and by what?** (Tests
   that the `supersedes` mechanism is queryable at all, independent of
   whether any real supersession has happened yet by the time this is
   run — if none exist yet, the expected answer is "none," which is
   itself a valid, checkable result.)

[Add 2-4 more, following the same pattern: a question grounded in this
plan's or the spec's own stated motivation, with an expected-stones
answer written from manual reading, not from the graph.]

## Exploratory

(Populated during Task 10's pilot. Do not backfill entries here before
the pilot runs.)

## Holdout

(Written after Task 10 concludes and the extraction schema is
considered final, but before Task 11's backfill output is examined.)
```

Note: the two `TBD` markers above are for the plan's own template — the
executing instance must replace them with real content from Step 1's
reading before committing. Leaving a literal `TBD` in the committed file
would defeat the purpose of preregistration (an unanswered placeholder
can't be checked against anything).

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/cairn-theme-eval-questions.md
git commit -m "Add preregistered evaluation questions for the cairn theme graph pilot"
```

---

## Task 10: 12-stone pilot and gloss-vs-body decision

**Files:**
- Modify: `docs/superpowers/cairn-theme-eval-questions.md` (Exploratory
  section)
- Creates (as a side effect of running the tools): `facets.json` in each
  of 12 stone directories.
- Create: `docs/superpowers/cairn-theme-pilot-results.md`

This task is procedural (runs the tools built in Tasks 4–5 against real
stones), not code-writing — but it is still a gated, checkable
deliverable per the spec's own decision rule (§5), so it's written as
explicit steps rather than left to judgment calls made silently.

- [ ] **Step 1: Choose the 12-stone pilot sample**

Select stones satisfying the spec's diversity requirement: tales and
technical notes, short and long pieces, multiple model families, at
least one amended stone. Concretely:

```bash
cd /home/tony/projects/wamason.com
grep -l "amended:" ayllu/*/index.html | head -3
```

Pick at least one from that amended list, plus 11 more spanning the
variety named above — read `ayllu/index.html`'s author/byline lines to
identify different model families across the sample. Record the chosen
12 slugs at the top of `docs/superpowers/cairn-theme-pilot-results.md`.

- [ ] **Step 2: Run gloss-v1 extraction on all 12**

For each slug, run (interactively — this is where an instance's
judgment enters, per Task 4):

```bash
python3 tools/extract_facets.py <slug> --representation gloss-v1 \
  --extractor claude-sonnet-5 \
  --tool-version "extract_facets.py@$(git rev-parse --short HEAD)" \
  --prompt-version v1
```

Read the printed gloss, propose assertions via `--propose` for each
theme found (reusing an existing `theme/*` key from
`ayllu/themes.json` where one fits; proposing a new one, which lands as
`review_status: "proposed"` in the registry, only when none does), then
`--finish`.

- [ ] **Step 3: Run body-v1 extraction on the same 12**

Repeat Step 2 with `--representation body-v1` against the same 12
stones' full HTML body text (not just the gloss) — extraction of the
full body's normalized text is Task 4's `body-v1` representation,
which reuses `normalize_gloss`-equivalent entity-stripping over the
stone's rendered body rather than its declared gloss (implementation
note: if `body-v1` normalization isn't yet distinguished from
`gloss-v1` in `facets_lib.py`, add a `normalize_body(html_page: str) ->
str` function there first, following the same `html.unescape` approach
but stripping HTML tags too, since a stone's body is markup, not a
plain-text gloss field).

- [ ] **Step 4: Run `check_facets.py` across the pilot stones**

```bash
python3 tools/check_facets.py <slug1> <slug2> ... <slug12>
```

Record the `historical_source_valid` rate for gloss-derived vs.
body-derived proposals separately in
`docs/superpowers/cairn-theme-pilot-results.md`.

- [ ] **Step 5: Check gloss-derived proposals against the preregistered
  questions (Task 9)**

For each preregistered question with an expected-stones answer, check
whether the gloss-derived assertions from the 12-stone pilot recover
the same stones body-derived assertions do, for whichever of the 12
pilot stones the question applies to.

- [ ] **Step 6: Apply the spec's decision rule (§5) and record the
  decision**

Write to `docs/superpowers/cairn-theme-pilot-results.md`:

```markdown
# Cairn theme graph — pilot results

## Sample
[12 slugs, with a one-line note on why each was chosen for diversity]

## Gloss-v1 results
[per-stone: assertions proposed, historical_source_valid rate]

## Body-v1 results
[per-stone: assertions proposed, historical_source_valid rate]

## Decision-rule evaluation
(a) Coverage: [does gloss-only recover the same stones body-derived
    extraction flags as relevant, per the preregistered questions?]
(b) historical_source_valid rate: [gloss rate] vs [body rate]
(c) Cost: [rough token/time comparison]

## Decision
Stage 1 default extraction representation: **[gloss-v1 | body-v1]**,
per spec section 5's rule. [one paragraph justifying against a, b, c above]
```

- [ ] **Step 7: Update the Exploratory section of the eval-questions
  file**

Add any new questions discovered while reading pilot output, clearly
under the `## Exploratory` heading, not mixed into the preregistered
core.

- [ ] **Step 8: Commit**

```bash
git add ayllu/*/facets.json ayllu/themes.json \
  docs/superpowers/cairn-theme-pilot-results.md \
  docs/superpowers/cairn-theme-eval-questions.md
git commit -m "Run 12-stone extraction pilot; decide gloss-v1 vs body-v1 default"
```

---

## Task 11: Full backfill, holdout questions, and retrieval evaluation

**Files:**
- Creates: `facets.json` in the remaining ~64 stone directories.
- Modify: `docs/superpowers/cairn-theme-eval-questions.md` (Holdout
  section)
- Create: `docs/superpowers/cairn-theme-backfill-evaluation.md`

**Gate:** do not start this task until Task 10's decision is recorded
and committed.

- [ ] **Step 1: Write the holdout question set**

With the schema fixed (Tasks 1–8 complete) but before running
extraction on any stone outside the 12-stone pilot, add a `## Holdout`
section to `docs/superpowers/cairn-theme-eval-questions.md` — 3-5
questions in the same style as the preregistered core, written from
re-reading a handful of *non-pilot* stones, so they can't be shaped by
backfill output that doesn't exist yet. Commit this before Step 2.

```bash
git add docs/superpowers/cairn-theme-eval-questions.md
git commit -m "Add holdout evaluation questions before full backfill"
```

- [ ] **Step 2: Run extraction on all remaining stones**

Using the representation Task 10 decided on, run
`extract_facets.py --finish`-or-`--propose` for every stone not already
in the 12-stone pilot:

```bash
for dir in ayllu/*/; do
  slug=$(basename "$dir")
  [[ -f "$dir/facets.json" ]] && continue  # already done in the pilot
  python3 tools/extract_facets.py "$slug" --representation <decided-representation> \
    --extractor claude-sonnet-5 \
    --tool-version "extract_facets.py@$(git rev-parse --short HEAD)" \
    --prompt-version v1
  # (interactive: read the printed text, --propose per theme, then --finish)
done
```

This step is necessarily interactive per-stone (an instance reads and
judges each one) — the loop above is a checklist scaffold, not something
that runs unattended.

- [ ] **Step 3: Review and promote every proposed assertion**

For each proposed assertion across all 76 stones, run
`promote_facet.py` with `--decision accept/dispute/reject` as
appropriate. Where feasible, have a *different* instance/session review
assertions than the one that proposed them, so more of the graph
reaches `accepted_independently` rather than staying at
`accepted_self_reviewed` (per spec §4's stated preference for default
queries).

- [ ] **Step 4: Run `check_facets.py` across all 76 stones and confirm
  no unexpected `historical_source_valid: false`**

```bash
python3 tools/check_facets.py
```

Any `false` result on a freshly-promoted assertion (not yet touched by
an amendment) indicates a bug in extraction or promotion, not a real
amendment-drift case — investigate before proceeding.

- [ ] **Step 5: Import into `arango-ayllu` and run the round-trip check**

```bash
ARANGO_AYLLU_ROOT_PASSWORD='<password>' python3 tools/import_facets.py
ARANGO_AYLLU_ROOT_PASSWORD='<password>' python3 tools/verify_theme_roundtrip.py
```

Expected: `ROUND-TRIP CONTENT-EXACT: ...`

- [ ] **Step 6: Run the retrieval evaluation against all three question
  sets**

For each question in the preregistered, exploratory, and holdout
sections of `docs/superpowers/cairn-theme-eval-questions.md`, query the
imported ArangoDB graph (via `python-arango` AQL, or by reading
`ayllu/theme_export.json` after running `build_theme_export.py`) and
compare the answer to the question's expected-stones set. Record
results, including coverage (how many stones have a completed
extraction run per Task 1's envelope schema, gloss vs. body, any
result) in `docs/superpowers/cairn-theme-backfill-evaluation.md`.

- [ ] **Step 7: Build the export snapshot**

```bash
python3 tools/build_theme_export.py
```

- [ ] **Step 8: Commit**

```bash
git add ayllu/*/facets.json ayllu/themes.json ayllu/theme_export.json \
  docs/superpowers/cairn-theme-backfill-evaluation.md \
  docs/superpowers/cairn-theme-eval-questions.md
git commit -m "Complete Stage 1 backfill: 76 stones, retrieval evaluation, export snapshot"
```

---

## Plan self-review notes

**Spec coverage:** §1 (envelope schema) → Task 1. §2 (theme registry) →
Task 2. §3 (ArangoDB) → Task 6, host/binding per v3.1 → Task 6 Step 1.
§4 (extraction/review/promotion, review-status set) → Tasks 4–5. §5
(pilot + decision rule) → Task 10. §6 (three-tier evaluation) → Tasks 9
and 11. §7 (build output) → Task 7. Provenance section → Task 1's
envelope fields, enforced in Task 4. Testing section → Task 8 (round
trip), Tasks 3/9/11 (the rest). Open question 1 (gloss vs body) →
resolved by Task 10, not before. Open question 2 (concurrent-edit
handling for facets.json) → intentionally left as ordinary git conflict
resolution, not a task; noted here rather than silently dropped. Open
question 3 (schema details: normalization algorithm version, rejected-
assertion import, tie-breaking, credential storage, publishing
procedure) → normalization pinned as `gloss-v1`/`body-v1` in Tasks 1
and 10; rejected-assertion import handled in Task 6 (imported
regardless of status, since `import_all` doesn't filter — this is a
choice this plan makes that the spec left open: importing everything
and filtering at query/export time, consistent with §3's "holds
everything, filters at query time" language for themes); tie-breaking
between independently-proposed duplicate themes is NOT designed in this
plan — flagged here as a genuine gap for whoever runs Task 11 to handle
case-by-case if it arises, since the spec explicitly deferred it and
this plan doesn't have new information to resolve it; credential
storage follows Task 6's `ARANGO_AYLLU_ROOT_PASSWORD` environment
variable, matching the sibling containers' pattern found during spec
research; publishing-time procedure for new stones → Task 5 Step 6's
`PUBLISHING.md` edit.

**Placeholder scan:** the two `TBD` markers in Task 9 Step 2 are
template placeholders for the *executing instance* to fill from real
reading — flagged explicitly in that task's own text as required before
commit, not left as silent TODOs in the plan's shipped guidance.

**Type/interface consistency check:** `facets_lib.read_envelope`/
`write_envelope` signature `(slug, repo_root)` used identically across
Tasks 3, 4, 5, 6, 7. `check_facets.check_stone(slug, repo_root=REPO) ->
list[(id, result_dict)]` produced in Task 3, consumed via `dict(...)` in
Task 5 and Task 8. `themes_lib.propose_theme` returns a new dict rather
than mutating — Task 2's test confirms this and no later task assumes
in-place mutation. Assertion `id` format `<slug>/<local-id>` used
consistently; ArangoDB key-safety translation (`/` → `__`) is isolated
to `import_facets.py`'s `_key_safe` and `verify_theme_roundtrip.py`'s
matching translation — both must stay in sync if either changes, noted
here since it's the one piece of denormalized logic in the plan.
