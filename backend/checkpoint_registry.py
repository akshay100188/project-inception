"""
In-memory registry for human-in-the-loop checkpoint pause/resume.

Each checkpoint node calls `register()` to create an asyncio.Event,
then awaits `wait_for_decision()`.  The HTTP checkpoint endpoint calls
`resolve()` with the user's decision, which unblocks the graph.
"""
import asyncio

_events: dict[str, asyncio.Event] = {}
_decisions: dict[str, dict] = {}


def register(key: str) -> None:
    _events[key] = asyncio.Event()
    _decisions.pop(key, None)


async def wait_for_decision(key: str, timeout: float = 600.0) -> dict:
    evt = _events.get(key)
    if evt:
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
    return _decisions.get(key, {"action": "approve"})


def resolve(key: str, decision: dict) -> bool:
    _decisions[key] = decision
    evt = _events.get(key)
    if not evt:
        return False
    evt.set()
    return True


def cleanup(key: str) -> None:
    _events.pop(key, None)
    _decisions.pop(key, None)


def checkpoint_key(project_id: str, name: str) -> str:
    return f"{project_id}:{name}"
