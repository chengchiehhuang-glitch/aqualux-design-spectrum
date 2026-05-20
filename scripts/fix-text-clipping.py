#!/usr/bin/env python3
"""Fix text clipping in 5 demos where hero/zone titles overflow container.

Written by Codex CLI (gpt-5.4), executed by Claude main.
Reviewed: minimal CSS injections, idempotent via marker, safety check on selectors.

Issues identified via playwright iframe measurements:
- c01: hero h1 947>698 at 1440px (Glassmorphism overflows 800px panel)
- c07: hero h1 2490>1232 at 1440px / 722>360 at 390px (catastrophic)
- c10: hero h1 1346>1216 at 1440px / 506>326 at 390px
- c13: .zone-en 273>248 at 1440px (MAIN_STREAM_FREQUENCY underscores)
- c19: hero h1 671>663 at 1440px / 273>265 at 390px (8px, minor)

Fix strategy: reduce max font-size + add overflow-wrap: anywhere as safety net.
"""
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
MARKER = "/* fix-text-clipping v2 */"

TARGETS = [
    ("c01-glassmorphism", ROOT / "works/c01-glassmorphism/index.html",
     [".hero-glass-panel", ".hero h1", "Glassmorphism"],
     ".hero h1 word-break + max-font 92px",
     """
  /* fix-text-clipping v2 */
  .hero-glass-panel { overflow: visible; }
  .hero h1 {
    font-size: clamp(46px, 7vw, 92px);
    overflow-wrap: anywhere;
    word-break: normal;
  }
"""),
    ("c07-y2k", ROOT / "works/c07-y2k/index.html",
     [".hero h1", "DESIGN SPECTRUM"],
     ".hero h1 max-font 72px + shine-sweep clip + overflow hidden",
     """
  /* fix-text-clipping v2 */
  .hero h1 {
    font-size: clamp(36px, 6vw, 72px);
    overflow-wrap: anywhere;
    word-break: normal;
    overflow: hidden;
  }
  .hero h1 .shine-sweep {
    display: inline-block;
    max-width: 100%;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: normal;
    overflow: hidden;
  }
"""),
    ("c10-synthwave", ROOT / "works/c10-synthwave/index.html",
     [".hero h1", "SPECTRUM"],
     ".hero h1 word-break + max-font 108px",
     """
  /* fix-text-clipping v2 */
  .hero h1 {
    font-size: clamp(42px, 7.4vw, 108px);
    overflow-wrap: anywhere;
    word-break: normal;
  }
"""),
    ("c13-glitch", ROOT / "works/c13-glitch/index.html",
     [".zone-en", "MAIN_STREAM_FREQUENCY"],
     ".zone-en overflow-wrap for underscored labels",
     """
  /* fix-text-clipping v2 */
  .zone .zone-en, .zone-en {
    overflow-wrap: anywhere;
    word-break: normal;
  }
"""),
    ("c19-chinoiserie", ROOT / "works/c19-chinoiserie/index.html",
     [".hero h1", "國潮"],
     ".hero h1 max-font 118px + wrapping guard",
     """
  /* fix-text-clipping v2 */
  .hero h1 {
    font-size: clamp(48px, 8.6vw, 118px);
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: normal;
    letter-spacing: 0.01em;
  }
"""),
]


def patch_file(slug, path, required, summary, css):
    if not path.exists():
        print(f"{slug}: SKIPPED (file not found)")
        return
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"{slug}: skipped (already patched)")
        return
    for needle in required:
        if needle not in text:
            print(f"{slug}: SKIPPED (required selector/text not found: {needle!r})")
            return
    close = text.find("</style>")
    if close == -1:
        print(f"{slug}: SKIPPED (no inline </style> found)")
        return
    path.write_text(text[:close] + css.rstrip() + "\n" + text[close:], encoding="utf-8")
    print(f"{slug}: patched ({summary})")


def main():
    for target in TARGETS:
        patch_file(*target)


if __name__ == "__main__":
    main()
