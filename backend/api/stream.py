import asyncio
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from graph.planning_graph import build_planning_graph
from graph.state import PlanningStage

router = APIRouter()
_compiled_graph = build_planning_graph()


async def _event_generator(state: dict):
    """Run the LangGraph graph and yield SSE-formatted events from the queue."""
    queue: asyncio.Queue = state["stream_queue"]

    async def run_graph():
        try:
            await _compiled_graph.ainvoke(state)
        except Exception as e:
            await queue.put({"event": "error", "agent": None, "data": str(e)})
        finally:
            await queue.put(None)   # sentinel — signals stream end

    task = asyncio.create_task(run_graph())

    while True:
        item = await queue.get()
        if item is None:
            yield _format_sse({"event": "done", "data": "Planning complete."})
            break
        yield _format_sse(item)

    await task


def _format_sse(data: dict) -> str:
    payload = json.dumps(data)
    return f"data: {payload}\n\n"


@router.post("/run/{project_id}")
async def stream_run(
    project_id: str,
    raw_input: str,
    authorization: str = Header(...),
):
    """
    Start a planning run for a project. Returns an SSE stream.
    The client connects here and receives token-by-token agent output.
    """
    user_id = _extract_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    queue: asyncio.Queue = asyncio.Queue()

    initial_state = {
        "project_id": project_id,
        "user_id": user_id,
        "raw_input": raw_input,
        "stage": PlanningStage.requirement,
        "requirements": None,
        "clarification_questions": None,
        "clarification_answers": None,
        "checkpoint_1_approved": None,
        "stream_queue": queue,
    }

    return StreamingResponse(
        _event_generator(initial_state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",    # disables Nginx buffering
        },
    )


def _extract_user_id(authorization: str) -> Optional[str]:
    """Extract user_id from Supabase JWT. Returns None if invalid."""
    try:
        import jwt
        token = authorization.replace("Bearer ", "")
        # Supabase JWT — decode without verification in dev; add secret in prod
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub")
    except Exception:
        return None
