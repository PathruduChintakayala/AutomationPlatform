from __future__ import annotations

from typing import Any
from enum import Enum, IntEnum

from bv.runtime._guard import require_bv_run


class Status(Enum):
    DONE = "DONE"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class ErrorType(Enum):
    APPLICATION = "APPLICATION"
    BUSINESS = "BUSINESS"


class Priority(IntEnum):
    """Priority levels mapped to backend integer values (runtime-only helper)."""

    LOW = 0
    NORMAL = 1
    MEDIUM = 2
    HIGH = 3


__all__ = ["add", "get", "set_status", "Status", "ErrorType", "Priority"]


def add(
    queue_name: str,
    content: Any,
    *,
    reference: str | None = None,
    priority: Priority = Priority.NORMAL,
) -> "QueueItem":
    """Enqueue an item and return a typed QueueItem.

    Backend contract is unchanged; we only wrap the response into an immutable QueueItem.
    """
    require_bv_run()
    from bv.runtime.client import OrchestratorClient
    from bv.runtime.queue_item import QueueItem

    client = OrchestratorClient()
    if not isinstance(priority, Priority):
        raise TypeError("priority must be a Priority enum value (e.g., Priority.NORMAL)")

    body = {
        "queue_name": queue_name,
        "payload": content,  # backend expects 'payload'
        "reference": reference,
        # Priority is an IntEnum; send its integer value to the backend API.
        "priority": int(priority),
    }
    resp = client.request("POST", "/api/queue-items/add", json=body)
    data = resp.data

    item_id = data.get("id") if isinstance(data, dict) else data

    # retries start at 0 on enqueue; QueueItem derives attempt as retries + 1
    return QueueItem(
        item_id=item_id,
        queue_name=queue_name,
        reference=reference,
        priority=priority,
        retries=0,
        content=content,
    )


def get(queue_name: str) -> "QueueItem | None":
    """Fetch the next available item; returns None when the queue is empty."""
    require_bv_run()
    from bv.runtime.client import OrchestratorClient
    from bv.runtime.queue_item import QueueItem

    client = OrchestratorClient()
    resp = client.request("GET", "/api/queue-items/next", params={"queue_name": queue_name})
    data = resp.data
    if data is None or not isinstance(data, dict):
        return None

    queue_name_value = data.get("queue_name") or queue_name
    retries = data.get("retries", 0)

    return QueueItem(
        item_id=data.get("id"),
        queue_name=queue_name_value,
        reference=data.get("reference"),
        priority=data.get("priority"),
        retries=retries,
        content=data.get("payload"),
    )


def set_status(
    item_id: str,
    status: Status,
    *,
    output: dict | None = None,
    error_type: ErrorType | None = None,
    error_reason: str | None = None,
) -> None:
    """Update queue item status with explicit, validated contract.

    Rules:
    - DONE: error_type and error_reason must be None.
    - FAILED: error_type and error_reason are required.
    - ABANDONED: error_reason is required (error_type optional).
    - BUSINESS errors are terminal.
    """
    require_bv_run()
    from bv.runtime.client import OrchestratorClient

    if not isinstance(status, Status):
        raise TypeError("status must be a Status enum value")
    if error_type is not None and not isinstance(error_type, ErrorType):
        raise TypeError("error_type must be an ErrorType enum value or None")

    # Validate state-specific contract
    if status is Status.DONE:
        if error_type is not None:
            raise ValueError("DONE status cannot include error_type")
        if error_reason is not None:
            raise ValueError("DONE status cannot include error_reason")
    elif status is Status.FAILED:
        if error_type is None:
            raise ValueError("FAILED status requires error_type")
        if error_reason is None:
            raise ValueError("FAILED status requires error_reason")
    elif status is Status.ABANDONED:
        if error_reason is None:
            raise ValueError("ABANDONED status requires error_reason")
    else:  # pragma: no cover - future-proof guard
        raise ValueError(f"Unsupported status {status}")

    client = OrchestratorClient()
    body = {
        "status": status.value,
        # Backend still expects 'result' and 'error_message'; public API uses explicit names.
        "result": output,
        "error_message": error_reason,
    }
    if error_type is not None:
        body["error_type"] = error_type.value
        if error_type is ErrorType.BUSINESS:
            body["terminal"] = True

    client.request("PUT", f"/api/queue-items/{item_id}/status", json=body)
