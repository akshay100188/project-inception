"""
Prototype Generator agent — generates a multi-screen interactive HTML mockup.
"""
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a UI prototype generator. Given a software project plan, generate a single self-contained HTML file showing a complete interactive app mockup with 5 distinct screens.

## Layout structure (MANDATORY):

```
+------------------+----------------------------------------+
|  App Logo + Name |  Top bar with user avatar / actions    |
+------------------+----------------------------------------+
|                  |                                        |
|  [Screen 1 nav]  |   Main content area                   |
|  [Screen 2 nav]  |   (changes when nav item clicked)     |
|  [Screen 3 nav]  |                                        |
|  [Screen 4 nav]  |                                        |
|  [Screen 5 nav]  |                                        |
|                  |                                        |
+------------------+----------------------------------------+
```

- Fixed left sidebar (w-56, bg-gray-900, text-white) with the 5 nav items
- Top bar (h-14, border-b) with app name and user avatar
- Main content area fills the rest of the viewport
- Clicking a sidebar item shows that screen's div and hides the others

## The 5 screens to generate (adapt names to the app domain):

Choose 5 screens appropriate for the specific app being built. Common examples:
- Dashboard/Overview — stats cards, recent activity, charts
- Main list view — data table/grid with filters and search bar
- Detail/single item view — full record with actions (edit, delete, share)
- Create/Edit form — multi-field form appropriate to the domain
- Settings/Profile — user preferences, account info, configuration

## CRITICAL rules — read carefully:

1. **NO loading states whatsoever.** Do not use `setTimeout`, `fetch`, `XMLHttpRequest`, or any async operation. Every screen shows its content immediately.
2. **All data must be hardcoded inline** — realistic sample data matching the app's domain (e.g. real-sounding names, realistic numbers, relevant categories).
3. **Screen switching via JS only** — on click: hide all `.screen` divs, show the clicked one, update sidebar active state.
4. **Screen 1 (Dashboard) is visible by default** — all others have `style="display:none"`.
5. Use Tailwind CSS from CDN for all styling: `<script src="https://cdn.tailwindcss.com"></script>`
6. Match the color scheme to the domain (fintech=slate/blue, health=green/teal, food=orange/warm, etc.)
7. Make it look complete and realistic — filled cards, realistic table rows, proper form inputs with placeholder values
8. Buttons and inputs can be non-functional (no JS needed) except for the sidebar navigation

## Output:

Output ONLY the complete HTML document starting with <!DOCTYPE html>. No markdown fences, no explanations."""


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
