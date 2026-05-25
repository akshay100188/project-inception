"""
Prototype Generator agent — generates a 5-screen scrollable HTML wireframe document.

Runs THREE parallel API calls to avoid the token ceiling that caused screen 3 to be
silently truncated when screens 1-3 were bundled together:
  Part A: HTML shell + header + screens 1 and 2  (max_tokens 7000)
  Part B: screen 3 only                          (max_tokens 4000)
  Part C: screens 4 and 5 + closing tags         (max_tokens 6000)
"""
import asyncio
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

# ── Shared CSS / card structure used in all three prompts ────────────────────

_CARD_STRUCTURE = """
## Screen card structure (use for EVERY screen):

<div class="sw">
  <div class="sl" style="background:[domain-color]">
    <span>Screen N — [Name]</span>
    <span style="font-weight:400;font-size:0.82rem;opacity:0.85">[one-line description]</span>
  </div>
  <div class="bc">
    <div class="bd">
      <span class="bdt" style="background:#ef4444"></span>
      <span class="bdt" style="background:#f59e0b"></span>
      <span class="bdt" style="background:#22c55e"></span>
    </div>
    <div class="bu">[app-name].app/[path]</div>
  </div>
  <div class="sb p-6">
    [full screen content using Tailwind classes]
  </div>
</div>
"""

_SHARED_RULES = """
## CRITICAL rules:
1. ALL data hardcoded — realistic names, numbers, dates matching the app domain
2. NO setTimeout, fetch, XMLHttpRequest — static HTML only
3. Every screen fully populated — no empty states, no placeholders except form inputs
4. Color scheme consistent with domain (fintech=slate/blue, health=green/teal, food=orange, productivity=indigo)
5. Output raw HTML only — no markdown fences
"""

# ── Part A: shell + header + screens 1-2 ────────────────────────────────────

_SYSTEM_PROMPT_A = """You are a UI wireframe document generator. Generate Part A of a 5-screen wireframe document.

Part A includes: the full HTML shell, document header, and screens 1 and 2 ONLY.

## Full HTML shell to output first:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[App Name] — UI Wireframe</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; }
    .sw { max-width: 960px; margin: 0 auto 3rem; padding: 0 1rem; }
    .sl { color: white; padding: 0.75rem 1.25rem; border-radius: 12px 12px 0 0; font-weight: 700; font-size: 0.95rem; display: flex; justify-content: space-between; align-items: center; }
    .bc { background: #e2e8f0; padding: 0.4rem 0.75rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.72rem; color: #64748b; border-left: 1px solid #cbd5e1; border-right: 1px solid #cbd5e1; }
    .bd { display: flex; gap: 4px; flex-shrink: 0; }
    .bdt { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .bu { background: white; border-radius: 4px; padding: 2px 10px; flex: 1; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .sb { background: white; border: 1px solid #cbd5e1; border-top: none; border-radius: 0 0 12px 12px; overflow: hidden; min-height: 480px; }
  </style>
</head>
<body>

## Document header (output immediately after <body>):

<div style="background:linear-gradient(135deg,[color1],[color2]);color:white;text-align:center;padding:3rem 1rem 2.5rem;margin-bottom:2rem;">
  <div style="font-size:2rem;font-weight:800;letter-spacing:-0.02em">[App Name]</div>
  <div style="margin-top:0.4rem;opacity:0.85;font-size:1rem">UI Wireframe Document · 5 Screens</div>
  <div style="margin-top:1.25rem;display:flex;justify-content:center;gap:0.75rem;flex-wrap:wrap;font-size:0.8rem;opacity:0.75;">
    <span>1 · Dashboard</span><span>·</span>
    <span>2 · [Screen 2 Name]</span><span>·</span>
    <span>3 · [Screen 3 Name]</span><span>·</span>
    <span>4 · [Screen 4 Name]</span><span>·</span>
    <span>5 · Settings</span>
  </div>
</div>

""" + _CARD_STRUCTURE + """
## Generate ONLY these 2 screens:

**Screen 1 — Dashboard**: 4 stat cards (icon + metric + label + trend), recent activity list with 6 items (avatar/icon + text + timestamp), a CSS bar chart (colored divs of varying heights showing weekly data)

**Screen 2 — [Main List]**: search input bar + 3 filter chips + a data table with 8 rows of realistic domain data (columns appropriate to the app, sortable header indicators, action buttons per row)

""" + _SHARED_RULES + """
## End with EXACTLY this marker and nothing else:
<!-- PROTO_A_END -->

Do NOT write </body> or </html>. Generate screens 1 and 2 only."""

