"""
Report Generator agent — produces a comprehensive, print-ready HTML planning document.

Generates in four PARALLEL API calls (all receive the same plan data):
  Part A: <!DOCTYPE html> … sections 1–5, main wrapper div left OPEN
  Part B: sections 6–10 as bare <section> elements
  Part C: sections 11–15 as bare <section> elements (CSS charts, no Chart.js)
  Part D: sections 16–19 as bare <section> elements + </div></body></html>

All four calls run concurrently via asyncio.gather, cutting total time to ~3–4 min.
"""
import asyncio
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# System prompts
# --------------------------------------------------------------------------- #

_SYSTEM_PROMPT_A = """You are a senior technical consultant writing a professional project planning document in HTML.

Generate Part A: the full document shell (DOCTYPE, head, CSS) plus sections 1–5 only.

## Exact HTML skeleton to start with:

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project Name] — Planning Report</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @media print {
      .no-print { display: none !important; }
      .page-break { page-break-after: always; break-after: page; }
      body { font-size: 11pt; }
    }
    .section-heading { border-left: 4px solid #4f46e5; padding-left: 12px; font-size: 1.25rem; font-weight: 700; color: #1e1b4b; margin-bottom: 1rem; }
    .page-break { page-break-after: always; break-after: page; margin: 2rem 0; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #eef2ff; color: #3730a3; padding: 8px 12px; text-align: left; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
    td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; }
    tr:nth-child(even) td { background: #f9fafb; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    footer { text-align: center; font-size: 0.7rem; color: #9ca3af; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }
    .chart-bar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.6rem; }
    .chart-bar-label { width: 160px; font-size: 0.82rem; color: #374151; flex-shrink: 0; }
    .chart-bar-track { flex: 1; height: 14px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
    .chart-bar-fill { height: 100%; border-radius: 4px; }
    .chart-bar-value { width: 70px; font-size: 0.82rem; font-weight: 600; color: #374151; text-align: right; flex-shrink: 0; }
    .gantt-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
    .gantt-label { width: 150px; font-size: 0.82rem; color: #374151; flex-shrink: 0; }
    .gantt-track { flex: 1; display: flex; gap: 3px; flex-wrap: wrap; }
    .gantt-week { height: 20px; width: 28px; flex-shrink: 0; border-radius: 3px; background: #4f46e5; }
    .gantt-duration { width: 65px; font-size: 0.78rem; color: #6b7280; text-align: right; flex-shrink: 0; }
  </style>
</head>
<body class="bg-white text-gray-800 font-sans">
<div class="max-w-4xl mx-auto px-8 py-10">

Then generate ONLY sections 1–5:

**Section 1 — Cover Page** (id="sec-1")
- Large project name, tagline, today's date, indigo "Confidential Planning Document" badge
- "Prepared by Project Inception AI" subtitle
- min-height:60vh; display:flex; flex-direction:column; justify-content:center

**Section 2 — Table of Contents** (id="sec-2")
- Numbered list of ALL 19 sections linked to #sec-1 through #sec-19
- Names: 1-Cover Page, 2-Table of Contents, 3-Executive Summary, 4-Business Problem Statement, 5-Proposed Solution, 6-Target Users, 7-Scope Definition, 8-Functional Modules, 9-System Architecture, 10-Technology Stack, 11-Database Design, 12-Infrastructure Plan, 13-Security Recommendations, 14-Budget Projection, 15-Team & Timeline, 16-Risk Register, 17-Implementation Readiness, 18-Recommended Implementation Approach, 19-Deliverables Summary
- Two-column layout inside the section

**Section 3 — Executive Summary** (id="sec-3")
- 3-4 sentence paragraph
- 4 metric cards side by side: MVP weeks | Full weeks | Team size | Confidence

**Section 4 — Business Problem Statement** (id="sec-4")
- Numbered list of 4-6 pain points derived from requirements

**Section 5 — Proposed Solution** (id="sec-5")
- Bulleted list of 5-7 platform capabilities

## CRITICAL — how to end Part A:
After section 5 output EXACTLY this marker and nothing else:
<!-- PART_A_END -->

Do NOT close the <div class="max-w-4xl"> wrapper.
Do NOT write </body> or </html>.
Do NOT generate sections 6-19.
Output raw HTML only — no markdown fences."""

