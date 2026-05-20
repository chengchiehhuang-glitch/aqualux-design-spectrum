#!/usr/bin/env python3
"""Replace every broken <img src="images/X"> in each demo's index.html with an inline SVG monogram.

Problem: Gemini-generated demos reference designer thumbnails (designer-d01.webp,
avatar-d001.webp, etc) that were never generated — only the 7 standard images
(hero/venue/zone-z01..z05) exist in each works/{slug}/images/ directory.

Fix: for each <img> referencing a non-existent file, replace with an inline SVG
monogram (initials extracted from alt text, with a soft-tone background). This
keeps each demo's visual layout intact while removing all broken-image icons.

Skips: c14-cyberpunk (hand-crafted, 40 images all present).

Idempotent: re-running is safe (already-replaced SVGs are skipped).
"""
import re
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
WORKS = ROOT / "works"

# Color palettes per cluster (pastel-soft, work across most styles)
PALETTES = [
    "#7c8aa6", "#8a7caa", "#a6857c", "#7caa8a", "#aa8a7c",
    "#8aa67c", "#7c9caa", "#aa7c8a", "#aaa07c", "#7caa9c",
    "#9c7caa", "#aa9c7c",
]


def initials_from_alt(alt_text, fallback="·"):
    """Extract 1-2 initials from alt text like 'Glass Yang abstract emblem' → 'GY'."""
    if not alt_text:
        return fallback
    # Strip common stopwords
    stop = {"abstract", "emblem", "avatar", "designer", "portrait", "thumbnail",
            "icon", "image", "photo", "headshot", "card", "風格", "示意圖"}
    words = re.findall(r"[A-Za-z一-鿿]+", alt_text)
    words = [w for w in words if w.lower() not in stop]
    if not words:
        return fallback
    first = words[0]
    # If CJK, take first char only
    if re.match(r"^[一-鿿]", first):
        return first[0]
    # Latin: take first letter of first 1-2 words
    if len(words) >= 2 and re.match(r"^[A-Za-z]", words[1]):
        return (first[0] + words[1][0]).upper()
    return first[0].upper()


def make_svg(initial, color, alt):
    """Build a self-contained inline SVG monogram."""
    # Keep the alt text and aria-label intact so a11y is preserved
    alt_esc = alt.replace('"', '&quot;')
    return (
        f'<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{alt_esc}" '
        f'style="width:100%;height:100%;display:block;background:{color}22">'
        f'<circle cx="60" cy="60" r="46" fill="{color}33" stroke="{color}" stroke-width="1.5" opacity="0.7"/>'
        f'<text x="60" y="74" text-anchor="middle" font-family="Inter,Helvetica,Arial,sans-serif" '
        f'font-weight="600" font-size="38" fill="{color}" letter-spacing="1">{initial}</text>'
        f'</svg>'
    )


def fix_demo(slug_dir):
    html_path = slug_dir / "index.html"
    imgs_dir = slug_dir / "images"
    if not html_path.exists():
        return None
    text = html_path.read_text(encoding="utf-8")
    original = text

    # Find every <img src="images/X..."> reference
    # Match the entire <img ...> tag (single line, no nested >)
    img_tag_re = re.compile(
        r'<img\s+[^>]*?src="images/([^"]+)"[^>]*?>',
        re.IGNORECASE | re.DOTALL,
    )

    replacements = 0
    counter = [0]  # mutable for sub() callback

    def replace_match(m):
        full_tag = m.group(0)
        src = m.group(1)
        target = imgs_dir / src
        if target.exists():
            return full_tag  # leave good images alone

        # Extract alt text
        alt_m = re.search(r'alt="([^"]*)"', full_tag)
        alt = alt_m.group(1) if alt_m else ""
        initial = initials_from_alt(alt, fallback="·")
        color = PALETTES[counter[0] % len(PALETTES)]
        counter[0] += 1
        replacements_local = make_svg(initial, color, alt or "decorative")
        return replacements_local

    new_text, n_replaced = img_tag_re.subn(replace_match, text)

    if new_text != original:
        html_path.write_text(new_text, encoding="utf-8")
    return n_replaced


def main():
    total = 0
    per_demo = []
    for d in sorted(WORKS.glob("c*/")):
        slug = d.name
        if slug == "c14-cyberpunk":
            per_demo.append((slug, "skip (hand-crafted, all imgs present)"))
            continue
        n = fix_demo(d)
        if n is None:
            per_demo.append((slug, "no index.html"))
            continue
        if n > 0:
            per_demo.append((slug, f"{n} replaced"))
            total += n
        else:
            per_demo.append((slug, "0 (already clean)"))

    print("=== fix-broken-images report ===")
    for slug, status in per_demo:
        print(f"  {slug:25} {status}")
    print(f"\nTotal broken <img> tags replaced with SVG monograms: {total}")


if __name__ == "__main__":
    main()
