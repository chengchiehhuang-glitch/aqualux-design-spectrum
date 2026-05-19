#!/bin/bash
# Wait for thumb generation to finish, then commit + push.
set -e

ROOT="$HOME/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum"
cd "$ROOT"

LOG="scripts/wait-and-deploy.log"
echo "[$(date +%H:%M:%S)] Watcher started" > "$LOG"

# Wait until gen-thumbs.py finishes (max 30 min)
DEADLINE=$(($(date +%s) + 1800))
while pgrep -f "gen-thumbs.py" > /dev/null 2>&1; do
  if [ $(date +%s) -gt $DEADLINE ]; then
    echo "[$(date +%H:%M:%S)] ❌ Watcher timeout (30 min)" >> "$LOG"
    exit 1
  fi
  COUNT=$(ls images/thumbs/ 2>/dev/null | wc -l | tr -d ' ')
  echo "[$(date +%H:%M:%S)] generating... $COUNT/40 thumbs done" >> "$LOG"
  sleep 30
done

FINAL_COUNT=$(ls images/thumbs/ 2>/dev/null | wc -l | tr -d ' ')
echo "[$(date +%H:%M:%S)] ✅ Generation finished: $FINAL_COUNT/40 thumbs" >> "$LOG"

if [ "$FINAL_COUNT" -lt 35 ]; then
  echo "[$(date +%H:%M:%S)] ❌ Only $FINAL_COUNT/40 thumbs — aborting auto-push, manual review needed" >> "$LOG"
  exit 1
fi

# Stage + commit + push
echo "[$(date +%H:%M:%S)] git add + commit + push..." >> "$LOG"
git add images/thumbs/ index.html scripts/

# Check if there's actually something to commit
if git diff --cached --quiet; then
  echo "[$(date +%H:%M:%S)] (no changes to commit)" >> "$LOG"
  exit 0
fi

git commit -m "$(cat <<'EOF'
Add 40 gallery thumbnails (gpt-image-2 generated)

Each card now displays a style-representative thumbnail image:
- C01-C25: 25 design style thumbs (low quality, $0.006/each, ~$0.15 total)
- C26-C40: 15 motion effect thumbs (m26-m40.png filename pattern)
- HTML uses <img> with onerror fallback so missing thumbs degrade gracefully
- New CSS rules layer cat-tag/id-num over the image with backdrop-blur badges

Inspired by Casper's casper.tw layout pattern (with permission); all 40
thumbnail images are aqualux original generations via gpt-image-2.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git push origin main 2>&1 | tee -a "$LOG"

echo "[$(date +%H:%M:%S)] ✅ Pushed. Netlify will auto-deploy in ~30s." >> "$LOG"

# Optional: poll Netlify for deploy success (max 5 min)
SITE="f66f1cb3-54dd-4b43-89eb-7bee976791bc"
DEADLINE=$(($(date +%s) + 300))
sleep 30
while [ $(date +%s) -lt $DEADLINE ]; do
  STATE=$(netlify api listSiteDeploys --data "{\"site_id\":\"$SITE\"}" 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0].get('state','?') if d else '?')" 2>/dev/null || echo "?")
  echo "[$(date +%H:%M:%S)] Netlify state=$STATE" >> "$LOG"
  if [ "$STATE" = "ready" ]; then
    echo "[$(date +%H:%M:%S)] 🟢 Deploy ready: https://design.aqualux.dev/" >> "$LOG"
    break
  fi
  if [ "$STATE" = "error" ]; then
    echo "[$(date +%H:%M:%S)] ❌ Deploy error — check Netlify dashboard" >> "$LOG"
    break
  fi
  sleep 20
done

echo "[$(date +%H:%M:%S)] === Watcher done ===" >> "$LOG"
