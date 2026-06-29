"""
Pydantic request schemas for the Project Inception API.

The app is ephemeral — no accounts, no stored projects. These models cover the
two things the browser posts: a human-in-the-loop checkpoint decision on the live
stream, and the plan data used to render a downloadable deliverable.
"""
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class CheckpointAction(str, Enum):
    approve = "approve"
    edit = "edit"
    reject = "reject"


class CheckpointRequest(BaseModel):
    action: CheckpointAction
    checkpoint_name: str = "checkpoint_1"
    edited_content: Optional[dict] = None


class GenerateRequest(BaseModel):
    """Plan data sent straight from the browser to generate a downloadable artifact.

    Nothing is read from or written to a database — the client holds the plan in
    memory and posts it here purely to render the HTML deliverable.
    """
    requirements: Optional[dict] = None
    architecture: Optional[dict] = None
    tech_stack: Optional[dict] = None
    estimation: Optional[dict] = None
