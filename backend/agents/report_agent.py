"""
Report Generator agent — produces a comprehensive, print-ready HTML planning document.

Generates the report in two parts to stay within model output limits:
  Part A: cover + TOC + sections 1-10 (structure through tech stack)
  Part B: sections 11-19 (database through deliverables) + closing tags
Both parts are stitched into a single self-contained HTML file.
"""
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

_SHARED_STYLE_NOTE = """
## Shared style rules (apply throughout):
- Tailwind CSS via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Chart.js via CDN: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- White background, professional typography, indigo/blue as primary accent color
- Each major section: `<section class="page-section" id="sec-N">` with a colored left-border heading
- `<div class="page-break"></div>` between major sections for PDF pagination
- All tables: alternating row backgrounds, clear headers
- `@media print` CSS: hide browser chrome, A4 paper, preserve page breaks
- Footer on every page: "Prepared by Project Inception AI"
"""

_SYSTEM_PROMPT_A = (
    """You are a senior technical consultant producing a professional project planning document.

Generate the FIRST HALF of a complete, single-file HTML planning document for a software project.
"""
    + _SHARED_STYLE_NOTE
    + """
## Sections to generate (in order):

1. **Cover Page** — project name, tagline, today's date, "Confidential Planning Document" badge
2. **Table of Contents** — all 19 section links with anchor hrefs (#sec-1 … #sec-19)
3. **Executive Summary** — 3–4 sentences, key metrics row: MVP weeks / team size / cost range / confidence
4. **Business Problem Statement** — numbered list of pain points derived from requirements
5. **Proposed Solution** — bulleted capabilities the platform delivers
6. **Target Users** — primary vs secondary users in a two-column card layout
7. **Scope Definition** — two-column table: In Scope | Out of Scope
8. **Functional Modules** — table: Module | Description | Priority (color-coded)
9. **System Architecture** — pattern + rationale, components table (Name | Role | Tech), data flow narrative, key decisions list
10. **Technology Stack** — card grid per layer, alternatives comparison table if alternatives exist

## CRITICAL: how to end this response

After section 10, output EXACTLY this marker on its own line and nothing after it:
<!-- PART_A_END -->

Do NOT include </body> or </html>. Do NOT generate sections 11-19 here.
Output ONLY the HTML, no markdown fences."""
)

_SYSTEM_PROMPT_B = (
    """You are a senior technical consultant completing the second half of a professional project planning document.

The document's <!DOCTYPE html>, <head>, all CSS, all JS CDN imports, and sections 1-10 have already been generated.
Generate ONLY the HTML content for sections 11-19 — no DOCTYPE, no <html>, no <head>, no repeated <style> or <script src> tags.
Use the same Tailwind CSS classes and indigo/blue color scheme as the rest of the document.
"""
    + _SHARED_STYLE_NOTE
    + """
## Sections to generate (in order):

11. **Database Design** (`id="sec-11"`) — recommended DB with schema hints, rationale, entity relationship hints
12. **Infrastructure Plan** (`id="sec-12"`) — table: Layer | Service | Rationale; deployment topology narrative
13. **Security Recommendations** (`id="sec-13"`) — two-column layout: Required Now | Recommended Later
14. **Budget Projection** (`id="sec-14"`) — cost breakdown table + Chart.js doughnut chart of cost categories; total range
15. **Team & Timeline** (`id="sec-15"`) — team roles table + Chart.js horizontal bar Gantt chart using actual phase names and week counts
16. **Risk Register** (`id="sec-16"`) — table: Risk | Severity | Mitigation; left-border color: red=High, yellow=Medium, green=Low
17. **Implementation Readiness** (`id="sec-17"`) — table: Area | Status | Notes; status badge color-coded
18. **Recommended Implementation Approach** (`id="sec-18"`) — numbered sequential steps with detail
19. **Deliverables Summary** (`id="sec-19"`) — checklist of all artifacts this project will produce

After section 19, close the document properly:
```
    </div><!-- end main wrapper -->
  </body>
</html>
```

Output ONLY the HTML fragment for sections 11-19 plus the closing tags. No markdown fences."""
)


async def _call_claude(system: str, user_content: str, label: str) -> str:
    """Single streaming Claude call; returns accumulated text."""
    full = ""
    try:
        async with _client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
        ) as stream:
            async for text in stream.text_stream:
                full += text
    except Exception as exc:
        logger.error("Report %s call failed: %s", label, exc)
    logger.info("Report %s: %d chars generated", label, len(full))
    return full


def _strip_fences(html: str) -> str:
    s = html.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines)
    return s.strip()


async def generate_report(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
    estimation: dict,
) -> str:
    """
    Generate a comprehensive HTML planning document split across two API calls.
    Returns the stitched HTML string, ready to serve as text/html.
    """
    plan_context = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        f"Estimation:\n{json.dumps(estimation, indent=2)}"
    )

    user_a = (
        plan_context
        + "\n\nGenerate Part A of the report now (sections 1-10). "
        "Be thorough but concise per section — all content must come from the plan data above."
    )
    user_b = (
        plan_context
        + "\n\nGenerate Part B of the report now (sections 11-19 + closing tags). "
        "Derive all content from the plan data. Make the budget chart and Gantt chart use real numbers."
    )

    part_a_raw, part_b_raw = await _call_claude(_SYSTEM_PROMPT_A, user_a, "Part-A"), ""
    part_a_raw = _strip_fences(part_a_raw)

    # Split at the marker — keep everything before it
    marker = "<!-- PART_A_END -->"
    if marker in part_a_raw:
        part_a_html = part_a_raw.split(marker)[0].rstrip()
    else:
        # Marker missing — trim any accidental closing tags Claude added
        part_a_html = part_a_raw
        for closing in ["</body>", "</html>"]:
            if part_a_html.rstrip().endswith(closing):
                part_a_html = part_a_html.rstrip()[: -len(closing)].rstrip()

    part_b_raw = await _call_claude(_SYSTEM_PROMPT_B, user_b, "Part-B")
    part_b_html = _strip_fences(part_b_raw)

    # Remove any accidental DOCTYPE / html / head re-declarations in Part B
    if "<!DOCTYPE" in part_b_html:
        # Find the first <section or <div after the head-like content
        for tag in ["<section", "<div"]:
            idx = part_b_html.find(tag)
            if idx != -1:
                part_b_html = part_b_html[idx:]
                break

    full_html = part_a_html + "\n\n" + part_b_html
    return full_html.strip()
