#!/usr/bin/env python3
"""Audit: cross-check each thumb image's prompt vs the corresponding SKILL.md's visual spec.

For each style (c01..m40):
1. Read SKILL.md
2. Extract: 色票 (hex codes), 字型 (font families), 圖片生成 prompts, 視覺關鍵詞
3. Compare to gen-thumbs.py prompt (which generated the current thumb)
4. Flag mismatches:
   - 色票 unique hex in SKILL but not mentioned in thumb prompt
   - 字型 stack in SKILL but absent from thumb prompt
   - Major visual element in SKILL "視覺語彙" not in thumb prompt

Output: skills-vs-thumbs-audit.md punch list with regen recommendations.
"""
import re
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
SKILLS = ROOT / "skills"
GEN_THUMBS = ROOT / "scripts/gen-thumbs.py"
REPORT = ROOT / "scripts/skills-vs-thumbs-audit.md"

# Parse gen-thumbs.py to extract (slug -> prompt) mapping
gen_text = GEN_THUMBS.read_text(encoding="utf-8")
# Match THUMBS list entries: ("c01", "prompt..."),
thumb_prompts = {}
for m in re.finditer(r'\("([cm]\d{2})",\s*"([^"]+)"\)', gen_text):
    thumb_prompts[m.group(1)] = m.group(2)

print(f"Loaded {len(thumb_prompts)} thumb prompts from gen-thumbs.py")

def parse_skill(slug):
    """Extract structured info from a SKILL.md."""
    f = SKILLS / f"{slug}.md"
    if not f.exists():
        return None
    text = f.read_text(encoding="utf-8")

    info = {
        "slug": slug,
        "is_real": ("status: drafting" not in text) and len(text.splitlines()) > 100,
        "hex_codes": [],
        "fonts": [],
        "visual_keywords": [],
        "image_prompts": [],
    }

    if not info["is_real"]:
        return info

    # Extract hex codes
    info["hex_codes"] = list(set(re.findall(r'#[0-9a-fA-F]{6}\b', text)))[:8]  # top 8 unique

    # Extract font family names from various patterns
    fonts = set()
    for fm in re.finditer(r"font-family[:\s]+['\"]?([A-Za-z][A-Za-z0-9\s,\-]+?)['\";,\n}]", text):
        f_name = fm.group(1).strip()
        if f_name and len(f_name) < 40:
            fonts.add(f_name.split(",")[0].strip().strip("'\""))
    info["fonts"] = sorted(fonts)[:8]

    # Try to extract image generation prompts
    # Look for ## 圖片生成 section and following blockquote/code blocks
    m_img = re.search(r'##\s*圖片[生產]生.*?(?=\n##|\Z)', text, re.DOTALL)
    if m_img:
        section = m_img.group(0)
        # Image prompts often quoted with > or in code blocks
        info["image_prompts"] = re.findall(r'> *(.+?)(?=\n|$)', section)[:5]

    # Visual keywords from 視覺語彙 section
    m_vis = re.search(r'##\s*視覺[語语]彙.*?(?=\n##|\Z)', text, re.DOTALL)
    if m_vis:
        section = m_vis.group(0)
        # Extract bold keywords
        info["visual_keywords"] = list(set(re.findall(r'\*\*([^*]{2,30})\*\*', section)))[:8]

    return info


