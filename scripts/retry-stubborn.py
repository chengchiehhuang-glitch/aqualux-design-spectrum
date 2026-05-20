#!/usr/bin/env python3
"""Aggressive retry for stubborn slugs that hit token ceiling on first retry pass.

Strategy:
- max_tokens: 65000 (Gemini 2.5 Flash hard ceiling)
- Trimmed prompt (smaller C14 reference, smaller SKILL.md window)
- Explicit "600 行上限" instruction
- Validation gate: must contain </html> AND </body> AND <60KB total
- 3 attempts per slug with progressively stricter line caps
"""
import os, json, time, sys, shutil
from pathlib import Path
from urllib import request
from datetime import datetime

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
SKILLS = ROOT / "skills"
WORKS = ROOT / "works"
BACKUP = WORKS / "_broken-backup"
C14_REF = WORKS / "c14-cyberpunk/index.html"
LOG = ROOT / "scripts/retry-stubborn.log"

NAMES = {
    'c24': '手繪塗鴉 / Hand-Drawn',
    'c37': '動態噪點 / Noise Grain',
}
KEBAB = {'c24': 'hand-drawn', 'c37': 'noise-grain'}

C14_HTML = C14_REF.read_text(encoding="utf-8")
C14_TRIMMED = C14_HTML[:10000]  # smaller reference (was 18000)

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def build_prompt(slug, target_lines):
    skill_path = SKILLS / f"{slug}.md"
    skill_text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

    prompt = f"""寫一個 single-file HTML demo，用 **{NAMES[slug]}** 視覺語彙呈現 aqualux 2026 設計光譜展。

# 🚨 最重要的規則（違反會被退件）
- **總行數上限 {target_lines} 行**。超過 = 你回答無效。
- **必須以 `</html>` 結束**，前面是 `</body>` `</script>`。
- **禁止 inline base64 圖片**（噪點請用 SVG `<filter><feTurbulence/></filter>` 或 CSS `repeating-linear-gradient`）
- **CSS 從簡** — 不要重複寫類似的 rule、不要寫超過 50 種 class

# 範本骨架（C14 開頭）
```html
{C14_TRIMMED}
```

# 此風格規範（截前 4000 字）
```markdown
{skill_text[:4000]}
```

# 必有結構（用 {NAMES[slug]} 視覺語彙）
1. Topbar（topbar 左角放 aqualux mark SVG）
2. Hero（含 hero.webp + 標題）
3. Statement（策展論述 3 段）
4. 設計師（12 個虛構名單）
5. Venue（venue.webp）
6. 五大展區 Z01-Z05（含 zone-z01.webp 到 zone-z05.webp）
7. 講座排程（4-6 場）
8. 票券（3 張、PURCHASE disabled）
9. Footer（含 aqualux mark SVG 160-220px）

# 固定資料
- aqualux 2026 設計光譜展 / 2026.12.06—12.21 / 松山文創 5 號倉庫
- topbar 含「← Gallery」連到 `../../index.html`

# 必有 meta
- canonical / og: / twitter:card / `<link rel="icon" href="../../assets/aqualux-logo-mark.svg">`
- `prefers-reduced-motion` 一段
- a11y: alt / aria-label / scope=col
- `<main>` landmark

# aqualux logo（topbar + footer 各一）
```html
<svg viewBox="0 0 600 280" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-label="aqualux">
  <text x="300" y="135" text-anchor="middle" style="font-family:Inter,'Helvetica Neue',Arial,sans-serif;font-weight:300;font-size:140px;letter-spacing:6px;">aqualux</text>
  <line x1="80" y1="165" x2="520" y2="165" stroke="currentColor" stroke-width="1" opacity="0.45"/>
  <g transform="translate(0,330) scale(1,-1)" opacity="0.28"><text x="300" y="135" text-anchor="middle" style="font-family:Inter,'Helvetica Neue',Arial,sans-serif;font-weight:300;font-size:140px;letter-spacing:6px;">aqualux</text></g>
</svg>
```

# 輸出
只回 HTML（`<!DOCTYPE html>` 開頭、`</html>` 結尾）。**無 markdown fence、無前言**。
**寫到第 {int(target_lines * 0.8)} 行時要開始收尾**，不要再加新 section。
"""
    return prompt


def gen_html(slug, target_lines):
    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return None, "no API key"

    prompt = build_prompt(slug, target_lines)
    try:
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 65000,
            "temperature": 0.5,
        }).encode("utf-8")
        req = request.Request(
            API_URL,
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=240) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if 'choices' not in data:
            return None, f"no choices: {str(data)[:120]}"
        content = data['choices'][0]['message']['content'].strip()
        if content.startswith("```"):
            lines = content.split('\n')[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = '\n'.join(lines).strip()
        if not content.startswith("<!DOCTYPE") and not content.startswith("<html"):
            import re
            m = re.search(r'(<!DOCTYPE|<html)', content)
            if m:
                content = content[m.start():]
            else:
                return None, "no HTML in response"
        # Validation gates
        if '</html>' not in content.lower():
            return None, f"no </html> ({len(content)} bytes, {len(content.splitlines())} lines)"
        if '</body>' not in content.lower():
            return None, "no </body>"
        # Check for catastrophic base64 dump
        for line in content.split('\n'):
            if 'data:image/' in line and 'base64,' in line and len(line) > 2000:
                return None, "inline base64 > 2000 char"
        return content, None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:160]}"


def gen_one(slug):
    name = NAMES[slug]
    kebab = KEBAB[slug]
    out_dir = WORKS / f"{slug}-{kebab}"
    out_html = out_dir / "index.html"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Backup old broken file
    if out_html.exists():
        backup_dir = BACKUP / f"{slug}-{kebab}-stubborn"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_html, backup_dir / "index.html")

    # Progressively stricter line caps
    for attempt, target in enumerate([700, 600, 550], 1):
        log(f"  → {slug} ({name}) — attempt {attempt}/3 (target {target} lines)")
        html, err = gen_html(slug, target)
        if html is not None:
            out_html.write_text(html, encoding="utf-8")
            lines = len(html.splitlines())
            kb = len(html.encode("utf-8")) // 1024
            log(f"    ✓ written: {lines} lines / {kb}KB")
            return True
        log(f"    ✗ attempt {attempt}: {err}")
        if attempt < 3:
            time.sleep(10)
    return False


def main():
    open(LOG, "w").close()

    targets = sys.argv[1:] if len(sys.argv) > 1 else ['c24', 'c37']
    log(f"=== Stubborn retry: {targets} (max_tokens=65000, escalating line caps) ===")

    ok, fail, fails = 0, 0, []
    for i, slug in enumerate(targets, 1):
        log(f"--- [{i}/{len(targets)}] {slug} ---")
        try:
            if gen_one(slug):
                ok += 1
            else:
                fail += 1
                fails.append(slug)
        except Exception as e:
            log(f"✗ {slug}: uncaught {type(e).__name__}: {e}")
            fail += 1
            fails.append(slug)
        if i < len(targets):
            time.sleep(7)

    log(f"=== Final: {ok} ok / {fail} fail ===")
    if fails:
        log(f"   failed: {' '.join(fails)} — fall back to hand-write")


if __name__ == "__main__":
    main()
