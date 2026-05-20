#!/usr/bin/env python3
"""Generate 39 demo sub-pages in background.

For each style (c01-c40 except c14):
1. Read its SKILL.md
2. Call Gemini Flash → write single-file HTML demo (works/{slug}/index.html)
3. Generate ~6 images via gpt-image-2 (works/{slug}/images/*.png → .webp)
4. Mark as complete in progress log

Watcher commits every 6 demos.
"""
import os, json, time, subprocess, re, sys
from pathlib import Path
from urllib import request, error
from datetime import datetime

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
SKILLS = ROOT / "skills"
WORKS = ROOT / "works"
C14_REF = WORKS / "c14-cyberpunk/index.html"
LOG = ROOT / "scripts/gen-all-demos.log"

# 39 slugs (c01-c40 except c14)
SLUGS = (
    [f"c{n:02d}" for n in range(1, 14)]
    + [f"c{n:02d}" for n in range(15, 26)]
    + [f"c{n}" for n in range(26, 41)]
)
assert len(SLUGS) == 39

NAMES = {
    'c01': '玻璃擬態 / Glassmorphism', 'c02': '新擬物化 / Neumorphism', 'c03': 'Material You / Material 3',
    'c04': '極簡主義 / Minimalism', 'c05': '沉浸暗黑 / Immersive Dark',
    'c06': '蒸氣波 / Vaporwave', 'c07': 'Y2K 千禧 / Y2K', 'c08': '90s Web 1.0 / Web 1.0',
    'c09': '美式復古印刷 / American Retro Print', 'c10': '80s Synthwave / Synthwave', 'c11': '包浩斯 / Bauhaus',
    'c12': '野獸派 / Brutalism', 'c13': '故障藝術 / Glitch Art',
    'c15': '構成主義 / Constructivism', 'c16': 'ASCII 終端機 / ASCII Terminal', 'c17': '雜誌排版 / Editorial',
    'c18': '日式禪意 / Wabi-Sabi', 'c19': '中國風國潮 / Chinoiserie', 'c20': '北歐極簡 / Scandinavian',
    'c21': '瑞士國際 / Swiss International', 'c22': '台灣廟會 / Taiwan Temple', 'c23': '等距 3D / Isometric 3D',
    'c24': '手繪塗鴉 / Hand-Drawn', 'c25': '漸層 Mesh / Gradient Mesh',
    'c26': '多層視差 / Parallax Layers', 'c27': 'Sticky 堆疊 / Sticky Stack',
    'c28': '橫向滾動 / Horizontal Scroll', 'c29': '全屏切換 / Scroll Snap', 'c30': '滾動進度 / Scroll Progress',
    'c31': '滾動跑馬燈 / Marquee', 'c32': '錯落淡入 / Fade Stagger', 'c33': '打字機 / Typewriter',
    'c34': '數字爆裂 / Counter Burst', 'c35': '極光流動 / Aurora Flow', 'c36': '漂浮幾何 / Floating Orbs',
    'c37': '動態噪點 / Noise Grain', 'c38': '滑鼠光暈 / Cursor Spotlight',
    'c39': '3D 傾斜卡片 / Tilt Cards', 'c40': '磁吸按鈕 / Magnetic CTA',
}

C14_HTML = C14_REF.read_text(encoding="utf-8")
# Trim C14 to ~6k tokens by keeping structure visible
C14_TRIMMED = C14_HTML[:18000]  # ~6k tokens

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def needs_gen(slug):
    f = WORKS / f"{slug}-{slug_to_name_kebab(slug)}" / "index.html"
    if f.exists() and f.stat().st_size > 5000:
        return False
    return True


def slug_to_name_kebab(slug):
    """c01 -> glassmorphism, etc."""
    en_map = {
        'c01':'glassmorphism','c02':'neumorphism','c03':'material-3','c04':'minimalism','c05':'immersive-dark',
        'c06':'vaporwave','c07':'y2k','c08':'web-1','c09':'retro-print','c10':'synthwave','c11':'bauhaus',
        'c12':'brutalism','c13':'glitch','c15':'constructivism','c16':'ascii-terminal','c17':'editorial',
        'c18':'wabi-sabi','c19':'chinoiserie','c20':'scandinavian','c21':'swiss','c22':'taiwan-temple',
        'c23':'isometric-3d','c24':'hand-drawn','c25':'gradient-mesh',
        'c26':'parallax-layers','c27':'sticky-stack','c28':'horizontal-scroll','c29':'scroll-snap',
        'c30':'scroll-progress','c31':'marquee','c32':'fade-stagger','c33':'typewriter','c34':'counter-burst',
        'c35':'aurora-flow','c36':'floating-orbs','c37':'noise-grain','c38':'cursor-spotlight',
        'c39':'tilt-cards','c40':'magnetic-cta',
    }
    return en_map.get(slug, slug)