_SYSTEM_PROMPT_B = """You are generating sections 6–10 of a professional HTML planning document. The document shell and sections 1–5 are already written and will be prepended to your output.

Generate ONLY sections 6–10 as bare <section> elements. Rules:
- Do NOT output DOCTYPE, html, head, body, style, or any wrapper divs
- Start your output directly with: <div class="page-break"></div><section id="sec-6">
- Close every <section> before opening the next
- Use CSS classes already defined: section-heading, badge, page-break, table/th/td styles

**Section 6 — Target Users** (id="sec-6")
- Two cards side by side: Primary Users | Secondary Users (each with bullet list of characteristics)

**Section 7 — Scope Definition** (id="sec-7")
- Table: In Scope column | Out of Scope column (4-5 rows each)

**Section 8 — Functional Modules** (id="sec-8")
- Table: Module | Description | Priority (must-have = indigo badge, nice-to-have = gray badge)

**Section 9 — System Architecture** (id="sec-9")
- Architecture pattern badge, rationale paragraph
- Components table: Name | Role | Tech Hint
- Data flow narrative paragraph
- Key decisions as numbered list

**Section 10 — Technology Stack** (id="sec-10")
- Card grid (2 columns): one card per layer (Frontend / Backend / Database / Auth / Infrastructure)
- Each card: layer name, tech name bold, rationale small text, key libs as inline tags

## End with EXACTLY:
<!-- PART_B_END -->

Do NOT write </div></body></html>. Output raw HTML only."""

_SYSTEM_PROMPT_C = """You are generating sections 11–15 of a professional HTML planning document. The document shell and sections 1–10 are already written and will be prepended to your output.

Generate ONLY sections 11–15 as bare <section> elements. Rules:
- Do NOT output DOCTYPE, html, head, body, style, or any wrapper divs
- Start your output directly with: <div class="page-break"></div><section id="sec-11">
- Close every <section> before opening the next
- Use CSS classes already defined: section-heading, badge, table styles, chart-bar-*, gantt-*
- Use CSS-based charts only — do NOT use Chart.js or <canvas> elements

**Section 11 — Database Design** (id="sec-11")
- Recommended DB with rationale paragraph
- Entity table: Entity | Key Fields | Relationships
- Schema hints paragraph

**Section 12 — Infrastructure Plan** (id="sec-12")
- Table: Layer | Service | Rationale
- Deployment topology narrative paragraph

**Section 13 — Security Recommendations** (id="sec-13")
- Table: Required Now column | Recommended Later column (4-5 rows each)

**Section 14 — Budget Projection** (id="sec-14")
- Cost breakdown table: Category | Low Estimate | High Estimate | Notes — USE ACTUAL mvp_low and mvp_high from estimation data
- CSS horizontal bar chart below the table using chart-bar / chart-bar-label / chart-bar-track / chart-bar-fill / chart-bar-value divs — bars sized proportionally (largest category = 90% width)
- Total range prominently shown in a highlighted box

**Section 15 — Team & Timeline** (id="sec-15")
- Team roles table: Role | Responsibilities | Count
- CSS Gantt chart using gantt-row / gantt-label / gantt-track / gantt-week / gantt-duration divs — USE ACTUAL phase names and week counts from estimation.phases; render one gantt-week div per week of that phase
- Footer: total MVP duration and full product duration

## End with EXACTLY:
<!-- PART_C_END -->

Do NOT write </div></body></html>. Output raw HTML only."""

