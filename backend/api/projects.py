from fastapi import APIRouter, HTTPException, Header
from supabase import create_client, Client
from config import settings
from models.schemas import ProjectCreate, ProjectUpdate, CheckpointRequest, CheckpointAction
import checkpoint_registry as cr
import uuid
from datetime import datetime, timezone

router = APIRouter()

_supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)


def _get_user(authorization: str) -> str:
    try:
        import jwt
        token = authorization.replace("Bearer ", "")
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/")
async def create_project(body: ProjectCreate, authorization: str = Header(...)):
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


@router.get("/")
async def list_projects(authorization: str = Header(...)):
    user_id = _get_user(authorization)
    result = (
        _supabase.table("incept_projects")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/{project_id}")
async def get_project(project_id: str, authorization: str = Header(...)):
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


@router.patch("/{project_id}")
async def update_project(
    project_id: str, body: ProjectUpdate, authorization: str = Header(...)
):
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
