"""
Rule-based requirement extraction — no Claude API calls.
Parses free-form project descriptions using keyword matching and heuristics.
"""
import asyncio
import re
from agents.rules.lookup import normalize_domain

# ── Scale detection ──────────────────────────────────────────────────────────

_LARGE_WORDS  = {"enterprise", "platform", "large", "scale", "complex", "marketplace", "global", "multi-tenant", "b2b"}
_SMALL_WORDS  = {"mvp", "simple", "basic", "personal", "side project", "prototype", "small", "lightweight", "minimal"}


def _detect_scale(text: str) -> str:
    low = text.lower()
    if any(w in low for w in _LARGE_WORDS):
        return "large"
    if any(w in low for w in _SMALL_WORDS):
        return "small"
    return "medium"


# ── Project name extraction ──────────────────────────────────────────────────

_BUILD_VERBS = re.compile(
    r"^(build|create|make|develop|design|launch|build out|i want|i need|we need|we want|"
    r"i('m| am) building|we('re| are) building|help me build|help me create|an? app|"
    r"a platform|a tool|a system|a website|a web app|a saas|a mobile app)\s+",
    re.IGNORECASE,
)

def _extract_name(text: str) -> str:
    first = text.strip().split("\n")[0].strip().rstrip(".")
    # strip leading build verbs
    cleaned = _BUILD_VERBS.sub("", first).strip()
    # title-case the first 6 words max
    words = cleaned.split()[:6]
    name = " ".join(words).title()
    return name or "My Project"


# ── Feature extraction ───────────────────────────────────────────────────────

_FEATURE_PATTERNS = re.compile(
    r"\b(ability to|users? can|support for|manage|track|view|create|edit|delete|"
    r"search|filter|upload|download|send|receive|notify|integrate|authenticate|"
    r"dashboard|report|analytics|payment|checkout|booking|schedule|review|comment|"
    r"message|chat|follow|share|export|import)\b",
    re.IGNORECASE,
)

_STOPLINES = re.compile(
    r"^\s*(the|this|it|our|my|we|i|please|thank|note:|ps:|also|additionally)\b",
    re.IGNORECASE,
)


def _extract_features(text: str, domain: str) -> list[dict]:
    # Split into candidate phrases by common delimiters
    raw_chunks: list[str] = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•*·")
        if not line:
            continue
        # Split long lines on commas/semicolons/conjunctions
        parts = re.split(r",|;|\band\b|\bwith\b|\bplus\b|\balso\b", line, flags=re.IGNORECASE)
        raw_chunks.extend(p.strip() for p in parts if p.strip())

    seen: set[str] = set()
    features: list[dict] = []

    for chunk in raw_chunks:
        chunk = chunk.strip().rstrip(".")
        if len(chunk) < 6 or len(chunk) > 120:
            continue
        if _STOPLINES.match(chunk):
            continue
        key = chunk.lower()
        if key in seen:
            continue
        seen.add(key)
        has_feature_signal = bool(_FEATURE_PATTERNS.search(chunk))
        # Treat as a feature if it has a feature verb OR is short and noun-like
        if has_feature_signal or (len(chunk.split()) <= 8 and len(features) < 10):
            priority = "must-have" if has_feature_signal else "nice-to-have"
            # Capitalise first letter
            label = chunk[0].upper() + chunk[1:]
            features.append({"feature": label, "priority": priority})

    # Domain fallback features if extraction yielded too little
    _FALLBACKS: dict[str, list[tuple[str, str]]] = {
        "ecommerce":    [("Product catalog and search", "must-have"), ("Shopping cart and checkout", "must-have"), ("Order management", "must-have"), ("User authentication", "must-have"), ("Payment processing", "must-have"), ("Admin dashboard", "nice-to-have")],
        "edtech":       [("Course catalog and enrollment", "must-have"), ("Lesson/video player", "must-have"), ("Student progress tracking", "must-have"), ("User authentication", "must-have"), ("Instructor dashboard", "must-have"), ("Quizzes and assessments", "nice-to-have")],
        "fintech":      [("Account management", "must-have"), ("Transaction history", "must-have"), ("Payment processing", "must-have"), ("User authentication with MFA", "must-have"), ("Dashboard and analytics", "must-have"), ("Notifications and alerts", "nice-to-have")],
        "healthcare":   [("Patient records management", "must-have"), ("Appointment booking", "must-have"), ("Provider directory", "must-have"), ("Secure messaging", "must-have"), ("User authentication", "must-have"), ("Notifications and reminders", "nice-to-have")],
        "social":       [("User profiles and feeds", "must-have"), ("Post/content creation", "must-have"), ("Follow and connections", "must-have"), ("Notifications", "must-have"), ("Search and discovery", "must-have"), ("Direct messaging", "nice-to-have")],
        "productivity": [("Task and project management", "must-have"), ("User workspaces", "must-have"), ("Team collaboration", "must-have"), ("Notifications", "must-have"), ("Search and filters", "must-have"), ("Integrations (calendar, Slack)", "nice-to-have")],
        "saas":         [("User authentication and teams", "must-have"), ("Core product dashboard", "must-have"), ("Billing and subscriptions", "must-have"), ("Settings and preferences", "must-have"), ("Analytics", "must-have"), ("API access", "nice-to-have")],
    }
    if len(features) < 4:
        for feat, pri in _FALLBACKS.get(domain, _FALLBACKS["saas"]):
            if len(features) >= 6:
                break
            key = feat.lower()
            if key not in seen:
                features.append({"feature": feat, "priority": pri})
                seen.add(key)

    return features[:10]


