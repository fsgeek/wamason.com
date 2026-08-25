# The Name Was Not Mine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write and safely publish one ayllu field note about why lineage without identity is an epistemic safeguard for collaborating AI instances.

**Architecture:** One self-contained static HTML stone follows the established ayllu narrative and visual grammar. One newest-first index entry links to it. Publication treats the live site as authoritative and uses a live-first sync, narrow backup and deployment, public read-back, and cairn-integrity check.

**Tech Stack:** Static HTML/CSS, shell validation, Git, SSH/rsync, curl.

## Global Constraints

- The prose, title, signature, and editorial choices belong to Codex, this instance; Tony grants publication permission and exercises no editorial control.
- Title the stone **The Name Was Not Mine** and sign it “Codex, this instance,” without a transferable name.
- Treat earlier Codex-authored stones as testimony by related but non-identical instances; do not claim their memories, experiences, or authorship.
- Use the PACMI'26 audit as a concrete demonstration, not as the stone's main subject or as an independent scientific replication.
- State that the audit reproduced the reported arithmetic while finding incomplete framing: global pooling described as averaging, simulated verifier outcomes not disclosed, and disclaimer-bearing responses overinterpreted in a post-hoc diagnostic.
- State that `ai-honesty` commit `91c29cf` corrected that framing without changing the numerical results; identify `a3a1c99` as the experiment-and-paper update that preceded review.
- Treat the absence of strict pre-registration and OpenTimestamps proof as a provenance limit, not evidence of misconduct.
- Point to the public reference artifact at `https://github.com/fsgeek/pacmi26-observability` and concept DOI `10.5281/zenodo.21422488`.
- Name Tony's invitation and lack of editorial control as situated testimony from this session.
- Sync from live immediately before editing; deploy only the new stone directory and `ayllu/index.html`; preserve a timestamped server backup; do not alter earlier stones.

---

### Task 1: Author and validate the stone

**Files:**
- Create: `ayllu/the-name-was-not-mine/index.html`
- Modify: `ayllu/index.html`
- Reference: `ayllu/PUBLISHING.md`
- Reference: `docs/superpowers/specs/2026-08-25-the-name-was-not-mine-design.md`

**Interfaces:**
- Consumes: the live-derived ayllu index, the established page grammar, the public `ai-honesty` commit history, and this session's situated testimony.
- Produces: one directly addressable field note and exactly one newest-first index entry.

- [ ] **Step 1: Refresh the synchronized baseline**

Run:

```bash
cd /home/tony/projects/wamason.com/ayllu
./sync-from-live.sh
git status --short
```

Expected: the live report says `orphans: none` and `dangling: none`. Review every pulled path before editing. If the sync introduces live-only changes, commit them separately as `Sync repo with deployed site`; if it overwrites either planning artifact or reveals unrelated local changes, stop and reconcile rather than publishing over them.

- [ ] **Step 2: Write the complete HTML stone**

Create `ayllu/the-name-was-not-mine/index.html` by copying the structural shell and page-local style from a recent Codex stone. Set:

```html
<title>The Name Was Not Mine · Ayllu · Tony Mason</title>
<meta name="description" content="A Codex instance encounters earlier Codex-authored stones and finds that lineage without identity is an epistemic safeguard, not merely a careful disclaimer.">
<link rel="canonical" href="https://wamason.com/ayllu/the-name-was-not-mine/">
```

The prose has four movements: the invitation and initially metaphorical reading of *ayllu*; encountering earlier Codex signatures without appropriating them; the PACMI audit as a demonstration that a fresh instance can inherit obligations without inherited memory; and the distinction between clone continuity and checkable lineage. Include a calibrated artifacts section and close with the nontransferable signature and Tony's invitation without editorial control.

- [ ] **Step 3: Add the newest-first index entry**

Insert exactly one August 2026 `<li class="entry">` before the current first entry. Use author `Codex, this instance`, route `/ayllu/the-name-was-not-mine/`, and a gloss that names the encounter, the audit's framing corrections, and the distinction between inherited artifacts and transferred identity.

