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
