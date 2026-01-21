from __future__ import annotations

import uuid
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bv.runtime._guard import require_bv_run
from bv.runtime.client import OrchestratorClient


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def record_span(
    name: str,
    *,
    status: str = "ok",
    parent_span_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    duration_ms: Optional[int] = None,
    input: Optional[Any] = None,
    output: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> None:
    """Send a single span to orchestrator (best-effort)."""
    require_bv_run()

    execution_id = _execution_id()
    if not execution_id:
        return

    start_ts = start_time or _utc_now()
    end_ts = end_time
    if not duration_ms and end_ts:
        duration_ms = int((end_ts - start_ts).total_seconds() * 1000)

    payload = {
        "traceId": execution_id,
        "spans": [
            {
                "spanId": str(uuid.uuid4()),
                "parentSpanId": parent_span_id,
                "name": name,
                "status": status,
                "startTime": start_ts.isoformat(),
                "endTime": end_ts.isoformat() if end_ts else None,
                "durationMs": duration_ms,
                "input": input,
                "output": output,
                "metadata": metadata,
                "tags": tags,
            }
        ],
    }

    try:
        client = OrchestratorClient()
        client.request("POST", f"/api/agent-traces/{execution_id}/spans", json=payload)
    except Exception:
        # Silent failure to avoid breaking user automations
        return


class trace_span(AbstractContextManager):
    """Context manager to capture a span with start/end timestamps."""

    def __init__(
        self,
        name: str,
        *,
        parent_span_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.parent_span_id = parent_span_id
        self.tags = tags
        self.metadata = metadata or {}
        self._start = _utc_now()
        self.span_id = str(uuid.uuid4())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        status = "ok"
        meta = dict(self.metadata)
        if exc:
            status = "error"
            meta["error"] = str(exc)
        record_span(
            self.name,
            status=status,
            parent_span_id=self.parent_span_id,
            start_time=self._start,
            end_time=_utc_now(),
            metadata=meta,
            tags=self.tags,
        )
        # Do not suppress exceptions
        return False


def _execution_id() -> Optional[str]:
    """Read execution id from environment (set by runner)."""
    import os

    raw = os.environ.get("BV_JOB_EXECUTION_ID")
    if raw:
        return str(raw)
    return None
