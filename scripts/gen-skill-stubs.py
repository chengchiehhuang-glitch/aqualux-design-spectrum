#!/usr/bin/env python3
"""Generate 39 SKILL.md stubs for styles other than C14 (which already has a real one)."""
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
SKILLS = ROOT / "skills"

STYLES = [
    # (slug, cluster, category, zh, en)
    ('c01', 'mainstream', '主流 UI', '玻璃擬態', 'Glassmorphism'),
    ('c02', 'mainstream', '主流 UI', '新擬物化', 'Neumorphism'),
    ('c03', 'mainstream', '主流 UI', 'Material You', 'Material 3'),
    ('c04', 'mainstream', '主流 UI', '極簡主義', 'Minimalism'),
    ('c05', 'mainstream', '主流 UI', '沉浸暗黑', 'Immersive Dark'),
    ('c06', 'retro', '復古懷舊', '蒸氣波', 'Vaporwave'),
    ('c07', 'retro', '復古懷舊', 'Y2K 千禧', 'Y2K'),
    ('c08', 'retro', '復古懷舊', '90s Web 1.0', 'Web 1.0'),
    ('c09', 'retro', '復古懷舊', '美式復古印刷', 'American Retro Print'),
    ('c10', 'retro', '復古懷舊', '80s Synthwave', 'Synthwave'),
    ('c11', 'retro', '復古懷舊', '包浩斯', 'Bauhaus'),
    ('c12', 'experimental', '實驗前衛', '野獸派', 'Brutalism'),
    ('c13', 'experimental', '實驗前衛', '故障藝術', 'Glitch Art'),
    # c14 already done — skip
    ('c15', 'experimental', '實驗前衛', '構成主義', 'Constructivism'),
    ('c16', 'experimental', '實驗前衛', 'ASCII 終端機', 'ASCII Terminal'),
    ('c17', 'experimental', '實驗前衛', '雜誌排版', 'Editorial Magazine'),
    ('c18', 'cultural', '文化在地', '日式禪意', 'Wabi-Sabi'),
    ('c19', 'cultural', '文化在地', '中國風國潮', 'Chinoiserie / Guochao'),
    ('c20', 'cultural', '文化在地', '北歐極簡', 'Scandinavian'),
    ('c21', 'cultural', '文化在地', '瑞士國際風格', 'Swiss International'),
    ('c22', 'cultural', '文化在地', '台灣廟會', 'Taiwan Temple Carnival'),
    ('c23', 'decorative', '裝飾性', '等距 3D', 'Isometric 3D'),
    ('c24', 'decorative', '裝飾性', '手繪塗鴉', 'Hand-Drawn Sketch'),
    ('c25', 'decorative', '裝飾性', '漸層 Mesh', 'Gradient Mesh'),
    # Motion 15
    ('m26', 'motion', '動態-視差', '多層視差', 'Parallax Layers'),
    ('m27', 'motion', '動態-視差', 'Sticky 堆疊章節', 'Sticky Stack'),
    ('m28', 'motion', '動態-視差', '橫向滾動陣容', 'Horizontal Scroll'),
    ('m29', 'motion', '動態-滾動', '全屏章節切換', 'Scroll Snap Acts'),
    ('m30', 'motion', '動態-滾動', '滾動進度指示', 'Scroll Progress'),
    ('m31', 'motion', '動態-滾動', '滾動跑馬燈', 'Marquee Band'),
    ('m32', 'motion', '動態-入場', '錯落淡入', 'Fade Stagger'),
    ('m33', 'motion', '動態-入場', '打字機標題', 'Typewriter'),
    ('m34', 'motion', '動態-入場', '數字爆裂計數', 'Counter Burst'),
    ('m35', 'motion', '動態-循環', '極光漸層流動', 'Aurora Flow'),
    ('m36', 'motion', '動態-循環', '漂浮幾何球', 'Floating Orbs'),
    ('m37', 'motion', '動態-循環', '動態噪點', 'Noise Grain'),
    ('m38', 'motion', '動態-指標', '滑鼠光暈', 'Cursor Spotlight'),
    ('m39', 'motion', '動態-指標', '3D 傾斜卡片', 'Tilt Cards'),
    ('m40', 'motion', '動態-指標', '磁吸按鈕', 'Magnetic CTA'),
]

STUB_TEMPLATE = """---
name: {slug}-{en_kebab}
slug: {slug}
cluster: {cluster}
category: {category}
edition: aqualux-2026
status: drafting
---

# {id} · {zh} / {en}

> Single-file HTML demo skill for the aqualux 2026 設計光譜展 codex.
> 此 Skill 完整版**撰寫中** — 預計 v0.2 上線完整視覺語彙、結構、生圖 prompt 與 a11y 規範。

---

## 已知方向（先行 spec）

- **設計流派**：{en}（{category}）
- **代表性視覺**：見主索引縮圖 [{slug}.webp](../images/thumbs/{slug}.webp)
- **適合場景**：— 撰寫中 —
- **跟 aqualux 主品牌的關係**：本子頁刻意偏離 aqualux 主紙感、用 {en} 流派自己的視覺語彙呈現一場虛構的 aqualux 2026 設計光譜展

---

## 完整 SKILL 內容預計包含（v0.2）

```
✓ 色票（hex + CSS variable 命名）
✓ 字型系統（display / mono / body 三層）
✓ 動態效果規範（含 reduced-motion fallback）
✓ 頁面結構（8 區段：topbar / hero / statement / 設計師 / venue / 展區 / 排程 / 票務 / footer）
✓ 圖片生成 prompts（20 張 gpt-image-2 spec）
✓ 內容文案（虛構展覽資訊；12 設計師名單；5 展區命名）
✓ 文案 voice（該流派專屬的策展論述語感）
✓ 互動行為（hover / scroll / click）
✓ a11y / 性能（landmark / WCAG AA / lazy-load / WebP）
✓ 部署（Netlify auto-deploy from GitHub）
```

可參考已完工的 [C14 賽博龐克 Skill](./c14.md) 作為結構範本。

---

## 想自己先試？

把以下 prompt 丟給 Claude Code：

```
依 aqualux 2026 設計光譜展的 spec，
生成 {zh}（{en}）風格的 single-file HTML demo。
參考 c14 cyberpunk skill 的 8 區段骨架，
但所有視覺語彙改用 {en} 流派的色票/字型/動態。
圖片用 gpt-image-2 low quality 生成（不可使用外部圖片）。
```

歡迎把你的版本 fork 回來、aqualux 圖鑑團隊會收錄參考。

---

**版本記錄**
- v0.1 — 2026-05-19 — Stub. 完整版預計 v0.2。
"""

def en_to_kebab(en: str) -> str:
    return en.lower().replace(' / ', '-').replace(' ', '-')

count = 0
for slug, cluster, category, zh, en in STYLES:
    out = SKILLS / f"{slug}.md"
    if out.exists():
        print(f"  · {slug}: skip (exists)")
        continue
    id_label = f"C {slug[1:]}"  # "C 01", "C 26" etc.
    content = STUB_TEMPLATE.format(
        slug=slug,
        en_kebab=en_to_kebab(en),
        cluster=cluster,
        category=category,
        zh=zh,
        en=en,
        id=id_label,
    )
    out.write_text(content, encoding="utf-8")
    count += 1
    print(f"  ✓ {slug}.md")

print(f"\n✅ {count} stub SKILL.md files created in {SKILLS}/")
print(f"   c14 already real (skipped) · 1 + {count} = {count+1} skills total")
