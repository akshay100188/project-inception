# Loom Demo Script — Project Inception

**Suggested recording time:** 3–4 minutes  
**Input to use:** "A SaaS tool that turns Loom recordings into Notion docs automatically using AI"

---

## 0 · Setup (before recording)
- Open the app at your production URL (or localhost:5173)
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
3. Narrate: *"The agent pipeline starts immediately — first the requirement analyst extracts structured requirements from the raw idea"*

---

## 4 · Phase 1 streaming — Requirement + Clarification (0:55 – 1:40)
1. Watch the **Requirement Analyst** token stream live
2. Watch the **Clarification Agent** fire next
3. Narrate: *"Two agents in sequence — the first extracts structured requirements (JSON), the second generates targeted questions about gaps"*
4. Graph pauses — **Checkpoint 1 modal** appears

---

## 5 · Checkpoint 1 — Requirements review (1:40 – 2:00)
1. Show the modal: project name, problem statement, feature cards, target users
2. Narrate: *"Human-in-the-loop — the graph is literally paused on the server, waiting for my decision"*
3. Click **Approve & Continue →**
4. Modal closes, Phase 2 agents begin immediately

---

## 6 · Phase 2 streaming — Architecture + Tech Stack + Estimation (2:00 – 2:45)
1. Watch **Architecture Architect** stream (pattern, components)
2. Watch **Tech Stack Selector** stream
3. Watch **Estimation Analyst** stream
4. Narrate: *"Each agent queries a pgvector RAG corpus for relevant reference patterns before calling Claude — so recommendations are grounded, not hallucinated"*
5. Graph pauses — plan review appears

---

## 7 · Checkpoint 2 — Plan review (2:45 – 3:15)
1. Scroll through the plan: architecture cards, tech stack layers, timeline phases, cost range
2. Narrate: *"Full plan — monolith pattern, recommended stack, 8-week MVP estimate, cost breakdown"*
3. Show **Copy Markdown** — briefly paste into notes
4. Click **Approve & Save →**
5. Navigates to Project Detail page

---

## 8 · Project Detail + Export (3:15 – 3:40)
1. Show the saved plan on the detail page
2. Click **Print / PDF** — browser print dialog opens
3. Narrate: *"One-click PDF export — ready to share with stakeholders"*
4. Cancel print

---

## 9 · Dashboard (3:40 – 3:55)
1. Navigate back to Dashboard
2. Show the saved project card: name, domain tag, architecture pattern, MVP weeks, "Complete" badge
3. Narrate: *"Every plan saved to Supabase with full history"*

---

## 10 · Closing (3:55 – 4:00)
> *"Project Inception — from rough idea to a complete, reviewed, exportable project plan in under 4 minutes."*

---

## Key talking points
| What to say | What to show |
|---|---|
| "Agents run sequentially in a LangGraph state machine" | AgentPanel with live tokens |
| "RAG-grounded with pgvector — not hallucinated" | Mention while Phase 2 streams |
| "True human-in-the-loop — server is paused" | Checkpoint modal |
| "Full plan in one SSE stream" | Continuous streaming UI |
| "PDF + Markdown export" | Export buttons |
| "Magic link auth, Supabase RLS per user" | Dashboard with user badge |