_SYSTEM_PROMPT_D = """You are completing a professional HTML planning document. Sections 1–15 are already written inside an open <div class="max-w-4xl mx-auto px-8 py-10"> wrapper. Generate sections 16–19 then close the document.

Rules:
- Do NOT output DOCTYPE, html, head, body, style, or any wrapper divs
- Start your output directly with: <div class="page-break"></div><section id="sec-16">
- Close every <section> before opening the next
- Use CSS classes: section-heading, badge, page-break, table styles

**Section 16 — Risk Register** (id="sec-16")
- Table: Risk | Severity | Probability | Mitigation
- Left border per row: style="border-left:4px solid #ef4444" for High, #f59e0b for Medium, #10b981 for Low
- 5-6 realistic risks derived from the project domain and tech stack

**Section 17 — Implementation Readiness** (id="sec-17")
- Table: Area | Status | Notes
- Status as colored badge: Ready=green, Partial=yellow, Pending=red
- Areas: Team, Infrastructure, Third-party APIs, Security, Testing, Compliance

**Section 18 — Recommended Implementation Approach** (id="sec-18")
- Numbered list of 6-8 sequential steps, each with a bold title and 1-2 sentence description

**Section 19 — Deliverables Summary** (id="sec-19")
- Checklist grouped by category (Planning / Technical / Documentation / Launch)
- Each item: ☐ artifact name — brief description

After section 19 output EXACTLY:
<footer>Prepared by Project Inception AI · Confidential · Generated on [today's date]</footer>
</div>
</body>
</html>

Output raw HTML only — no markdown fences."""

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


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


def _cut_before(html: str, marker: str) -> str:
    """Keep only content before marker; fall back to stripping closing tags."""
    if marker in html:
        return html.split(marker)[0].rstrip()
    for tag in ("</body>", "</html>"):
        if html.rstrip().endswith(tag):
            html = html.rstrip()[: -len(tag)].rstrip()
    return html


def _drop_doc_shell(html: str) -> str:
    """Remove any accidental DOCTYPE/html/head re-declarations from continuation parts."""
    if "<!DOCTYPE" not in html and "<html" not in html:
        return html
    for tag in ('<div class="page-break"', "<section"):
        idx = html.find(tag)
        if idx != -1:
            return html[idx:]
    return html


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


async def generate_report(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
    estimation: dict,
) -> str:
    """
    Generate a 19-section professional HTML planning document via four parallel API calls.
    All parts receive the same plan data and run concurrently — total time ~3-4 min.
    Returns stitched HTML ready to serve as text/html.
    """
    plan_json = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        f"Estimation:\n{json.dumps(estimation, indent=2)}"
    )

    raw_a, raw_b, raw_c, raw_d = await asyncio.gather(
        _call(_SYSTEM_PROMPT_A, plan_json + "\n\nGenerate Part A (sections 1–5). Derive all content from the plan data.", "Part-A"),
        _call(_SYSTEM_PROMPT_B, plan_json + "\n\nGenerate Part B (sections 6–10). Derive all content from the plan data.", "Part-B"),
        _call(_SYSTEM_PROMPT_C, plan_json + "\n\nGenerate Part C (sections 11–15). Use CSS charts only — no Chart.js canvas elements.", "Part-C"),
        _call(_SYSTEM_PROMPT_D, plan_json + "\n\nGenerate Part D (sections 16–19 + closing). Derive risks from the actual tech stack.", "Part-D"),
    )

    part_a = _cut_before(_strip_fences(raw_a), "<!-- PART_A_END -->")
    part_b = _cut_before(_drop_doc_shell(_strip_fences(raw_b)), "<!-- PART_B_END -->")
    part_c = _cut_before(_drop_doc_shell(_strip_fences(raw_c)), "<!-- PART_C_END -->")
    part_d = _drop_doc_shell(_strip_fences(raw_d))

    return (part_a + "\n\n" + part_b + "\n\n" + part_c + "\n\n" + part_d).strip()
