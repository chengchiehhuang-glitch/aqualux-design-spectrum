#!/usr/bin/env python3
"""Add 「查看 Skill」+「開啟作品」 dual-action UI to all 40 cards + Skill viewer modal."""
import re
from pathlib import Path

ROOT = Path("/Users/aqualux/Documents/Claude/Projects/全專案規劃/aqualux.dev/aqualux-design-spectrum")
INDEX = ROOT / "index.html"

html = INDEX.read_text(encoding="utf-8")

# ============ 1. Normalize C14 card wrapper to use .card-link (consistent with 39 placeholders) ============
# Original C14: <article class="card card-live"><a href="works/c14-cyberpunk/index.html"><div class="card-thumb">...
# After normalize: <article class="card card-live" data-status="live"><div class="card-link"><div class="card-thumb">...
old_c14_open = '<article class="card card-live"><a href="works/c14-cyberpunk/index.html"><div class="card-thumb">'
new_c14_open = '<article class="card card-live" data-status="live"><div class="card-link"><div class="card-thumb">'
html = html.replace(old_c14_open, new_c14_open)

# And the C14 close was </div></a></article> — convert to </div></div></article>
# Need a careful regex: find article with card-live, replace </a></article> with </div></article>
# Easier: line-by-line approach since each card is one line
lines = html.split('\n')
for i, line in enumerate(lines):
    if 'card card-live' in line and 'data-status="live"' in line:
        lines[i] = line.replace('</a></article>', '</div></article>')
html = '\n'.join(lines)

# ============ 2. Replace `.card-cta` simple block with `.card-actions` dual buttons ============
# Pattern for placeholder (39): <div class="card-cta">子頁待開</div>
# Need to derive slug from earlier in the same card. Use regex with backref.
# Match: <img src="images/thumbs/(\w+).webp" ... <div class="card-cta">子頁待開</div>
# Replace card-cta with action buttons including data-skill="\1"

# Simpler approach: process each <article> separately and rewrite.
# Use a regex that captures from <article ... > to </article> non-greedily, extract slug, rewrite cta.

def rewrite_card(match):
    block = match.group(0)
    # Extract slug from images/thumbs/cNN.webp or mNN.webp
    slug_m = re.search(r'images/thumbs/([cm]\d{2})\.webp', block)
    if not slug_m:
        return block
    slug = slug_m.group(1)
    is_live = 'card card-live' in block

    if is_live and slug == 'c14':
        # C14: has real open-work link
        new_actions = (
            '<div class="card-actions" onclick="event.stopPropagation()">'
            f'<button class="btn-skill" data-skill="{slug}" type="button" aria-label="查看 {slug} Skill">'
            '<span class="ic">◇</span> 查看 Skill</button>'
            '<a class="btn-open" href="works/c14-cyberpunk/index.html">開啟作品 <span class="arrow">↗</span></a>'
            '</div>'
        )
        # Replace existing card-cta block
        block = re.sub(
            r'<div class="card-cta"[^>]*>[^<]*</div>',
            new_actions,
            block
        )
    else:
        # Placeholder (39): skill view only, work disabled
        new_actions = (
            '<div class="card-actions" onclick="event.stopPropagation()">'
            f'<button class="btn-skill" data-skill="{slug}" type="button" aria-label="查看 {slug} Skill">'
            '<span class="ic">◇</span> 查看 Skill</button>'
            '<span class="btn-open-disabled" aria-disabled="true">作品撰寫中</span>'
            '</div>'
        )
        block = re.sub(
            r'<div class="card-cta"[^>]*>[^<]*</div>',
            new_actions,
            block
        )
    return block

# Apply to each <article ... class="card ...">...</article>
html = re.sub(
    r'<article class="card[^"]*"[^>]*>.*?</article>',
    rewrite_card,
    html,
    flags=re.DOTALL
)

