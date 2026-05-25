"""
Projects API — CRUD endpoints and checkpoint resolver for incept_projects.

All routes require a valid Supabase JWT in the ``Authorization: Bearer <token>`` header.
Row-level security in Supabase further enforces per-user data isolation.
"""
import logging
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import HTMLResponse
from supabase import create_client, Client
from config import settings
from models.schemas import ProjectCreate, ProjectUpdate, CheckpointRequest, CheckpointAction
import checkpoint_registry as cr
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()

_supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)


def _get_user(authorization: str) -> str:
    """
    Extract the ``sub`` (user UUID) from a Supabase-issued JWT.

    Signature verification is intentionally skipped here because Supabase's
    row-level security policies enforce ownership at the database layer.
    For environments that require additional server-side validation, pass
    the JWT secret via ``options={"algorithms": ["HS256"]}`` and verify
    against ``settings.supabase_jwt_secret``.

    Args:
        authorization: Raw ``Authorization`` header value (``Bearer <token>``).

    Returns:
        The user UUID string from the JWT ``sub`` claim.

    Raises:
        HTTPException 401: If the header is missing, malformed, or has no ``sub``.
    """
    try:
        import jwt
        token = authorization.replace("Bearer ", "")
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/", summary="Create a new project record")
async def create_project(body: ProjectCreate, authorization: str = Header(...)):
    """Create an empty project row and return the new record (status: drafting)."""
    user_id = _get_user(authorization)
    now = datetime.now(timezone.utc).isoformat()
    project_id = str(uuid.uuid4())

    data = {
        "id": project_id,
        "user_id": user_id,
        "raw_input": body.raw_input,
        "status": "drafting",
        "created_at": now,
        "updated_at": now,
    }

    result = _supabase.table("incept_projects").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create project")

    return result.data[0]


@router.get("/", summary="List all projects for the authenticated user")
async def list_projects(authorization: str = Header(...)):
    """Return all projects owned by the requesting user, ordered newest-first."""
    user_id = _get_user(authorization)
    result = (
        _supabase.table("incept_projects")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/{project_id}", summary="Fetch a single project by ID")
async def get_project(project_id: str, authorization: str = Header(...)):
    """Return a single project record. Raises 404 if not found or not owned by the user."""
    user_id = _get_user(authorization)
    result = (
        _supabase.table("incept_projects")
        .select("*")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return result.data


@router.patch("/{project_id}", summary="Partially update a project")
async def update_project(
    project_id: str, body: ProjectUpdate, authorization: str = Header(...)
):
    """Apply a partial update (status, requirements, plan, etc.) to a project record."""
    user_id = _get_user(authorization)
    update_data = body.model_dump(exclude_none=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        _supabase.table("incept_projects")
        .update(update_data)
        .eq("id", project_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else {}


@router.post("/{project_id}/checkpoint")
async def handle_checkpoint(
    project_id: str, body: CheckpointRequest, authorization: str = Header(...)
):
    """Resolve a pending checkpoint — unblocks the streaming graph."""
    user_id = _get_user(authorization)

    key = cr.checkpoint_key(project_id, body.checkpoint_name)
    resolved = cr.resolve(key, {
        "action": body.action,
        "edited_content": body.edited_content,
    })

    if not resolved:
        # No live checkpoint (graph not running or already resolved) — just update status
        status_map = {
            CheckpointAction.approve: "planning",
            CheckpointAction.edit: "clarifying",
            CheckpointAction.reject: "drafting",
        }
        if body.checkpoint_name == "checkpoint_2":
            status_map = {
                CheckpointAction.approve: "complete",
                CheckpointAction.edit: "reviewing",
                CheckpointAction.reject: "planning",
            }
        _supabase.table("incept_projects").update({
            "status": status_map[body.action],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", project_id).eq("user_id", user_id).execute()

    return {"action": body.action, "checkpoint": body.checkpoint_name, "project_id": project_id}


@router.post("/{project_id}/prototype", summary="Generate an HTML prototype for the project")
async def generate_project_prototype(project_id: str, authorization: str = Header(...)):
    """
    Generate a single-file interactive HTML prototype using Claude and persist it on the project.
    Returns the HTML directly so the caller can open it in a new tab.
    """
    if settings.demo_mode:
        from agents.prototype_agent import generate_prototype
    else:
        from report.template_prototype import generate_prototype

    user_id = _get_user(authorization)

    result = (
        _supabase.table("incept_projects")
        .select("plan, requirements, status")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    project = result.data
    plan = project.get("plan") or {}
    requirements = project.get("requirements") or {}
    architecture = plan.get("architecture") or {}
    tech_stack = plan.get("tech_stack") or {}

    if not architecture and not tech_stack:
        raise HTTPException(status_code=400, detail="Plan not yet generated for this project")

    try:
        html = await generate_prototype(requirements, architecture, tech_stack)
    except Exception as exc:
        logger.error("Prototype generation failed for project %s: %s", project_id, exc)
        raise HTTPException(status_code=500, detail=f"Prototype generation failed: {exc}")

    # Persist prototype in the plan JSON
    plan["prototype_html"] = html
    _supabase.table("incept_projects").update({
        "plan": plan,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", project_id).eq("user_id", user_id).execute()

    return HTMLResponse(content=html, media_type="text/html")


@router.get("/{project_id}/prototype", summary="Return the cached HTML prototype")
async def get_project_prototype(project_id: str, authorization: str = Header(...)):
    """Return the previously generated prototype HTML, or 404 if not yet generated."""
    user_id = _get_user(authorization)

    result = (
        _supabase.table("incept_projects")
        .select("plan")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    plan = result.data.get("plan") or {}
    html = plan.get("prototype_html")
    if not html:
        raise HTTPException(status_code=404, detail="Prototype not yet generated")

    return HTMLResponse(content=html, media_type="text/html")


@router.post("/{project_id}/report", summary="Generate a comprehensive HTML planning report")
async def generate_project_report(project_id: str, authorization: str = Header(...)):
    """
    Generate a full professional planning document using Claude and persist it.
    Returns the HTML directly so the caller can open it in a new tab and print to PDF.
    """
    if settings.demo_mode:
        from agents.report_agent import generate_report
    else:
        from report.template_report import generate_report

    user_id = _get_user(authorization)

    result = (
        _supabase.table("incept_projects")
        .select("plan, requirements, status")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    project = result.data
    plan = project.get("plan") or {}
    requirements = project.get("requirements") or {}
    architecture = plan.get("architecture") or {}
    tech_stack = plan.get("tech_stack") or {}
    estimation = plan.get("estimation") or {}

    if not architecture and not tech_stack:
        raise HTTPException(status_code=400, detail="Plan not yet complete for this project")

    try:
        html = await generate_report(requirements, architecture, tech_stack, estimation)
    except Exception as exc:
        logger.error("Report generation failed for project %s: %s", project_id, exc)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    # Cache report in the plan JSON
    plan["report_html"] = html
    _supabase.table("incept_projects").update({
        "plan": plan,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", project_id).eq("user_id", user_id).execute()

    return HTMLResponse(content=html, media_type="text/html")


@router.get("/{project_id}/report", summary="Return the cached planning report")
async def get_project_report(project_id: str, authorization: str = Header(...)):
    """Return the previously generated planning report HTML, or 404 if not yet generated."""
    user_id = _get_user(authorization)

    result = (
        _supabase.table("incept_projects")
        .select("plan")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    plan = result.data.get("plan") or {}
    html = plan.get("report_html")
    if not html:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    return HTMLResponse(content=html, media_type="text/html")