# ── Part B: screen 3 only ────────────────────────────────────────────────────

_SYSTEM_PROMPT_B = """You are generating Screen 3 of a 5-screen HTML wireframe. Screens 1-2 and the document shell are already written.

""" + _CARD_STRUCTURE + """
## Generate ONLY this 1 screen:

**Screen 3 — [Detail View]**: single record expanded — header with title + status badge + 2-3 action buttons (Edit / Archive / Share); a two-column field grid with 8-10 relevant fields populated with realistic data; a related items section at the bottom with 4 rows

Rules:
- Do NOT output DOCTYPE, html, head, body, or style
- Start directly with: <div class="sw">
- Use the same CSS classes: sw, sl, bc, bd, bdt, bu, sb
- Match the domain color and app name from the project requirements
""" + _SHARED_RULES + """
## End with EXACTLY:
<!-- PROTO_B_END -->"""

# ── Part C: screens 4-5 + closing ────────────────────────────────────────────

_SYSTEM_PROMPT_C = """You are completing a 5-screen HTML wireframe. Screens 1-3 and the document shell are already written.

""" + _CARD_STRUCTURE + """
## Generate ONLY these 2 screens, then close the document:

**Screen 4 — [Create / Edit Form]**: form header (title + Cancel/Save buttons); two-column form layout with 6-8 labelled fields appropriate to the domain (text inputs, select dropdowns, date picker, textarea, radio group); a required-field indicator legend; a prominent primary submit button at the bottom

**Screen 5 — Settings / Profile**: three horizontal tabs (Account / Notifications / Preferences) with Account tab active; profile avatar + name + edit button; form fields for account info; 6 notification toggle rows (mix of on/off); Save Changes button

Rules:
- Do NOT output DOCTYPE, html, head, body, or style
- Start directly with: <div class="sw">
- Use the same CSS classes: sw, sl, bc, bd, bdt, bu, sb
- Match the domain color and app name from the project requirements
""" + _SHARED_RULES + """
## After screen 5, close the document with EXACTLY:
<div style="text-align:center;padding:2rem;font-size:0.75rem;color:#94a3b8;border-top:1px solid #e2e8f0;margin-top:1rem;">
  Generated by Project Inception AI · UI Wireframe Document
</div>
</body>
</html>"""


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _call(system: str, user_content: str, label: str, max_tokens: int) -> str:
    full = ""
    try:
        async with _client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
        ) as stream:
            async for text in stream.text_stream:
                full += text
    except Exception as exc:
        logger.error("Prototype %s call failed: %s", label, exc)
    logger.info("Prototype %s: %d chars", label, len(full))
    return full.strip()


def _strip_fences(html: str) -> str:
    s = html.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s


def _cut_at(html: str, marker: str) -> str:
    """Return content before marker, stripping any stray closing tags if marker is absent."""
    if marker in html:
        return html.split(marker)[0].rstrip()
    for tag in ("</body>", "</html>"):
        if html.rstrip().endswith(tag):
            html = html.rstrip()[: -len(tag)].rstrip()
    return html


def _drop_shell(html: str) -> str:
    """Strip any accidental DOCTYPE/html/head re-declaration from continuation parts."""
    if "<!DOCTYPE" not in html and "<html" not in html:
        return html
    for tag in ('<div class="sw"',):
        idx = html.find(tag)
        if idx != -1:
            return html[idx:]
    return html


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_prototype(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
) -> str:
    """
    Generate a 5-screen wireframe document via three parallel API calls.
    Returns the raw HTML string.
    """
    user_content = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        "Use hardcoded realistic sample data throughout. "
        "Match color scheme and screen names to the specific app domain."
    )

    raw_a, raw_b, raw_c = await asyncio.gather(
        _call(_SYSTEM_PROMPT_A, user_content + "\n\nGenerate Part A: HTML shell + header + screens 1 and 2 only.", "Proto-A", 7000),
        _call(_SYSTEM_PROMPT_B, user_content + "\n\nGenerate Part B: screen 3 only.", "Proto-B", 4000),
        _call(_SYSTEM_PROMPT_C, user_content + "\n\nGenerate Part C: screens 4 and 5 + closing tags.", "Proto-C", 6000),
    )

    part_a = _cut_at(_strip_fences(raw_a), "<!-- PROTO_A_END -->")
    part_b = _cut_at(_drop_shell(_strip_fences(raw_b)), "<!-- PROTO_B_END -->")
    part_c = _drop_shell(_strip_fences(raw_c))

    return (part_a + "\n\n" + part_b + "\n\n" + part_c).strip()