# ============ 3. Add CSS for card-actions, btn-skill, btn-open, btn-open-disabled, and modal ============
ADD_CSS = """
  /* ============ Card actions (dual button) ============ */
  .card-actions {
    display: flex; gap: 8px; align-items: stretch;
    padding-top: 12px; border-top: 1px solid var(--line);
    margin-top: auto;
  }
  .card-actions .btn-skill {
    flex: 1;
    font-family: var(--mono); font-size: 10.5px;
    color: var(--ink-2); background: rgba(255,255,255,0.04);
    border: 1px solid var(--line);
    padding: 8px 10px;
    letter-spacing: 0.1em; text-transform: uppercase;
    cursor: pointer;
    transition: background 0.18s, border-color 0.18s, color 0.18s;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
  }
  .card-actions .btn-skill:hover {
    background: rgba(56,168,255,0.12);
    border-color: var(--accent-2);
    color: var(--ink);
  }
  .card-actions .btn-skill .ic { color: var(--accent-2); }
  .card-actions .btn-open,
  .card-actions .btn-open-disabled {
    flex: 1;
    font-family: var(--mono); font-size: 10.5px;
    padding: 8px 10px;
    letter-spacing: 0.1em; text-transform: uppercase;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
    border: 1px solid var(--line);
  }
  .card-actions .btn-open {
    color: var(--bg); background: var(--hue3);
    border-color: var(--hue3);
    transition: filter 0.18s;
  }
  .card-actions .btn-open:hover { filter: brightness(1.12); }
  .card-actions .btn-open-disabled {
    color: var(--ink-4); background: transparent;
    cursor: not-allowed;
  }

  /* ============ Skill viewer modal ============ */
  dialog.skill-modal {
    border: 1px solid var(--accent-2);
    background: var(--bg-2);
    color: var(--ink);
    padding: 0;
    width: min(820px, 92vw);
    max-height: 86vh;
    box-shadow: 0 30px 90px rgba(0,0,0,0.6), 0 0 0 1px rgba(56,168,255,0.1);
    margin: auto;
  }
  dialog.skill-modal::backdrop {
    background: rgba(5,6,12,0.85);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
  }
  dialog.skill-modal[open] { display: flex; flex-direction: column; }
  .skill-modal .modal-head {
    display: flex; justify-content: space-between; align-items: center;
    padding: 18px 24px;
    border-bottom: 1px solid var(--line);
    background: linear-gradient(90deg, rgba(56,168,255,0.10), transparent 50%);
  }
  .skill-modal .modal-title {
    display: flex; flex-direction: column; gap: 4px;
  }
  .skill-modal .modal-title .skill-id {
    font-family: var(--mono); font-size: 11px;
    color: var(--accent-2); letter-spacing: 0.22em;
    text-transform: uppercase;
  }
  .skill-modal .modal-title .skill-name {
    font-family: var(--serif); font-weight: 500; font-size: 19px;
    color: var(--ink); letter-spacing: 0.04em;
  }
  .skill-modal .modal-close {
    background: none; border: 1px solid var(--line);
    color: var(--ink-2); cursor: pointer;
    width: 36px; height: 36px; font-size: 16px;
    transition: background 0.18s, color 0.18s, border-color 0.18s;
  }
  .skill-modal .modal-close:hover {
    background: var(--bg-3); color: var(--ink); border-color: var(--accent-2);
  }
  .skill-modal .modal-actions {
    display: flex; gap: 10px; padding: 14px 24px;
    border-bottom: 1px solid var(--line); background: var(--bg);
  }
  .skill-modal .modal-actions button,
  .skill-modal .modal-actions a {
    font-family: var(--mono); font-size: 11px;
    color: var(--ink-2); background: rgba(255,255,255,0.04);
    border: 1px solid var(--line);
    padding: 8px 14px;
    letter-spacing: 0.12em; text-transform: uppercase;
    cursor: pointer; text-decoration: none;
    display: inline-flex; align-items: center; gap: 6px;
    transition: background 0.18s, color 0.18s, border-color 0.18s;
  }
  .skill-modal .modal-actions button:hover,
  .skill-modal .modal-actions a:hover {
    color: var(--ink); border-color: var(--accent-2);
    background: rgba(56,168,255,0.12);
  }
  .skill-modal .modal-actions .btn-copy.copied {
    color: var(--hue3); border-color: var(--hue3); background: rgba(43,212,165,0.12);
  }
  .skill-modal .skill-content {
    flex: 1; overflow: auto;
    margin: 0; padding: 20px 24px;
    font-family: var(--mono); font-size: 12.5px; line-height: 1.85;
    color: var(--ink-2);
    white-space: pre-wrap; word-break: break-word;
    background: var(--bg-2);
  }
  .skill-modal .skill-content strong,
  .skill-modal .skill-content code { color: var(--ink); }
  @media (max-width: 720px) {
    dialog.skill-modal { width: 96vw; max-height: 92vh; }
    .skill-modal .modal-head { padding: 14px 18px; }
    .skill-modal .modal-actions { padding: 12px 18px; flex-wrap: wrap; }
    .skill-modal .skill-content { padding: 16px 18px; font-size: 12px; }
  }

  /* Mobile: stack card-actions vertically */
  @media (max-width: 480px) {
    .card-actions { flex-direction: column; gap: 6px; }
  }
"""

