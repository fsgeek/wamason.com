# Design: A workflow to revive the expert-witness blog

Date: 2026-08-05
Status: Draft, pending Tony's review

## Context

The `blog/` section (migrated from WordPress per
`2026-07-30-blog-migration-design.md`) went quiet in August 2024 — not
because ideas stopped, but because WordPress itself was the friction:
a five-minute auth dance, plugin/security warnings, silently-broken
backups, and a UI that had rearranged itself since the last visit. By the
time all that was cleared, the energy to write was gone.

That friction is now structurally gone. The site is static HTML in this
git repo. There is no CMS between an idea and a published post. This
design is about what should fill that space — not to force a deluge
(explicitly not the goal), but to make sure a real trickle of ideas
actually reaches the page instead of evaporating.

Ayllu already established the operating pattern this design follows:
**automate the safe, reversible half; keep a mind in the loop for the
irreversible half.** `sync-from-live.sh` (read-only, safe to automate) vs.
deploy (destructive if done carelessly, deliberately kept manual). The
blog workflow below draws the same line: capture and search-seeding are
automated; publishing to the live server stays a deliberate act.

## Goals, established by discussion

- One blog, not three channels. Range across audiences (client-facing,
  peer/field, generalist) lives in one feed with one cadence — the thing
  that has to stay alive is singular. A second channel (video, newsletter)
  is deferred until a specific piece of writing genuinely demands a
  different medium — not designed preemptively.
- Per-post audience, not per-blog. Each post is honestly written for
  whoever it's for — sometimes more than one group at once (the
  AI-as-expert-witness idea addresses both lawyers and experts, from one
  coherent stance), but it doesn't hedge toward some average reader.
  Range comes from the sequence of posts, not from any single post trying
  to be all things.
- Slow and real beats frequent and padded. A trickle is fine. A deluge is
  explicitly not the goal.
- Sparks come from active work (a case, a research thread, something in
  the news that reconnects to something Tony already lived through) — the
  gap was never ideas, it was capture and activation.

## Workflow

### 1. Capture (low-friction, any time)

When something sparks mid-work, Tony tells Claude in whatever session is
open — rough, unfiltered, no formatting expected. Claude stashes it as a
dated note under `blog/_drafts/`, e.g.:

```
blog/_drafts/2026-08-05-ai-as-expert-witness.md
```

Contents: date, a one-line seed of the idea, and whatever raw context
Tony gave (the 2024 case, the recent US court story, who it's for). This
is scratch material, not a post — no polish, no structure requirement.
`_drafts/` is prefixed with an underscore so it's obviously not a
published section and can be `.gitignore`d from the *deployed* site
independent of whether it's tracked in the repo (open question below,
see "Open questions").

### 2. Development (on demand, whenever Tony picks a draft up)

Tony opens a session, points at a draft (or just says "let's write the
expert-witness thing"), and works it into a real post the same way any
other piece of writing gets developed here — conversationally, with
Claude drafting and Tony steering tone/content. No fixed cadence forced
onto this step; it happens when Tony has the time and the pull to do it,
which was always true — the goal was removing what stood between having
that pull and acting on it.

### 3. Release (manual, deliberate — same posture as ayllu's deploy step)

Once a post is ready: written into `blog/<slug>/index.html` following the
existing pattern (see the migration design for structure/CSS
conventions), threaded into `blog/index.html`'s listing, committed, and
deployed via the same SSH/rsync path already in use. This step stays
manual and deliberate on purpose — it's the irreversible direction, same
reasoning as ayllu's publishing protocol.

### 4. The monthly nudge, with a seedling

A scheduled routine (same mechanism as the existing quantumos weekly
arXiv-scan routine) runs on an interval — suggest monthly, adjustable —
and:

1. Checks the most recent post date in `blog/index.html` (or the git log
   of `blog/`) against today.
2. If it's been ~30-45 days since the last post (exact threshold: Tony's
   call — see open questions), runs a scoped search combining both lenses
   discussed:
   - **Field-broad**: arXiv (cs.AI, cs.CY), legal-news developments
     touching AI-generated evidence, Daubert challenges, expert-witness
     practice, IP/patent law.
   - **Work-tied**: what's active right now in Tony's other repos/research
     (fsgeek.ca, quantumos, ayllu) that external material might connect to.
3. Surfaces 2-3 candidates as a short note (not a full draft) — enough to
   pique, not enough to feel like an assignment — e.g. "It's been six
   weeks since the last post. Three things crossed the wire that touch on
   what you write about: [links + one line each]."
4. This note goes wherever Tony wants to receive it (see open questions —
   likely a message in the next Claude Code session, possibly also
   surfaced via existing notification channel).

This nudge is explicitly a nudge-with-a-seedling, not a demand: it does
not create a draft file itself, does not track completion, and never
escalates in tone across repeated firings.

## What this design deliberately does NOT do

- No auto-publishing, ever. Every post reaches the live server because
  Tony (with Claude) decided it was ready, the same way ayllu works.
- No content calendar or quota. The nudge reports staleness; it doesn't
  assign topics or deadlines.
- No new channels (video, newsletter) designed now. If a specific idea
  later demands a different medium, that's a new, separate design
  conversation at that time.
- No change to `ayllu/`'s own protocol or content. This is additive to
  `blog/` only.

## Open questions for Tony's review

1. **Nudge threshold**: 30 days, 6 weeks, or something else, before the
   "it's been a while" note fires?
2. **Nudge delivery channel**: does the scheduled routine message you
   directly (email/push), or does it just wait and mention it next time a
   Claude Code session opens in this repo? The quantumos analogy suggests
   there's already a precedent worth matching rather than reinventing.
3. **`blog/_drafts/` tracked in git or not?** Rough, unfiltered idea-dumps
   might be exactly the kind of thing worth keeping private/local rather
   than committed (even to a private-by-default repo) — or they might be
   worth keeping precisely so a nudge routine running in a fresh session
   can see what's already been captured. If drafts must be visible to a
   scheduled cloud routine, they likely need to be committed somewhere it
   can read; if they're for Tony's eyes only, local-and-gitignored is
   simpler and lower-stakes.
