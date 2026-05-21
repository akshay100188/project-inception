"""
Pydantic request/response schemas for the Project Inception API.

Defines models for project CRUD, checkpoint resolution, and SSE event payloads.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    drafting = "drafting"
    clarifying = "clarifying"
    planning = "planning"
    reviewing = "reviewing"
    complete = "complete"


class CheckpointAction(str, Enum):
    approve = "approve"
    edit = "edit"
    reject = "reject"


class ProjectCreate(BaseModel):
    raw_input: str


class ProjectUpdate(BaseModel):
    status: Optional[ProjectStatus] = None
    requirements: Optional[dict] = None
    clarifications: Optional[dict] = None
    plan: Optional[dict] = None


class CheckpointRequest(BaseModel):
    action: CheckpointAction
    checkpoint_name: str = "checkpoint_1"
    edited_content: Optional[dict] = None


class Project(BaseModel):
    id: UUID
    user_id: str
    raw_input: str
    status: ProjectStatus
    requirements: Optional[dict] = None
    clarifications: Optional[dict] = None
    plan: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class StreamEvent(BaseModel):
    event: str        # agent_start | token | agent_done | checkpoint | error | done
    agent: Optional[str] = None
    data: Optional[str] = None