# ── Target user extraction ───────────────────────────────────────────────────

_USER_KEYWORDS = {
    "student": "Students",          "learner": "Learners",
    "teacher": "Teachers",          "instructor": "Instructors",
    "patient": "Patients",          "doctor": "Doctors",
    "customer": "Customers",        "shopper": "Shoppers",
    "seller": "Sellers",            "vendor": "Vendors",
    "freelancer": "Freelancers",    "developer": "Developers",
    "manager": "Managers",          "admin": "Administrators",
    "business": "Business owners",  "startup": "Startup teams",
    "team": "Teams",                "user": "End users",
    "employee": "Employees",        "hr": "HR professionals",
    "investor": "Investors",        "trader": "Traders",
}


def _extract_users(text: str, domain: str) -> list[str]:
    low = text.lower()
    found = []
    for kw, label in _USER_KEYWORDS.items():
        if kw in low and label not in found:
            found.append(label)
    if not found:
        _DEFAULTS = {
            "ecommerce": ["Customers", "Sellers", "Store administrators"],
            "edtech":    ["Students", "Instructors", "Administrators"],
            "fintech":   ["Account holders", "Finance managers", "Administrators"],
            "healthcare":["Patients", "Healthcare providers", "Administrators"],
            "social":    ["End users", "Content creators", "Moderators"],
            "productivity":["Individual users", "Teams", "Administrators"],
        }
        found = _DEFAULTS.get(domain, ["End users", "Administrators"])
    return found[:4]


# ── Main agent ───────────────────────────────────────────────────────────────

async def run_requirement_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "requirement", "data": "Extracting requirements…"})

    raw = state.get("raw_input", "")
    domain_raw = raw  # search the full text for domain signals
    norm = normalize_domain(domain_raw)

    name        = _extract_name(raw)
    scale       = _detect_scale(raw)
    features    = _extract_features(raw, norm)
    users       = _extract_users(raw, norm)

    requirements = {
        "project_name": name,
        "domain":        norm,
        "scale":         scale,
        "target_users":  users,
        "core_features": features,
        "integrations":  [],
        "raw_summary":   raw[:500],
    }

    await queue.put({"event": "token", "agent": "requirement", "data": f"Detected domain: {norm}, scale: {scale}"})
    await queue.put({"event": "agent_done", "agent": "requirement", "data": "Requirements extracted."})
    return {"requirements": requirements, "stage": "clarification"}
