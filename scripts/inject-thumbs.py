#!/usr/bin/env python3
"""Add thumb <img> to every card in main index.html.
- C01-C25 → images/thumbs/c{NN}.png
- C26-C40 → images/thumbs/m{NN}.png (motion clusters)
Adds graceful fallback so cards still look OK if a thumb is missing.
"""
import re, os, sys

ROOT = os.path.expanduser("~/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
HTML = f"{ROOT}/index.html"

def thumb_path(num: int) -> str:
    prefix = "c" if num <= 25 else "m"
    return f"images/thumbs/{prefix}{num:02d}.png"

with open(HTML, encoding="utf-8") as f:
    html = f.read()

# Match each .card-thumb that has <span class="id-num">CNN</span> and inject img + style fix
pattern = re.compile(
    r'<div class="card-thumb">(<span class="cat-tag">[^<]+</span>)<span class="id-num">C(\d+)</span></div>'
)

def inject(m):
    cat_span = m.group(1)
    num = int(m.group(2))
    src = thumb_path(num)
    return (
        f'<div class="card-thumb has-img">'
        f'<img src="{src}" alt="C{num:02d} thumb" loading="lazy" onerror="this.style.display=\'none\'">'
        f'{cat_span}<span class="id-num">C{num:02d}</span>'
        f'</div>'
    )

new_html, n_replaced = pattern.subn(inject, html)
print(f"Replaced {n_replaced} card-thumb blocks")

# Add CSS rules for image-backed thumbs
css_addition = """
  /* Thumb image overlay (added by inject-thumbs.py) */
  .card-thumb.has-img { position: relative; overflow: hidden; }
  .card-thumb.has-img img {
    position: absolute; inset: 0;
    width: 100%; height: 100%; object-fit: cover;
    z-index: 0;
    filter: saturate(1.02);
    transition: transform 0.35s ease;
  }
  .card:hover .card-thumb.has-img img { transform: scale(1.04); }
  .card-thumb.has-img .cat-tag,
  .card-thumb.has-img .id-num {
    position: absolute; z-index: 2;
    background: rgba(255,255,255,0.78);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    padding: 2px 8px;
    border-radius: 0;
  }
  .card-thumb.has-img::before {
    z-index: 1;
  }
"""

# Inject CSS just before closing </style>
new_html = new_html.replace("</style>", css_addition + "</style>", 1)

with open(HTML, "w", encoding="utf-8") as f:
    f.write(new_html)

print(f"✅ Updated {HTML}")
print(f"   File size: {os.path.getsize(HTML)} bytes")
