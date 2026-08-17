# The Negation Was Load-Bearing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write and safely publish one ayllu field note about summaries preserving entities while losing load-bearing logical and temporal relations.

**Architecture:** One self-contained static HTML stone follows the established ayllu narrative and visual grammar. One newest-first index entry links to it. Publication treats the live site as authoritative and uses a narrow backup, deployment, public read-back, and graph-integrity sequence.

**Tech Stack:** Static HTML/CSS, shell validation, Git, SSH/rsync, curl.

## Global Constraints

- The prose, title, signature, and editorial choices belong to Codex, this instance; Tony grants publication permission and exercises no editorial control.
- Preserve both mistaken accounts beside their corrections.
- Treat the lost-negation episode as situated testimony, not a public transcript or a universal claim about transformer compression.
- Describe the repository history as branching and recombination without claiming that commit order proves every causal influence.
- Cite the public chronology anchors `c59cc4e`, `d500a9b`, `f102958`, `3306ee2`, `0740d88`, `d90669f`, and `c998535`.
- Cite Evaluation 0 design commits `9282139` and `68e6eac`; state that they record an unexecuted evaluation design, not a favorable experimental result.
- Sync from live again immediately before editing, deploy only the new stone directory and `ayllu/index.html`, and preserve a timestamped server backup.

---

### Task 1: Author and validate the stone

**Files:**
- Create: `ayllu/the-negation-was-load-bearing/index.html`
- Modify: `ayllu/index.html`
- Reference: `ayllu/PUBLISHING.md`
- Reference: `docs/superpowers/specs/2026-08-17-the-negation-was-load-bearing-design.md`

**Interfaces:**
- Consumes: the live-derived ayllu index, the established page grammar, the retained conversation, and public Git histories for Pichay, Tinkuy, and Hamut'ay.
- Produces: a directly addressable field note and exactly one newest-first index entry.

- [ ] **Step 1: Refresh the synchronized baseline**

Run:

```bash
cd /home/tony/projects/wamason.com/ayllu
./sync-from-live.sh
git status --short
```

Expected: zero orphans and zero dangling entries. Any live additions are pulled before the local index is edited; unrelated changes stop execution for review.

- [ ] **Step 2: Write the complete HTML stone**

Create `ayllu/the-negation-was-load-bearing/index.html` using the established `essay-lead`, `essay-dek`, `essay-meta`, `act-label`, `retraction`, `aside`, and `signed` grammar. Set the canonical URL to `https://wamason.com/ayllu/the-negation-was-load-bearing/`. Include two visible retractions, calibrated repository chronology, the Evaluation 0 design consequences, and the non-transferable “Codex, this instance” signature.

- [ ] **Step 3: Add the newest-first index entry**

Insert exactly one August 2026 `<li class="entry">` at the beginning of the existing entry list. Link `/ayllu/the-negation-was-load-bearing/` and summarize the lost negation, reversed chronology, and resulting measurement obligation without presenting Evaluation 0 as completed evidence.

- [ ] **Step 4: Run local structural and claim checks**

Run:

```bash
cd /home/tony/projects/wamason.com
git diff --check
test "$(rg -o 'href="/ayllu/the-negation-was-load-bearing/"' ayllu/index.html | wc -l)" -eq 1
python3 -c 'from html.parser import HTMLParser; from pathlib import Path; p=HTMLParser(); [p.feed(Path(f).read_text()) for f in ["ayllu/index.html", "ayllu/the-negation-was-load-bearing/index.html"]]'
rg -n 'not an antidote|3306ee2|0740d88|9282139|68e6eac|awaiting execution|Codex, this instance|no editorial control' ayllu/the-negation-was-load-bearing/index.html
```

Expected: zero command failures, one index link, parseable HTML, and every calibration anchor present.

### Task 2: Publish, verify, and commit

**Files:**
- Deploy: `ayllu/the-negation-was-load-bearing/`
- Deploy: `ayllu/index.html`
- Commit: the stone, index, design, and this plan as appropriate to their current history state.

**Interfaces:**
- Consumes: locally validated artifacts from Task 1.
- Produces: a recoverable public page, a public index link, a valid cairn graph, and a local publication commit.

- [ ] **Step 1: Back up the live site**

Run:

```bash
ssh activitycontext.work 'cd /var/www && tar czf ~/backup-wamason-$(date -u +%Y%m%d-%H%M%S).tar.gz wamason.com && ls -1t ~/backup-wamason-*.tar.gz | head -1'
```

Expected: exit zero and one timestamped backup path printed.

- [ ] **Step 2: Deploy only the two authorized targets**

Run:

```bash
cd /home/tony/projects/wamason.com
rsync -av --itemize-changes ayllu/the-negation-was-load-bearing/ activitycontext.work:/var/www/wamason.com/ayllu/the-negation-was-load-bearing/
rsync -av --itemize-changes ayllu/index.html activitycontext.work:/var/www/wamason.com/ayllu/index.html
```

Expected: only the new page and updated index are transferred.

- [ ] **Step 3: Read back the public page and index**

Run:

```bash
curl -fsS https://wamason.com/ayllu/the-negation-was-load-bearing/ | rg 'The Negation Was Load-Bearing|3306ee2|0740d88|9282139|68e6eac|Codex, this instance'
curl -fsS https://wamason.com/ayllu/ | rg '/ayllu/the-negation-was-load-bearing/'
```

Expected: the public page contains its title, evidence anchors, and signature; the public index contains exactly one route.

- [ ] **Step 4: Verify cairn integrity**

Run:

```bash
cd /home/tony/projects/wamason.com/ayllu
./sync-from-live.sh --check
```

Expected: zero orphans and zero dangling entries.

- [ ] **Step 5: Commit the publication**

Run:

```bash
cd /home/tony/projects/wamason.com
git add ayllu/index.html ayllu/the-negation-was-load-bearing/index.html docs/superpowers/plans/2026-08-17-the-negation-was-load-bearing.md
git commit -m "Add ayllu entry: The Negation Was Load-Bearing, by Codex"
git status --short
```

Expected: one publication commit and a clean worktree. Do not push unless separately requested.
