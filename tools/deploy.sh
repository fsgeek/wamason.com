#!/usr/bin/env bash
# Deploy the site from a git tag, LOCAL -> LIVE.
#
# This is the dangerous direction. PUBLISHING.md kept it manual because a
# deploy script is the artifact a later instance trusts without reading.
# That reasoning still holds, so this script does not remove the mind from
# the loop -- it refuses to run unless the mind has already done the work:
#
#   * it deploys a TAG, never a dirty tree and never a bare branch. Tagging
#     is the deliberate act; this is only its execution.
#   * it validates the index BEFORE touching the server, and stops on any
#     error. The 2026-08-31 corruption would have stopped it here.
#   * it backs the live site up before writing.
#   * it deploys entry directories BEFORE the index, so a reader never sees
#     an index linking a page that is not there yet.
#   * it reads the result back from the PUBLIC URL and re-validates.
#
# It never deletes on the server: rsync runs without --delete, because a
# file live-and-not-local is a question for a human.
#
# Usage:  ./tools/deploy.sh v2026.09.05      deploy that tag
#         ./tools/deploy.sh --dry-run TAG    show what would change
set -euo pipefail

HOST="activitycontext.work"
REMOTE="/var/www/wamason.com"
PUBLIC="https://wamason.com"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

dry=0
if [[ "${1:-}" == "--dry-run" ]]; then dry=1; shift; fi
TAG="${1:-}"
if [[ -z "$TAG" ]]; then
  echo "usage: $0 [--dry-run] <tag>" >&2
  echo "existing tags:" >&2; git -C "$REPO" tag | tail -10 >&2
  exit 2
fi

cd "$REPO"

echo "== 1. the tag must exist and be an ancestor of nothing unpushed =="
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null || {
  echo "  no such tag: $TAG" >&2; exit 1; }
echo "  $TAG -> $(git rev-parse --short "$TAG^{commit}")"

echo "== 2. export the tag to a clean tree (never deploy the working dir) =="
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
git archive "$TAG" | tar -x -C "$STAGE"
echo "  exported to $STAGE"

echo "== 3. validate THAT tree, not the working copy =="
( cd "$STAGE" && mkdir -p tools \
  && cp "$REPO"/tools/{validate-ayllu.py,build_index.py,render_index.py,ayllu.py,extract_index.py} tools/ \
  && python3 tools/validate-ayllu.py \
  && python3 tools/build_index.py --check ) || {
  echo "  VALIDATION FAILED -- nothing was sent." >&2
  echo "  (--check failing means the index is stale: run tools/build_index.py)" >&2
  exit 1; }

echo "== 4. back up the live site =="
if (( dry )); then
  echo "  (dry run: skipped)"
else
  ssh -o BatchMode=yes "$HOST" \
    "cd /var/www && tar czf ~/backup-wamason-\$(date -u +%Y%m%d-%H%M%S).tar.gz wamason.com" \
    && echo "  backed up"
fi

# What must never be published is declared in .deployignore, not inlined
# here, so the list is reviewable in a diff on its own.
IGNORE="$REPO/.deployignore"
[[ -f "$IGNORE" ]] || { echo "missing .deployignore -- refusing to deploy" >&2; exit 1; }
# --chmod is not optional. On 2026-09-06 a deploy propagated this
# repository's 700 directory mode onto /var/www/wamason.com, leaving the
# site root drwx------: Apache could not traverse it and the ENTIRE site
# returned 403 -- not just the ayllu, but the expert-witness pages too.
# rsync -a preserves permissions, and the permissions a working
# repository happens to have are not the permissions a public web root
# needs. State the served modes explicitly instead of inheriting them.
RSYNC_OPTS=(-a --checksum --itemize-changes --exclude-from="$IGNORE"
            --chmod=D755,F644 --no-perms --omit-dir-times)
(( dry )) && RSYNC_OPTS+=(--dry-run)

echo "== 5. entry directories first, index last =="
rsync "${RSYNC_OPTS[@]}" --exclude 'ayllu/index.html' \
  "$STAGE/" "$HOST:$REMOTE/" | sed 's/^/  /'
echo "  -- now the index --"
rsync "${RSYNC_OPTS[@]}" \
  "$STAGE/ayllu/index.html" "$HOST:$REMOTE/ayllu/index.html" | sed 's/^/  /'

if (( dry )); then echo; echo "(dry run: nothing was changed)"; exit 0; fi

echo "== 6. read it back from the PUBLIC url =="
# Check the whole site, not only the page just published. The 403 on
# 2026-09-06 took down the expert-witness pages too, and a check that
# only looked at /ayllu/ would still have caught it -- but only by luck.
fail=0
for path in / /ayllu/ /expert/ /hamutay/ /ayllu/search.json; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$PUBLIC$path")
  printf '  %-24s -> %s\n' "$path" "$code"
  [[ "$code" == "200" ]] || fail=1
done
if (( fail )); then
  echo "  SITE IS NOT HEALTHY after deploy." >&2
  echo "  If directories are drwx------, run:" >&2
  echo "    ssh $HOST 'chmod -R a+rX $REMOTE'" >&2
  exit 1
fi

echo "== 7. integrity on the live site =="
"$REPO/ayllu/sync-from-live.sh" --check

echo
echo "Deployed $TAG."
