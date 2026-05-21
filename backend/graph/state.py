from typing import TypedDict, Optional
from enum import Enum


class PlanningStage(str, Enum):
    requirement = "requirement"
    clarification = "clarification"
    checkpoint_1 = "checkpoint_1"
    architecture = "architecture"
    techstack = "techstack"
    estimation = "estimation"
    checkpoint_2 = "checkpoint_2"
    risk = "risk"
    compile = "compile"
    checkpoint_3 = "checkpoint_3"
    done = "done"


class PlanningState(TypedDict):
    project_id: str
    user_id: str
    raw_input: str
    stage: PlanningStage

    # Phase 1
    requirements: Optional[dict]
    clarification_questions: Optional[list]
    clarification_answers: Optional[dict]
    checkpoint_1_approved: Optional[bool]

    # Phase 2
    architecture: Optional[dict]
    tech_stack: Optional[dict]
    estimation: Optional[dict]
    checkpoint_2_approved: Optional[bool]

    # Streaming callback
    stream_queue: Optional[object]
