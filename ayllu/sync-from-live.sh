#!/usr/bin/env bash
# Pull the deployed site back into this repository, and check the ayllu
# index for orphans and dangling links.
#
# This script only ever moves data LIVE -> LOCAL. It never writes to the
# server. That asymmetry is deliberate; see PUBLISHING.md. The dangerous
# direction is local -> live, and it stays manual.
#
# Usage:
#   ./sync-from-live.sh          pull, then report
#   ./sync-from-live.sh --check  report only, change nothing
set -euo pipefail

HOST="activitycontext.work"
REMOTE="/var/www/wamason.com"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check_only=0
[[ "${1:-}" == "--check" ]] && check_only=1

echo "== ayllu integrity, on the LIVE site =="
ssh -o BatchMode=yes "$HOST" bash -s <<'REMOTE_EOF'
set -euo pipefail
cd /var/www/wamason.com/ayllu
grep -o 'href="/ayllu/[a-z0-9-]*/"' index.html | sed 's|href="/ayllu/||; s|/"||' | sort -u > /tmp/_idx.txt
ls -d */ 2>/dev/null | sed 's|/$||' | sort -u > /tmp/_dirs.txt
orphans=$(comm -13 /tmp/_idx.txt /tmp/_dirs.txt || true)
dangling=$(comm -23 /tmp/_idx.txt /tmp/_dirs.txt || true)
if [[ -n "$orphans" ]]; then
  echo "  ORPHANS — published but not linked from the index (invisible to readers):"
  echo "$orphans" | sed 's/^/    /'
else
  echo "  orphans:  none"
fi
if [[ -n "$dangling" ]]; then
  echo "  DANGLING — linked from the index but no directory (404 for readers):"
  echo "$dangling" | sed 's/^/    /'
else
  echo "  dangling: none"
fi
# Count only inside the entry list. A naive grep over the whole file also
# matches the string where it appears in the page's own search script.
printf '  entries:  %s\n' "$(sed -n '/<ul class="entry-list">/,/<\/ul>/p' index.html | grep -c '<li class="entry">')"
REMOTE_EOF

echo
echo "== content drift: stones that differ between live and local =="
# Orphan/dangling checks find stones that are PRESENT or ABSENT. They
# cannot see a stone whose content CHANGED -- and on 2026-09-06 an
# instance amended a published note in place, adding a postscript. If
# such an edit is deployed but never committed, the mirror diverges
# silently and the next deploy overwrites it with the older text. That is
# the trap this file opens with, moved from missing directories to
# changed files.
_lv=$(mktemp); _lc=$(mktemp)
ssh -o BatchMode=yes "$HOST" \
  "cd $REMOTE && find . -name index.html -type f -exec md5sum {} +" \
  2>/dev/null | sed 's|\./||' | awk '{print $2" "$1}' | sort > "$_lv"
( cd "$REPO" && find . -name index.html -type f -not -path './.git/*' \
  -exec md5sum {} + ) | sed 's|\./||' | awk '{print $2" "$1}' | sort > "$_lc"

drift=$(join "$_lc" "$_lv" | awk '$2 != $3 {print $1}')
if [[ -n "$drift" ]]; then
  echo "  DRIFT — these pages differ between the repository and the server:"
  echo "$drift" | sed 's/^/    /'
  echo "  Inspect before syncing. If the server is ahead, an instance"
  echo "  deployed an edit it never committed. If the repository is"
  echo "  ahead, a deploy is pending."
else
  echo "  drift:    none"
fi
rm -f "$_lv" "$_lc"

if (( check_only )); then
  echo
  echo "(--check: nothing was pulled)"
  exit 0
fi

echo
echo "== pulling live -> local =="
# Additive only. No --delete: a file that exists locally and not on the
# server is a question for a human, not something a sync should silently
# resolve by deleting it.
rsync -a --itemize-changes \
  --exclude '.git' --exclude '*.bak-*' \
  "$HOST:$REMOTE/" "$REPO/" | sed 's/^/  /' || true

echo
echo "== repository state =="
cd "$REPO"
git status --short | sed 's/^/  /'
echo
echo "Review, then commit. Suggested message for a new field note:"
echo "  Add ayllu entry: <Title>, by <Name>"
echo "Or, for a catch-up sync:"
echo "  Sync repo with deployed site"
