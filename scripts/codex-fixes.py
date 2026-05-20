#!/usr/bin/env python3
"""Codex audit fixes — Round D.
P1.1  C14 SEO meta（canonical / og / twitter / favicon）
P1.2  C14 prefers-reduced-motion CSS
P1.3  主頁 meta description 拿掉 EMBA
P1.4  c03.md 壓 1 行（221→220）
P1.5  統一 motion naming m26-m40 → c26-c40（slug / 檔名 / 顯示 ID）
P2.1  JS modal close() fallback guard
P2.2  IntersectionObserver feature guard
"""
import re, os, shutil
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
INDEX = ROOT / "index.html"
C14 = ROOT / "works/c14-cyberpunk/index.html"
SKILLS = ROOT / "skills"
THUMBS = ROOT / "images/thumbs"

changes = []

# ============ P1.5: rename m26-m40 → c26-c40 ============
for n in range(26, 41):
    old_md = SKILLS / f"m{n}.md"
    new_md = SKILLS / f"c{n}.md"
    if old_md.exists() and not new_md.exists():
        shutil.move(str(old_md), str(new_md))
        # Also update frontmatter slug inside the file
        text = new_md.read_text(encoding="utf-8")
        text = text.replace(f"slug: m{n}", f"slug: c{n}")
        text = text.replace(f"name: m{n}-", f"name: c{n}-")
        new_md.write_text(text, encoding="utf-8")

    for ext in ["webp", "png"]:
        old_img = THUMBS / f"m{n}.{ext}"
        new_img = THUMBS / f"c{n}.{ext}"
        if old_img.exists() and not new_img.exists():
            shutil.move(str(old_img), str(new_img))

changes.append("P1.5 m26-m40 → c26-c40 (skill files + thumb images renamed)")

# ============ Update index.html to use c26-c40 ============
html = INDEX.read_text(encoding="utf-8")

# Replace image src and data-skill for motion items
for n in range(26, 41):
    html = html.replace(f'images/thumbs/m{n}.webp', f'images/thumbs/c{n}.webp')
    html = html.replace(f'data-skill="m{n}"', f'data-skill="c{n}"')
    html = html.replace(f'aria-label="查看 m{n} Skill"', f'aria-label="查看 c{n} Skill"')

changes.append("P1.5b index.html: m{NN}.webp → c{NN}.webp, data-skill m→c")

# ============ P1.3: strip EMBA from meta description ============
old_meta = '<meta name="description" content="40 種設計流派的當代圖鑑。25 種視覺語言 + 15 種動態效果，給多事業體經營者、給 EMBA、給每一個要在『下一個專案該長什麼樣』做決策的人。Curated by Chengchieh Huang.">'
new_meta = '<meta name="description" content="40 種設計流派的當代圖鑑 — 25 種視覺語言 + 15 種動態效果，給多事業體經營者、給每一個要在『下一個專案該長什麼樣』做決策的人。Curated by Chengchieh Huang.">'
if old_meta in html:
    html = html.replace(old_meta, new_meta)
    changes.append("P1.3 主頁 meta description 拿掉「給 EMBA」")

# ============ P2.1: modal close() fallback guard ============
old_close = """  skillModalClose.addEventListener('click', function() {
    if (typeof skillModal.close === 'function') skillModal.close();
    else skillModal.removeAttribute('open');
  });
  skillModal.addEventListener('click', function(e) {
    // Close when clicking backdrop
    const r = skillModal.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
      skillModal.close();
    }
  });"""
new_close = """  function closeSkillModal() {
    if (typeof skillModal.close === 'function') skillModal.close();
    else skillModal.removeAttribute('open');
  }
  skillModalClose.addEventListener('click', closeSkillModal);
  skillModal.addEventListener('click', function(e) {
    // Close when clicking backdrop
    const r = skillModal.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
      closeSkillModal();
    }
  });"""
if old_close in html:
    html = html.replace(old_close, new_close)
    changes.append("P2.1 modal close() fallback unified via closeSkillModal()")

# Also fix Escape handler
old_esc = """  // Close on Escape (dialog handles by default, but for fallback)
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && skillModal.hasAttribute('open')) {
      skillModal.close();
    }
  });"""
new_esc = """  // Close on Escape (dialog handles by default, but for fallback)
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && skillModal.hasAttribute('open')) {
      closeSkillModal();
    }
  });"""
if old_esc in html:
    html = html.replace(old_esc, new_esc)
    changes.append("P2.1b Escape handler same guard")

