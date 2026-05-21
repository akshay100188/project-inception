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
    """Create a fresh Event for *key*, clearing any stale decision from a previous run."""
    _events[key] = asyncio.Event()
    _decisions.pop(key, None)


async def wait_for_decision(key: str, timeout: float = 600.0) -> dict:
    """
    Suspend the calling coroutine until ``resolve()`` is called with *key*.

    Args:
        key: Checkpoint key returned by :func:`checkpoint_key`.
        timeout: Seconds to wait before auto-approving (safety valve for crashed clients).

    Returns:
        The decision dict passed to :func:`resolve`, or ``{"action": "approve"}`` on timeout.
    """
    evt = _events.get(key)
    if evt:
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
    return _decisions.get(key, {"action": "approve"})


def resolve(key: str, decision: dict) -> bool:
    """
    Record *decision* and unblock the graph coroutine waiting on *key*.

    Args:
        key: Checkpoint key returned by :func:`checkpoint_key`.
        decision: Dict with at minimum ``{"action": "approve"|"edit"|"reject"}``.

    Returns:
        ``True`` if a live waiter was found and unblocked; ``False`` if no active checkpoint.
    """
    _decisions[key] = decision
    evt = _events.get(key)
    if not evt:
        return False
    evt.set()
    return True


def cleanup(key: str) -> None:
    """Remove the event and decision for *key* once the checkpoint node has finished."""
    _events.pop(key, None)
    _decisions.pop(key, None)


def checkpoint_key(project_id: str, name: str) -> str:
    """Return a namespaced key scoped to a single project and checkpoint name."""
    return f"{project_id}:{name}"
