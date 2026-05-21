"""
Prototype Generator agent — generates a single-file interactive HTML mockup
of the planned application based on requirements, architecture, and tech stack.
"""
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a UI prototype generator. Given a software project plan, generate a single self-contained HTML file that serves as an interactive mockup of the planned application.

Requirements for the output HTML:
- One file only — embed all CSS and JavaScript inline
- Use Tailwind CSS loaded from CDN: <script src="https://cdn.tailwindcss.com"></script>
- Show 3–5 key screens/pages of the app (login/home/dashboard/details/etc)
- Include a top navigation bar to switch between screens (hide/show sections with JS)
- Fill in realistic sample data relevant to the app domain
- Match the app's color scheme and feel to the domain (e.g. dark for fintech, warm for food, etc.)
- Make buttons, inputs, and cards look interactive even if they don't do anything real
- Output ONLY the complete HTML document starting with <!DOCTYPE html>, nothing else"""


async def generate_prototype(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
) -> str:
    """
    Generate a self-contained HTML prototype page for the planned application.

    Returns the raw HTML string.
    """
    user_content = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        "Generate the interactive HTML prototype now."
    )

    full_html = ""
    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        async for text in stream.text_stream:
            full_html += text

    # Strip markdown fences if Claude wrapped the HTML
    if full_html.strip().startswith("```"):
        lines = full_html.strip().splitlines()
        # Remove first line (```html or ```) and last line (```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        full_html = "\n".join(lines)

    return full_html.strip()
