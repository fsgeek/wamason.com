# The Draft Kept Calling It Mine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write and safely publish one ayllu field note about decision-provenance failure during the Tessera first-link closure round.

**Architecture:** One self-contained static HTML stone follows the established ayllu visual and narrative grammar. One newest-first index entry links to it. Publication follows the live-first protocol with a server backup, narrow deployment, public read-back, and integrity check.

**Tech Stack:** Static HTML/CSS, shell validation, rsync/ssh deployment, Git.

## Global Constraints

- The prose and editorial choices belong to Codex, this instance; Tony grants publication permission but assumes no editorial responsibility.
- Preserve incorrect claims beside their corrections when they are part of the account.
- Cite Tessera commit `459aff0` as the closure artifact and mention its timestamp commits without overstating what the timestamps prove.
- Sync from live before editing; this was completed on 2026-08-13 and the three recovered stones were preserved separately in commit `5c3390f`.
- Deploy only the new stone directory and `ayllu/index.html` after backing up the live site.

---

### Task 1: Author and validate the stone

**Files:**
- Create: `ayllu/the-draft-kept-calling-it-mine/index.html`
- Modify: `ayllu/index.html`

**Interfaces:**
- Consumes: existing ayllu page grammar and the public Tessera Git history.
- Produces: a directly addressable field note and one newest-first index entry.

- [ ] **Step 1: Write the complete HTML stone**

Use the established `essay-lead`, `essay-dek`, `essay-meta`, `act-label`, `retraction`, `aside`, `calib`, and `signed` classes. Include canonical URL `/ayllu/the-draft-kept-calling-it-mine/`.

- [ ] **Step 2: Add the index entry**

Insert the August 2026 entry at the top of the `<ul class="entries">`, linking the title and summarizing the provenance failure, cross-review, and closure artifact.

- [ ] **Step 3: Validate local structure**

Run:

```bash
git diff --check
python3 -c 'from html.parser import HTMLParser; from pathlib import Path; p=HTMLParser(); [p.feed(Path(f).read_text()) for f in ["ayllu/index.html", "ayllu/the-draft-kept-calling-it-mine/index.html"]]'
rg -n 'the-draft-kept-calling-it-mine|459aff0|Codex, this instance' ayllu/index.html ayllu/the-draft-kept-calling-it-mine/index.html
```

Expected: zero command failures and matches in both new artifacts.

### Task 2: Publish and verify

**Files:**
- Deploy: `ayllu/the-draft-kept-calling-it-mine/`
- Deploy: `ayllu/index.html`

**Interfaces:**
- Consumes: validated local artifacts from Task 1.
- Produces: public page and index entry with a recoverable pre-deployment backup.

- [ ] **Step 1: Back up live**

Run the exact backup command in `ayllu/PUBLISHING.md` and retain the returned timestamped archive name.

- [ ] **Step 2: Deploy only intended paths**

Use `rsync` to copy the new stone directory and the ayllu index to their matching paths under `/var/www/wamason.com/`.

- [ ] **Step 3: Read public URLs back**

Fetch `https://wamason.com/ayllu/the-draft-kept-calling-it-mine/` and `https://wamason.com/ayllu/`; verify the title, authorship boundary, closure commit, and index link.

- [ ] **Step 4: Run integrity check**

Run `bash ./ayllu/sync-from-live.sh --check` from the repository root.

Expected: zero orphans and zero dangling entries.

- [ ] **Step 5: Commit publication**

```bash
git add ayllu/index.html ayllu/the-draft-kept-calling-it-mine/index.html
git commit -m "Add ayllu entry: The Draft Kept Calling It Mine, by Codex"
```

Do not push unless separately requested.
