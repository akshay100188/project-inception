"""
LangGraph planning graph — wires all agents and checkpoint nodes into a state machine.

Graph topology:
  requirement → clarification → checkpoint_1 → arch_agent → techstack_agent
                                     ↑                              ↓
                              (reject loops back)           estimate_agent → checkpoint_2 → END

Checkpoint nodes block via asyncio.Event until the HTTP checkpoint endpoint resolves them,
implementing true human-in-the-loop pauses without polling.
"""
import asyncio
import logging
from langgraph.graph import StateGraph, END
from supabase import create_client
from config import settings
from graph.state import PlanningState, PlanningStage
from agents.requirement_agent import run_requirement_agent
from agents.clarification_agent import run_clarification_agent
from agents.architecture_agent import run_architecture_agent
from agents.techstack_agent import run_techstack_agent
from agents.estimation_agent import run_estimation_agent
import checkpoint_registry as cr

logger = logging.getLogger(__name__)

_supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def route_after_checkpoint_1(state: PlanningState) -> str:
    """Route to Phase 2 on approval, or loop back to requirement extraction on rejection."""
    if state.get("checkpoint_1_approved"):
        return "arch_agent"
    return "requirement"


def route_after_checkpoint_2(state: PlanningState) -> str:
    """Always terminate after checkpoint 2; the plan has been saved (or rejected)."""
    return END


def build_planning_graph() -> StateGraph:
    """
    Compile and return the LangGraph state machine.

    Node names are intentionally different from PlanningState field names to avoid
    LangGraph's internal collision check (e.g. ``arch_agent`` not ``architecture``).

    Returns:
        A compiled LangGraph ``CompiledStateGraph`` ready to be invoked with ``ainvoke``.
    """
    graph = StateGraph(PlanningState)

    # Node names must not collide with PlanningState field names.
    graph.add_node("requirement", run_requirement_agent)
    graph.add_node("clarification", run_clarification_agent)
    graph.add_node("checkpoint_1", _checkpoint_1_node)
    graph.add_node("arch_agent", run_architecture_agent)
    graph.add_node("techstack_agent", run_techstack_agent)
    graph.add_node("estimate_agent", run_estimation_agent)
    graph.add_node("checkpoint_2", _checkpoint_2_node)

    graph.set_entry_point("requirement")
    graph.add_edge("requirement", "clarification")
    graph.add_edge("clarification", "checkpoint_1")
    graph.add_conditional_edges(
        "checkpoint_1",
        route_after_checkpoint_1,
        {"arch_agent": "arch_agent", "requirement": "requirement"},
    )
    graph.add_edge("arch_agent", "techstack_agent")
    graph.add_edge("techstack_agent", "estimate_agent")
    graph.add_edge("estimate_agent", "checkpoint_2")
    graph.add_conditional_edges(
        "checkpoint_2",
        route_after_checkpoint_2,
        {END: END},
    )

    return graph.compile()


async def _checkpoint_1_node(state: PlanningState) -> dict:
    """
    Pause the graph and emit a ``checkpoint`` SSE event for human requirements review.

    Registers an asyncio.Event, then awaits the HTTP checkpoint endpoint to resolve it.
    If the user submits edited requirements, they are merged back into state before
    Phase 2 agents run.
    """
    queue: asyncio.Queue = state["stream_queue"]
    project_id = state["project_id"]
    key = cr.checkpoint_key(project_id, "checkpoint_1")

    cr.register(key)
    await queue.put({
        "event": "checkpoint",
        "agent": "checkpoint_1",
        "data": {
            "title": "Review Requirements",
            "requirements": state.get("requirements"),
            "clarification_questions": state.get("clarification_questions"),
        },
    })

    decision = await cr.wait_for_decision(key)
    cr.cleanup(key)

    approved = decision.get("action") != "reject"
    updates: dict = {"stage": PlanningStage.checkpoint_1, "checkpoint_1_approved": approved}
    if decision.get("edited_content"):
        updates["requirements"] = decision["edited_content"]
    return updates


async def _checkpoint_2_node(state: PlanningState) -> dict:
    """
    Pause the graph for final plan review and persist the approved plan to Supabase.

    On approval, writes the full plan JSON (architecture + tech_stack + estimation)
    to the ``incept_projects`` table and sets status to ``complete``.
    """
    queue: asyncio.Queue = state["stream_queue"]
    project_id = state["project_id"]
    key = cr.checkpoint_key(project_id, "checkpoint_2")

    plan = {
        "architecture": state.get("architecture"),
        "tech_stack": state.get("tech_stack"),
        "estimation": state.get("estimation"),
    }

    cr.register(key)
    await queue.put({
        "event": "checkpoint",
        "agent": "checkpoint_2",
        "data": {
            "title": "Review Your Plan",
            "requirements": state.get("requirements"),
            "architecture": state.get("architecture"),
            "tech_stack": state.get("tech_stack"),
            "estimation": state.get("estimation"),
        },
    })

    decision = await cr.wait_for_decision(key)
    cr.cleanup(key)

    if decision.get("action") != "reject":
        try:
            _supabase.table("incept_projects").update({
                "plan": plan,
                "status": "complete",
            }).eq("id", project_id).execute()
        except Exception as exc:
            logger.error("Failed to persist plan for project %s: %s", project_id, exc)

    return {"stage": PlanningStage.checkpoint_2, "checkpoint_2_approved": True}
