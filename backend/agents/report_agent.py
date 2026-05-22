"""
Report Generator agent — produces a comprehensive, print-ready HTML planning document.

Generates the report in three parts to stay within model output limits (~8k tokens each):
  Part A: cover + TOC + sections 1–10 (structure through tech stack)
  Part B: sections 11–15 (database, infrastructure, security, budget chart, Gantt chart)
  Part C: sections 16–19 (risk register, readiness, approach, deliverables) + closing tags
All three parts are stitched into a single self-contained HTML file.
"""
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

_STYLE_NOTE = """
Style rules (consistent across all parts):
- Tailwind CSS via CDN already loaded in <head>
- Chart.js via CDN already loaded in <head>
- White background, indigo/blue primary accent color
- Each section: `<section class="page-section" id="sec-N">` with colored left-border heading
- `<div class="page-break"></div>` between major sections for PDF page breaks
- All tables: alternating row backgrounds (bg-gray-50 / white), sticky headers where helpful
- @media print CSS applied globally from Part A's <style>
- Footer "Prepared by Project Inception AI" on each conceptual page
"""

_SYSTEM_PROMPT_A = """You are a senior technical consultant producing a professional project planning document.

Generate the FIRST PART of a complete single-file HTML planning document.
""" + _STYLE_NOTE + """

## Your output must include:

- Full `<!DOCTYPE html>` … `<head>` with Tailwind CDN, Chart.js CDN, and a `<style>` block containing:
  - `.page-section { margin: 2rem 0; padding: 1.5rem; }` and similar base styles
  - `.page-break { page-break-after: always; break-after: page; }`
  - `@media print { nav { display:none; } .page-break { page-break-after: always; } body { font-size: 11pt; } }`
  - A sticky left-border heading style for section titles
- Opening `<body>` and a centered max-width wrapper `<div class="max-w-4xl mx-auto px-6 py-8">`

Then generate these sections:

1. **Cover Page** (`id="sec-1"`) — project name large, tagline, today's date, "Confidential Planning Document" badge
2. **Table of Contents** (`id="sec-2"`) — anchor links to all 19 sections (#sec-1 … #sec-19), numbered list
3. **Executive Summary** (`id="sec-3"`) — 3–4 sentences; metrics row showing MVP weeks, team size, cost range, confidence level
4. **Business Problem Statement** (`id="sec-4"`) — numbered list of pain points from requirements
5. **Proposed Solution** (`id="sec-5"`) — bulleted list of platform capabilities
6. **Target Users** (`id="sec-6"`) — two-column card layout: primary users vs secondary users
7. **Scope Definition** (`id="sec-7"`) — two-column table: In Scope | Out of Scope
8. **Functional Modules** (`id="sec-8"`) — HTML table: Module | Description | Priority (Priority cell color-coded)
9. **System Architecture** (`id="sec-9"`) — pattern badge + rationale paragraph, components table (Name | Role | Tech Hint), data flow narrative, key decisions list
10. **Technology Stack** (`id="sec-10"`) — card grid per layer (Frontend/Backend/Database/Auth/Infrastructure), alternatives table if present

## CRITICAL: End your output with EXACTLY this marker and nothing after it:
<!-- PART_A_END -->

Do NOT write </body> or </html>. Do NOT generate sections 11-19.
Output ONLY valid HTML — no markdown fences, no explanations."""

_SYSTEM_PROMPT_B = """You are continuing a professional HTML planning document. Sections 1-10 and all CSS/JS are already generated.

Generate ONLY the HTML for sections 11-15 — no DOCTYPE, no <html>, no <head>, no repeated <style> or CDN tags.
Use the same Tailwind classes and indigo/blue color scheme.
""" + _STYLE_NOTE + """

## Generate these sections:

11. **Database Design** (`id="sec-11"`) — recommended DB engine, schema hints, entity overview table (Entity | Key Fields | Relationships), rationale paragraph
12. **Infrastructure Plan** (`id="sec-12"`) — table: Layer | Service | Rationale; plus a deployment topology narrative paragraph
13. **Security Recommendations** (`id="sec-13"`) — two-column layout table: Required Now | Recommended Later, each with 4-5 specific items
14. **Budget Projection** (`id="sec-14"`) — cost breakdown table (Category | Estimate | Notes); PLUS a Chart.js doughnut chart using REAL cost numbers from the estimation data; total range prominently displayed
15. **Team & Timeline** (`id="sec-15"`) — team roles table (Role | Responsibilities | % Time); PLUS a Chart.js horizontal bar Gantt chart using REAL phase names and week counts from the estimation data

## CRITICAL: End your output with EXACTLY this marker and nothing after it:
<!-- PART_B_END -->

Do NOT write </body> or </html>. Do NOT generate sections 16-19.
Output ONLY valid HTML — no markdown fences."""