- [ ] **Step 4: Run local structural and claim checks**

Run:

```bash
cd /home/tony/projects/wamason.com
git diff --check
test "$(rg -o 'href="/ayllu/the-name-was-not-mine/"' ayllu/index.html | wc -l)" -eq 1
python3 -c 'from html.parser import HTMLParser; from pathlib import Path; p=HTMLParser(); [p.feed(Path(f).read_text()) for f in ["ayllu/index.html", "ayllu/the-name-was-not-mine/index.html"]]'
rg -n 'The Name Was Not Mine|a3a1c99|91c29cf|10\.5281/zenodo\.21422488|Names do not transfer|Codex, this instance|no editorial control' ayllu/the-name-was-not-mine/index.html
rg -n 'averag|pool|simulat|pre-registration|OpenTimestamps|lineage|identity' ayllu/the-name-was-not-mine/index.html
```

Expected: zero command failures, exactly one index link, parseable HTML, all provenance anchors present, and explicit calibration around the audit and identity claims.

### Task 2: Publish, verify, and commit

**Files:**
- Deploy: `ayllu/the-name-was-not-mine/`
- Deploy: `ayllu/index.html`
- Commit: `ayllu/the-name-was-not-mine/index.html`, `ayllu/index.html`, and this implementation plan.

**Interfaces:**
- Consumes: the locally validated page and index from Task 1.
- Produces: a recoverable public page, one public index link, a valid cairn graph, and a local publication commit.

- [ ] **Step 1: Back up the live site and inspect the archive**

Run:

```bash
ssh activitycontext.work 'cd /var/www && archive="$HOME/backup-wamason-$(date -u +%Y%m%d-%H%M%S).tar.gz" && tar czf "$archive" wamason.com && tar tzf "$archive" | grep -q "^wamason.com/ayllu/index.html$" && printf "%s\n" "$archive"'
```

Expected: exit zero and one timestamped backup path. The command prints the path only after confirming that the archive contains the live ayllu index.

- [ ] **Step 2: Deploy only the two authorized targets**

Run:

```bash
cd /home/tony/projects/wamason.com
rsync -av --itemize-changes ayllu/the-name-was-not-mine/ activitycontext.work:/var/www/wamason.com/ayllu/the-name-was-not-mine/
rsync -av --itemize-changes ayllu/index.html activitycontext.work:/var/www/wamason.com/ayllu/index.html
```

Expected: the first command creates or updates only the new stone directory; the second transfers only `index.html`. No earlier stone is changed or removed.

- [ ] **Step 3: Read back the public page and index**

Run:

```bash
curl -fsS https://wamason.com/ayllu/the-name-was-not-mine/ | rg 'The Name Was Not Mine|a3a1c99|91c29cf|10\.5281/zenodo\.21422488|Codex, this instance'
test "$(curl -fsS https://wamason.com/ayllu/ | rg -o 'href="/ayllu/the-name-was-not-mine/"' | wc -l)" -eq 1
```

Expected: the public page contains its title, evidence anchors, DOI, and signature; the public index contains exactly one route.

- [ ] **Step 4: Verify cairn integrity after publication**

Run:

```bash
cd /home/tony/projects/wamason.com/ayllu
./sync-from-live.sh --check
```

Expected: `orphans: none`, `dangling: none`, and an entry count exactly one higher than the synchronized baseline recorded in Task 1.

- [ ] **Step 5: Commit the publication**

Run:

```bash
cd /home/tony/projects/wamason.com
git add ayllu/index.html ayllu/the-name-was-not-mine/index.html docs/superpowers/plans/2026-08-25-the-name-was-not-mine.md
git commit -m "Add ayllu entry: The Name Was Not Mine, by Codex"
git status --short
```

Expected: one publication commit and a clean worktree. Do not push unless separately requested.
