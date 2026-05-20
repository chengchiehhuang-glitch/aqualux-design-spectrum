#!/usr/bin/env python3
"""Hide the designer roster section across all demos via CSS injection.

User decision (2026-05-20): designer section adds no real meaning to demos
— monograms feel like placeholders. Hide them entirely. Use CSS injection
(rather than HTML surgery) for robustness across varying markup.

Injected at the end of each demo's <style> block:
  section:has(.designer-card),
  section:has(.designers),
  .designers,
  .designer-card { display: none !important; }

Skips c14-cyberpunk (hand-crafted with real images — user may want it intact).

Idempotent: re-running detects the marker comment and skips already-patched files.
"""
import re
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
WORKS = ROOT / "works"

MARKER = "/* hide-designer-section v1 */"
CSS_INJECTION = f"""
{MARKER}
section:has(.designer-card),
section:has(.designers),
section:has(.designer-list),
section:has(.designer-grid),
section:has(.designer-section),
section:has(.designer-row),
section:has(.designer-roster),
section:has(.cast-grid),
section:has(.cast),
.designers, .designer-card, .designer-list, .designer-grid,
.designer-roster, .cast-grid, .cast {{
  display: none !important;
}}
"""


def patch_demo(slug_dir):
    html_path = slug_dir / "index.html"
    if not html_path.exists():
        return "missing"
    text = html_path.read_text(encoding="utf-8")
    if MARKER in text:
        return "already patched"
    # Find last </style> before </head> (the inline stylesheet)
    style_close_idx = text.rfind("</style>")
    if style_close_idx < 0:
        return "no </style> found"
    new_text = text[:style_close_idx] + CSS_INJECTION + text[style_close_idx:]
    html_path.write_text(new_text, encoding="utf-8")
    return "patched"


def main():
    results = []
    for d in sorted(WORKS.glob("c*/")):
        slug = d.name
        if slug == "c14-cyberpunk":
            results.append((slug, "skipped (hand-crafted, kept intact)"))
            continue
        status = patch_demo(d)
        results.append((slug, status))

    print("=== hide-designer-section report ===")
    for slug, status in results:
        print(f"  {slug:25} {status}")
    patched = sum(1 for _, s in results if s == "patched")
    print(f"\nTotal patched: {patched}/{len(results)-1}")


if __name__ == "__main__":
    main()
