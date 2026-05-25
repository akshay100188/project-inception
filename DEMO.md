# Loom Demo Script — Project Inception

**Suggested recording time:** 3–4 minutes  
**Input to use:** "A SaaS tool that turns Loom recordings into Notion docs automatically using AI"

> **Before recording:** Set `DEMO_MODE=true` in `backend/.env` and confirm both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are present. This script shows the full Claude-powered experience. The default public deployment runs in rule-based mode (`DEMO_MODE=false`) with zero API credits consumed.

---

## 0 · Setup (before recording)

- Confirm `DEMO_MODE=true` in your backend `.env` and the server has restarted
- Open the app at your production URL (or `localhost:5173`)
- Open a second browser tab with the Dashboard so you can end on it
- Have the input text copied to clipboard
- Make sure screen resolution is clean — 1440×900 or similar

---

## 1 · Login (0:00 – 0:20)

1. Show the login screen briefly — "magic link auth via Supabase"
2. Already logged in? Go straight to Dashboard

---

## 2 · Dashboard (0:20 – 0:35)

1. Show the Dashboard — may be empty or have previous projects
2. Click **+ New Project**
3. "Let's give it a real idea"

---

## 3 · Submit an idea (0:35 – 0:55)

1. Paste: **"A SaaS tool that turns Loom recordings into Notion docs automatically using AI"**
2. Click **Start Planning →**
3. Narrate: *"The agent pipeline kicks off — first the requirement analyst extracts structured requirements from the raw idea"*

---

## 4 · Phase 1 streaming — Requirement + Clarification (0:55 – 1:40)

1. Watch the **Requirement Analyst** token stream live
2. Watch the **Clarification Agent** fire next — four targeted questions appear
3. Narrate: *"Two Claude agents in sequence — the first produces a structured requirements JSON, the second surfaces the most important open questions for this domain"*
4. Graph pauses — **Checkpoint 1 modal** appears

---

## 5 · Checkpoint 1 — Requirements review (1:40 – 2:00)

1. Show the modal: project name, feature cards, clarifying questions, target users
2. Narrate: *"Human-in-the-loop — the LangGraph state machine is paused on the server, waiting for my decision via an asyncio.Event"*
3. Click **Approve & Continue →**
4. Modal closes, Phase 2 agents begin immediately

---

## 6 · Phase 2 streaming — Architecture + Tech Stack + Estimation (2:00 – 2:45)

1. Watch **Architecture Architect** stream (pattern, components, rationale)
2. Watch **Tech Stack Selector** stream
3. Watch **Estimation Analyst** stream
4. Narrate: *"Three Claude agents run in sequence — each one produces structured JSON that feeds the next"*
5. Graph pauses — plan review appears

---

## 7 · Checkpoint 2 — Plan review (2:45 – 3:15)

1. Scroll through the plan: architecture cards, tech stack layers, timeline phases, cost range
2. Narrate: *"Full plan — architecture pattern, recommended stack, phase-by-phase timeline, cost breakdown"*
3. Click **Approve & Save →**
4. Navigates to Project Detail page

---

## 8 · Project Detail + Export (3:15 – 3:45)

1. Show the saved plan on the detail page
2. Click **Download Report** — browser opens the 19-section HTML planning document
3. Narrate: *"One-click export — a complete planning report ready to share with stakeholders or print to PDF"*
4. Click **Download Wireframe** — browser opens the 5-screen interactive prototype
5. Narrate: *"A domain-aware UI wireframe — five screens, realistic sample data, no design tool needed"*

---

## 9 · Dashboard (3:45 – 3:55)

1. Navigate back to Dashboard
2. Show the saved project card: name, domain tag, architecture pattern, MVP weeks, **Complete** badge
3. Narrate: *"Every plan saved to Supabase with full history"*

---

## 10 · Closing (3:55 – 4:00)

> *"Project Inception — from rough idea to a reviewed, exportable project plan in under 4 minutes."*

---

## Key talking points

| What to say | What to show |
|---|---|
| "Seven agents, two modes — Claude-powered or fully rule-based" | Mention at the start |
| "Agents run in a LangGraph state machine" | AgentPanel with live tokens |
| "True human-in-the-loop — server is paused on an asyncio.Event" | Checkpoint modal |
| "Full plan delivered over a single SSE stream" | Continuous streaming UI |
| "19-section HTML report + 5-screen wireframe on download" | Both export buttons |
| "Magic link auth, Supabase RLS enforces per-user isolation" | Dashboard with user badge |
| "Default mode uses zero Anthropic credits — safe for public access" | Can mention at close |

---

## Switching back to default mode after recording

```bash
# In backend/.env
DEMO_MODE=false
# ANTHROPIC_API_KEY and OPENAI_API_KEY can be left blank or removed
```

Restart the server. All agents revert to rule-based mode — no credits can be consumed.