def gen_html(slug):
    """Call Gemini Flash to write the demo HTML."""
    skill_path = SKILLS / f"{slug}.md"
    if not skill_path.exists():
        return None, "SKILL.md missing"
    skill_text = skill_path.read_text(encoding="utf-8")

    prompt = f"""你正在為 aqualux 2026 設計光譜展 codex 撰寫一個 demo sub-page 的 HTML。

## 任務
寫一個 single-file HTML（含 inline CSS + 必要的 inline JS），用 **{NAMES.get(slug, slug)}** 的視覺語彙呈現 aqualux 2026 設計光譜展。

## 參考 1: 範本骨架（C14 cyberpunk demo 開頭 ~6k tokens）
```html
{C14_TRIMMED}
```
（這只是參考骨架的 1/3。完整 demo 約 800 行。你要按相同 8-section 結構寫但**視覺語彙完全用 {NAMES.get(slug, slug)} 流派**）

## 參考 2: 此風格的 SKILL.md spec
```markdown
{skill_text[:8000]}
```

## 8 個必有區段（同 c14 結構）
1. Topbar（系統狀態列、該流派風格的標題）
2. Hero（大圖 placeholder + 該流派標題字 + meta strip）
3. Statement 策展論述
4. 設計師名單（12 個虛構設計師 — 沿用 c14 的 12 個名字，或可換更貼合此流派）
5. Venue 場地圖（atmospheric placeholder）
6. 五大展區 Z01-Z05
7. 講座排程
8. 票務（3 張價位卡）
9. Footer

## 內容固定（aqualux 既定虛構展覽）
- 名稱：aqualux 2026 設計光譜展
- 日期：2026.12.06 — 12.21
- 場地：松山文創園區 5 號倉庫
- 12 設計師、5 展區、3 票價

## 圖片路徑
所有 <img> 標籤 src 用 `images/{{filename}}.webp`：
- 1 張 hero: `images/hero.webp`
- 1 張 venue: `images/venue.webp`
- 5 張 zone: `images/zone-z01.webp` 到 `zone-z05.webp`

## 要求
- single-file HTML、inline CSS、inline JS（無外部 .css .js）
- ~600-1000 行
- 視覺語彙完全用 {NAMES.get(slug, slug)} 的真實 signature 色票/字型/排版
- `<main>` landmark
- prefers-reduced-motion 完整 CSS
- a11y: alt 文字、aria-label、scope=col 等
- SEO meta: canonical / og: / twitter:card
- 票券 PURCHASE 按鈕 disabled
- topbar 含「← Gallery」回主頁連結指向 `../../index.html`

## 【強制】aqualux logo 嵌入（每個 demo 必有）
此 demo 是 **個人 AI 品牌 aqualux.dev 的推廣 portfolio piece**，aqualux logo 必須以該流派的視覺語彙融入。

具體要求：
- **topbar 左角**：嵌入 aqualux mark SVG（小尺寸 24-32px 高、currentColor 自動跟著該流派 ink 色）
- **footer 中央**：嵌入 aqualux mark SVG（中尺寸 160-220px 寬）+ 「MMXXVI · AQUALUX.DEV」seal
- inline SVG 直接貼下方 markup：

```html
<svg viewBox="0 0 600 280" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-label="aqualux">
  <text x="300" y="135" text-anchor="middle" style="font-family:Inter,'Helvetica Neue',Arial,sans-serif;font-weight:300;font-size:140px;letter-spacing:6px;">aqualux</text>
  <line x1="80" y1="165" x2="520" y2="165" stroke="currentColor" stroke-width="1" opacity="0.45"/>
  <g transform="translate(0,330) scale(1,-1)" opacity="0.28"><text x="300" y="135" text-anchor="middle" style="font-family:Inter,'Helvetica Neue',Arial,sans-serif;font-weight:300;font-size:140px;letter-spacing:6px;">aqualux</text></g>
</svg>
```

- logo 可以放在「白/紙色的小容器」內讓它從各流派的彩底浮出來（如賽博龐克黑底時、玻璃擬態漸層底時）
- 該流派的設計語彙要**融入** logo 呈現方式（如野獸派用 raw concrete 邊框、Bauhaus 加紅黃藍幾何裝飾、瑞士國際對齊 grid）
- logo **不可被流派風格主導**到看不出來、必須清晰可讀

## 輸出
只回 HTML 完整內容（`<!DOCTYPE html>` 開頭、`</html>` 結尾），**無 markdown code fence**、**無前言**。
"""

    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return None, "no API key"
    try:
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 12000,
            "temperature": 0.6,
        }).encode("utf-8")
        req = request.Request(
            API_URL,
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if 'choices' not in data:
            return None, f"no choices: {str(data)[:100]}"
        content = data['choices'][0]['message']['content'].strip()
        # Strip markdown code fence
        if content.startswith("```"):
            lines = content.split('\n')
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = '\n'.join(lines).strip()
        if not content.startswith("<!DOCTYPE") and not content.startswith("<html"):
            # Try to find first HTML tag
            m = re.search(r'(<!DOCTYPE|<html)', content)
            if m:
                content = content[m.start():]
            else:
                return None, "no HTML in response"
        return content, None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"


def gen_images(slug, out_dir):
    """Generate ~7 images via gpt-image-2."""
    out_dir.mkdir(parents=True, exist_ok=True)
    name = NAMES.get(slug, slug)
    en = name.split('/')[-1].strip()
    zh = name.split('/')[0].strip()

    # 7 image specs (hero + venue + 5 zones)
    specs = [
        ("hero", "1536x1024",
         f"A {en} design style scene depicting an aqualux 2026 設計光譜展 exhibition opening. Wide cinematic composition. Centered text 'AQUALUX SPECTRUM 2026' in {en}-appropriate typography. No people. Aspect 3:2."),
        ("venue", "1024x1024",
         f"Gallery interior depicting an exhibition venue in {en} aesthetic. Empty pedestals, soft lighting. No people. Square composition."),
        ("zone-z01", "1024x1024",
         f"Exhibition zone for mainstream UI works, in {en} visual language. Abstract composition. No people. No text. Square."),
        ("zone-z02", "1024x1024",
         f"Exhibition zone for retro works, in {en} visual language. Abstract composition with hint of vintage. No people. No text. Square."),
        ("zone-z03", "1024x1024",
         f"Exhibition zone for avant-garde experiments, in {en} visual language. Abstract experimental composition. No people. No text. Square."),
        ("zone-z04", "1024x1024",
         f"Exhibition zone for cultural design, in {en} visual language. Abstract composition with subtle cultural hint. No people. No text. Square."),
        ("zone-z05", "1024x1024",
         f"Exhibition zone for motion effects, in {en} visual language. Abstract composition with subtle motion. No people. No text. Square."),
    ]

    success = 0
    for name, size, p in specs:
        png_path = out_dir / f"{name}.png"
        webp_path = out_dir / f"{name}.webp"
        if webp_path.exists():
            success += 1
            continue
        try:
            subprocess.run(
                ["genimg", p, "--quality", "low", "--size", size, "--out", str(png_path)],
                capture_output=True, text=True, timeout=180, check=True
            )
            # Convert to webp
            if png_path.exists():
                subprocess.run(["cwebp", "-q", "82", "-quiet", str(png_path), "-o", str(webp_path)],
                              capture_output=True, text=True, timeout=60, check=False)
                png_path.unlink(missing_ok=True)  # Save space
                success += 1
        except subprocess.CalledProcessError as e:
            log(f"    ✗ {name}: {e.stderr[:80] if e.stderr else 'unknown'}")
        except Exception as e:
            log(f"    ✗ {name}: {type(e).__name__}")
        time.sleep(13)  # RPM throttle (5/min)
    return success


def gen_one_demo(slug):
    name = NAMES.get(slug, slug)
    out_dir = WORKS / f"{slug}-{slug_to_name_kebab(slug)}"
    out_html = out_dir / "index.html"
    out_imgs = out_dir / "images"

    # Skip if already done
    if out_html.exists() and out_html.stat().st_size > 5000:
        log(f"  ✓ {slug} ({name}) — already done, skip")
        return True

    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Gen HTML
    log(f"  → {slug} ({name}) — gen HTML...")
    html, err = gen_html(slug)
    if html is None:
        log(f"    ✗ HTML gen failed: {err}")
        return False
    out_html.write_text(html, encoding="utf-8")
    line_count = len(html.splitlines())
    log(f"    ✓ HTML written: {line_count} lines")

    # 2. Gen images
    log(f"  → {slug} — gen images...")
    img_count = gen_images(slug, out_imgs)
    log(f"    ✓ {img_count}/7 images")

    return True


def main():
    open(LOG, "w").close()
    log(f"=== Generating 39 demo sub-pages ===")
    log(f"   target dir: {WORKS}")
    log(f"   est cost: ~$2.30 / est time: ~2-3 hours")

    ok = 0
    fail = 0
    for i, slug in enumerate(SLUGS, 1):
        log(f"--- [{i}/39] {slug} ---")
        try:
            if gen_one_demo(slug):
                ok += 1
            else:
                fail += 1
        except KeyboardInterrupt:
            log("⏸ Interrupted by user")
            break
        except Exception as e:
            log(f"✗ {slug}: uncaught {type(e).__name__}: {e}")
            fail += 1
        log(f"   progress: {ok} ok / {fail} fail")

    log(f"=== Final: {ok} ok / {fail} fail ===")


if __name__ == "__main__":
    main()
