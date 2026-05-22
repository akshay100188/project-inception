"""
Prototype Generator agent — generates a multi-screen interactive HTML mockup.
"""
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a UI wireframe document generator. Given a software project plan, generate a single self-contained HTML file that presents all 5 key screens of the application as a scrollable wireframe document — like a design spec deliverable.

## Document structure (MANDATORY):

A vertically-scrolling page with:
1. A gradient header (app name + "UI Wireframe · 5 Screens" subtitle)
2. Five screen sections stacked top-to-bottom, each inside a "browser frame" card
3. Clean light background (#f1f5f9)

## Each screen section structure:
```html
<div style="max-width:960px; margin:0 auto 3rem;">
  <!-- Screen label bar -->
  <div style="background:[domain-color]; color:white; padding:0.75rem 1.25rem; border-radius:12px 12px 0 0; font-weight:700; display:flex; justify-content:space-between; align-items:center;">
    <span>Screen N — [Screen Name]</span>
    <span style="font-weight:400; font-size:0.85rem; opacity:0.85">[one-line description]</span>
  </div>
  <!-- Fake browser chrome -->
  <div style="background:#e2e8f0; padding:0.5rem 1rem; display:flex; align-items:center; gap:0.5rem; font-size:0.75rem; color:#64748b; border-left:1px solid #cbd5e1; border-right:1px solid #cbd5e1;">
    <span style="display:flex;gap:4px;"><span style="width:10px;height:10px;border-radius:50%;background:#ef4444;display:inline-block"></span><span style="width:10px;height:10px;border-radius:50%;background:#f59e0b;display:inline-block"></span><span style="width:10px;height:10px;border-radius:50%;background:#22c55e;display:inline-block"></span></span>
    <span style="background:white;border-radius:4px;padding:2px 12px;flex:1;max-width:300px;">[app-name].app/[path]</span>
  </div>
  <!-- Screen content (white bg, bordered) -->
  <div style="background:white; border:1px solid #cbd5e1; border-top:none; border-radius:0 0 12px 12px; overflow:hidden; min-height:500px;">
    ... full screen content here ...
  </div>
</div>
```

## The 5 screens to generate (adapt names to the app domain):

1. **Dashboard / Overview** — 4 stat cards, a recent activity list, a chart placeholder (use a colored bar-chart built with divs of varying heights, not Chart.js)
2. **[Main List / Browse]** — search input + filter chips + a data table or card grid with 8+ rows/cards of realistic data
3. **[Detail / Profile View]** — single record expanded view with all fields, action buttons (Edit, Archive, Share)
4. **[Create / Edit Form]** — multi-section form with labels, text inputs, selects, textarea, a submit button — domain-appropriate fields
5. **[Settings / Notifications]** — tabbed settings panel, preference toggles, account info, a Save Changes button

## CRITICAL content rules:

1. **ALL data hardcoded inline** — realistic sample data for this specific app domain (real-looking names, numbers, dates, categories)
2. **Use Tailwind CSS CDN**: `<script src="https://cdn.tailwindcss.com"></script>`
3. **NO setTimeout, NO fetch, NO XMLHttpRequest** — everything is static HTML
4. **NO loading states** — all content visible immediately, no spinners
5. Every screen must look **complete and dense** — filled tables, populated cards, form fields with placeholder values
6. Color scheme must match the domain (fintech=slate/blue, health=green/teal, food=orange/warm, productivity=indigo/purple)
7. Buttons and inputs are visual only — no JS interactivity needed

## Document header to include at the top:
```html
<div style="text-align:center; padding:3rem 1rem 2.5rem; background:linear-gradient(135deg,[color1],[color2]); color:white; margin-bottom:2.5rem;">
  <div style="font-size:2rem;font-weight:800;letter-spacing:-0.02em">[App Name]</div>
  <div style="margin-top:0.5rem;opacity:0.85;font-size:1rem">UI Wireframe Document · 5 Screens</div>
  <div style="margin-top:1.5rem;display:flex;justify-content:center;gap:1rem;font-size:0.8rem;opacity:0.7">
    <span>Screen 1: Dashboard</span><span>·</span>
    <span>Screen 2: [Name]</span><span>·</span>
    <span>Screen 3: [Name]</span><span>·</span>
    <span>Screen 4: [Name]</span><span>·</span>
    <span>Screen 5: [Name]</span>
  </div>
</div>
```

## Output:

Output ONLY the complete HTML document starting with `<!DOCTYPE html>`. No markdown fences, no explanations."""


async def generate_prototype(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
) -> str:
    """
    Generate a 5-screen interactive HTML prototype for the planned application.
    Returns the raw HTML string.
    """
    user_content = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        "Generate the 5-screen interactive HTML prototype now. "
        "Show all screens immediately — no loading states. "
        "Use hardcoded realistic sample data throughout."
    )

    full_html = ""
    try:
        async with _client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
        ) as stream:
            async for text in stream.text_stream:
                full_html += text
    except Exception as exc:
        logger.error("Prototype generation failed: %s", exc)

    # Strip markdown fences if Claude wrapped the HTML
    s = full_html.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines)

    return s.strip()
