#!/bin/bash
# Wait for gen-skills-gemini.py to finish, then commit + push as Round C.
set -e

ROOT="$HOME/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum"
cd "$ROOT"

LOG="scripts/wait-and-deploy-roundC.log"
echo "[$(date +%H:%M:%S)] Round C watcher started" > "$LOG"

# Wait until gen-skills-gemini.py finishes (max 30 min)
DEADLINE=$(($(date +%s) + 1800))
while pgrep -f "gen-skills-gemini.py" > /dev/null 2>&1; do
  if [ $(date +%s) -gt $DEADLINE ]; then
    echo "[$(date +%H:%M:%S)] ❌ Watcher timeout (30 min)" >> "$LOG"
    exit 1
  fi
  REAL=$(for f in skills/*.md; do
    l=$(wc -l < "$f" | tr -d ' ')
    if [ "$l" -gt 100 ] && ! grep -q "status: drafting" "$f"; then echo 1; fi
  done | wc -l | tr -d ' ')
  echo "[$(date +%H:%M:%S)] generating... $REAL/40 real" >> "$LOG"
  sleep 25
done

# Final tally
REAL=$(for f in skills/*.md; do
  l=$(wc -l < "$f" | tr -d ' ')
  if [ "$l" -gt 100 ] && ! grep -q "status: drafting" "$f"; then echo 1; fi
done | wc -l | tr -d ' ')

echo "[$(date +%H:%M:%S)] ✅ Generation finished: $REAL/40 real SKILL.md files" >> "$LOG"

if [ "$REAL" -lt 35 ]; then
  echo "[$(date +%H:%M:%S)] ❌ Only $REAL/40 — aborting auto-push, manual review needed" >> "$LOG"
  exit 1
fi

# Stage + commit + push
echo "[$(date +%H:%M:%S)] git add + commit + push..." >> "$LOG"
git add skills/ scripts/

if git diff --cached --quiet; then
  echo "[$(date +%H:%M:%S)] (no changes to commit)" >> "$LOG"
  exit 0
fi

git commit -m "$(cat <<'EOF'
Round B+C: 33 remaining SKILL.md files written (Claude Batch 1 + Gemini Flash)

- Batch 1 (Claude Sonnet subagent): c01/c02/c03/c05/c06/c07 (6 files, ~200 lines each)
- Gemini Flash via OpenRouter: 27 remaining (18 design + 9 motion that needed gen)
- All 40 SKILL.md files now have real content (no more "status: drafting" stubs)
- Structure follows c14.md template (13 sections each)
- Original aqualux specs based on public design movement knowledge
- Each skill includes: 視覺語彙 / 頁面結構 / 圖片 gpt-image-2 prompts / a11y / 部署

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" >> "$LOG" 2>&1

git push origin main 2>&1 | tail -3 | tee -a "$LOG"

echo "[$(date +%H:%M:%S)] ✅ Pushed. Netlify will auto-deploy." >> "$LOG"

# Poll Netlify
SITE="f66f1cb3-54dd-4b43-89eb-7bee976791bc"
DEADLINE=$(($(date +%s) + 240))
sleep 25
while [ $(date +%s) -lt $DEADLINE ]; do
  STATE=$(netlify api listSiteDeploys --data "{\"site_id\":\"$SITE\"}" 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0].get('state','?') if d else '?')" 2>/dev/null || echo "?")
  echo "[$(date +%H:%M:%S)] Netlify state=$STATE" >> "$LOG"
  if [ "$STATE" = "ready" ]; then
    echo "[$(date +%H:%M:%S)] 🟢 Round C live: https://design.aqualux.dev/" >> "$LOG"
    break
  fi
  if [ "$STATE" = "error" ]; then
    echo "[$(date +%H:%M:%S)] ❌ Deploy error" >> "$LOG"
    break
  fi
  sleep 15
done

echo "[$(date +%H:%M:%S)] === Round C watcher done ===" >> "$LOG"
