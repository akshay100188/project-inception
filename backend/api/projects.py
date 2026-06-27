"""
Projects API — ephemeral, no database, no authentication.

Project plans are never persisted. The browser holds the plan in memory for the
duration of the session and posts it here only to (a) resolve human-in-the-loop
checkpoints on the live stream and (b) render downloadable HTML deliverables.
Closing the tab discards everything.
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from config import settings
from models.schemas import CheckpointRequest, GenerateRequest
import checkpoint_registry as cr

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{project_id}/checkpoint", summary="Resolve a live human-in-the-loop checkpoint")
async def handle_checkpoint(project_id: str, body: CheckpointRequest):
    """Unblock the streaming graph waiting on this checkpoint.

    Purely in-memory: ``project_id`` is the ephemeral id the browser generated for
    the current run. If no live waiter exists (stream ended), this is a no-op.
    """
    key = cr.checkpoint_key(project_id, body.checkpoint_name)
    resolved = cr.resolve(key, {
        "action": body.action,
        "edited_content": body.edited_content,
    })
    return {
        "action": body.action,
        "checkpoint": body.checkpoint_name,
        "project_id": project_id,
        "resolved": resolved,
    }


@router.post("/prototype", summary="Generate an HTML prototype from posted plan data")
async def generate_prototype_artifact(body: GenerateRequest):
    """Render a single-file interactive HTML prototype and return it for download."""
    if settings.demo_mode:
        from agents.prototype_agent import generate_prototype
    else:
        from report.template_prototype import generate_prototype

    architecture = body.architecture or {}
    tech_stack = body.tech_stack or {}
    if not architecture and not tech_stack:
        raise HTTPException(status_code=400, detail="No plan data provided")

    try:
        html = await generate_prototype(body.requirements or {}, architecture, tech_stack)
    except Exception as exc:
        logger.error("Prototype generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Prototype generation failed: {exc}")

    return HTMLResponse(content=html, media_type="text/html")


@router.post("/report", summary="Generate a full HTML planning report from posted plan data")
async def generate_report_artifact(body: GenerateRequest):
    """Render the 19-section HTML planning report and return it for download."""
    if settings.demo_mode:
        from agents.report_agent import generate_report
    else:
        from report.template_report import generate_report

    architecture = body.architecture or {}
    tech_stack = body.tech_stack or {}
    if not architecture and not tech_stack:
        raise HTTPException(status_code=400, detail="No plan data provided")

    try:
        html = await generate_report(
            body.requirements or {}, architecture, tech_stack, body.estimation or {}
        )
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    return HTMLResponse(content=html, media_type="text/html")
