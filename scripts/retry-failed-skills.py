#!/usr/bin/env python3
"""Retry SKILL.md generation for files that still failed (stub or bad format).
Uses stricter prompt with explicit no-preamble instruction.
"""
import os, json, time, sys
from pathlib import Path
from urllib import request, error

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
TEMPLATE = (ROOT / "skills/c14.md").read_text(encoding="utf-8")
SKILLS_DIR = ROOT / "skills"

# Same style list (from gen-skills-gemini.py)
STYLES = {
    'c04': ('mainstream', '主流 UI', '極簡主義', 'Minimalism', '大量留白、單色字體、編輯級排版'),
    'c08': ('retro', '復古懷舊', '90s Web 1.0', 'Web 1.0', '系統字、tile、灰按鈕、default-blue 連結；1996 風'),
    'c09': ('retro', '復古懷舊', '美式復古印刷', 'American Retro Print', '網點質感、油墨偏色、粗襯線標題；1970s 海報'),
    'c10': ('retro', '復古懷舊', '80s Synthwave', 'Synthwave', '霓虹線、紫紅落日、透視格線；80s 數位'),
    'c11': ('retro', '復古懷舊', '包浩斯', 'Bauhaus', '紅黃藍三原色 + 圓三角方塊；1920s 德國學院'),
    'c12': ('experimental', '實驗前衛', '野獸派', 'Brutalism', '裸露結構、強對比、粗暴排版；反 UX'),
    'c13': ('experimental', '實驗前衛', '故障藝術', 'Glitch Art', 'RGB 錯位、掃描線、隨機破碎；數位失真'),
    'c15': ('experimental', '實驗前衛', '構成主義', 'Constructivism', '紅黑斜切、宣傳海報語法；俄式前衛'),
    'c16': ('experimental', '實驗前衛', 'ASCII 終端機', 'ASCII Terminal', '綠 phosphor、ASCII art、80×24 終端機網格'),
    'c17': ('experimental', '實驗前衛', '雜誌排版', 'Editorial Magazine', '12 欄網格、粗襯線標題、圖文混排；Monocle 風'),
    'c18': ('cultural', '文化在地', '日式禪意', 'Wabi-Sabi', '米色紙質、墨筆觸、不完美留白；侘寂'),
    'c19': ('cultural', '文化在地', '中國風國潮', 'Chinoiserie / Guochao', '硃紅、墨黑、宋體、水墨點綴；中式古典 + 當代潮流'),
    'c20': ('cultural', '文化在地', '北歐極簡', 'Scandinavian', '木質暖灰、無襯線清爽、北歐插畫'),
    'c21': ('cultural', '文化在地', '瑞士國際風格', 'Swiss International', '左對齊網格、Helvetica、紅色強調'),
    'c22': ('cultural', '文化在地', '台灣廟會', 'Taiwan Temple Carnival', '霓虹招牌、紅黃對比、民俗符號'),
    'c23': ('decorative', '裝飾性', '等距 3D', 'Isometric 3D', '30 度斜角立體、玩具世界、小人物'),
    'c24': ('decorative', '裝飾性', '手繪塗鴉', 'Hand-Drawn Sketch', '蠟筆、歪斜手寫、隨意箭頭'),
    'c25': ('decorative', '裝飾性', '漸層 Mesh', 'Gradient Mesh', '液態極光漸層、柔光球體'),
    'm26': ('motion', '動態-視差', '多層視差', 'Parallax Layers', 'scroll-driven 多層 translateY'),
    'm27': ('motion', '動態-視差', 'Sticky 堆疊章節', 'Sticky Stack', '章節 sticky 再被下一章疊上'),
    'm28': ('motion', '動態-視差', '橫向滾動陣容', 'Horizontal Scroll', '垂直滾動 → 橫向 translate'),
    'm29': ('motion', '動態-滾動', '全屏章節切換', 'Scroll Snap Acts', 'scroll-snap mandatory'),
    'm30': ('motion', '動態-滾動', '滾動進度指示', 'Scroll Progress', '頂部 progress bar + 側邊章節點陣'),
    'm31': ('motion', '動態-滾動', '滾動跑馬燈', 'Marquee Band', 'requestAnimationFrame + transform 無限循環'),
    'm32': ('motion', '動態-入場', '錯落淡入', 'Fade Stagger', 'IntersectionObserver + transition-delay'),
    'm33': ('motion', '動態-入場', '打字機標題', 'Typewriter', 'JS char-by-char + blinking caret'),
    'm34': ('motion', '動態-入場', '數字爆裂計數', 'Counter Burst', 'requestAnimationFrame + easeOutCubic'),
    'm35': ('motion', '動態-循環', '極光漸層流動', 'Aurora Flow', '@keyframes radial-gradient + transform'),
    'm36': ('motion', '動態-循環', '漂浮幾何球', 'Floating Orbs', 'CSS animation + sine wave'),
    'm37': ('motion', '動態-循環', '動態噪點', 'Noise Grain', 'SVG turbulence + hue-rotate'),
    'm38': ('motion', '動態-指標', '滑鼠光暈', 'Cursor Spotlight', 'mousemove + radial-gradient'),
    'm39': ('motion', '動態-指標', '3D 傾斜卡片', 'Tilt Cards', 'perspective + rotateX/Y'),
    'm40': ('motion', '動態-指標', '磁吸按鈕', 'Magnetic CTA', 'linear interpolation toward cursor'),
}

