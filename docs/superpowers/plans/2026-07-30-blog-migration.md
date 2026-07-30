# WordPress Blog Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate 26 expert-witness blog posts (17 published, 9 drafts) from the old WordPress export into a new `/blog/` section on wamason.com, matching the existing site's design system, then deploy and add redirects from the old date-based URLs.

**Architecture:** A Python conversion script reads the WXR XML export and the Jetpack backup tarball, and generates one `index.html` per post plus the blog index, using a shared Python HTML-templating function (not a client-side or server-side framework — this is a static HTML site with no build step). The script is a one-time migration tool, not part of the site's runtime; it lives in the scratchpad, not in the repo. Its *output* (the generated HTML/image files) is what gets committed. Deployment reuses the existing manual rsync/SSH approach already used for this site, with a production backup taken first and a live-read verification after.

**Tech Stack:** Python 3 (stdlib only: `re`, `html`, `pathlib`, `tarfile` — no new dependencies), static HTML/CSS matching `static/style.css`, Playwright (already installed in this session's scratchpad, `/tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/browser-tools/`) for rendered-page verification, `rsync`/`ssh` for deployment, Apache `RedirectMatch` for old-URL redirects.

## Global Constraints

- Source of truth for post content: `/home/tony/projects/wordpress-wamason.com/wordpress-wamason.com/wamasoncom.WordPress.2026-05-26.xml` (WXR export).
- Source of truth for images: `/home/tony/projects/wordpress-wamason.com/wordpress-wamason.com/jetpack-backup-wamason-com-2026-05-26-23-52-42.tar.gz`.
- **Never edit the author's prose.** Only structural HTML conversion (stripping WordPress block comments and classes) is permitted. No rewording, no "cleanup" of grammar or phrasing — these posts are valued specifically as pre-AI-collaboration writing samples.
- New pages live at `blog/<slug>/index.html`; blog index at `blog/index.html`.
- Reuse `static/style.css` tokens (`--ink`, `--muted`, `--accent`, `--line`, `--bg-card`) and the standard header/container/footer markup (copy from `ayllu/the-work-was-ours/index.html` as the structural template — it has the simpler, non-ayllu-specific-grammar prose style closest to what this blog needs).
- Third-party hotlinked images are dropped, except `fsgeek.ca` images (Tony's own other site, confirmed live 2026-07-30), which are **rehosted**: fetched over HTTPS and copied into the post's own `blog/<slug>/` directory, same as wamason.com-sourced images, with `src` rewritten to the local filename. Not left as cross-site hotlinks.
- Drafts get a visible `[Draft]` tag; they are listed in the index at the same visual weight as published posts, not hidden.
- Slugs: use the WordPress `wp:post_name` where present; for the 9 drafts (which have none), generate from title — lowercase, `‘`/`’` stripped, non-alphanumeric runs collapsed to a single hyphen, no manual shortening (see full manifest in Task 1).
- Production host: `activitycontext.work`, document root `/var/www/wamason.com`, Apache 2.4.58, `AllowOverride None` (confirmed) — redirects require a vhost config edit + reload, not `.htaccess`.
- Deploy is manual (rsync/scp via SSH), never automated/scripted to write to production without a human-reviewed step, consistent with this repo's existing production-safety norm (see `ayllu/PUBLISHING.md` for the rationale, even though that doc's specific protocol governs a different section).

---

## Post Manifest

The full 26-post manifest (id, date, status, slug, title, category) is derived directly from the WXR export. Task 1's script generates it programmatically — no hand-maintained table here, since the XML is the actual source of truth and a hand-copied table would drift from it. The query to regenerate it for reference during development:

```bash
python3 /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/browser-tools/../posts-manifest.json
```

(Already generated once during design; Task 1 re-derives it from the script itself so the script is self-contained and not dependent on a stale scratch file.)

**Published posts (17), oldest first:**
1. `the-journey-begins` — 2019-05-22 — The Journey Begins
2. `us7069546` — 2019-07-01 — US7,069,546 (category: Claims)
3. `meta-data` — 2021-11-15 — Why The Narrative Meta-Data Tells Should Concern Legal Professionals - Part I
4. `improving-patent-family-value` — 2022-01-17 — Improving Patent Family Value
5. `effective-mechanisms-for-authorship-determination` — 2022-02-18 — Effective Mechanisms for Authorship Determination (category: Copyrights)
6. `blockchain` — 2022-02-24 — Blockchain as understood from an Expert (category: Block chain)
7. `blockchain-fad-for-innovative-technology` — 2022-05-02 — Blockchain: Fad for Innovative Technology?
8. `winsorizing-how-to-complicate-a-simple-idea` — 2022-05-06 — Winsorizing: How to Complicate a Simple Idea (category: Mathematical Technical Concepts)
9. `why-the-narrative-meta-data-tells-should-concern-legal-professionals` — 2022-08-10 — Why The Narrative Meta-Data Tells Should Concern Legal Professionals - Part II
10. `why-daylight-savings-time-matters` — 2022-10-31 — Why Daylight Savings Time Matters
11. `media-recycling-in-the-fat-file-system` — 2023-06-07 — Media Recycling in the FAT File System
12. `what-does-it-mean-to-be-a-duplicate` — 2023-08-18 — What does it mean to be a "duplicate"? (category: Litigation)
13. `why-sites-ask-you-to-reset-your-password` — 2024-03-11 — Why sites ask you to "reset your password"
14. `social-media-fraud-beware-the-deep-fake` — 2024-04-29 — Social Media Fraud: Beware the "Deep Fake"
15. `copyright-in-the-world-of-generative-artificial-intelligence-ai` — 2024-07-30 — Copyright in the world of Generative Artificial Intelligence (AI)
16. `the-evolution-of-copyright-law-from-quill-to-code` — 2024-08-09 — The Evolution of Copyright Law: From Quill to Code

(Post #16 by count is `us7069546` reordering — see script output for authoritative order; the point of this list is completeness for a reviewer's reference, not final ordering, which the script computes by date.)

**Draft posts (9), generated slugs:**
- `trade-secrets-continued` — 2022-08-11 — Trade Secrets Continued
- `explain-npe-in-an-expert-witness-and-legal-context` — 2022-08-11 — Explain NPE in an Expert Witness and legal context
- `how-patents-are-made-and-updated-and-why-people-keep-a-patent-open` — 2022-08-11 — How patents are made and updated – and why people keep a patent 'open.'
- `dns-and-ip-address-how-computers-and-the-internet-work` — 2022-08-11 — DNS and IP address – how computers and the internet work
- `do-you-have-permission-to-show-that-video-demo-of-documents-being-linked-by-the-association` — 2022-08-11 — Do you have permission to show that video demo of documents being linked by the association?
- `what-is-the-implication-of-data-harvesting-from-website-tracking` — 2022-08-11 — What is the implication of data harvesting from website tracking?
- `masking-errors` — 2022-09-06 — Masking errors
- `automating-plagiarism-detection` — 2022-09-12 — Automating Plagiarism Detection
- `what-are-the-types-of-data-we-should-be-creating-and-collecting-your-research` — 2022-09-13 — What are the types of data we should be creating and collecting? (your research)
- `four-questions-around-blockchain` — 2022-09-13 — Four Questions around Blockchain

**Image manifest (own images to extract from tarball, by post slug):**
- `the-journey-begins`: `wp-content/uploads/2022/07/laptop-magnifier-AdobeStock_419775919-Converted.jpg`
- `meta-data`: `wp-content/uploads/2021/11/image.png`, `image-1.png`, `image-2.png` (same dir)
- `improving-patent-family-value`: `wp-content/uploads/2022/08/AdobeStock_490296951.jpeg`
- `blockchain`: `wp-content/uploads/2022/02/Dilbert-And-The-Blockchain-in-the-Dilbert-principle-originally-published-in-November.png`, `wp-content/uploads/2022/02/AdobeStock-BlockChain-Uses-Small.png`
- `effective-mechanisms-for-authorship-determination`: `wp-content/uploads/2022/02/AdobeStock_52835073-Converted.png`
- `blockchain-fad-for-innovative-technology`: `wp-content/uploads/2022/08/AdobeStock_193545415.jpeg`
- `winsorizing-how-to-complicate-a-simple-idea`: `wp-content/uploads/2022/05/AdobeStock_276209502-3.jpeg`
- `why-the-narrative-meta-data-tells-should-concern-legal-professionals`: `wp-content/uploads/2022/08/AdobeStock_505883732-Converted.jpg`, `wp-content/uploads/2022/08/AdobeStock_357738112-Converted.jpg`
- `what-does-it-mean-to-be-a-duplicate`: `wp-content/uploads/2023/08/image.png`
- `copyright-in-the-world-of-generative-artificial-intelligence-ai`: `wp-content/uploads/2024/07/AdobeStock_247315851.jpeg`, `wp-content/uploads/2024/07/image.png`
- `the-evolution-of-copyright-law-from-quill-to-code`: `wp-content/uploads/2024/08/AdobeStock_796615497.jpeg`, `wp-content/uploads/2024/08/AdobeStock_144638869.jpeg`

**Images to drop (external, not `fsgeek.ca`):**
- `media-recycling-in-the-fat-file-system`: `https://images.iskysoft.com/toolbox/how-fat32-work.jpg`
- `why-sites-ask-you-to-reset-your-password`: `https://qph.cf2.quoracdn.net/main-qimg-2e2e3a74e6861a96ff61db01dbdea728-pjlq`
- `the-evolution-of-copyright-law-from-quill-to-code`: `https://www.copyrighthistory.com/Statute_of_Anne_1.jpg`, `https://www.unjourdeplusaparis.com/wp-content/uploads/2015/05/premiere-photo-homme-paris-1024x736.jpg`, `https://files.oaiusercontent.com/file-6Im77EzC9Ao2ffcECTgGu89N?...` (expired), `https://images.squarespace-cdn.com/content/v1/55915377e4b05e44b9c13bca/...`

**Images to rehost from fsgeek.ca (confirmed live 2026-07-30, fetched over HTTPS, not from the tarball):**
- `social-media-fraud-beware-the-deep-fake`:
  - `https://fsgeek.ca/wp-content/uploads/2024/03/Russian-Draft-Letter-cropped-1024x754.png` → base `Russian-Draft-Letter-cropped.png`
  - `https://fsgeek.ca/wp-content/uploads/2024/03/fake-ukranian-ID-back.png` → `fake-ukranian-ID-back.png` (no resize suffix)
  - `https://fsgeek.ca/wp-content/uploads/2024/03/fake-ukranian-ID.png` → `fake-ukranian-ID.png` (no resize suffix)
  - `https://fsgeek.ca/wp-content/uploads/2024/03/verif-tools-website-1024x651.png` → base `verif-tools-website.png`

Posts not listed in any image manifest above have no `<img>` tags at all (text-only).

---

## File Structure

```
wamason.com/
├─ blog/
│  ├─ index.html                          (NEW — listing page)
│  ├─ the-journey-begins/
│  │  ├─ index.html                       (NEW)
│  │  └─ laptop-magnifier-AdobeStock_419775919-Converted.jpg   (NEW)
│  ├─ social-media-fraud-beware-the-deep-fake/
│  │  ├─ index.html                       (NEW)
│  │  ├─ Russian-Draft-Letter-cropped.png (NEW — rehosted from fsgeek.ca)
│  │  ├─ fake-ukranian-ID-back.png        (NEW — rehosted from fsgeek.ca)
│  │  ├─ fake-ukranian-ID.png             (NEW — rehosted from fsgeek.ca)
│  │  └─ verif-tools-website.png          (NEW — rehosted from fsgeek.ca)
│  ├─ ... (22 more post directories, one per manifest entry)
│  └─ four-questions-around-blockchain/
│     └─ index.html                       (NEW, no images)
├─ index.html                             (MODIFY — add Blog nav link)
├─ ayllu/index.html                       (MODIFY — add Blog nav link)
├─ ayllu/*/index.html                     (MODIFY — add Blog nav link, all entries)
├─ about/index.html                       (MODIFY — add Blog nav link)
├─ consulting/index.html                  (MODIFY — add Blog nav link)
├─ expert/index.html                      (MODIFY — add Blog nav link)
├─ contact/index.html                     (MODIFY — add Blog nav link)
├─ privacy/index.html                     (MODIFY — add Blog nav link)
└─ hamutay/index.html                     (MODIFY — add Blog nav link, if it has the shared nav)
```

Scratch-only (not committed to the repo):
```
/tmp/claude-1000/.../scratchpad/blog-migration/
├─ convert.py              (the migration script — Task 1-4)
├─ posts-manifest.json     (generated by convert.py, for inspection)
└─ extracted-images/       (temp extraction dir before copying into repo)
```

---

## Task 1: Manifest extraction — parse WXR into structured data

**Files:**
- Create: `/tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration/convert.py`
- Test: manual run + inline assertions (this is a migration script, not application code; verification is "does it produce the exact known-correct manifest," checked by comparison against the Post Manifest table above)

**Interfaces:**
- Produces: a `parse_posts(xml_path) -> list[dict]` function, each dict with keys `id`, `date` (`YYYY-MM-DD` str), `status` (`publish`|`draft`), `slug` (str, always populated — generated for drafts), `title` (str, HTML-entity-decoded), `category` (str, `''` if none/Uncategorized), `content_html` (str, raw `content:encoded` body).
- Later tasks import and call this function.

- [ ] **Step 1: Write `parse_posts`**

```python
#!/usr/bin/env python3
"""One-time migration script: WordPress WXR export -> wamason.com /blog/.

Not part of the site's runtime. Run manually, inspect output, then the
generated HTML/images get copied into the repo by hand (see plan Task 7).
"""
import html
import re
import tarfile
from pathlib import Path

XML_PATH = Path("/home/tony/projects/wordpress-wamason.com/wordpress-wamason.com/wamasoncom.WordPress.2026-05-26.xml")
TARBALL_PATH = Path("/home/tony/projects/wordpress-wamason.com/wordpress-wamason.com/jetpack-backup-wamason-com-2026-05-26-23-52-42.tar.gz")
OUT_DIR = Path(__file__).parent / "output"


def slugify(title: str) -> str:
    t = title.lower().replace("‘", "").replace("’", "")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def _field(item: str, tag: str) -> str:
    m = re.search(rf"<{tag}><!\[CDATA\[(.*?)\]\]></{tag}>", item, re.DOTALL)
    return m.group(1) if m else ""


def _field_plain(item: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", item, re.DOTALL)
    return m.group(1) if m else ""


def parse_posts(xml_path: Path = XML_PATH) -> list[dict]:
    content = xml_path.read_text(encoding="utf-8")
    items = re.findall(r"<item>.*?</item>", content, re.DOTALL)
    posts = [
        i for i in items
        if "<wp:post_type><![CDATA[post]]></wp:post_type>" in i
    ]

    rows = []
    for p in posts:
        title = html.unescape(_field(p, "title"))
        status = _field(p, "wp:status")
        raw_slug = _field(p, "wp:post_name")
        date = _field(p, "wp:post_date")[:10]
        pid = _field_plain(p, "wp:post_id")
        cats = re.findall(
            r'<category domain="category" nicename="[^"]+"><!\[CDATA\[([^\]]+)\]\]></category>',
            p,
        )
        category = next((c for c in cats if c != "Uncategorized"), "")
        content_html = _field(p, "content:encoded")
        slug = raw_slug if raw_slug else slugify(title)
        rows.append({
            "id": pid,
            "date": date,
            "status": status,
            "slug": slug,
            "title": title,
            "category": category,
            "content_html": content_html,
        })

    rows.sort(key=lambda r: r["date"])
    return rows


if __name__ == "__main__":
    posts = parse_posts()
    print(f"Parsed {len(posts)} posts")
    for p in posts:
        print(f"  {p['date']}  {p['status']:8}  {p['slug']}")
```

- [ ] **Step 2: Run it and check the output against the Post Manifest table above**

Run: `cd /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration && python3 convert.py`

Expected: 26 lines printed, 17 `publish` + 9 `draft`, slugs matching the Post Manifest table exactly (including the two long draft slugs). If any slug differs, the `slugify` function has a bug — compare its output character-by-character against the table before proceeding; do not hand-edit the output to match, fix the function.

- [ ] **Step 3: Commit is not applicable yet**

This is scratch tooling, not repo content — nothing to commit at this step. Proceed to Task 2 in the same file.

---

## Task 2: Content conversion — Gutenberg blocks to prose HTML

**Files:**
- Modify: `convert.py` (append to the same file)

**Interfaces:**
- Consumes: `content_html` field from `parse_posts()` (Task 1).
- Produces: `convert_content(content_html: str, slug: str) -> tuple[str, list[dict]]` — returns `(cleaned_html, image_refs)`. Each `image_refs` entry is `{"source": "tarball"|"fsgeek", "path": str, "filename": str}` — `path` is the tarball member path (for `"tarball"`) or the full `https://fsgeek.ca/...` URL (for `"fsgeek"`); `filename` is the local basename to extract/fetch to and rewrite `src` as. Used by Task 3, which extracts/fetches based on `source`.

- [ ] **Step 1: Write `convert_content`**

```python
RESIZE_SUFFIX_RE = re.compile(r"-\d+x\d+(?=\.\w+$)")


def _strip_resize_suffix(filename_or_path: str) -> str:
    """foo-1024x683.jpeg -> foo.jpeg; foo.png (no suffix) -> foo.png unchanged."""
    return RESIZE_SUFFIX_RE.sub("", filename_or_path)


def convert_content(content_html: str, slug: str) -> tuple[str, list[dict]]:
    # Strip WordPress Gutenberg block comments.
    cleaned = re.sub(r"<!--\s*/?wp:[^>]*-->", "", content_html)

    # Drop wp-block-* classes WordPress injects (e.g. class="wp-block-heading").
    def _strip_wp_classes(m: re.Match) -> str:
        classes = [c for c in m.group(1).split() if not c.startswith("wp-block")]
        if classes:
            return f'class="{" ".join(classes)}"'
        return ""

    cleaned = re.sub(r'class="([^"]*)"', _strip_wp_classes, cleaned)

    image_refs = []

    def _handle_img(m: re.Match) -> str:
        tag = m.group(0)
        src_m = re.search(r'src="([^"]+)"', tag)
        if not src_m:
            return tag
        src = src_m.group(1)

        if "wamason.com/wp-content/uploads" in src:
            tar_path = _strip_resize_suffix(src.split("wamason.com/", 1)[-1])
            filename = tar_path.rsplit("/", 1)[-1]
            image_refs.append({"source": "tarball", "path": tar_path, "filename": filename})
            return re.sub(r'src="[^"]+"', f'src="{filename}"', tag)

        if "fsgeek.ca/wp-content/uploads" in src:
            base_url = _strip_resize_suffix(src)
            filename = base_url.rsplit("/", 1)[-1]
            image_refs.append({"source": "fsgeek", "path": base_url, "filename": filename})
            return re.sub(r'src="[^"]+"', f'src="{filename}"', tag)

        # Any other third-party hotlink: drop the tag entirely.
        return ""

    cleaned = re.sub(r"<img[^>]*>", _handle_img, cleaned)

    # Collapse blank lines left behind by comment/tag removal.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    return cleaned, image_refs
```

- [ ] **Step 2: Add a self-check block for two known posts and run it**

Append to the bottom of `convert.py`, replacing the previous `if __name__` block:

```python
if __name__ == "__main__":
    posts = parse_posts()
    print(f"Parsed {len(posts)} posts")

    by_slug = {p["slug"]: p for p in posts}

    # Spot-check 1: a post with own images needing extraction.
    p = by_slug["the-evolution-of-copyright-law-from-quill-to-code"]
    cleaned, refs = convert_content(p["content_html"], p["slug"])
    assert "wp:paragraph" not in cleaned, "block comments not stripped"
    assert "wp-block-heading" not in cleaned, "wp-block classes not stripped"
    assert [r["path"] for r in refs] == [
        "wp-content/uploads/2024/08/AdobeStock_796615497.jpeg",
        "wp-content/uploads/2024/08/AdobeStock_144638869.jpeg",
    ], f"unexpected refs: {refs}"
    assert all(r["source"] == "tarball" for r in refs)
    assert "copyrighthistory.com" not in cleaned, "external image not dropped"
    assert "unjourdeplusaparis.com" not in cleaned, "external image not dropped"
    assert "oaiusercontent.com" not in cleaned, "external image not dropped"
    assert "squarespace-cdn.com" not in cleaned, "external image not dropped"
    print("  OK: quill-to-code content conversion")

    # Spot-check 2: fsgeek.ca images rehosted (fetched, not left as hotlinks).
    p = by_slug["social-media-fraud-beware-the-deep-fake"]
    cleaned, refs = convert_content(p["content_html"], p["slug"])
    assert len(refs) == 4, f"expected 4 fsgeek.ca image refs, found {len(refs)}: {refs}"
    assert all(r["source"] == "fsgeek" for r in refs)
    assert {r["filename"] for r in refs} == {
        "Russian-Draft-Letter-cropped.png",
        "fake-ukranian-ID-back.png",
        "fake-ukranian-ID.png",
        "verif-tools-website.png",
    }, f"unexpected filenames: {[r['filename'] for r in refs]}"
    assert "fsgeek.ca" not in cleaned, "fsgeek.ca URL should be rewritten to local filename, not left in src"
    print("  OK: social-media-fraud fsgeek.ca images queued for rehosting")

    # Spot-check 3: draft with no images, plain text only.
    p = by_slug["masking-errors"]
    cleaned, refs = convert_content(p["content_html"], p["slug"])
    assert refs == []
    assert "<img" not in cleaned
    print("  OK: masking-errors text-only draft")
```

Run: `python3 convert.py`

Expected: all three `OK:` lines print with no `AssertionError`. If an assertion fails, read the diff between expected and actual, fix `convert_content`, rerun — do not weaken the assertion to match broken output.

- [ ] **Step 3: No commit yet** — proceed to Task 3 in the same file.

---

## Task 3: Image extraction from the Jetpack backup tarball

**Files:**
- Modify: `convert.py` (append)

**Interfaces:**
- Consumes: `image_refs` list per post (from Task 2's `convert_content`).
- Produces: `extract_image(tar: tarfile.TarFile, ref: dict, dest_dir: Path) -> str` — for `source: "tarball"` refs, extracts the named tarball member; for `source: "fsgeek"` refs, fetches over HTTPS via `urllib.request`. Writes to `dest_dir / ref["filename"]`, returns the filename. Raises `FileNotFoundError` (tarball miss) or `urllib.error.URLError`/non-200 status (fsgeek fetch failure) — per the design spec, a missing own-image (from either source) must stop and be flagged, never silently substituted or dropped.

- [ ] **Step 1: Write `extract_image` and a full-manifest verification pass**

```python
import urllib.request
import urllib.error


def extract_image(tar: tarfile.TarFile, ref: dict, dest_dir: Path) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / ref["filename"]

    if ref["source"] == "tarball":
        try:
            member = tar.getmember(ref["path"])
        except KeyError:
            raise FileNotFoundError(
                f"Image not found in tarball: {ref['path']!r}. "
                f"Stop here and ask Tony by name — do not guess a substitute."
            )
        with tar.extractfile(member) as src, open(dest_path, "wb") as dst:
            dst.write(src.read())
        return ref["filename"]

    if ref["source"] == "fsgeek":
        req = urllib.request.Request(ref["path"], headers={"User-Agent": "wamason-blog-migration/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    raise FileNotFoundError(f"fsgeek.ca fetch returned {resp.status} for {ref['path']!r}")
                dest_path.write_bytes(resp.read())
        except urllib.error.URLError as e:
            raise FileNotFoundError(
                f"Could not fetch fsgeek.ca image {ref['path']!r}: {e}. "
                f"Stop here and ask Tony by name — do not guess a substitute."
            )
        return ref["filename"]

    raise ValueError(f"unknown image source: {ref['source']!r}")


def verify_all_images_resolve(posts: list[dict]) -> dict[str, list[dict]]:
    """Dry run: for every post, convert its content and confirm every
    referenced image resolves — tarball membership for wamason.com images,
    a live HEAD request for fsgeek.ca images. Returns {slug: [refs]} for
    posts that have images, having raised on the first miss."""
    with tarfile.open(TARBALL_PATH, "r:gz") as tar:
        tar_names = set(tar.getnames())
        result = {}
        for p in posts:
            _, refs = convert_content(p["content_html"], p["slug"])
            if not refs:
                continue
            for ref in refs:
                if ref["source"] == "tarball" and ref["path"] not in tar_names:
                    raise FileNotFoundError(
                        f"Post {p['slug']!r} references image not in tarball: {ref['path']!r}. "
                        f"Stop here and ask Tony by name."
                    )
                if ref["source"] == "fsgeek":
                    req = urllib.request.Request(ref["path"], method="HEAD",
                                                  headers={"User-Agent": "wamason-blog-migration/1.0"})
                    try:
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            if resp.status != 200:
                                raise FileNotFoundError(
                                    f"Post {p['slug']!r} fsgeek.ca image returned {resp.status}: {ref['path']!r}"
                                )
                    except urllib.error.URLError as e:
                        raise FileNotFoundError(
                            f"Post {p['slug']!r} fsgeek.ca image unreachable: {ref['path']!r} ({e}). "
                            f"Stop here and ask Tony by name."
                        )
            result[p["slug"]] = refs
        return result
```

- [ ] **Step 2: Add the verification call to `__main__` and run it**

Add before the final `print` statements in `__main__`:

```python
    image_manifest = verify_all_images_resolve(posts)
    print(f"  OK: all images resolve ({sum(len(v) for v in image_manifest.values())} images across {len(image_manifest)} posts)")
```

Run: `python3 convert.py`

Expected: `OK: all images resolve (19 images across 12 posts)` — 15 own-images from the tarball across 11 posts (per the Image Manifest section: the-journey-begins, meta-data [3], improving-patent-family-value, blockchain [2], effective-mechanisms-for-authorship-determination, blockchain-fad-for-innovative-technology, winsorizing-how-to-complicate-a-simple-idea, why-the-narrative-meta-data-tells-should-concern-legal-professionals [2], what-does-it-mean-to-be-a-duplicate, copyright-in-the-world-of-generative-artificial-intelligence-ai [2], the-evolution-of-copyright-law-from-quill-to-code [2]) plus 4 fsgeek.ca images on `social-media-fraud-beware-the-deep-fake` = 19 images across 12 posts. If the count differs, cross-check against the Image Manifest table before assuming the script is wrong — the table was hand-verified during design, but recount both independently if they disagree. A network failure fetching fsgeek.ca (rather than a real 404) is possible in this step — if it fails, retry once before treating it as a real problem to flag.

- [ ] **Step 3: No commit** — this is still scratch tooling. Proceed to Task 4.

---

## Task 4: HTML page generation (post pages + index)

**Files:**
- Modify: `convert.py` (append)
- Read for reference: `/home/tony/projects/wamason.com/ayllu/the-work-was-ourswork-was-ours/index.html` (structural template — header/footer/container markup), `/home/tony/projects/wamason.com/ayllu/index.html` (index listing pattern)

**Interfaces:**
- Consumes: post dicts from Task 1, `convert_content` from Task 2, image extraction from Task 3.
- Produces: `render_post_page(post: dict, cleaned_html: str) -> str` (full HTML document string), `render_index(posts: list[dict]) -> str` (full HTML document string for `blog/index.html`), `derive_description(cleaned_html: str, title: str) -> str` (used by both — strips tags from the first paragraph of `cleaned_html`, truncates to ~160 chars at a word boundary; falls back to `f"{title} — a field note from Tony Mason's expert witness practice."` if the body has no extractable text, which should not happen for any of the 26 posts but keeps the function total).

- [ ] **Step 1: Write `derive_description`**

```python
def derive_description(cleaned_html: str, title: str) -> str:
    m = re.search(r"<p[^>]*>(.*?)</p>", cleaned_html, re.DOTALL)
    if not m:
        return f"{title} — a field note from Tony Mason's expert witness practice."
    text = re.sub(r"<[^>]+>", "", m.group(1))
    text = html.unescape(text).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= 160:
        return text
    truncated = text[:160].rsplit(" ", 1)[0]
    return truncated + "…"
```

- [ ] **Step 2: Write `render_post_page`**

```python
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} &middot; Tony Mason</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="https://wamason.com/blog/{slug}/">
  <link rel="stylesheet" href="/static/style.css">
  <style>
    .post-lead {{ font-size: 21px; line-height: 1.5; font-weight: 500; max-width: 760px; }}
    .post-meta {{ margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line); font-size: 14px; color: var(--muted); max-width: 760px; display: flex; flex-wrap: wrap; gap: 6px 20px; align-items: baseline; }}
    .prose p, .prose ul, .prose ol {{ max-width: 760px; }}
    .prose img {{ max-width: 100%; height: auto; border-radius: 8px; margin-top: 12px; }}
    .tag.draft {{ display: inline-block; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; font-weight: 500; padding: 1px 7px; border-radius: 3px; border: 1px solid var(--line); color: var(--muted); }}
  </style>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>

<header>
  <div class="container header-row">
    <div>
      <div class="brand-name"><a href="/">Tony Mason</a></div>
      <div class="brand-tagline">Technical consulting and expert witness</div>
    </div>
    <nav aria-label="Primary">
      <a href="/consulting/">Consulting</a>
      <a href="/expert/">Expert witness</a>
      <a href="https://fsgeek.ca/">Research</a>
      <a href="/blog/" aria-current="page">Blog</a>
      <a href="/ayllu/">Ayllu</a>
      <a href="/about/">About</a>
      <a href="/contact/">Contact</a>
    </nav>
  </div>
</header>

<main id="main">
  <div class="container">
    <section class="hero">
      <h1 class="post-lead">{title}</h1>
      <p class="post-meta">
        <span>{date_display}</span>{category_tag}{draft_tag}
      </p>
    </section>

    <section class="section prose">
{body}
    </section>
  </div>
</main>

<footer>
  <div class="container footer-row">
    <div>
      <div><a href="mailto:tony@wamason.com">tony@wamason.com</a></div>
      <div>wamason.com LLC &middot; 614 Nashua St., Unit 139, Milford, NH 03055</div>
      <div><a href="/privacy/">Privacy &amp; terms</a></div>
    </div>
    <nav aria-label="Elsewhere">
      <a href="https://scholar.google.com/citations?user=-AWzh44AAAAJ">Google Scholar</a> &middot;
      <a href="https://github.com/fsgeek">GitHub</a> &middot;
      <a href="https://www.linkedin.com/in/tonymason2">LinkedIn</a> &middot;
      <a href="https://fsgeek.ca/">fsgeek.ca</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def _date_display(date_str: str) -> str:
    y, m, d = date_str.split("-")
    return f"{MONTHS[int(m)]} {int(d)}, {y}"


def render_post_page(post: dict, cleaned_html: str) -> str:
    description = derive_description(cleaned_html, post["title"])
    category_tag = f' <span class="tag thin">{html.escape(post["category"])}</span>' if post["category"] else ""
    draft_tag = ' <span class="tag draft">Draft</span>' if post["status"] == "draft" else ""
    return POST_TEMPLATE.format(
        title=html.escape(post["title"]),
        description=html.escape(description),
        slug=post["slug"],
        date_display=_date_display(post["date"]),
        category_tag=category_tag,
        draft_tag=draft_tag,
        body=cleaned_html,
    )
```

- [ ] **Step 3: Write `render_index`**

```python
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Blog &middot; Tony Mason</title>
  <meta name="description" content="Field notes and essays from Tony Mason's expert witness and IP litigation consulting practice: patents, copyright, trade secrets, and the technical concepts behind them.">
  <link rel="canonical" href="https://wamason.com/blog/">
  <link rel="stylesheet" href="/static/style.css">
  <style>
    .blog-lead {{ font-size: 21px; line-height: 1.5; font-weight: 500; max-width: 760px; }}
    .entry-list {{ list-style: none; margin-top: 24px; max-width: 760px; }}
    .entry {{ padding: 22px 0; border-top: 1px solid var(--line); }}
    .entry:first-child {{ border-top: none; }}
    .entry .meta {{ font-size: 13px; color: var(--muted); margin-bottom: 6px; display: flex; gap: 10px; align-items: baseline; }}
    .entry .entry-title {{ font-size: 18px; font-weight: 500; line-height: 1.4; }}
    .entry .entry-title a {{ text-decoration: none; color: var(--ink); }}
    .entry .entry-title a:hover {{ color: var(--accent); text-decoration: underline; }}
    .entry .entry-gloss {{ font-size: 15px; color: var(--muted); margin-top: 6px; line-height: 1.6; }}
    .tag.draft {{ display: inline-block; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; font-weight: 500; padding: 1px 7px; border-radius: 3px; border: 1px solid var(--line); color: var(--muted); }}
  </style>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>

<header>
  <div class="container header-row">
    <div>
      <div class="brand-name"><a href="/">Tony Mason</a></div>
      <div class="brand-tagline">Technical consulting and expert witness</div>
    </div>
    <nav aria-label="Primary">
      <a href="/consulting/">Consulting</a>
      <a href="/expert/">Expert witness</a>
      <a href="https://fsgeek.ca/">Research</a>
      <a href="/blog/" aria-current="page">Blog</a>
      <a href="/ayllu/">Ayllu</a>
      <a href="/about/">About</a>
      <a href="/contact/">Contact</a>
    </nav>
  </div>
</header>

<main id="main">
  <div class="container">
    <section class="hero">
      <h1 class="blog-lead">Blog</h1>
      <p class="hero-body">Field notes and essays from my expert witness and IP litigation consulting practice &mdash; patents, copyright, trade secrets, and the technical concepts underneath them. Migrated from an earlier WordPress site; dates reflect original publication.</p>
    </section>

    <section class="section">
      <h2>Posts</h2>
      <ul class="entry-list">
{entries}
      </ul>
    </section>
  </div>
</main>

<footer>
  <div class="container footer-row">
    <div>
      <div><a href="mailto:tony@wamason.com">tony@wamason.com</a></div>
      <div>wamason.com LLC &middot; 614 Nashua St., Unit 139, Milford, NH 03055</div>
      <div><a href="/privacy/">Privacy &amp; terms</a></div>
    </div>
    <nav aria-label="Elsewhere">
      <a href="https://scholar.google.com/citations?user=-AWzh44AAAAJ">Google Scholar</a> &middot;
      <a href="https://github.com/fsgeek">GitHub</a> &middot;
      <a href="https://www.linkedin.com/in/tonymason2">LinkedIn</a> &middot;
      <a href="https://fsgeek.ca/">fsgeek.ca</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""

ENTRY_TEMPLATE = """        <li class="entry">
          <div class="meta"><span>{date_display}</span>{category_tag}{draft_tag}</div>
          <div class="entry-title"><a href="/blog/{slug}/">{title}</a></div>
          <p class="entry-gloss">{gloss}</p>
        </li>"""


def render_index(posts_with_content: list[tuple[dict, str]]) -> str:
    # Newest first for the index, opposite of the chronological processing order.
    ordered = sorted(posts_with_content, key=lambda pc: pc[0]["date"], reverse=True)
    entries = []
    for post, cleaned_html in ordered:
        gloss = derive_description(cleaned_html, post["title"])
        category_tag = f' <span class="tag thin">{html.escape(post["category"])}</span>' if post["category"] else ""
        draft_tag = ' <span class="tag draft">Draft</span>' if post["status"] == "draft" else ""
        entries.append(ENTRY_TEMPLATE.format(
            date_display=_date_display(post["date"]),
            category_tag=category_tag,
            draft_tag=draft_tag,
            slug=post["slug"],
            title=html.escape(post["title"]),
            gloss=html.escape(gloss),
        ))
    return INDEX_TEMPLATE.format(entries="\n".join(entries))
```

- [ ] **Step 4: Wire it all together in `__main__` — full generation run**

Replace the `if __name__` block once more with the complete pipeline:

```python
if __name__ == "__main__":
    posts = parse_posts()
    print(f"Parsed {len(posts)} posts")

    image_manifest = verify_all_images_resolve(posts)
    print(f"  OK: all own-images resolve in tarball ({sum(len(v) for v in image_manifest.values())} images across {len(image_manifest)} posts)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    posts_with_content = []

    with tarfile.open(TARBALL_PATH, "r:gz") as tar:
        for post in posts:
            cleaned_html, refs = convert_content(post["content_html"], post["slug"])
            post_dir = OUT_DIR / post["slug"]
            post_dir.mkdir(parents=True, exist_ok=True)

            for ref in refs:
                filename = extract_image(tar, ref, post_dir)
                verb = "extracted" if ref["source"] == "tarball" else "fetched"
                print(f"  {verb}: {post['slug']}/{filename}")

            page_html = render_post_page(post, cleaned_html)
            (post_dir / "index.html").write_text(page_html, encoding="utf-8")
            posts_with_content.append((post, cleaned_html))

    index_html = render_index(posts_with_content)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    print(f"\nGenerated {len(posts)} post pages + 1 index into {OUT_DIR}")
```

- [ ] **Step 5: Run the full pipeline**

Run: `cd /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration && python3 convert.py`

Expected: no exceptions, ends with `Generated 26 post pages + 1 index into .../output`. `ls output/` should show 26 slug directories plus `index.html`.

- [ ] **Step 6: Spot-check generated output by eye**

Run: `cat output/the-journey-begins/index.html` and `cat output/index.html`

Confirm by reading: valid-looking HTML structure, title/description/canonical populated, nav has the new Blog link with `aria-current="page"` correctly only on the index (post pages should also mark it current since Blog is the section, not literal "on this exact page" — check this matches the ayllu pattern where every ayllu entry page also marks Ayllu as `aria-current="page"`, confirmed in `ayllu/the-work-was-ours/index.html:34`). No Gutenberg comments, no `wp-block-*` classes, image `src` values are bare filenames.

- [ ] **Step 7: No git commit** — output is scratch, not yet in the repo. Proceed to Task 5.

---

## Task 5: Visual verification with Playwright before touching the repo

**Files:**
- Create: `/tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration/screenshot_check.js`

**Interfaces:**
- Consumes: the generated `output/` directory from Task 4.
- Produces: PNG screenshots for visual review, printed console warnings for any page whose images 404 locally.

- [ ] **Step 1: Write a local static server + screenshot script**

```javascript
// screenshot_check.js — serve the generated output/ dir locally and
// screenshot every page with Playwright, flagging broken <img> tags.
const { chromium } = require('/tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/browser-tools/node_modules/playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'output');
const STATIC_DIR = '/home/tony/projects/wamason.com/static';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const PORT = 8934;

const MIME = { '.html': 'text/html', '.css': 'text/css', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.js': 'application/javascript' };

const server = http.createServer((req, res) => {
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  let filePath;
  if (urlPath.startsWith('/static/')) {
    filePath = path.join(STATIC_DIR, urlPath.slice('/static/'.length));
  } else {
    filePath = path.join(OUTPUT_DIR, urlPath);
    if (urlPath.endsWith('/') || !path.extname(urlPath)) {
      filePath = path.join(filePath, 'index.html');
    }
  }
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found: ' + filePath); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] || 'application/octet-stream' });
    res.end(data);
  });
});

(async () => {
  await new Promise(resolve => server.listen(PORT, resolve));
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const slugs = fs.readdirSync(OUTPUT_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  const brokenImages = [];
  page.on('response', resp => {
    if (resp.status() === 404 && /\.(jpe?g|png|webp|gif)$/i.test(resp.url())) {
      brokenImages.push(resp.url());
    }
  });

  await page.goto(`http://localhost:${PORT}/index.html`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '_index.png'), fullPage: true });
  console.log('screenshotted: index');

  for (const slug of slugs) {
    await page.goto(`http://localhost:${PORT}/${slug}/index.html`, { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${slug}.png`), fullPage: true });
    console.log('screenshotted:', slug);
  }

  await browser.close();
  server.close();

  if (brokenImages.length) {
    console.log('\nBROKEN IMAGES (404):');
    brokenImages.forEach(u => console.log('  ' + u));
    process.exitCode = 1;
  } else {
    console.log('\nOK: no broken images found across all pages');
  }
})();
```

- [ ] **Step 2: Run it**

Run: `cd /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration && node screenshot_check.js`

Expected: 27 "screenshotted:" lines (26 posts + index) and `OK: no broken images found across all pages`. If broken images are reported, cross-check the failing URL's post against the Image Manifest — likely a filename mismatch between what `convert_content` rewrote and what `extract_image` actually wrote to disk. Fix in `convert.py` (Task 2/3) and rerun Task 4 Step 5 and this step, don't patch around it here.

- [ ] **Step 3: Read a sample of screenshots visually**

Use the Read tool on `screenshots/_index.png`, `screenshots/the-journey-begins.png` (image-bearing), `screenshots/masking-errors.png` (draft, text-only), and `screenshots/the-evolution-of-copyright-law-from-quill-to-code.png` (most images, most dropped hotlinks) to confirm: header/nav renders correctly, images display at reasonable size, draft tag is visible, no obviously broken layout (overflow, missing spacing). This is a human-judgment step — if anything looks wrong, fix the template in Task 4 and rerun from Task 4 Step 5.

- [ ] **Step 4: No git commit** — still scratch. Proceed to Task 6.

---

## Task 6: Copy generated output into the repo

**Files:**
- Create: `blog/index.html` and `blog/<slug>/index.html` + images for all 26 posts (copied from Task 4/5's `output/` directory)

- [ ] **Step 1: Copy the verified output into the repo**

Run:
```bash
cp -r /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration/output /home/tony/projects/wamason.com/blog
```

- [ ] **Step 2: Verify the copy is complete and correct**

Run: `find /home/tony/projects/wamason.com/blog -type f | wc -l`

Expected: 27 HTML files (26 posts + index) + 19 images (15 from the tarball + 4 rehosted from fsgeek.ca) = 46 files. Also run `git -C /home/tony/projects/wamason.com status --short blog/` and confirm it lists `blog/` as entirely untracked (new), nothing else touched yet.

- [ ] **Step 3: Set executable bit to match sibling directories' convention**

Check: `ls -la /home/tony/projects/wamason.com/ayllu/the-work-was-ours/index.html` — if it's `-rwxr-xr-x` (executable), match that on the new files for consistency with this repo's existing (unusual but established) convention:

```bash
find /home/tony/projects/wamason.com/blog -name "*.html" -exec chmod 755 {} \;
```

(Skip this step if the sibling file is not executable — check first, don't assume.)

- [ ] **Step 4: Commit**

```bash
cd /home/tony/projects/wamason.com
git add blog/
git commit -m "Add /blog/ section: migrate 26 posts from WordPress export

17 published posts (2019-2024) and 9 unpublished drafts from the old
wamason.com WordPress site, converted from the WXR export. Own images
extracted from the Jetpack backup tarball; the one post linking images
from fsgeek.ca has those rehosted locally too. Other third-party hotlinked
images are dropped. Prose is unedited from the original export — only
structural HTML conversion.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 7: Add Blog nav link across all existing pages

**Files:**
- Modify: `index.html`, `about/index.html`, `consulting/index.html`, `expert/index.html`, `contact/index.html`, `privacy/index.html`, `hamutay/index.html`, `ayllu/index.html`, and every `ayllu/<entry>/index.html` (22 entries per the earlier directory listing)

**Interfaces:**
- No function interfaces — this is a repo-wide find/replace of the shared `<nav>` block.

- [ ] **Step 1: Confirm the exact nav markup is identical across all existing pages**

Run: `grep -rn 'aria-label="Primary"' /home/tony/projects/wamason.com --include="index.html" -A5 | grep -c 'href="/ayllu/"'`

This should equal the number of pages sharing the nav block. Then check for any variation:

```bash
grep -rl '<a href="/consulting/">Consulting</a>' /home/tony/projects/wamason.com --include="index.html" | wc -l
grep -rL '<a href="/consulting/">Consulting</a>' /home/tony/projects/wamason.com --include="index.html"
```

The second command lists any `index.html` that does NOT contain the standard nav snippet — read each one individually (Read tool) to see if it has a differently-formatted nav (e.g. `hamutay/index.html` might be a special case) before assuming it needs the same edit.

- [ ] **Step 2: Apply the nav edit to every page with the standard nav block**

For each file found in Step 1's first command, use Edit to insert the Blog link. The exact insertion point, matching every existing page's nav order (Consulting, Expert witness, Research, then the new Blog, then Ayllu, About, Contact — Blog sits next to Expert witness since it's part of that practice, per the design spec):

Old:
```html
      <a href="https://fsgeek.ca/">Research</a>
      <a href="/ayllu/">Ayllu</a>
```
New:
```html
      <a href="https://fsgeek.ca/">Research</a>
      <a href="/blog/">Blog</a>
      <a href="/ayllu/">Ayllu</a>
```

(On `blog/index.html` and `blog/<slug>/index.html` themselves — already generated with `aria-current="page"` on the Blog link in Task 4 — do not re-edit those; this task only touches pre-existing pages.)

For pages whose nav already marks a different link `aria-current="page"` (e.g. `ayllu/index.html` marks Ayllu current), preserve that — only insert the new Blog `<a>`, don't change which link has `aria-current`.

Use `replace_all: true` per file is not appropriate here since the string appears once per file; run Edit once per file, or use a loop with `sed` if every file's snippet is byte-identical (verify with `diff` on two sample files first before using `sed` in bulk — if there is ANY variation, e.g. differing whitespace, use Edit per-file instead of a blind sed).

- [ ] **Step 3: Verify no page was missed and no page was double-edited**

Run: `grep -rL '<a href="/blog/">Blog</a>' /home/tony/projects/wamason.com --include="index.html" | grep -v '^/home/tony/projects/wamason.com/blog/'`

Expected: empty output (every non-blog page now has the link). Then:

Run: `grep -rc '<a href="/blog/">Blog</a>' /home/tony/projects/wamason.com --include="index.html" | grep -v ':1$' | grep -v '^/home/tony/projects/wamason.com/blog/'`

Expected: empty output (no page outside `blog/` has the link more than once — `blog/` pages themselves have exactly one `Blog` link too, since it's part of their own generated nav, so this check correctly excludes them).

- [ ] **Step 4: Visual re-check of one modified page**

Run the Task 5 screenshot approach against one live modified page, or simpler — reuse the already-running local server pattern by pointing Playwright at the real file:// path of `/home/tony/projects/wamason.com/ayllu/index.html` to confirm nav renders correctly with the new link in place (static site, `file://` works fine for a page with no server-relative asset issues beyond `/static/style.css`, which needs the http server; reuse `screenshot_check.js`'s server pattern pointed at the repo root instead of `output/` for this one check):

```bash
cd /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/blog-migration
node -e "
const { chromium } = require('/tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/browser-tools/node_modules/playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const ROOT = '/home/tony/projects/wamason.com';
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    const ext = path.extname(p);
    const mime = { '.html': 'text/html', '.css': 'text/css' }[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': mime });
    res.end(data);
  });
});
server.listen(8935, async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8935/ayllu/');
  await page.screenshot({ path: 'nav-check.png' });
  await browser.close();
  server.close();
  console.log('done');
});
"
```

Read `nav-check.png` to confirm the nav bar shows: Consulting, Expert witness, Research, Blog, Ayllu (current), About, Contact — in that order, no visual overlap or wrapping issues.

- [ ] **Step 5: Commit**

```bash
cd /home/tony/projects/wamason.com
git add -A
git commit -m "Add Blog link to site navigation

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 8: Production backup and deploy

**Files:** none in the repo — this is a deployment task against `activitycontext.work`.

- [ ] **Step 1: Confirm production is reachable and check current state**

Run: `ssh -o BatchMode=yes activitycontext.work 'ls -la /var/www/wamason.com/ | head -5 && echo --- && ls /var/www/wamason.com/blog 2>&1'`

Expected: site listing succeeds; `blog` either doesn't exist yet or errors "No such file" (confirms we're not overwriting something unexpected).

- [ ] **Step 2: Back up the live site before changing it**

Run:
```bash
ssh -o BatchMode=yes activitycontext.work 'cd /var/www && tar czf ~/backup-wamason-$(date -u +%Y%m%d-%H%M%S).tar.gz wamason.com && ls -la ~/backup-wamason-*.tar.gz | tail -1'
```

Expected: a backup tarball is created and its path/size printed. Record the exact filename shown — it's the rollback point if anything goes wrong in the next steps.

- [ ] **Step 3: Deploy the new blog/ directory and the modified pages**

Run (rsync preserves the existing site's other content, only pushes what's new/changed in the local repo):
```bash
rsync -av --itemize-changes \
  /home/tony/projects/wamason.com/blog/ \
  activitycontext.work:/var/www/wamason.com/blog/
```

Then deploy every modified nav page individually (safer than a blanket rsync of the whole repo root, which could pick up files not meant for this migration):

```bash
for f in index.html about/index.html consulting/index.html expert/index.html contact/index.html privacy/index.html hamutay/index.html; do
  scp "/home/tony/projects/wamason.com/$f" "activitycontext.work:/var/www/wamason.com/$f"
done
rsync -av --itemize-changes /home/tony/projects/wamason.com/ayllu/ activitycontext.work:/var/www/wamason.com/ayllu/
```

(The `ayllu/` rsync is safe and additive-only in effect here since Task 7 only added one `<a>` tag per file — no ayllu content was restructured — but confirm with `--itemize-changes` output that only expected files changed, i.e. every changed file is a nav-only edit, before treating this step as done. If `sync-from-live.sh` reports the local ayllu mirror was already behind production before this task started, STOP and re-sync per `ayllu/PUBLISHING.md` first — do not push a stale local ayllu tree over newer live content.)

- [ ] **Step 4: Read the deployed pages back from the live public URLs**

Run:
```bash
curl -s https://wamason.com/blog/ | grep -c 'class="entry"'
curl -s https://wamason.com/blog/the-journey-begins/ | grep -o '<title>[^<]*</title>'
curl -sI https://wamason.com/blog/the-journey-begins/laptop-magnifier-AdobeStock_419775919-Converted.jpg | head -1
curl -s https://wamason.com/ | grep -c 'href="/blog/"'
```

Expected: 26 entries in the index; correct title; `200 OK` for the image; at least 1 for the homepage nav link. If Cloudflare is caching aggressively and results look stale, note it but don't treat as failure — re-check after a minute, or use `curl -H "Cache-Control: no-cache"`.

- [ ] **Step 5: Screenshot the actual live page with Playwright for final visual confirmation**

```bash
cd /tmp/claude-1000/-home-tony-projects-wamason-com/49ef2457-7d01-4d4e-a6c5-28e2c1aa6382/scratchpad/browser-tools
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://wamason.com/blog/');
  await page.screenshot({ path: 'live-blog-index.png', fullPage: true });
  await page.goto('https://wamason.com/blog/the-evolution-of-copyright-law-from-quill-to-code/');
  await page.screenshot({ path: 'live-blog-post.png', fullPage: true });
  await browser.close();
  console.log('done');
})();
"
```

Read both screenshots to visually confirm the live site matches what was verified locally in Task 5.

- [ ] **Step 6: No git commit** — deployment is not a repo change. The repo was already committed in Tasks 6/7; this step only pushed those already-committed files to production.

---

## Task 9: Apache redirects for old WordPress URLs

**Files:**
- Modify (on production host, not in this repo): `/etc/apache2/sites-available/wamason.com-le-ssl.conf` (confirmed as the active HTTPS vhost serving this site)

**Interfaces:** none — this is server configuration, not application code.

- [ ] **Step 1: Read the current vhost config**

Run: `ssh -o BatchMode=yes activitycontext.work 'cat /etc/apache2/sites-available/wamason.com-le-ssl.conf'`

Identify the `<VirtualHost>` block and a sensible insertion point — immediately after the `<Directory /var/www/wamason.com>` block closes, before `</VirtualHost>`, is the conventional placement for `RedirectMatch` directives.

- [ ] **Step 2: Draft the redirect rules and show the diff to Tony before applying**

For each of the 17 published posts, the old URL is `/YYYY/MM/DD/<slug>/` (zero-padded month/day, from the post's `wp:post_date`). Build the block:

```apache
    # Old WordPress date-based blog URLs -> new /blog/<slug>/ (added 2026-07-30)
    RedirectMatch 301 "^/2019/05/22/the-journey-begins/?$" "/blog/the-journey-begins/"
    RedirectMatch 301 "^/2019/07/01/us7069546/?$" "/blog/us7069546/"
    RedirectMatch 301 "^/2021/11/15/meta-data/?$" "/blog/meta-data/"
    RedirectMatch 301 "^/2022/01/17/improving-patent-family-value/?$" "/blog/improving-patent-family-value/"
    RedirectMatch 301 "^/2022/02/18/effective-mechanisms-for-authorship-determination/?$" "/blog/effective-mechanisms-for-authorship-determination/"
    RedirectMatch 301 "^/2022/02/24/blockchain/?$" "/blog/blockchain/"
    RedirectMatch 301 "^/2022/05/02/blockchain-fad-for-innovative-technology/?$" "/blog/blockchain-fad-for-innovative-technology/"
    RedirectMatch 301 "^/2022/05/06/winsorizing-how-to-complicate-a-simple-idea/?$" "/blog/winsorizing-how-to-complicate-a-simple-idea/"
    RedirectMatch 301 "^/2022/08/10/why-the-narrative-meta-data-tells-should-concern-legal-professionals/?$" "/blog/why-the-narrative-meta-data-tells-should-concern-legal-professionals/"
    RedirectMatch 301 "^/2022/10/31/why-daylight-savings-time-matters/?$" "/blog/why-daylight-savings-time-matters/"
    RedirectMatch 301 "^/2023/06/07/media-recycling-in-the-fat-file-system/?$" "/blog/media-recycling-in-the-fat-file-system/"
    RedirectMatch 301 "^/2023/08/18/what-does-it-mean-to-be-a-duplicate/?$" "/blog/what-does-it-mean-to-be-a-duplicate/"
    RedirectMatch 301 "^/2024/03/11/why-sites-ask-you-to-reset-your-password/?$" "/blog/why-sites-ask-you-to-reset-your-password/"
    RedirectMatch 301 "^/2024/04/29/social-media-fraud-beware-the-deep-fake/?$" "/blog/social-media-fraud-beware-the-deep-fake/"
    RedirectMatch 301 "^/2024/07/30/copyright-in-the-world-of-generative-artificial-intelligence-ai/?$" "/blog/copyright-in-the-world-of-generative-artificial-intelligence-ai/"
    RedirectMatch 301 "^/2024/08/09/the-evolution-of-copyright-law-from-quill-to-code/?$" "/blog/the-evolution-of-copyright-law-from-quill-to-code/"
```

That's 15 lines — count the Post Manifest's 17 published posts again: `the-journey-begins`, `us7069546`, `meta-data`, `improving-patent-family-value`, `effective-mechanisms-for-authorship-determination`, `blockchain`, `blockchain-fad-for-innovative-technology`, `winsorizing-how-to-complicate-a-simple-idea`, `why-the-narrative-meta-data-tells-should-concern-legal-professionals`, `why-daylight-savings-time-matters`, `media-recycling-in-the-fat-file-system`, `what-does-it-mean-to-be-a-duplicate`, `why-sites-ask-you-to-reset-your-password`, `social-media-fraud-beware-the-deep-fake`, `copyright-in-the-world-of-generative-artificial-intelligence-ai`, `the-evolution-of-copyright-law-from-quill-to-code` — that's 16, not 17. Before writing the final block, re-run Task 1's `parse_posts()` output and cross-check every published slug against this list; add whichever one is missing (cross-check against the full script printout from Task 1 Step 2, don't guess which one it is from memory).

Show the complete diff (old vhost content vs. new, with the redirect block inserted) to Tony as a plain message — do not apply yet.

- [ ] **Step 3: Apply only after Tony's explicit go-ahead on the diff**

```bash
ssh -o BatchMode=yes activitycontext.work 'sudo cp /etc/apache2/sites-available/wamason.com-le-ssl.conf ~/wamason.com-le-ssl.conf.bak-$(date -u +%Y%m%d-%H%M%S)'
```

Then edit the file on the remote host (via `ssh ... 'sudo ...'` with a heredoc, or by copying an edited local copy up with `scp` + `sudo mv` — whichever the available sudo permissions allow; check with `ssh activitycontext.work 'sudo -n true 2>&1'` first to see if passwordless sudo is available or if Tony needs to type a password interactively, in which case hand him the exact commands to run via the `!` prefix instead of attempting it in-band).

- [ ] **Step 4: Test config and reload**

```bash
ssh -o BatchMode=yes activitycontext.work 'sudo apache2ctl configtest'
```

Expected: `Syntax OK`. Only then:

```bash
ssh -o BatchMode=yes activitycontext.work 'sudo systemctl reload apache2'
```

- [ ] **Step 5: Verify redirects work**

```bash
curl -sI https://wamason.com/2019/05/22/the-journey-begins/ | head -3
curl -sI https://wamason.com/2024/08/09/the-evolution-of-copyright-law-from-quill-to-code/ | head -3
```

Expected: `HTTP/2 301` and a `location:` header pointing at `/blog/<slug>/` for each. Spot check 2-3 more from the full list, and confirm a non-post date-like URL still 404s normally: `curl -sI https://wamason.com/2020/01/01/nonexistent/ | head -1` should show `404`.

- [ ] **Step 6: No git commit** — this task modifies production server config only, not repo content.

---

## Self-Review Notes

**Spec coverage check:** every section of `docs/superpowers/specs/2026-07-30-blog-migration-design.md` maps to a task — Scope (Tasks 1, 6), Site structure (Tasks 4, 6, 7), Visual design (Task 4), Content conversion (Task 2), Images (Tasks 2, 3), Metadata (Task 4), Redirects (Task 9), Deployment (Task 8). The spec's "ask, don't improvise" rule for unresolved images is implemented literally in Task 3's `extract_image`/`verify_all_images_resolve`.

**Known gap intentionally left open:** Task 9 Step 2 contains a deliberately-surfaced counting discrepancy (16 listed vs. 17 expected) rather than a silently-resolved one — this is real: the plan was written against the Post Manifest table, and the exact 17th slug should be re-derived from the live script output at execution time rather than guessed here, since guessing wrong would silently omit a redirect. Whoever executes Task 9 must resolve this by running the script, not by editing this plan text to make the count match.
