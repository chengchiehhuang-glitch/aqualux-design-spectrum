#!/usr/bin/env python3
"""Unlock 'live' status on main index.html for demos that have a complete index.html.

A demo is 'live' when:
- works/{slug}-{kebab}/index.html exists
- contains </html> AND </body>

For each live demo:
- Replace `data-status="placeholder"` → `data-status="live"`
- Replace `class="card"` → `class="card card-live"`
- Replace `<span class="btn-open-disabled" aria-disabled="true">作品撰寫中</span>`
  with `<a class="btn-open" href="works/{slug}-{kebab}/index.html">開啟作品 <span class="arrow">↗</span></a>`

Idempotent: re-running is safe (already-live cards are skipped).
"""
import re
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
INDEX = ROOT / "index.html"
WORKS = ROOT / "works"

SLUG_TO_KEBAB = {
    'c01':'glassmorphism','c02':'neumorphism','c03':'material-3','c04':'minimalism','c05':'immersive-dark',
    'c06':'vaporwave','c07':'y2k','c08':'web-1','c09':'retro-print','c10':'synthwave','c11':'bauhaus',
    'c12':'brutalism','c13':'glitch','c14':'cyberpunk','c15':'constructivism','c16':'ascii-terminal',
    'c17':'editorial','c18':'wabi-sabi','c19':'chinoiserie','c20':'scandinavian','c21':'swiss',
    'c22':'taiwan-temple','c23':'isometric-3d','c24':'hand-drawn','c25':'gradient-mesh',
    'c26':'parallax-layers','c27':'sticky-stack','c28':'horizontal-scroll','c29':'scroll-snap',
    'c30':'scroll-progress','c31':'marquee','c32':'fade-stagger','c33':'typewriter','c34':'counter-burst',
    'c35':'aurora-flow','c36':'floating-orbs','c37':'noise-grain','c38':'cursor-spotlight',
    'c39':'tilt-cards','c40':'magnetic-cta',
}


def is_demo_live(slug, kebab):
    html = WORKS / f"{slug}-{kebab}" / "index.html"
    if not html.exists():
        return False
    text = html.read_text(encoding="utf-8", errors="ignore").lower()
    return "</html>" in text and "</body>" in text


def main():
    html = INDEX.read_text(encoding="utf-8")
    original = html
    live, skipped, already, missing = [], [], [], []

    for slug, kebab in SLUG_TO_KEBAB.items():
        if not is_demo_live(slug, kebab):
            missing.append(slug)
            continue

        # Find this card's article tag using data-skill="{slug}" as anchor
        marker = f'data-skill="{slug}"'
        idx = html.find(marker)
        if idx < 0:
            skipped.append(f"{slug} (data-skill not found)")
            continue

        # Find the surrounding <article>...</article>
        article_start = html.rfind("<article", 0, idx)
        article_end = html.find("</article>", idx)
        if article_start < 0 or article_end < 0:
            skipped.append(f"{slug} (article bounds not found)")
            continue
        article_end += len("</article>")
        article = html[article_start:article_end]

        # Already live?
        if 'data-status="live"' in article:
            already.append(slug)
            continue

        # Replace status attr and class
        new_article = article.replace('data-status="placeholder"', 'data-status="live"', 1)
        new_article = new_article.replace('class="card"', 'class="card card-live"', 1)

        # Replace disabled span with real link
        link_html = f'<a class="btn-open" href="works/{slug}-{kebab}/index.html">開啟作品 <span class="arrow">↗</span></a>'
        new_article = re.sub(
            r'<span class="btn-open-disabled"[^>]*>作品撰寫中</span>',
            link_html,
            new_article,
            count=1,
        )

        if new_article == article:
            skipped.append(f"{slug} (no change applied)")
            continue

        html = html[:article_start] + new_article + html[article_end:]
        live.append(slug)

    if html != original:
        INDEX.write_text(html, encoding="utf-8")

    print(f"=== Index.html unlock summary ===")
    print(f"✅ Unlocked ({len(live)}): {', '.join(live)}")
    if already:
        print(f"ℹ️  Already live ({len(already)}): {', '.join(already)}")
    if skipped:
        print(f"⚠️  Skipped ({len(skipped)}):")
        for s in skipped:
            print(f"    - {s}")
    if missing:
        print(f"⏳ Still placeholder — demo broken/missing ({len(missing)}): {', '.join(missing)}")


if __name__ == "__main__":
    main()
