"""
Template-based HTML report generator — zero API calls, zero credits.
Produces the same 19-section planning document as report_agent.py using structured
data already computed by the rule-based (or Claude) agents.
"""
from datetime import date


# ── CSS shell ────────────────────────────────────────────────────────────────

_CSS = """
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
"""

_SECTION_NAMES = [
    "Cover Page", "Table of Contents", "Executive Summary", "Business Problem Statement",
    "Proposed Solution", "Target Users", "Scope Definition", "Functional Modules",
    "System Architecture", "Technology Stack", "Database Design", "Infrastructure Plan",
    "Security Recommendations", "Budget Projection", "Team & Timeline",
    "Risk Register", "Implementation Readiness", "Recommended Implementation Approach",
    "Deliverables Summary",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _h(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _badge(text: str, color: str = "indigo") -> str:
    colors = {
        "indigo": "background:#eef2ff;color:#4338ca",
        "gray":   "background:#f3f4f6;color:#374151",
        "green":  "background:#dcfce7;color:#166534",
        "yellow": "background:#fef9c3;color:#854d0e",
        "red":    "background:#fee2e2;color:#991b1b",
    }
    style = colors.get(color, colors["indigo"])
    return f'<span class="badge" style="{style}">{_h(text)}</span>'


def _pb() -> str:
    return '<div class="page-break"></div>'


def _toc_rows() -> str:
    rows = ""
    for i, name in enumerate(_SECTION_NAMES, 1):
        rows += f'<li><a href="#sec-{i}" style="color:#4f46e5;text-decoration:none;">{i}. {_h(name)}</a></li>'
    return rows


# ── Section builders ─────────────────────────────────────────────────────────

def _sec1_cover(req: dict) -> str:
    name = _h(req.get("project_name") or req.get("name") or "Your Project")
    domain = _h(req.get("domain", "Software Platform"))
    today = date.today().strftime("%B %d, %Y")
    return f"""
<section id="sec-1" style="min-height:60vh;display:flex;flex-direction:column;justify-content:center;padding:3rem 0;">
  <div style="margin-bottom:1.5rem;">{_badge("Confidential Planning Document", "indigo")}</div>
  <h1 style="font-size:2.8rem;font-weight:800;color:#1e1b4b;margin-bottom:0.5rem;">{name}</h1>
  <p style="font-size:1.2rem;color:#6b7280;margin-bottom:2rem;">{domain} · {today}</p>
  <p style="color:#9ca3af;font-size:0.9rem;">Prepared by Project Inception AI</p>
</section>"""


def _sec2_toc() -> str:
    return f"""
{_pb()}
<section id="sec-2">
  <h2 class="section-heading">Table of Contents</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.25rem 2rem;">
    <ol style="padding-left:1.2rem;color:#374151;">{_toc_rows()}</ol>
  </div>
</section>"""


def _sec3_executive(req: dict, est: dict) -> str:
    name = req.get("project_name") or req.get("name") or "This project"
    domain = req.get("domain", "software")
    scale = req.get("scale", "medium")
    features = req.get("core_features", [])
    mvp = est.get("mvp_weeks", "—")
    full = est.get("full_product_weeks", "—")
    team = est.get("recommended_team", {}).get("size", "—")
    conf = est.get("confidence", "medium").capitalize()
    must_have = [f for f in features if isinstance(f, dict) and f.get("priority") == "must-have"]
    summary = (
        f"{_h(str(name))} is a {_h(scale)}-scale {_h(domain)} platform targeting "
        f"{_h(', '.join(req.get('target_users', ['end users'])[:2]))}. "
        f"The MVP focuses on {len(must_have)} core capabilities and is estimated at "
        f"{mvp} weeks with a team of {team} engineers. "
        f"The full product roadmap extends to {full} weeks."
    )
    cards = [
        ("MVP", f"{mvp} weeks"), ("Full Product", f"{full} weeks"),
        ("Team Size", f"{team} engineers"), ("Confidence", conf),
    ]
    card_html = "".join(
        f'<div style="background:#eef2ff;border-radius:8px;padding:1rem;text-align:center;">'
        f'<div style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">{_h(k)}</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:#4f46e5;">{_h(str(v))}</div>'
        f'</div>'
        for k, v in cards
    )
    return f"""
{_pb()}
<section id="sec-3">
  <h2 class="section-heading">Executive Summary</h2>
  <p style="color:#374151;line-height:1.7;margin-bottom:1.5rem;">{summary}</p>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">{card_html}</div>
</section>"""


def _sec4_problem(req: dict) -> str:
    features = req.get("core_features", [])
    domain = req.get("domain", "this space")
    pain_points = [
        f"Lack of a unified {_h(domain)} platform forces users to rely on fragmented tools",
        f"Manual processes lead to inefficiency and human error in core workflows",
        "Existing solutions are either too expensive or lack customisation for specific needs",
        "Poor mobile and web experience reduces user engagement and retention",
    ]
    if features:
        for f in features[:2]:
            feat = f.get("feature", "") if isinstance(f, dict) else str(f)
            pain_points.append(f"No dedicated tooling for {_h(feat.lower())}")
    items = "".join(f"<li style='margin-bottom:0.5rem;'>{p}</li>" for p in pain_points[:6])
    return f"""
{_pb()}
<section id="sec-4">
  <h2 class="section-heading">Business Problem Statement</h2>
  <ol style="color:#374151;line-height:1.8;padding-left:1.2rem;">{items}</ol>
</section>"""


def _sec5_solution(req: dict) -> str:
    features = req.get("core_features", [])
    capabilities = [
        f.get("feature", str(f)) if isinstance(f, dict) else str(f)
        for f in features
    ]
    if not capabilities:
        capabilities = ["Core platform functionality", "User authentication and onboarding",
                        "Admin management dashboard", "Analytics and reporting", "API integrations"]
    items = "".join(f"<li style='margin-bottom:0.5rem;'>{_h(c)}</li>" for c in capabilities[:8])
    return f"""
{_pb()}
<section id="sec-5">
  <h2 class="section-heading">Proposed Solution</h2>
  <ul style="color:#374151;line-height:1.8;padding-left:1.2rem;">{items}</ul>
</section>"""


def _sec6_users(req: dict) -> str:
    users = req.get("target_users", ["End users", "Administrators"])
    primary = users[:max(1, len(users) // 2)]
    secondary = users[max(1, len(users) // 2):]
    def card(title, items):
        lis = "".join(f"<li>{_h(u)}</li>" for u in items)
        return f'<div style="background:#f9fafb;border-radius:8px;padding:1.25rem;"><strong style="color:#1e1b4b;">{title}</strong><ul style="margin-top:0.5rem;color:#374151;padding-left:1.2rem;">{lis}</ul></div>'
    return f"""
{_pb()}
<section id="sec-6">
  <h2 class="section-heading">Target Users</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
    {card("Primary Users", primary or ["End users"])}
    {card("Secondary Users", secondary or ["Administrators"])}
  </div>
</section>"""


def _sec7_scope(req: dict) -> str:
    features = req.get("core_features", [])
    in_scope = [f.get("feature", str(f)) if isinstance(f, dict) else str(f) for f in features[:5]]
    out_scope = [
        "Native mobile app (Phase 2)",
        "Multi-language / i18n support (Phase 2)",
        "Advanced analytics and BI dashboards",
        "White-label / multi-tenant branding",
        "Third-party marketplace integrations",
    ]
    max_rows = max(len(in_scope), len(out_scope))
    rows = ""
    for i in range(max_rows):
        ins = _h(in_scope[i]) if i < len(in_scope) else ""
        out = _h(out_scope[i]) if i < len(out_scope) else ""
        rows += f"<tr><td>✅ {ins}</td><td>❌ {out}</td></tr>"
    return f"""
{_pb()}
<section id="sec-7">
  <h2 class="section-heading">Scope Definition</h2>
  <table><thead><tr><th>In Scope (MVP)</th><th>Out of Scope</th></tr></thead><tbody>{rows}</tbody></table>
</section>"""


def _sec8_modules(req: dict) -> str:
    features = req.get("core_features", [])
    rows = ""
    for f in features:
        if isinstance(f, dict):
            feat = _h(f.get("feature", ""))
            pri = f.get("priority", "must-have")
        else:
            feat = _h(str(f))
            pri = "must-have"
        badge = _badge("must-have", "indigo") if pri == "must-have" else _badge("nice-to-have", "gray")
        rows += f"<tr><td>{feat}</td><td>{feat} module handling all related logic</td><td>{badge}</td></tr>"
    return f"""
{_pb()}
<section id="sec-8">
  <h2 class="section-heading">Functional Modules</h2>
  <table><thead><tr><th>Module</th><th>Description</th><th>Priority</th></tr></thead><tbody>{rows}</tbody></table>
</section>"""


def _sec9_architecture(arch: dict) -> str:
    pattern = arch.get("pattern", "monolith")
    description = arch.get("description", "")
    components = arch.get("components", [])
    data_flow = arch.get("data_flow", "")
    decisions = arch.get("key_decisions", [])

    comp_rows = "".join(
        f"<tr><td><strong>{_h(c.get('name',''))}</strong></td><td>{_h(c.get('role',''))}</td><td><code style='background:#f3f4f6;padding:1px 6px;border-radius:4px;font-size:0.82rem;'>{_h(c.get('tech_hint',''))}</code></td></tr>"
        for c in components
    )
    dec_items = "".join(f"<li style='margin-bottom:0.4rem;'>{_h(d)}</li>" for d in decisions)

    return f"""
{_pb()}
<section id="sec-9">
  <h2 class="section-heading">System Architecture</h2>
  <p style="margin-bottom:1rem;">{_badge(pattern.upper(), "indigo")} &nbsp; {_h(description)}</p>
  <h3 style="font-weight:600;margin-bottom:0.5rem;">Components</h3>
  <table style="margin-bottom:1rem;"><thead><tr><th>Component</th><th>Role</th><th>Tech Hint</th></tr></thead><tbody>{comp_rows}</tbody></table>
  <h3 style="font-weight:600;margin-bottom:0.5rem;">Data Flow</h3>
  <p style="color:#374151;background:#f9fafb;padding:0.75rem 1rem;border-radius:6px;margin-bottom:1rem;">{_h(data_flow)}</p>
  <h3 style="font-weight:600;margin-bottom:0.5rem;">Key Decisions</h3>
  <ol style="color:#374151;padding-left:1.2rem;">{dec_items}</ol>
</section>"""


def _sec10_techstack(stack: dict) -> str:
    layers = stack.get("layers") or stack
    layer_order = ["frontend", "backend", "database", "auth", "infrastructure"]
    layer_labels = {
        "frontend": "Frontend", "backend": "Backend", "database": "Database",
        "auth": "Auth", "infrastructure": "Infrastructure",
    }
    cards = ""
    for key in layer_order:
        layer = layers.get(key)
        if not layer or not isinstance(layer, dict):
            continue
        name = _h(layer.get("name", ""))
        rationale = _h(layer.get("rationale", ""))
        libs = layer.get("key_libs", [])
        lib_tags = " ".join(
            f'<span style="background:#eef2ff;color:#4338ca;padding:1px 8px;border-radius:9999px;font-size:0.72rem;">{_h(l)}</span>'
            for l in libs
        )
        schema = layer.get("schema_hint", "")
        schema_html = f'<p style="font-size:0.78rem;color:#6b7280;margin-top:0.3rem;font-style:italic;">{_h(schema)}</p>' if schema else ""
        cards += f"""
        <div style="background:#f9fafb;border-radius:8px;padding:1rem;">
          <div style="font-size:0.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.07em;">{layer_labels.get(key, key)}</div>
          <div style="font-size:1rem;font-weight:700;color:#1e1b4b;margin:0.25rem 0;">{name}</div>
          <div style="font-size:0.82rem;color:#374151;margin-bottom:0.5rem;">{rationale}</div>
          {lib_tags}
          {schema_html}
        </div>"""
    return f"""
{_pb()}
<section id="sec-10">
  <h2 class="section-heading">Technology Stack</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">{cards}</div>
</section>"""


def _sec11_database(stack: dict) -> str:
    layers = stack.get("layers") or stack
    db_layer = layers.get("database", {}) if isinstance(layers, dict) else {}
    db_name = db_layer.get("name", "PostgreSQL") if isinstance(db_layer, dict) else "PostgreSQL"
    schema_hint = db_layer.get("schema_hint", "") if isinstance(db_layer, dict) else ""
    rationale = db_layer.get("rationale", "") if isinstance(db_layer, dict) else ""

    entities = []
    if schema_hint:
        for e in schema_hint.split(","):
            e = e.strip()
            if e:
                entities.append(e)
    if not entities:
        entities = ["users", "sessions", "records", "audit_log"]

    rows = "".join(
        f"<tr><td><strong>{_h(e)}</strong></td><td>id, created_at, updated_at + domain fields</td><td>Linked to related entities via FK</td></tr>"
        for e in entities
    )

    return f"""
{_pb()}
<section id="sec-11">
  <h2 class="section-heading">Database Design</h2>
  <p style="margin-bottom:1rem;"><strong>{_h(db_name)}</strong> — {_h(rationale)}</p>
  <table style="margin-bottom:1rem;"><thead><tr><th>Entity</th><th>Key Fields</th><th>Relationships</th></tr></thead><tbody>{rows}</tbody></table>
  {f'<p style="color:#6b7280;font-size:0.85rem;font-style:italic;">Schema hint: {_h(schema_hint)}</p>' if schema_hint else ""}
</section>"""


def _sec12_infra(stack: dict) -> str:
    layers = stack.get("layers") or stack
    infra = layers.get("infrastructure", {}) if isinstance(layers, dict) else {}
    infra_name = infra.get("name", "Vercel + Supabase") if isinstance(infra, dict) else str(infra)
    infra_rationale = infra.get("rationale", "") if isinstance(infra, dict) else ""

    rows = [
        ("Frontend", "Vercel / Netlify", "Zero-config CDN deploys from git"),
        ("Backend API", "Railway / Fly.io / AWS ECS", "Containerised service with auto-scaling"),
        ("Database", "Supabase / AWS RDS", "Managed Postgres with automated backups"),
        ("Storage", "Cloudflare R2 / S3", "Object storage for user uploads and assets"),
        ("Monitoring", "Datadog / Sentry", "Error tracking and uptime alerting"),
    ]
    trows = "".join(f"<tr><td>{_h(l)}</td><td>{_h(s)}</td><td>{_h(r)}</td></tr>" for l, s, r in rows)

    return f"""
{_pb()}
<section id="sec-12">
  <h2 class="section-heading">Infrastructure Plan</h2>
  <p style="margin-bottom:1rem;"><strong>{_h(infra_name)}</strong> — {_h(infra_rationale)}</p>
  <table><thead><tr><th>Layer</th><th>Service</th><th>Rationale</th></tr></thead><tbody>{trows}</tbody></table>
</section>"""


def _sec13_security() -> str:
    now = [
        ("HTTPS everywhere", "Enforce TLS 1.2+ on all endpoints"),
        ("JWT authentication", "Short-lived access tokens + refresh token rotation"),
        ("Input validation", "Zod / Pydantic schemas on all API inputs"),
        ("SQL injection prevention", "Parameterised queries / ORM only"),
        ("Secrets management", "Env vars via vault; no secrets in source code"),
    ]
    later = [
        ("Rate limiting", "Per-IP and per-user throttling on sensitive endpoints"),
        ("WAF", "Web Application Firewall for OWASP Top 10 protection"),
        ("Penetration testing", "Annual third-party pen test"),
        ("SOC 2 Type II", "Audit controls for enterprise customers"),
        ("RBAC audit logs", "Immutable access log for compliance"),
    ]
    max_rows = max(len(now), len(later))
    rows = ""
    for i in range(max_rows):
        n = f"<strong>{_h(now[i][0])}</strong> — {_h(now[i][1])}" if i < len(now) else ""
        l = f"<strong>{_h(later[i][0])}</strong> — {_h(later[i][1])}" if i < len(later) else ""
        rows += f"<tr><td>{n}</td><td>{l}</td></tr>"
    return f"""
{_pb()}
<section id="sec-13">
  <h2 class="section-heading">Security Recommendations</h2>
  <table><thead><tr><th>Required Now</th><th>Recommended Later</th></tr></thead><tbody>{rows}</tbody></table>
</section>"""


def _sec14_budget(est: dict) -> str:
    cost = est.get("cost_range", {})
    low = cost.get("mvp_low", 0)
    high = cost.get("mvp_high", 0)
    basis = cost.get("basis", "")
    currency = cost.get("currency", "USD")

    categories = [
        ("Engineering", int(high * 0.55), int(high * 0.65)),
        ("Design (UI/UX)", int(high * 0.10), int(high * 0.15)),
        ("Infrastructure", int(high * 0.05), int(high * 0.08)),
        ("QA & Testing",  int(high * 0.08), int(high * 0.12)),
        ("Contingency",   int(high * 0.08), int(high * 0.12)),
    ]
    max_val = max(h for _, _, h in categories) or 1

    table_rows = "".join(
        f"<tr><td>{_h(cat)}</td><td>${l:,.0f}</td><td>${h:,.0f}</td><td>Estimated allocation</td></tr>"
        for cat, l, h in categories
    )

    bar_colors = ["#4f46e5", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff"]
    bars = ""
    for i, (cat, l, h) in enumerate(categories):
        pct = int((h / max_val) * 90)
        color = bar_colors[i % len(bar_colors)]
        bars += f"""
        <div class="chart-bar">
          <div class="chart-bar-label">{_h(cat)}</div>
          <div class="chart-bar-track"><div class="chart-bar-fill" style="width:{pct}%;background:{color};"></div></div>
          <div class="chart-bar-value">${h:,.0f}</div>
        </div>"""

    return f"""
{_pb()}
<section id="sec-14">
  <h2 class="section-heading">Budget Projection</h2>
  <table style="margin-bottom:1.5rem;"><thead><tr><th>Category</th><th>Low</th><th>High</th><th>Notes</th></tr></thead><tbody>{table_rows}</tbody></table>
  <div style="margin-bottom:1.5rem;">{bars}</div>
  <div style="background:#eef2ff;border-radius:8px;padding:1rem;text-align:center;">
    <div style="font-size:0.8rem;color:#6b7280;">Total MVP Range ({currency})</div>
    <div style="font-size:1.8rem;font-weight:700;color:#4f46e5;">${low:,.0f} – ${high:,.0f}</div>
    <div style="font-size:0.8rem;color:#6b7280;margin-top:0.25rem;">{_h(basis)}</div>
  </div>
</section>"""


def _sec15_team_timeline(est: dict) -> str:
    team = est.get("recommended_team", {})
    roles = team.get("roles", ["Full-Stack Engineer"])
    phases = est.get("phases", [])
    mvp_weeks = est.get("mvp_weeks", 12)
    full_weeks = est.get("full_product_weeks", 24)

    role_rows = "".join(
        f"<tr><td><strong>{_h(r)}</strong></td><td>Feature development, code review, and delivery</td><td>1</td></tr>"
        for r in roles
    )

    gantt_rows = ""
    colors = ["#4f46e5", "#7c3aed", "#db2777", "#0891b2", "#059669"]
    for i, phase in enumerate(phases):
        pname = phase.get("name", f"Phase {i+1}")
        weeks = phase.get("weeks", 2)
        color = colors[i % len(colors)]
        week_blocks = "".join(
            f'<div class="gantt-week" style="background:{color};"></div>' for _ in range(weeks)
        )
        gantt_rows += f"""
        <div class="gantt-row">
          <div class="gantt-label">{_h(pname)}</div>
          <div class="gantt-track">{week_blocks}</div>
          <div class="gantt-duration">{weeks}w</div>
        </div>"""

    return f"""
{_pb()}
<section id="sec-15">
  <h2 class="section-heading">Team &amp; Timeline</h2>
  <h3 style="font-weight:600;margin-bottom:0.5rem;">Recommended Team</h3>
  <table style="margin-bottom:1.5rem;"><thead><tr><th>Role</th><th>Responsibilities</th><th>Count</th></tr></thead><tbody>{role_rows}</tbody></table>
  <h3 style="font-weight:600;margin-bottom:0.75rem;">MVP Gantt Chart</h3>
  {gantt_rows}
  <p style="margin-top:1rem;font-size:0.85rem;color:#6b7280;">
    MVP duration: <strong>{mvp_weeks} weeks</strong> &nbsp;·&nbsp; Full product: <strong>{full_weeks} weeks</strong>
  </p>
</section>"""


def _sec16_risks(req: dict, arch: dict, stack: dict) -> str:
    risks_base = [
        ("Scope creep from evolving requirements", "High", "Medium",
         "Lock scope for MVP sprint; change requests go to backlog"),
        ("Third-party API downtime or breaking changes", "Medium", "Medium",
         "Abstract integrations behind an adapter layer; circuit-breaker pattern"),
        ("Performance bottlenecks at scale", "Medium", "Low",
         "Load test at 2× expected peak before launch; cache hot paths"),
        ("Security vulnerabilities in dependencies", "High", "Low",
         "Automated dependency scanning (Dependabot / Snyk) in CI"),
        ("Team availability and knowledge gaps", "Medium", "Medium",
         "Document architecture decisions; pair-program critical modules"),
        ("Data migration complexity", "Medium", "Low",
         "Incremental migration scripts with rollback procedures"),
    ]
    severity_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
    rows = ""
    for risk, sev, prob, mit in risks_base:
        color = severity_color.get(sev, "#6b7280")
        rows += f'<tr style="border-left:4px solid {color};"><td>{_h(risk)}</td><td>{_badge(sev, "red" if sev=="High" else "yellow" if sev=="Medium" else "green")}</td><td>{_h(prob)}</td><td>{_h(mit)}</td></tr>'
    return f"""
{_pb()}
<section id="sec-16">
  <h2 class="section-heading">Risk Register</h2>
  <table><thead><tr><th>Risk</th><th>Severity</th><th>Probability</th><th>Mitigation</th></tr></thead><tbody>{rows}</tbody></table>
</section>"""


def _sec17_readiness() -> str:
    areas = [
        ("Team",              "Partial", "Core team identified; need to confirm availability"),
        ("Infrastructure",    "Pending", "Cloud accounts and CI/CD pipeline to be provisioned"),
        ("Third-party APIs",  "Partial", "API keys requested; sandbox environments available"),
        ("Security",          "Pending", "Security review and secrets management setup required"),
        ("Testing",           "Partial", "Unit test framework selected; E2E setup pending"),
        ("Compliance",        "Pending", "Legal review of data handling and privacy policy needed"),
    ]
    status_color = {"Ready": "green", "Partial": "yellow", "Pending": "red"}
    rows = "".join(
        f"<tr><td>{_h(area)}</td><td>{_badge(status, status_color.get(status,'gray'))}</td><td>{_h(notes)}</td></tr>"
        for area, status, notes in areas
    )
    return f"""
{_pb()}
<section id="sec-17">
  <h2 class="section-heading">Implementation Readiness</h2>
  <table><thead><tr><th>Area</th><th>Status</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table>
</section>"""


def _sec18_approach() -> str:
    steps = [
        ("Discovery & Architecture Sign-off",
         "Finalise requirements, confirm architecture pattern, and get stakeholder sign-off before writing a line of code."),
        ("Environment Setup & CI/CD",
         "Provision cloud accounts, configure the repo, set up automated testing and deployment pipelines."),
        ("Authentication & Core Data Model",
         "Implement auth, define the database schema, and seed reference data — everything else builds on this."),
        ("MVP Feature Build (Iterative Sprints)",
         "Deliver must-have features in 1–2 week sprints with demos at the end of each sprint."),
        ("Integration Sprint",
         "Connect all third-party services (payments, email, storage) and harden error handling."),
        ("Quality & Performance Pass",
         "Run E2E tests, load tests, and a security scan; fix any critical findings before launch."),
        ("Soft Launch & Monitoring",
         "Deploy to production with feature flags; monitor error rates and performance dashboards."),
        ("Feedback Loop & Roadmap",
         "Collect user feedback, prioritise the backlog, and plan Phase 2 features."),
    ]
    items = "".join(
        f"<li style='margin-bottom:0.75rem;'><strong>{_h(title)}</strong> — {_h(desc)}</li>"
        for title, desc in steps
    )
    return f"""
{_pb()}
<section id="sec-18">
  <h2 class="section-heading">Recommended Implementation Approach</h2>
  <ol style="color:#374151;line-height:1.8;padding-left:1.2rem;">{items}</ol>
</section>"""


def _sec19_deliverables() -> str:
    groups = {
        "Planning": [
            ("Requirements document", "Signed-off functional and non-functional requirements"),
            ("Architecture decision record", "Rationale for all key architecture choices"),
            ("Project timeline", "Gantt chart with milestones and owner assignments"),
        ],
        "Technical": [
            ("Source code repository", "Versioned monorepo with CI/CD configured"),
            ("Database schema + migrations", "Version-controlled migration scripts"),
            ("API documentation", "OpenAPI / Swagger spec for all endpoints"),
            ("Deployed MVP", "Production environment with monitoring enabled"),
        ],
        "Documentation": [
            ("README and setup guide", "Local development and environment variable reference"),
            ("Architecture diagram", "Component diagram and data-flow walkthrough"),
            ("Runbook", "On-call procedures and incident response guide"),
        ],
        "Launch": [
            ("QA sign-off report", "Test coverage summary and critical bug resolution log"),
            ("Security scan results", "OWASP dependency and SAST scan output"),
            ("Post-launch monitoring baseline", "Error rate and latency SLOs agreed with team"),
        ],
    }
    body = ""
    for group, items in groups.items():
        lis = "".join(
            f"<li style='margin-bottom:0.3rem;'>☐ <strong>{_h(name)}</strong> — {_h(desc)}</li>"
            for name, desc in items
        )
        body += f"<h3 style='font-weight:600;margin:1rem 0 0.5rem;color:#1e1b4b;'>{_h(group)}</h3><ul style='padding-left:1.5rem;color:#374151;'>{lis}</ul>"
    return f"""
{_pb()}
<section id="sec-19">
  <h2 class="section-heading">Deliverables Summary</h2>
  {body}
</section>"""


# ── Public API ───────────────────────────────────────────────────────────────

async def generate_report(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
    estimation: dict,
) -> str:
    """
    Generate a 19-section HTML planning document from structured plan data.
    No API calls — pure template rendering. Drop-in replacement for report_agent.generate_report.
    """
    today = date.today().strftime("%B %d, %Y")
    project_name = requirements.get("project_name") or requirements.get("name") or "Project"

    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_h(project_name)} — Planning Report</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>{_CSS}</style>
</head>
<body class="bg-white text-gray-800 font-sans">
<div class="max-w-4xl mx-auto px-8 py-10">"""

    sections = "".join([
        _sec1_cover(requirements),
        _sec2_toc(),
        _sec3_executive(requirements, estimation),
        _sec4_problem(requirements),
        _sec5_solution(requirements),
        _sec6_users(requirements),
        _sec7_scope(requirements),
        _sec8_modules(requirements),
        _sec9_architecture(architecture),
        _sec10_techstack(tech_stack),
        _sec11_database(tech_stack),
        _sec12_infra(tech_stack),
        _sec13_security(),
        _sec14_budget(estimation),
        _sec15_team_timeline(estimation),
        _sec16_risks(requirements, architecture, tech_stack),
        _sec17_readiness(),
        _sec18_approach(),
        _sec19_deliverables(),
    ])

    foot = f"""
<footer>Prepared by Project Inception AI · Confidential · Generated on {today}</footer>
</div>
</body>
</html>"""

    return head + sections + foot
