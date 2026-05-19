#!/usr/bin/env python3
"""Generate 40 thumbnails for aqualux design spectrum gallery.
gpt-image-2 RPM = 5/min → batch 4 + sleep 60s between batches.
"""
import subprocess, time, os, sys, json
from datetime import datetime

OUT_DIR = os.path.expanduser("~/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum/images/thumbs")
LOG = os.path.expanduser("~/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum/scripts/gen-thumbs.log")
os.makedirs(OUT_DIR, exist_ok=True)

# (filename, prompt) — prompts intentionally avoid identifying text/brands, focus on visual style essence
THUMBS = [
    # Design 25
    ("c01", "Square graphic showcasing glassmorphism: a translucent frosted glass rounded card floating on a soft pastel gradient, with subtle backdrop blur and faint light refraction. Centered. Modern UI thumbnail. No text."),
    ("c02", "Square graphic in neumorphism style: a single soft monochrome rounded button with subtle inset and outset shadows on a light cream-gray background. Calm tactile minimal look. No text."),
    ("c03", "Square graphic in Material 3 / Material You: dynamic color rounded UI components in soft sage green and warm coral, layered elevation, expressive surfaces. Centered. No text."),
    ("c04", "Square graphic embodying editorial minimalism: a single thin black serif letterform centered on vast pure white canvas with one thin horizontal hairline. Generous whitespace. No additional text."),
    ("c05", "Square graphic in immersive dark UI aesthetic: deep black background with a single subtle spotlight glow in low-saturation teal, suggesting cinematic stage lighting. Atmospheric. No text."),
    ("c06", "Square graphic in vaporwave aesthetic: soft purple-pink-cyan gradient, classic Greek bust silhouette in pastel, distant retro grid horizon. Internet nostalgia. No text."),
    ("c07", "Square graphic in Y2K 2000s aesthetic: chrome metallic blob shapes, translucent frosted plastic textures, small star decorations, bubblegum pink and silver. No text."),
    ("c08", "Square graphic in 1996 Web 1.0 aesthetic: gray system font heading shape, tile-pattern background, beveled gray button, default-blue underlined link shape. No identifiable text."),
    ("c09", "Square graphic in 1970s American retro print poster aesthetic: halftone dot texture, off-register ink colors in burnt orange and teal, chunky serif headline shape. Vintage screenprint feel. No text."),
    ("c10", "Square graphic in 80s synthwave aesthetic: neon pink and purple sunset, geometric perspective grid receding to horizon, retro chrome sun. No text."),
    ("c11", "Square graphic in Bauhaus 1920s design: primary red yellow and blue arranged as circle, triangle, square in pure geometric composition. No text."),
    ("c12", "Square graphic in brutalist web design: raw exposed structure, harsh monospace heading shape, intentionally jagged grid, concrete gray and stark black. Anti-design. No text."),
    ("c13", "Square graphic in glitch art aesthetic: RGB chromatic aberration, horizontal scan line distortion, fragmented geometric shapes in cyan and magenta, digital noise. No text."),
    ("c14", "Square graphic in cyberpunk aesthetic: neon pink and electric cyan glowing on deep black background, hints of japanese katakana shapes, tech-noir mood, glowing borders. No identifiable text."),
    ("c15", "Square graphic in Russian constructivism aesthetic: bold red and black diagonal composition, geometric propaganda-poster shapes. No text."),
    ("c16", "Square graphic in ASCII terminal aesthetic: pure black background, glowing green phosphor characters arranged as ASCII art pattern, monospaced grid feel. No actual words."),
    ("c17", "Square graphic in editorial magazine aesthetic: 12-column grid hint, heavy serif headline shape, blocky black-and-white photographic composition. Monocle style. No text."),
    ("c18", "Square graphic in Japanese wabi-sabi aesthetic: cream textured paper background, single sumi-e ink brush stroke off-center, calligraphic mark, asymmetric balance. No text."),
    ("c19", "Square graphic in Chinese guochao aesthetic: vermillion cinnabar red and ink black, traditional cloud pattern, Song-typeface character shape silhouette, modern-classical fusion. No identifiable text."),
    ("c20", "Square graphic in Scandinavian Nordic aesthetic: warm pale wood tone, simple cozy line illustration of pine trees, soft warm gray, clean sans-serif feel. No text."),
    ("c21", "Square graphic in Swiss International typographic style: pure white background, single bold red square, strict grid alignment, Helvetica typographic shapes. No text."),
    ("c22", "Square graphic in Taiwan temple carnival aesthetic: red and gold neon signboard shapes, brushstroke calligraphic character silhouette, festive night-market lights. No identifiable text."),
    ("c23", "Square graphic in isometric 3D illustration aesthetic: 30-degree axonometric tiny world with stacked colorful geometric buildings, small figure silhouettes, toy-like scene. No text."),
    ("c24", "Square graphic in hand-drawn sketch aesthetic: colored crayon scribbles, handwritten doodle arrows, slightly tilted hand-drawn shapes, designer notebook page. No text."),
    ("c25", "Square graphic showcasing gradient mesh design: liquid aurora gradient flowing in pinks, blues and greens, soft glowing orbs, fluid abstract composition. No text."),
    # Motion 15
    ("m26", "Square graphic representing parallax scrolling: three stacked layers of mountain silhouettes at different scales in cool pastel tones, suggesting depth. Minimal illustration. No text."),
    ("m27", "Square graphic representing sticky stack scroll animation: stacked rectangular cards offset vertically in mid-transition, suggesting motion. Apple-style aesthetic. No text."),
    ("m28", "Square graphic representing horizontal scroll: a row of geometric card shapes flowing sideways with motion blur trails. Clean modern. No text."),
    ("m29", "Square graphic representing scroll-snap full-screen acts: full-bleed gradient bands stacked vertically in stage-curtain transition. No text."),
    ("m30", "Square graphic representing scroll progress indicator: a horizontal progress bar at top, small dots in a side rail glowing in sequence. Minimal UI. No text."),
    ("m31", "Square graphic representing marquee scrolling band: large abstract letterform shapes running horizontally with speed lines. Bold typographic motion. No identifiable text."),
    ("m32", "Square graphic representing staggered fade-in: a wave of small card shapes appearing in sequence with subtle motion blur, gentle organic curve. No text."),
    ("m33", "Square graphic representing typewriter animation: a heavy black underscore cursor caret on clean white space. Minimal. No actual letters."),
    ("m34", "Square graphic representing animated number counter: large numerical zero exploding into colorful confetti particles, kinetic energy. No specific numerals."),
    ("m35", "Square graphic representing aurora flow loop: multiple soft radial gradient orbs in aurora colors (green pink purple) flowing in slow motion. No text."),
    ("m36", "Square graphic representing floating orb background: gentle colorful geometric spheres drifting at different speeds in soft pastel space. No text."),
    ("m37", "Square graphic representing animated film grain: heavy film noise texture overlay on a muted gradient base, vintage cinematic feel. No text."),
    ("m38", "Square graphic representing cursor spotlight effect: dark background with a single bright radial glow positioned off-center, mimicking mouse-following light. No text."),
    ("m39", "Square graphic representing 3D tilt card effect: a single rectangular card tilted in 3D perspective with subtle shadow, suggesting hover. No text."),
    ("m40", "Square graphic representing magnetic button effect: a circular button shape with arrows suggesting attraction, faint magnetic field lines. No text."),
]

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def gen_one(slug, prompt):
    out = f"{OUT_DIR}/{slug}.png"
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        return ("skip", slug, "exists")
    p = subprocess.run(
        ["genimg", prompt, "--quality", "low", "--size", "1024x1024", "--out", out],
        capture_output=True, text=True, timeout=180
    )
    if p.returncode == 0 and os.path.exists(out):
        return ("ok", slug, "")
    err = (p.stderr or p.stdout or "").strip()[:120]
    return ("err", slug, err)