def audit_one(slug):
    skill = parse_skill(slug)
    thumb_prompt = thumb_prompts.get(slug, "")

    if not skill:
        return {"slug": slug, "status": "MISSING", "issues": ["SKILL.md not found"]}
    if not skill["is_real"]:
        return {"slug": slug, "status": "STUB", "issues": ["SKILL.md still stub — wait for gen"]}
    if not thumb_prompt:
        return {"slug": slug, "status": "NO_PROMPT", "issues": ["thumb prompt missing from gen-thumbs.py"]}

    issues = []
    # Check 1: any hex code in SKILL that's NOT mentioned (loosely) in thumb prompt?
    skill_hexes = [h.lower() for h in skill["hex_codes"]]
    thumb_lower = thumb_prompt.lower()
    # Count how many SKILL hexes appear in thumb prompt
    matched_hexes = sum(1 for h in skill_hexes if h in thumb_lower)
    if len(skill_hexes) >= 3 and matched_hexes == 0:
        issues.append(f"thumb prompt mentions no SKILL hex codes (SKILL has {len(skill_hexes)})")

    # Check 2: any "signature" font in SKILL that's missing from thumb prompt?
    distinctive_fonts = [f for f in skill["fonts"] if f.lower() not in {"sans-serif", "serif", "monospace", "system-ui", "arial", "helvetica"}]
    for f in distinctive_fonts[:3]:
        if f.lower() not in thumb_lower:
            issues.append(f"thumb prompt missing distinctive font: {f}")
            break  # only flag one

    # Check 3: visual keyword check
    distinctive_kw = [kw for kw in skill["visual_keywords"] if len(kw) > 2 and not kw.replace(" ", "").isalpha()]
    missing_kw = [kw for kw in distinctive_kw if kw.lower() not in thumb_lower][:3]
    if len(missing_kw) >= 2:
        issues.append(f"thumb prompt missing visual keywords: {', '.join(missing_kw)}")

    status = "OK" if not issues else ("MISMATCH" if len(issues) >= 2 else "MINOR")
    return {
        "slug": slug,
        "status": status,
        "issues": issues,
        "skill_hexes": skill["hex_codes"][:5],
        "skill_fonts": distinctive_fonts[:3],
        "thumb_prompt_preview": thumb_prompt[:120] + ("..." if len(thumb_prompt) > 120 else ""),
    }


# Run audit
slugs = [f"c{n:02d}" for n in range(1, 26)] + [f"m{n}" for n in range(26, 41)]
results = [audit_one(s) for s in slugs]

# Generate report
lines = [
    "# Skills ↔ Thumbs Alignment Audit",
    "",
    "目的：每個 SKILL.md 寫好之後，回頭檢查既有 thumb 圖是否符合 SKILL spec 的視覺語彙。",
    "",
    "## Status legend",
    "- ✅ **OK** — thumb 跟 SKILL 一致",
    "- ⚠️ **MINOR** — 1 個小不一致",
    "- ❌ **MISMATCH** — 多個視覺語彙不對位，建議重生",
    "- ⏳ **STUB** — SKILL 還是 stub、無法 audit",
    "- ❓ **NO_PROMPT / MISSING** — 缺資料",
    "",
    "## 統計",
]

stats = {}
for r in results:
    stats[r["status"]] = stats.get(r["status"], 0) + 1
for k, v in sorted(stats.items()):
    lines.append(f"- {k}: {v}")

lines += ["", "## 明細", ""]
icons = {"OK": "✅", "MINOR": "⚠️", "MISMATCH": "❌", "STUB": "⏳", "NO_PROMPT": "❓", "MISSING": "❓"}
for r in results:
    icon = icons.get(r["status"], "❓")
    lines.append(f"### {icon} {r['slug']} — {r['status']}")
    if r["issues"]:
        for iss in r["issues"]:
            lines.append(f"- {iss}")
    if r.get("skill_hexes"):
        lines.append(f"- SKILL hexes: `{', '.join(r['skill_hexes'])}`")
    if r.get("skill_fonts"):
        lines.append(f"- SKILL fonts: `{', '.join(r['skill_fonts'])}`")
    if r.get("thumb_prompt_preview"):
        lines.append(f"- Thumb prompt: _{r['thumb_prompt_preview']}_")
    lines.append("")

# Regen recommendations
mismatch_slugs = [r["slug"] for r in results if r["status"] == "MISMATCH"]
if mismatch_slugs:
    lines += [
        "## 建議重生的 thumb",
        "",
        f"預估成本：{len(mismatch_slugs)} × $0.006 = ${len(mismatch_slugs) * 0.006:.3f}",
        f"預估時間：{len(mismatch_slugs) // 4 + 1} × 60s (RPM 5/min batch) ≈ {(len(mismatch_slugs) // 4 + 1) * 60}s",
        "",
        "Slugs:",
        ", ".join(f"`{s}`" for s in mismatch_slugs),
    ]

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"✅ Audit report: {REPORT}")
print(f"   Stats: {stats}")
