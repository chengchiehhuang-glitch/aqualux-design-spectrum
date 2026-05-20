#!/usr/bin/env python3
"""Generate remaining 33 SKILL.md files via Gemini 2.5 Flash (OpenRouter).
Skips files that already have real content (>100 lines, no status: drafting).
"""
import os, sys, json, time
from pathlib import Path
from urllib import request, error

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
TEMPLATE = (ROOT / "skills/c14.md").read_text(encoding="utf-8")
BRAND = (Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/brand-guidelines.md")).read_text(encoding="utf-8")
SKILLS_DIR = ROOT / "skills"
LOG = ROOT / "scripts/gen-skills-gemini.log"

# 33 styles to write
STYLES = [
    # Design — 18 (excludes c01,c02,c03,c05,c06,c07 already done by Batch 1; c14 was always real)
    ('c04', 'mainstream', '主流 UI', '極簡主義', 'Minimalism', '大量留白、單色字體、編輯級排版；prompts.aqualux.dev 同源風格'),
    ('c08', 'retro', '復古懷舊', '90s Web 1.0', 'Web 1.0', '系統字、tile 平鋪、灰色按鈕、default-blue 連結；1996 風'),
    ('c09', 'retro', '復古懷舊', '美式復古印刷', 'American Retro Print', '網點質感、油墨偏色、粗襯線標題；1970s 海報'),
    ('c10', 'retro', '復古懷舊', '80s Synthwave', 'Synthwave', '霓虹線、紫紅落日、透視格線；80s 數位'),
    ('c11', 'retro', '復古懷舊', '包浩斯', 'Bauhaus', '紅黃藍三原色 + 圓三角方塊；1920s 德國學院'),
    ('c12', 'experimental', '實驗前衛', '野獸派', 'Brutalism', '裸露結構、強對比、粗暴排版；反 UX'),
    ('c13', 'experimental', '實驗前衛', '故障藝術', 'Glitch Art', 'RGB 錯位、掃描線、隨機破碎；數位失真'),
    ('c15', 'experimental', '實驗前衛', '構成主義', 'Constructivism', '紅黑斜切、宣傳海報語法；俄式前衛'),
    ('c16', 'experimental', '實驗前衛', 'ASCII 終端機', 'ASCII Terminal', '綠 phosphor、ASCII art、80×24 終端機網格'),
    ('c17', 'experimental', '實驗前衛', '雜誌排版', 'Editorial Magazine', '12 欄網格、粗襯線標題、圖文混排；Monocle 風'),
    ('c18', 'cultural', '文化在地', '日式禪意', 'Wabi-Sabi', '米色紙質、墨筆觸、不完美留白；侘寂'),
    ('c19', 'cultural', '文化在地', '中國風國潮', 'Chinoiserie / Guochao', '硃紅、墨黑、宋體、水墨點綴；中式古典 + 當代潮流'),
    ('c20', 'cultural', '文化在地', '北歐極簡', 'Scandinavian', '木質暖灰、無襯線清爽、北歐插畫'),
    ('c21', 'cultural', '文化在地', '瑞士國際風格', 'Swiss International', '左對齊網格、Helvetica、紅色強調；二戰後排版革命'),
    ('c22', 'cultural', '文化在地', '台灣廟會', 'Taiwan Temple Carnival', '霓虹招牌、紅黃對比、民俗符號；在地熱鬧'),
    ('c23', 'decorative', '裝飾性', '等距 3D', 'Isometric 3D', '30 度斜角立體、玩具世界、小人物'),
    ('c24', 'decorative', '裝飾性', '手繪塗鴉', 'Hand-Drawn Sketch', '蠟筆、歪斜手寫、隨意箭頭'),
    ('c25', 'decorative', '裝飾性', '漸層 Mesh', 'Gradient Mesh', '液態極光漸層、柔光球體'),
    # Motion — 15
    ('m26', 'motion', '動態-視差', '多層視差', 'Parallax Layers', 'scroll-driven 多層 translateY；技術重點：scroll-handler + transform GPU'),
    ('m27', 'motion', '動態-視差', 'Sticky 堆疊章節', 'Sticky Stack', '章節先 sticky 再被下一章從底部疊上；Apple AirPods 風'),
    ('m28', 'motion', '動態-視差', '橫向滾動陣容', 'Horizontal Scroll', '垂直滾動 → 橫向 translate；position:sticky + transform'),
    ('m29', 'motion', '動態-滾動', '全屏章節切換', 'Scroll Snap Acts', 'scroll-snap-type:y mandatory + scroll-snap-align:start'),
    ('m30', 'motion', '動態-滾動', '滾動進度指示', 'Scroll Progress', '頂部 progress bar + 側邊章節點陣'),
    ('m31', 'motion', '動態-滾動', '滾動跑馬燈', 'Marquee Band', 'requestAnimationFrame + transform translateX 無限循環'),
    ('m32', 'motion', '動態-入場', '錯落淡入', 'Fade Stagger', 'IntersectionObserver + transition-delay 波浪入場'),
    ('m33', 'motion', '動態-入場', '打字機標題', 'Typewriter', 'JS char-by-char + blinking caret'),
    ('m34', 'motion', '動態-入場', '數字爆裂計數', 'Counter Burst', 'requestAnimationFrame + easeOutCubic 0→target'),
    ('m35', 'motion', '動態-循環', '極光漸層流動', 'Aurora Flow', '@keyframes radial-gradient + transform 慢速 loop'),
    ('m36', 'motion', '動態-循環', '漂浮幾何球', 'Floating Orbs', 'CSS animation + sine wave；不同 phase'),
    ('m37', 'motion', '動態-循環', '動態噪點', 'Noise Grain', 'SVG turbulence filter + hue-rotate; film grain'),
    ('m38', 'motion', '動態-指標', '滑鼠光暈', 'Cursor Spotlight', 'mousemove + radial-gradient at (x,y)'),
    ('m39', 'motion', '動態-指標', '3D 傾斜卡片', 'Tilt Cards', 'perspective + rotateX/rotateY based on cursor offset'),
    ('m40', 'motion', '動態-指標', '磁吸按鈕', 'Magnetic CTA', 'linear interpolation toward cursor; touch fallback'),
]

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"
TIMEOUT = 90

# Trim brand guidelines (just include voice + DNA sections) to save tokens
BRAND_VOICE_EXCERPT = BRAND[:4000]


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        from datetime import datetime
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    print(msg, flush=True)


def needs_gen(slug):
    """Return True if the file is still a stub."""
    f = SKILLS_DIR / f"{slug}.md"
    if not f.exists():
        return True
    text = f.read_text(encoding="utf-8")
    return ("status: drafting" in text) or (len(text.splitlines()) < 100)


def gen_skill(slug, cluster, category, zh, en, notes):
    if not needs_gen(slug):
        log(f"  ✓ {slug} (already real, skip)")
        return True

    is_motion = cluster == 'motion'

    prompt = f"""你正在為 aqualux 2026 設計光譜展 codex 撰寫一份 SKILL.md 規格檔。

## 任務目標
完整撰寫一份 SKILL.md 給設計風格 **{slug}** ({zh} / {en})，**完全 follow** 下方 c14 賽博龐克 SKILL.md 的 13 個 section 結構，但所有視覺語彙改用 {en} 的真實 signature 視覺。

## 設計風格 metadata
- Slug: {slug}
- Cluster: {cluster}
- Category: {category}
- 中文名: {zh}
- 英文名: {en}
- 風格提示: {notes}
- 類型: {'motion effect (技術 / 動態實作 為主)' if is_motion else 'visual design style (色票 + 字型 + 視覺語彙 為主)'}

---

## 範本（請完全 follow 結構）

{TEMPLATE}

---

## aqualux 品牌語氣參考（摘錄）

{BRAND_VOICE_EXCERPT}

---

## 撰寫要求（嚴格遵守）

1. **完全 follow c14 的 13 個 section 結構**：
   - frontmatter（name, slug, cluster, category, edition: aqualux-2026, license）
   - `# {{ID}} · {zh} / {en}` 標題 + 簡介
   - `## 用法（給 Claude Code 使用者）`
   - `## 視覺語彙`（含 ### 色票、### 字型系統、### 動態效果、### 構圖原則）{'但 motion effect 偏向動態實作規範' if is_motion else ''}
   - `## 頁面結構（8 區段）`
   - `## 圖片生成（gpt-image-2，{'1-2 個示意' if is_motion else '5-10 個'}）`
   - `## 內容（虛構展覽資訊）` — 保留 c14 既定：aqualux 2026 設計光譜展 / 2026.12.06–12.21 / 松山文創 5 號倉庫 / 12 設計師 / 5 展區
   - `## 文案 voice`
   - `## 互動行為`
   - `## a11y / 性能`
   - `## 部署`
   - `## 衍生提示`
   - `**版本記錄**`

2. **原創**：純從 {en} 設計流派的公開知識撰寫、不參照任何外部站

3. **行數**：150-220 行

4. **色票**：用 {en} 的真實 signature hex 值；給 5-10 個 CSS variables

5. **字型**：web-safe 且反映 {en} 風格

6. **a11y**：必含 prefers-reduced-motion 處理

7. **語氣**：策展型 + Operator 視角；avoid「EMBA」、「已取得授權」、「Casper」字樣

8. **輸出格式**：只回 SKILL.md 完整內容（從 `---` frontmatter 開頭、到「**版本記錄**」結尾）。**不要包 markdown code fence**、**不要前言或後語**。

開始寫："""

    try:
        api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
        if not api_key:
            log(f"  ✗ {slug}: OPENROUTER_API_KEY missing")
            return False

        req_body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000,
            "temperature": 0.7,
        }).encode("utf-8")
        req = request.Request(
            API_URL,
            data=req_body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if 'choices' not in data or not data['choices']:
            log(f"  ✗ {slug}: no choices in response — {str(data)[:200]}")
            return False

        content = data['choices'][0]['message']['content'].strip()

        # Strip markdown code fence if Gemini added one
        if content.startswith("```"):
            lines = content.split('\n')
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = '\n'.join(lines).strip()

        if not content.startswith("---"):
            log(f"  ✗ {slug}: bad format (no frontmatter)")
            return False

        line_count = len(content.splitlines())
        if line_count < 80:
            log(f"  ⚠ {slug}: too short ({line_count} lines), keeping anyway")

        out = SKILLS_DIR / f"{slug}.md"
        out.write_text(content, encoding='utf-8')
        log(f"  ✓ {slug} ({line_count} lines)")
        return True

    except error.HTTPError as e:
        log(f"  ✗ {slug}: HTTP {e.code} — {e.read().decode('utf-8')[:200]}")
        return False
    except Exception as e:
        log(f"  ✗ {slug}: {type(e).__name__}: {str(e)[:200]}")
        return False


# Main
log(f"=== Generating {len(STYLES)} SKILL.md files via Gemini 2.5 Flash ===")
ok = 0
fail = 0
skipped = 0

for s in STYLES:
    if not needs_gen(s[0]):
        skipped += 1
        continue
    result = gen_skill(*s)
    if result:
        ok += 1
    else:
        fail += 1
    time.sleep(1.5)  # rate limit padding

log(f"=== Done: {ok} ok / {fail} fail / {skipped} skipped ===")
log(f"=== Files in {SKILLS_DIR} ===")