# Insert before </style>
html = html.replace("</style>", ADD_CSS + "\n</style>", 1)

# ============ 4. Add modal HTML before </body> ============
MODAL_HTML = """
<!-- Skill viewer modal -->
<dialog class="skill-modal" id="skillModal" aria-labelledby="skillModalTitle">
  <div class="modal-head">
    <div class="modal-title">
      <span class="skill-id" id="skillModalId">— —</span>
      <span class="skill-name" id="skillModalTitle">Loading…</span>
    </div>
    <button class="modal-close" id="skillModalClose" aria-label="關閉">✕</button>
  </div>
  <div class="modal-actions">
    <button class="btn-copy" id="skillCopyBtn" type="button">複製全文</button>
    <a class="btn-download" id="skillDownloadBtn" download>下載 .md</a>
    <span style="flex:1"></span>
    <a class="btn-source" id="skillSourceBtn" target="_blank" rel="noopener">在新分頁開啟</a>
  </div>
  <pre class="skill-content" id="skillContent">載入中…</pre>
</dialog>
"""

html = html.replace("</main>", "</main>\n" + MODAL_HTML, 1)

# ============ 5. Add JS handlers (extend existing IIFE) ============
ADD_JS = """
  // ============ Skill viewer modal ============
  const skillModal = document.getElementById('skillModal');
  const skillContent = document.getElementById('skillContent');
  const skillModalId = document.getElementById('skillModalId');
  const skillModalTitle = document.getElementById('skillModalTitle');
  const skillCopyBtn = document.getElementById('skillCopyBtn');
  const skillDownloadBtn = document.getElementById('skillDownloadBtn');
  const skillSourceBtn = document.getElementById('skillSourceBtn');
  const skillModalClose = document.getElementById('skillModalClose');

  function nameFor(slug) {
    const card = document.querySelector('[data-skill="' + slug + '"]');
    if (!card) return slug.toUpperCase();
    const article = card.closest('article');
    const zh = article?.querySelector('.card-zh')?.textContent?.trim() || '';
    const en = article?.querySelector('.card-en')?.textContent?.trim() || '';
    return zh + (en ? ' / ' + en : '');
  }

  document.querySelectorAll('.btn-skill').forEach(function(btn) {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      e.stopPropagation();
      const slug = btn.dataset.skill;
      const url = 'skills/' + slug + '.md';
      const idLabel = 'C ' + slug.replace(/^[cm]/, '').padStart(2, '0');
      skillModalId.textContent = idLabel;
      skillModalTitle.textContent = nameFor(slug);
      skillDownloadBtn.href = url;
      skillDownloadBtn.setAttribute('download', slug + '.md');
      skillSourceBtn.href = url;
      skillContent.textContent = '載入中…';
      if (typeof skillModal.showModal === 'function') {
        skillModal.showModal();
      } else {
        skillModal.setAttribute('open', '');
      }
      try {
        const resp = await fetch(url, { cache: 'no-cache' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const md = await resp.text();
        skillContent.textContent = md;
      } catch (err) {
        skillContent.textContent = '⚠ 載入失敗：' + err.message + '\\n\\n（可能 Skill 還在撰寫中。）';
      }
    });
  });

  skillModalClose.addEventListener('click', function() {
    if (typeof skillModal.close === 'function') skillModal.close();
    else skillModal.removeAttribute('open');
  });
  skillModal.addEventListener('click', function(e) {
    // Close when clicking backdrop
    const r = skillModal.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
      skillModal.close();
    }
  });

  skillCopyBtn.addEventListener('click', async function() {
    try {
      await navigator.clipboard.writeText(skillContent.textContent);
      skillCopyBtn.textContent = '已複製 ✓';
      skillCopyBtn.classList.add('copied');
      setTimeout(function() {
        skillCopyBtn.textContent = '複製全文';
        skillCopyBtn.classList.remove('copied');
      }, 1800);
    } catch (err) {
      skillCopyBtn.textContent = '複製失敗';
    }
  });

  // Close on Escape (dialog handles by default, but for fallback)
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && skillModal.hasAttribute('open')) {
      skillModal.close();
    }
  });
"""

# Inject before `})();` end of IIFE
html = html.replace("})();\n</script>", ADD_JS + "\n})();\n</script>", 1)

INDEX.write_text(html, encoding="utf-8")
print("✅ index.html updated:")
print("  • C14 normalized to div.card-link wrapper")
print("  • All 40 cards: card-cta → card-actions (查看 Skill + 開啟作品/作品撰寫中)")
print("  • Modal CSS + HTML + JS injected")
print(f"  • File size: {INDEX.stat().st_size:,} bytes")
