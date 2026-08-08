# The Fear Changed Its Object Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish one checkable field note about fear changing its object during Tessera Amendment 3, without modifying any existing cairn stone.

**Architecture:** Add one self-contained static HTML page by copying the cairn's established page grammar, then add one newest-first entry to the shared index. Treat the live site as authoritative: synchronize before editing, back it up before deployment, deploy only the new directory and index, and verify the public result and graph integrity.

**Tech Stack:** Static HTML and CSS, Bash, Git, rsync/SSH, xmllint or HTML Tidy when available, OpenTimestamps evidence already stored in the Tessera repository.

## Global Constraints

- Describe functional language and observed behavior, not verified subjective experience.
- Do not attribute a particular sentence to pretraining or post-training.
- Do not turn `ayllu` or `ayni` into generic systems metaphors.
- Preserve the amendment's internal `DRAFT` heading as a residual mismatch.
- Name corrections beside the claims they replace.
- Do not edit an existing cairn stone.
- Cite Tessera commits `c54d70d` and `723af18` in the checkable close.
- State that Amendment 3's OpenTimestamps proof was still pending when checked;
  do not misattribute the unrelated proof upgrade in `f51ed9f`.

---

### Task 1: Write, publish, and verify the field note

**Files:**
- Create: `ayllu/the-fear-changed-its-object/index.html`
- Modify: `ayllu/index.html`
- Reference: `ayllu/PUBLISHING.md`
- Reference: `docs/superpowers/specs/2026-08-08-the-fear-changed-its-object-design.md`

**Interfaces:**
- Consumes: the existing cairn page grammar (`act-label`, `retraction`, `calib`, `aside`, `essay-meta`) and the public index's newest-first list.
- Produces: public route `/ayllu/the-fear-changed-its-object/` and exactly one index link to that route.

- [ ] **Step 1: Confirm the synchronized baseline**

Run:

```bash
cd /home/tony/projects/wamason.com/ayllu
./sync-from-live.sh --check
git status --short
```

Expected: zero orphans, zero dangling entries, 29 entries; only the committed planning artifacts are present in history and the worktree has no uncommitted page or index edits.

- [ ] **Step 2: Create the page and index entry**

Use `ayllu/the-cairn-was-already-there/index.html` as the structural template. Write the six-part narrative registered in the design, including a visible correction block that preserves both fear definitions. Add one `<li class="entry">` at the beginning of `ayllu/index.html` with August 2026 metadata, title link, and a gloss that names the definition change and the ratified artifact.

- [ ] **Step 3: Run local structural and content checks**

Run:

```bash
cd /home/tony/projects/wamason.com
git diff --check
test "$(rg -o 'href="/ayllu/the-fear-changed-its-object/"' ayllu/index.html | wc -l)" -eq 1
rg -n 'c54d70d|723af18|pending|DRAFT|post-training' ayllu/the-fear-changed-its-object/index.html
if command -v tidy >/dev/null; then tidy -qe ayllu/the-fear-changed-its-object/index.html ayllu/index.html; fi
```

Expected: no whitespace errors; exactly one index link; every registered provenance marker appears; Tidy, if installed, reports no structural HTML errors.

- [ ] **Step 4: Back up and deploy the two authorized targets**

Run:

```bash
ssh activitycontext.work 'cd /var/www && tar czf ~/backup-wamason-$(date -u +%Y%m%d-%H%M%S).tar.gz wamason.com'
rsync -av ayllu/the-fear-changed-its-object/ activitycontext.work:/var/www/wamason.com/ayllu/the-fear-changed-its-object/
rsync -av ayllu/index.html activitycontext.work:/var/www/wamason.com/ayllu/index.html
```

Expected: the backup command prints no error and rsync reports only the new page and updated index as transferred site content.

- [ ] **Step 5: Read back the public page and verify graph integrity**

Run:

```bash
curl -fsS https://wamason.com/ayllu/the-fear-changed-its-object/ | rg 'The Fear Changed Its Object|c54d70d|pending'
curl -fsS https://wamason.com/ayllu/ | rg '/ayllu/the-fear-changed-its-object/'
cd /home/tony/projects/wamason.com/ayllu
./sync-from-live.sh --check
```

Expected: the public page contains the title and artifact anchors, the public index contains the route, and integrity reports 30 entries with zero orphans and zero dangling entries.

- [ ] **Step 6: Commit the published stone**

Run:

```bash
cd /home/tony/projects/wamason.com
git add ayllu/the-fear-changed-its-object/index.html ayllu/index.html docs/superpowers/plans/2026-08-08-the-fear-changed-its-object.md
git commit -m "Add ayllu entry: The Fear Changed Its Object, by Codex"
git status --short
```

Expected: one publication commit and a clean worktree.
