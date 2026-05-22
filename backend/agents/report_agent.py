"""
Report Generator agent — produces a comprehensive, print-ready HTML planning document.

Generates in three sequential API calls to stay within the 8k output token limit:
  Part A: <!DOCTYPE html> … sections 1–10, main wrapper div left OPEN
  Part B: sections 11–15 as bare <section> elements (no wrapper)
  Part C: sections 16–19 as bare <section> elements + </div></body></html>
"""
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

Generate Part A of the report: the full document shell (DOCTYPE, head, CSS) plus sections 1–10.

## Exact HTML skeleton to follow:

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project Name] — Planning Report</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    @media print {
      .no-print { display: none !important; }
      .page-break { page-break-after: always; break-after: page; }
      body { font-size: 11pt; }
    }
    .section-heading {
      border-left: 4px solid #4f46e5;
      padding-left: 12px;
      font-size: 1.25rem;
      font-weight: 700;
      color: #1e1b4b;
      margin-bottom: 1rem;
    }
    .page-break { page-break-after: always; break-after: page; margin: 2rem 0; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #eef2ff; color: #3730a3; padding: 8px 12px; text-align: left; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
    td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; }
    tr:nth-child(even) td { background: #f9fafb; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    footer { text-align: center; font-size: 0.7rem; color: #9ca3af; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }
  </style>
</head>
<body class="bg-white text-gray-800 font-sans">
<div class="max-w-4xl mx-auto px-8 py-10">
```

Then generate content for:

**Section 1 — Cover Page** (`<section id="sec-1">`)
- Large project name, tagline, today's date, "Confidential Planning Document" badge (indigo bg)
- "Prepared by Project Inception AI" subtitle
- Full-page feel: `min-height: 60vh; display:flex; flex-direction:column; justify-content:center`

**Section 2 — Table of Contents** (`<section id="sec-2">`)
- Numbered list, all 19 sections, hyperlinked to #sec-1 through #sec-19
- Two-column layout inside the section only

**Section 3 — Executive Summary** (`<section id="sec-3">`)
- 3–4 sentence paragraph
- Metrics row: 4 cards side by side (MVP weeks | Full weeks | Team size | Confidence)

**Section 4 — Business Problem Statement** (`<section id="sec-4">`)
- Numbered list of 4–6 pain points derived from requirements

**Section 5 — Proposed Solution** (`<section id="sec-5">`)
- Bulleted list of 5–7 platform capabilities

**Section 6 — Target Users** (`<section id="sec-6">`)
- Two cards side by side: Primary Users | Secondary Users (each with bullet list of characteristics)

**Section 7 — Scope Definition** (`<section id="sec-7">`)
- Single table: "In Scope" column | "Out of Scope" column

**Section 8 — Functional Modules** (`<section id="sec-8">`)
- Table: Module | Description | Priority (Priority cell: must-have=indigo badge, nice-to-have=gray badge)

**Section 9 — System Architecture** (`<section id="sec-9">`)
- Architecture pattern badge, rationale paragraph
- Components table: Name | Role | Tech Hint
- Data flow narrative paragraph
- Key decisions as numbered list

**Section 10 — Technology Stack** (`<section id="sec-10">`)
- Card grid (2 columns): one card per layer (Frontend / Backend / Database / Auth / Infrastructure)
- Each card: layer name, tech name bold, rationale small text, key libs as inline tags
- If alternatives exist: small table below the grid

## CRITICAL — how to end Part A:

After section 10, add a footer inside the section, then output EXACTLY:
<!-- PART_A_END -->

Do NOT close the `<div class="max-w-4xl mx-auto">` wrapper.
Do NOT write </body> or </html>.
Do NOT generate sections 11–19.
Output raw HTML only — no markdown fences, no comments outside the HTML."""

_SYSTEM_PROMPT_B = """You are continuing a professional HTML planning document. Sections 1–10 are already generated inside an open `<div class="max-w-4xl mx-auto px-8 py-10">` wrapper.

Generate ONLY sections 11–15 as bare `<section>` elements. Rules:
- Do NOT output DOCTYPE, html, head, body, style, or any wrapper divs
- Start your output directly with `<div class="page-break"></div><section id="sec-11">`
- Close every `<section>` properly before starting the next one
- Use the same CSS classes defined in Part A (section-heading, badge, page-break, table styles)
- Chart.js is already loaded — you can use `<canvas>` + inline `<script>` for charts

**Section 11 — Database Design** (`<section id="sec-11">`)
- Recommended DB with rationale paragraph
- Entity overview: table with columns Entity | Key Fields | Relationships
- Schema hints paragraph

**Section 12 — Infrastructure Plan** (`<section id="sec-12">`)
- Table: Layer | Service | Rationale
- Deployment topology narrative paragraph

**Section 13 — Security Recommendations** (`<section id="sec-13">`)
- Table with two columns: Required Now | Recommended Later (4–5 rows each)

**Section 14 — Budget Projection** (`<section id="sec-14">`)
- Cost breakdown table: Category | Low Estimate | High Estimate | Notes
- USE THE ACTUAL mvp_low and mvp_high numbers from estimation data
- Chart.js doughnut chart showing cost category breakdown (inline canvas + script)
- Total range prominently shown

**Section 15 — Team & Timeline** (`<section id="sec-15">`)
- Team roles table: Role | Responsibilities | Count
- Chart.js horizontal bar Gantt chart using ACTUAL phase names and week counts from estimation.phases
- Footer line: total MVP duration and full product duration

## End with EXACTLY:
<!-- PART_B_END -->

Do NOT write </div></body></html>. Output raw HTML only."""

_SYSTEM_PROMPT_C = """You are completing a professional HTML planning document. Sections 1–15 are already generated inside an open `<div class="max-w-4xl mx-auto px-8 py-10">` wrapper.

Generate sections 16–19 as bare `<section>` elements, then close the document. Rules:
- Do NOT output DOCTYPE, html, head, body, style, or any wrapper divs
- Start your output directly with `<div class="page-break"></div><section id="sec-16">`
- Close every `<section>` properly before starting the next one
- Use the same CSS classes: section-heading, badge, page-break, table styles

**Section 16 — Risk Register** (`<section id="sec-16">`)
- Table: Risk | Severity | Probability | Mitigation
- Left border color per row: `style="border-left: 4px solid #ef4444"` for High, `#f59e0b` for Medium, `#10b981` for Low
- 5–6 realistic risks derived from the project domain and tech stack

**Section 17 — Implementation Readiness** (`<section id="sec-17">`)
- Table: Area | Status | Notes
- Status as colored badge: Ready=green, Partial=yellow, Pending=red
- Areas: Team, Infrastructure, Third-party APIs, Security, Testing, Compliance

**Section 18 — Recommended Implementation Approach** (`<section id="sec-18">`)
- Numbered list of 6–8 sequential steps, each with a bold title and 1–2 sentence description

**Section 19 — Deliverables Summary** (`<section id="sec-19">`)
- Checklist grouped by category (Planning / Technical / Documentation / Launch)
- Each item: ☐ checkbox style, artifact name, brief description

After section 19 add:
```html
<footer>Prepared by Project Inception AI · Confidential · Generated on [today's date]</footer>
</div>
</body>
</html>
```

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
    """Keep only the content before `marker`; fall back to stripping closing tags."""
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
    for tag in ("<div class=\"page-break\"", "<section"):
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
    Generate a 19-section professional HTML planning document via three API calls.
    Returns stitched HTML ready to serve as text/html.
    """
    plan_json = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        f"Estimation:\n{json.dumps(estimation, indent=2)}"
    )

    part_a = _strip_fences(await _call(
        _SYSTEM_PROMPT_A,
        plan_json + "\n\nGenerate Part A (sections 1–10). Derive all content from the plan data.",
        "Part-A",
    ))
    part_b = _strip_fences(await _call(
        _SYSTEM_PROMPT_B,
        plan_json + "\n\nGenerate Part B (sections 11–15). Use real numbers for charts.",
        "Part-B",
    ))
    part_c = _strip_fences(await _call(
        _SYSTEM_PROMPT_C,
        plan_json + "\n\nGenerate Part C (sections 16–19 + closing). Derive risks from the actual stack.",
        "Part-C",
    ))

    part_a = _cut_before(part_a, "<!-- PART_A_END -->")
    part_b = _cut_before(_drop_doc_shell(part_b), "<!-- PART_B_END -->")
    part_c = _drop_doc_shell(part_c)

    return (part_a + "\n\n" + part_b + "\n\n" + part_c).strip()
