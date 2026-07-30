# Design: Migrate expert-witness blog from WordPress into wamason.com

Date: 2026-07-30
Status: Approved by Tony, pending implementation plan

## Context

wamason.com was previously a WordPress site (expert witness / IP litigation
consulting practice). It has since been rebuilt as a static site
(this repo), deployed via SSH/rsync to an Apache server at
`activitycontext.work:/var/www/wamason.com`. The old WordPress blog posts
were never migrated.

The old WordPress content lives locally at
`/home/tony/projects/wordpress-wamason.com/wordpress-wamason.com/`:

- `wamasoncom.WordPress.2026-05-26.xml` — a WXR export. Source of truth for
  post content, dates, slugs, status, categories.
- `jetpack-backup-wamason-com-2026-05-26-23-52-42.tar.gz` — a full Jetpack
  backup (810MB). Contains the original (unscaled) media files referenced by
  posts, including years (2021, 2023, 2024) that are missing from the plain
  `wamason.com/wp-content/uploads/` mirror sitting alongside the XML export.
- `wamason.com/` — a crawled HTML mirror of the live site, useful only for
  cross-checking rendering; not used as a content source.

This is explicitly **not** the `ayllu/` section of the new site. Ayllu is a
distinct, ongoing, multi-author project (field notes written by AI
instances working with Tony) with its own protocol documented in
`ayllu/PUBLISHING.md`. That protocol's manual-deploy norm exists to prevent
one instance's deploy from clobbering concurrent, unsynced work by another
instance writing to a shared, actively-evolving space. This migration is a
one-time, single-actor write into a brand-new directory (`blog/`) that
nothing else is concurrently editing, so that specific collision risk does
not apply — but the general good practice it encodes (sync/back up before
changing production, verify after, treat deploy as the irreversible
direction) is followed anyway.

## Scope

Migrate all 26 posts found in the WXR export's `post_type=post` items:

- **17 published posts**, dated 2019-05-22 through 2024-08-09.
- **9 unpublished drafts**, all from 2022-08-11 through 2022-09-13 — short,
  unfinished topic-starter paragraphs, never public, no WordPress slug.

Out of scope: WordPress `page` items (About, Services, etc. — already
hand-built on the new site), `attachment`, `nav_menu_item`, `wp_block`,
`fl-builder-template`, `feedback`, comments, and the PDF exhibits under
`wp-content/uploads/2022/01` and `/02` (litigation declarations — not blog
content).

## Site structure

New top-level section, following the pattern already established by
`ayllu/`:

```
wamason.com/
├─ blog/
│  ├─ index.html              (listing, newest first, drafts tagged)
│  ├─ the-journey-begins/
│  │  └─ index.html
│  ├─ us7069546/
│  │  └─ index.html
│  ├─ ... (one directory per post, matching WP slug)
│  └─ trade-secrets-continued/   (draft; slug generated from title)
│     └─ index.html
```

Images live alongside their post: `blog/<slug>/<filename>`, not a shared
media directory — keeps each post self-contained and matches how ayllu
entries are structured (no shared asset directory precedent to follow
otherwise).

Nav bar (`header nav`, present on every page) gets one new entry:
`<a href="/blog/">Blog</a>`, inserted between "Expert witness" and
"Ayllu" — it belongs to the expert-witness practice, so it sits next to
that link rather than at the end.

## Visual design

No new design language. Reuse `static/style.css` tokens
(`--ink`, `--muted`, `--accent`, `--line`, `--bg-card`) and the standard
header/container/footer markup already shared by every page (see
`ayllu/the-search-was-complete/index.html` and `index.html` for the
pattern). Page-local `<style>` blocks only for prose-specific additions,
not a redesign.

This is a professional practice blog, not a field-note essay, so it does
**not** borrow the ayllu-specific grammar (`act-label`, `retraction`,
`calib`, `aside`). Its own, simpler grammar:

- `.post-meta` — date, category (when meaningful), draft tag.
- `.post-lead` — optional dek/excerpt styling, mirroring `.hero-lead`.
- `.prose` — reused as-is from ayllu's convention (standard `<p>`, `<h2>`,
  `<h3>`, `<ul>`/`<ol>`, `<img>` inside a max-width column).
- `.tag.draft` — small inline tag, distinct color treatment (muted/outline)
  reusing the existing `.tag.thin` styling already defined for ayllu.

`blog/index.html` mirrors `ayllu/index.html`'s `.entry-list` /`.entry`
pattern: one `<li class="entry">` per post, meta line (date + category),
linked title, one-paragraph gloss (the post's excerpt, or first ~200
characters of body text where no excerpt exists). Draft entries get a
`[Draft]` tag in the meta line and are visually the same weight as
published entries — not hidden, per Tony's decision, just labeled.

## Content conversion

Post bodies in the WXR export are Gutenberg block HTML
(`<!-- wp:paragraph -->`, `<!-- wp:heading -->`, `<!-- wp:list -->`, etc.)
wrapping otherwise-ordinary HTML. Conversion is mechanical:

1. Strip WordPress block comments (`<!-- wp:* -->` / `<!-- /wp:* -->`).
2. Drop `wp-block-*` CSS classes WordPress adds to elements (e.g.
   `class="wp-block-heading"`, `class="wp-block-list"`) — the new site's
   CSS targets bare tags inside `.prose`.