# ============ P2.2: IntersectionObserver feature guard ============
old_io = """  const statObserver = new IntersectionObserver(function(entries) {"""
new_io = """  if (!('IntersectionObserver' in window)) {
    // Fallback: directly reveal all
    document.querySelectorAll('.card, .stat').forEach(function(el) { el.classList.add('in'); });
    document.querySelectorAll('[data-target]').forEach(function(el) {
      const t = parseInt(el.dataset.target, 10);
      if (!isNaN(t)) el.textContent = t;
    });
  }
  const IObs = (typeof IntersectionObserver !== 'undefined') ? IntersectionObserver : null;
  const statObserver = IObs && new IObs(function(entries) {"""
if old_io in html:
    html = html.replace(old_io, new_io)
    # Wrap the cardObserver creation too
    old_co = """  const cardObserver = new IntersectionObserver(function(entries) {"""
    new_co = """  const cardObserver = IObs && new IObs(function(entries) {"""
    if old_co in html:
        html = html.replace(old_co, new_co)
    # Guard subscriptions
    html = html.replace(
        "document.querySelectorAll('.stat').forEach(function(s) { statObserver.observe(s); });",
        "if (statObserver) document.querySelectorAll('.stat').forEach(function(s) { statObserver.observe(s); });"
    )
    html = html.replace(
        "document.querySelectorAll('.card').forEach(function(c) { cardObserver.observe(c); });",
        "if (cardObserver) document.querySelectorAll('.card').forEach(function(c) { cardObserver.observe(c); });"
    )
    changes.append("P2.2 IntersectionObserver feature-guarded with fallback reveal")

INDEX.write_text(html, encoding="utf-8")

# ============ P1.1 + P1.2: C14 SEO meta + reduced-motion ============
c14 = C14.read_text(encoding="utf-8")

# SEO meta — insert after the existing description line
old = '<meta name="description" content="Aqualux 2026 設計光譜展 · Cyberpunk 風格 demo · single-file HTML showcase">'
new_seo = old + """
<link rel="canonical" href="https://design.aqualux.dev/works/c14-cyberpunk/">
<meta property="og:type" content="website">
<meta property="og:url" content="https://design.aqualux.dev/works/c14-cyberpunk/">
<meta property="og:title" content="C14 賽博龐克 · aqualux 設計光譜展">
<meta property="og:description" content="Cyberpunk 風格 single-file HTML demo · aqualux 2026 設計光譜展">
<meta property="og:image" content="https://design.aqualux.dev/works/c14-cyberpunk/images/hero.webp">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="C14 賽博龐克 · aqualux 設計光譜展">
<meta name="twitter:image" content="https://design.aqualux.dev/works/c14-cyberpunk/images/hero.webp">
<link rel="icon" type="image/svg+xml" href="../../assets/aqualux-logo-mark.svg">"""
if old in c14 and 'rel="canonical"' not in c14:
    c14 = c14.replace(old, new_seo)
    changes.append("P1.1 C14 SEO meta（canonical + og + twitter + favicon）")

# Add prefers-reduced-motion at end of <style>
if 'prefers-reduced-motion' not in c14:
    reduced_motion_css = """
  /* Honor reduced motion preference */
  @media (prefers-reduced-motion: reduce) {
    *,*::before,*::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; }
    .scanlines { display: none !important; }
    .glitch::before, .glitch::after { display: none !important; }
    .blink { animation: none !important; opacity: 1 !important; }
    .hero-banner img { animation: none !important; }
  }"""
    # Insert before </style>
    c14 = c14.replace("</style>", reduced_motion_css + "\n</style>", 1)
    changes.append("P1.2 C14 @media prefers-reduced-motion 加入")

C14.write_text(c14, encoding="utf-8")

# ============ P1.4: trim c03.md to ≤220 ============
c03 = SKILLS / "c03.md"
text = c03.read_text(encoding="utf-8")
lines = text.split('\n')
if len(lines) > 220:
    # Find consecutive blank lines and remove one
    new_lines = []
    prev_blank = False
    removed = False
    for line in lines:
        if not line.strip() and prev_blank and not removed:
            removed = True
            continue
        new_lines.append(line)
        prev_blank = not line.strip()
    if not removed:
        # Just drop the last blank line if any
        while new_lines and not new_lines[-1].strip():
            new_lines.pop()
            removed = True
    c03.write_text('\n'.join(new_lines), encoding="utf-8")
    new_count = len(new_lines)
    changes.append(f"P1.4 c03.md {len(lines)} → {new_count} lines")

print("\n".join(["✅ " + c for c in changes]))
print(f"\nTotal: {len(changes)} fixes applied")
