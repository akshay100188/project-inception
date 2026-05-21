"""
Report Generator agent — produces a comprehensive, print-ready HTML planning document.

Takes all plan data (requirements, architecture, tech stack, estimation) and generates
a single-file HTML report with Chart.js charts, tables, and professional formatting.
The HTML is suitable for opening in a browser and printing to PDF via Ctrl+P.
"""
import json
import logging
import anthropic
from config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a senior technical consultant who produces professional project planning documents for software startups.

Given a structured project plan (requirements, architecture, tech stack, estimation), generate a complete, polished, single-file HTML planning document — the kind a consulting firm would deliver to a client.

## Document sections to include (in order):

1. **Cover Page** — project name, tagline, date, "Confidential Planning Document"
2. **Table of Contents** — linked anchors to each section
3. **Executive Summary** — 3–4 sentence overview, key metrics row (MVP weeks, team size, cost range, confidence)
4. **Business Problem Statement** — numbered list of pain points
5. **Proposed Solution** — bulleted capabilities the platform will deliver
6. **Target Users** — primary vs secondary users in a styled two-column card layout
7. **Scope Definition** — two-column table: In Scope vs Out of Scope
8. **Functional Modules** — HTML table with Module | Description | Priority columns
9. **System Architecture** — chosen pattern with rationale, components table (Name | Role | Tech), data flow narrative, key decisions list
10. **Technology Stack** — card grid per layer (Frontend / Backend / Database / Auth / Infrastructure), then a comparison table if alternatives exist
11. **Database Design** — recommended DB, schema hints, rationale
12. **Infrastructure Plan** — table: Layer | Service | Rationale; deployment topology narrative
13. **Security Recommendations** — two columns: Required Now vs Recommended Later
14. **Budget Projection** — table with cost heads + monthly estimates, PLUS a Chart.js doughnut chart of cost breakdown; total range
15. **Team & Timeline** — team roles table, PLUS a Chart.js horizontal bar Gantt chart of phases with week numbers
16. **Risk Register** — table: Risk | Severity | Mitigation; severity color-coded (High=red, Medium=yellow, Low=green)
17. **Implementation Readiness** — table: Area | Status | Notes; status color-coded
18. **Recommended Implementation Approach** — numbered sequential steps
19. **Deliverables Summary** — checklist of all generated artifacts

## HTML technical requirements:

- Single self-contained file, all CSS and JS inline
- Load Tailwind CSS: `<script src="https://cdn.tailwindcss.com"></script>`
- Load Chart.js: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- White background, professional typography, subtle section dividers
- Cover page takes the full first page (100vh with flex centering)
- Each major section starts with `<section class="page-section">` and has a colored left-border heading
- Add `<div class="page-break"></div>` between major sections for clean PDF pagination
- `@media print` CSS: hide browser chrome, ensure page breaks work, set paper to A4
- The Budget doughnut chart should use the actual cost categories and amounts from the estimation data
- The Gantt chart should use the actual phases and week counts from the estimation data
- Risk table rows must have colored left borders: red for High, yellow for Medium, green for Low
- All tables use alternating row backgrounds for readability
- Hyperlinks in the TOC must jump to section anchors

## Content quality requirements:

- Derive ALL content from the provided plan data — do NOT use placeholder text like "TBD" or "..."
- Expand abbreviated data into full professional sentences
- For budget: if cost data uses USD, show in USD; infer reasonable India-based cost breakdown if domain/region suggests it
- For team roles: derive from recommended_team.roles list
- For phases: use the estimation phases array with deliverables
- Add a professional "Prepared by Project Inception AI" footer on each page
- Color scheme: use indigo/blue as the primary accent color throughout

Output ONLY the complete HTML document starting with <!DOCTYPE html>. No explanations, no markdown fences."""


async def generate_report(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
    estimation: dict,
) -> str:
    """
    Generate a comprehensive HTML planning document for the project.

    Returns the raw HTML string, ready to serve as text/html.
    """
    user_content = (
        f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
        f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
        f"Estimation:\n{json.dumps(estimation, indent=2)}\n\n"
        "Generate the full professional planning document HTML now. "
        "Make every section rich and detailed — this is the primary deliverable the client receives."
    )

    full_html = ""
    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=12000,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        async for text in stream.text_stream:
            full_html += text

    # Strip markdown fences if Claude wrapped the HTML
    stripped = full_html.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)

    return stripped.strip()