_SYSTEM_PROMPT_C = """You are completing a professional HTML planning document. Sections 1-15 and all CSS/JS are already generated.

Generate ONLY the HTML for sections 16-19 plus the proper document closing tags.
No DOCTYPE, no <html>, no <head>, no repeated <style> or CDN tags.
Use the same Tailwind classes and indigo/blue color scheme.
""" + _STYLE_NOTE + """

## Generate these sections:

16. **Risk Register** (`id="sec-16"`) — table: Risk | Severity | Mitigation; left-border color per row: red border for High, yellow for Medium, green for Low; derive 4-6 realistic risks from the project data
17. **Implementation Readiness** (`id="sec-17"`) — table: Area | Status | Notes; Status shown as a colored badge (Ready=green, Partial=yellow, Pending=red); cover areas like Team, Infrastructure, Data, Compliance, Testing
18. **Recommended Implementation Approach** (`id="sec-18"`) — numbered step-by-step plan (6-8 steps) with a short description per step
19. **Deliverables Summary** (`id="sec-19"`) — checklist of all artifacts this engagement produces (checkboxes styled with ✓), grouped by category

After section 19, close the document:
```
  </div><!-- end main wrapper -->
  </body>
</html>
```

Output ONLY valid HTML — no markdown fences."""


async def _call(system: str, user_content: str, label: str) -> str:
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
    logger.info("Report %s: %d chars", label, len(full))
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
    """Return everything before marker; if missing, strip accidental closing tags."""
    if marker in html:
        return html.split(marker)[0].rstrip()
    # Marker absent — trim accidental closing tags Claude may have added
    for tag in ["</body>", "</html>"]:
        if html.rstrip().endswith(tag):
            html = html.rstrip()[: -len(tag)].rstrip()
    return html


def _remove_doc_boilerplate(html: str) -> str:
    """Strip any accidental DOCTYPE/html/head re-declarations from continuation parts."""
    if "<!DOCTYPE" not in html and "<html" not in html:
        return html
    for tag in ["<section", "<div"]:
        idx = html.find(tag)
        if idx != -1:
            return html[idx:]
    return html


async def generate_report(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
    estimation: dict,
) -> str:
    """
    Generate a comprehensive 19-section HTML planning document via three API calls.
    Returns stitched HTML ready to serve as text/html.
    """
    plan_json = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        f"Estimation:\n{json.dumps(estimation, indent=2)}"
    )

    user_a = plan_json + "\n\nGenerate Part A (sections 1–10). Use real data throughout."
    user_b = plan_json + "\n\nGenerate Part B (sections 11–15). Use real cost/phase numbers for charts."
    user_c = plan_json + "\n\nGenerate Part C (sections 16–19 + closing tags). Derive risks from actual project data."

    # Run sequentially — each part is independent content-wise
    part_a = _strip_fences(await _call(_SYSTEM_PROMPT_A, user_a, "Part-A"))
    part_b = _strip_fences(await _call(_SYSTEM_PROMPT_B, user_b, "Part-B"))
    part_c = _strip_fences(await _call(_SYSTEM_PROMPT_C, user_c, "Part-C"))

    part_a = _cut_at(part_a, "<!-- PART_A_END -->")
    part_b = _cut_at(_remove_doc_boilerplate(part_b), "<!-- PART_B_END -->")
    part_c = _remove_doc_boilerplate(part_c)

    return (part_a + "\n\n" + part_b + "\n\n" + part_c).strip()