def needs_retry(slug):
    f = SKILLS_DIR / f"{slug}.md"
    if not f.exists():
        return True
    text = f.read_text(encoding="utf-8")
    return ("status: drafting" in text) or (len(text.splitlines()) < 100)

def gen(slug, meta):
    cluster, category, zh, en, notes = meta
    is_motion = cluster == 'motion'

    prompt = f"""[重要] 嚴格只輸出 markdown SKILL.md 完整內容，**禁止任何前言、後語、解釋、markdown code fence**。

第一個字符必須是 `-`（frontmatter `---` 開頭）。最後一個 section 是 `**版本記錄**`。

撰寫 aqualux 2026 設計光譜展 codex 的 SKILL.md，對應設計風格 {zh} ({en})。

完全 follow c14.md 範本的 13 個 section 結構：frontmatter / 標題 / 用法 / 視覺語彙 / 頁面結構 / 圖片生成 / 內容 / voice / 互動 / a11y / 部署 / 衍生提示 / 版本記錄。

## metadata
- slug: {slug}
- cluster: {cluster}
- category: {category}
- 中文: {zh} / 英文: {en}
- 提示: {notes}
- 類型: {'motion effect (技術實作為主、圖片 1-2 張示意即可)' if is_motion else 'visual style (色票+字型+視覺語彙為主、圖片 5-10 個 prompt)'}

## 範本（請完全 follow 結構）
{TEMPLATE}

## 寫作守則
- 原創、純從 {en} 公開知識撰寫、不參照外部站
- 150-220 行
- 真實 signature hex 色 5-10 個
- web-safe 字型反映 {en}
- 保留 c14 既定虛構展覽（aqualux 2026 設計光譜展 / 12.06–12.21 / 松山文創 5 號倉庫）
- 必含 prefers-reduced-motion
- 不提 EMBA、不提已取得授權、不提 Casper

[再次強調] 第一個字符 `-`，無前言。"""

    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return False, "no API key"

    try:
        req_body = json.dumps({
            "model": "google/gemini-2.5-flash",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000,
            "temperature": 0.6,
        }).encode("utf-8")
        req = request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=req_body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if 'choices' not in data or not data['choices']:
            return False, "no choices"

        content = data['choices'][0]['message']['content'].strip()

        # Strip markdown fence
        if content.startswith("```"):
            lines = content.split('\n')
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = '\n'.join(lines).strip()

        # Strip preamble — find first '---' and start from there
        if not content.startswith("---"):
            idx = content.find("\n---")
            if idx > 0:
                content = content[idx+1:]
            elif "---" in content:
                content = content[content.find("---"):]
            else:
                return False, "no frontmatter found"

        if not content.startswith("---"):
            return False, f"still bad format: {content[:80]}"

        line_count = len(content.splitlines())
        out = SKILLS_DIR / f"{slug}.md"
        out.write_text(content, encoding='utf-8')
        return True, f"{line_count} lines"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"


# Main: retry any stub
to_retry = [s for s in STYLES if needs_retry(s)]
print(f"=== Retrying {len(to_retry)} stub/failed skills ===")
for slug in to_retry:
    ok, msg = gen(slug, STYLES[slug])
    icon = "✓" if ok else "✗"
    print(f"  {icon} {slug}: {msg}")
    time.sleep(1.2)
print("=== Done ===")