def main():
    open(LOG, "w").close()
    log(f"=== Start: {len(THUMBS)} thumbs ===")

    BATCH = 4
    PAUSE = 65

    results = {"ok":0, "skip":0, "err":0}
    failed = []

    for batch_idx in range(0, len(THUMBS), BATCH):
        batch = THUMBS[batch_idx:batch_idx+BATCH]
        log(f"--- Batch {batch_idx//BATCH+1}/{(len(THUMBS)+BATCH-1)//BATCH} ({len(batch)} items) ---")

        # Parallel via subprocess.Popen
        procs = []
        for slug, prompt in batch:
            out = f"{OUT_DIR}/{slug}.png"
            if os.path.exists(out) and os.path.getsize(out) > 10000:
                log(f"  ✓ {slug} (skip, exists)")
                results["skip"] += 1
                continue
            p = subprocess.Popen(
                ["genimg", prompt, "--quality", "low", "--size", "1024x1024", "--out", out],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            procs.append((slug, p))

        for slug, p in procs:
            try:
                stdout, stderr = p.communicate(timeout=180)
                out = f"{OUT_DIR}/{slug}.png"
                if p.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 10000:
                    log(f"  ✓ {slug}")
                    results["ok"] += 1
                else:
                    err = (stderr or stdout or "?").strip()[:100]
                    log(f"  ✗ {slug}: {err}")
                    failed.append((slug, dict(THUMBS).get(slug, "")))
                    results["err"] += 1
            except subprocess.TimeoutExpired:
                p.kill()
                log(f"  ✗ {slug}: timeout")
                failed.append((slug, dict(THUMBS).get(slug, "")))
                results["err"] += 1

        # Pause between batches (except last)
        if batch_idx + BATCH < len(THUMBS):
            log(f"  ⏳ Sleeping {PAUSE}s for RPM…")
            time.sleep(PAUSE)

    # Retry failed (1 round)
    if failed:
        log(f"=== Retry round: {len(failed)} failed ===")
        time.sleep(PAUSE)
        for slug, prompt in failed:
            status, _, msg = gen_one(slug, prompt)
            log(f"  {status} {slug} retry: {msg}")
            time.sleep(15)

    log(f"=== Final: ok={results['ok']} skip={results['skip']} err={results['err']} ===")
    log(f"=== Files: {OUT_DIR} ===")

if __name__ == "__main__":
    main()