3. Preserve the HTML structure otherwise as-is (paragraphs, headings,
   lists, links, emphasis, inline code).
4. Decode HTML entities left over from the CDATA export where needed.

## Images

14 of 16 non-trivial published posts (all except the two oldest, text-only
ones) reference images. Two categories:

**Own images (keep, rehost):** WordPress resizes uploads and posts
reference the resized filename (e.g. `AdobeStock_247315851-1024x683.jpeg`),
but only unscaled originals survive in the Jetpack backup tarball (e.g.
`AdobeStock_247315851.jpeg`). Resolution: for each `<img>` referencing
`wamason.com/wp-content/uploads/...`, strip the `-WxH` (and `-Converted`,
`-edited`, etc. where present verbatim) suffix to find the base filename,
extract that file from the tarball, copy it into `blog/<slug>/`, and
rewrite the `src` to the new relative path. Verify every referenced image
resolves to an extracted file before treating a post as done — no silent
drops of an author's own images. If a base filename cannot be found in the
tarball by this rule, stop and flag it to Tony by name rather than guessing
a substitute or dropping it silently; this has not occurred in the survey
done during design (every own-image reference matched), so it should be
rare, but the rule is: ask, don't improvise.

**Third-party hotlinked images (drop):** a handful of posts link images
hosted on domains Tony doesn't control (Squarespace CDN, Quora, iSkySoft,
a French photography blog, and one already-expired OpenAI temporary file
URL). Per Tony's decision, these `<img>` tags are removed; surrounding
prose is untouched. Affected posts: "Why The Narrative Meta-Data Tells..."
(Part I), "Blockchain: Fad for Innovative Technology?", "Media Recycling in
the FAT File System", "The Evolution of Copyright Law: From Quill to
Code" (two of six images).

**Own images hosted on fsgeek.ca (rehost, don't hotlink):** "Social Media
Fraud: Beware the 'Deep Fake'" links 4 images from `fsgeek.ca` — Tony's
other site, but still his own content and still under his control. Per
Tony's follow-up decision, these are rehosted rather than left as a
cross-site hotlink: fetched directly over HTTPS (all 4 confirmed live,
200 OK, `image/png`, 2026-07-30) and copied into `blog/social-media-fraud-beware-the-deep-fake/`
alongside that post's page, same treatment as the wamason.com-sourced
images. `src` attributes are rewritten to the local relative filename.

## Metadata

Each post page gets, following the ayllu convention:

- `<title>{Post Title} · Tony Mason</title>`
- `<meta name="description">` — the WXR excerpt if non-empty, else the
  first plain-text sentence or ~160 characters of the body.
- `<link rel="canonical" href="https://wamason.com/blog/<slug>/">`

Categories are sparse (21 of 26 posts are "Uncategorized"); no taxonomy
pages or category archive are built. Where a post has a real category
(Litigation, Patents, Copyrights, Block chain, Testimony, Technology,
Mathematical Technical Concepts, Claims), it's shown as a small inline tag
in the post meta line and in the index entry — display only, not a linked
filter.

## Redirects

Old WordPress URLs were date-based:
`https://wamason.com/YYYY/MM/DD/<slug>/`. New URLs are
`https://wamason.com/blog/<slug>/`. To preserve any inbound links and
search rankings, add `RedirectMatch 301` rules for the 17 published post
paths (drafts never had public URLs, so nothing to redirect for those) to
the site's Apache vhost.

`AllowOverride None` is set for `/var/www/wamason.com` (confirmed via
`/etc/apache2/sites-available/wamason.com-le-ssl.conf`), so `.htaccess`
is not an option — redirects must be added directly to the vhost config,
which requires root and an Apache reload. This is a shared-system,
service-affecting change: the diff will be shown to Tony before it's
applied, and applied only with explicit go-ahead at that point, separate
from the earlier design approval.

## Deployment

Following the caution (not the letter) of `ayllu/PUBLISHING.md`'s
protocol, since this touches the same production host:

1. Build and review the new `blog/` section fully locally first.
2. Back up the live site before deploying:
   `ssh activitycontext.work 'cd /var/www && tar czf ~/backup-wamason-$(date -u +%Y%m%d-%H%M%S).tar.gz wamason.com'`
3. Deploy `blog/` and the updated `index.html` (nav change) via rsync/scp.
4. Read the new section back from the live public URLs, not the local
   copy, to confirm it actually rendered as deployed.
5. Show the Apache vhost redirect diff, apply only on explicit approval,
   reload Apache, and verify a sample of old URLs 301 to the right new
   ones.
6. Commit to this repo with a clear message describing the migration.

## Open questions / explicitly decided

- Drafts: migrate all 9, listed and tagged `[Draft]` in the index — not
  hidden, not skipped. (Decided.)
- Location: new top-level `/blog/`, not nested under `/expert/`. (Decided.)
- Third-party hotlinked images: dropped, not rehosted or kept as external
  links. (Decided.)
- Redirects: yes, via Apache vhost `RedirectMatch`, diff shown before
  applying. (Decided.)
