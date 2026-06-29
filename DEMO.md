# Loom Demo Script — Project Inception

**Suggested recording time:** 3–4 minutes
**Input to use:** "A SaaS tool that turns Loom recordings into Notion docs automatically using AI"

> **Before recording:** Set `DEMO_MODE=true` in `backend/.env` and confirm `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and the Supabase RAG vars are present. This script shows the full Claude-powered experience. The default public deployment runs in rule-based mode (`DEMO_MODE=false`) with zero API credits and no database.

---

## 0 · Setup (before recording)

- Confirm `DEMO_MODE=true` in your backend `.env` and the server has restarted
- Open the app at your production URL (or `localhost:5173`) — you land straight on the portal, no login
- Have the input text copied to clipboard
- Make sure screen resolution is clean — 1440×900 or similar

---

## 1 · The portal (0:00 – 0:20)

1. Show the landing page — *"No sign-up, no account. You land right on the portal."*
2. Narrate: *"Everything here is ephemeral — nothing about your idea is stored. You run it, download your plan, and closing the tab wipes it."*
3. Mention you could also drag in a PDF / Word / text requirements doc instead of typing.

---

## 2 · Submit an idea (0:20 – 0:45)

1. Paste: **"A SaaS tool that turns Loom recordings into Notion docs automatically using AI"**
2. Click **Start Planning →**
3. Narrate: *"The agent pipeline kicks off — first the requirement analyst extracts structured requirements from the raw idea."*

---

## 3 · Phase 1 streaming — Requirement + Clarification (0:45 – 1:30)

1. Watch the **Requirement Analyst** stream live, then the **Clarification Agent** fire next.
2. Narrate: *"Two Claude agents in sequence — each receives the top 3 most similar real-world projects as grounding context before it calls Claude, so the output is calibrated against actual precedents, not just training data."*
3. The graph pauses — the **requirements checkpoint** appears.

---

## 4 · Checkpoint — Requirements review (1:30 – 1:55)

1. Show the modal: project name, feature cards, clarifying questions, target users.
2. Narrate: *"The one human-in-the-loop step — the LangGraph state machine is paused on the server on an in-memory asyncio.Event, waiting for my decision. I can approve, edit, or reject."*
3. Click **Approve & Continue →** — the modal closes and Phase 2 begins immediately.

---

## 5 · Phase 2 streaming — Architecture + Tech Stack + Estimation (1:55 – 2:45)

1. Watch **Architecture Architect**, **Tech Stack Selector**, and **Estimation Analyst** stream in sequence.
2. Narrate: *"Three Claude agents — each grounded with the top 4 most similar real-world projects alongside curated reference docs, so the recommendations are backed by precedent rather than pure model intuition."*

---

## 6 · The plan appears (2:45 – 3:15)

1. The finished plan renders right in the page — architecture cards, tech stack layers, timeline phases, cost range.
2. Narrate: *"The full plan — architecture pattern, recommended stack, phase-by-phase timeline, cost breakdown — all in the browser. Nothing was saved to do this."*

---

## 7 · Download deliverables (3:15 – 3:50)

1. Click **Download Planning Report** — the 19-section HTML planning document downloads to your device.
2. Narrate: *"One click — a complete planning report, ready to share or print to PDF."*
3. Click **Download App Prototype** — the 5-screen interactive wireframe downloads.
4. Narrate: *"A domain-aware UI wireframe — five screens, realistic sample data, no design tool needed. Both files are yours; the app keeps nothing."*

---

## 8 · Closing (3:50 – 4:00)

> *"Project Inception — from a rough idea to a downloadable, reviewed project plan in under 4 minutes. No account, no database, no trace left behind."*

---

## Key talking points

| What to say | What to show |
|---|---|
| "No login, no account — you land right on the portal" | The landing page |
| "Fully ephemeral — nothing is stored, closing the tab wipes it" | Mention at the start |
| "Seven agents, two modes — Claude-powered or fully rule-based" | Mention at the start |
| "Both modes use the same 81 real-world project examples as grounding" | During Phase 1 or 2 |
| "Agents run in a LangGraph state machine" | Live token streaming |
| "True human-in-the-loop — server paused on an in-memory asyncio.Event" | Requirements checkpoint |
| "Full plan delivered over a single SSE stream" | Continuous streaming UI |
| "19-section HTML report + 5-screen wireframe, downloaded to your device" | Both download buttons |
| "Default mode uses zero Anthropic credits and no database — safe for public access" | At the close |

---

## Switching back to default mode after recording

```bash
# In backend/.env
DEMO_MODE=false
# ANTHROPIC_API_KEY, OPENAI_API_KEY, and the Supabase vars can be left blank or removed
```

Restart the server. All agents revert to rule-based mode — no credits can be consumed and no database is touched.
