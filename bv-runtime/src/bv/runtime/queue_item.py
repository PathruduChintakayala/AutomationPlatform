from __future__ import annotations

from typing import Any


class QueueItem:
    """Immutable, attribute-only queue item wrapper."""

    # Slots + frozen flag avoid accidental mutation and dict-style access.
    __slots__ = (
        "_id",
        "_queue_name",
        "_reference",
        "_priority",
        "_retries",
        "_attempt",
        "_content",
        "_frozen",
    )

    def __init__(
        self,
        *,
        item_id: str,
        queue_name: str,
        reference: str | None,
        priority: Any,
        retries: int,
        content: Any,
    ) -> None:
        object.__setattr__(self, "_frozen", False)
        object.__setattr__(self, "_id", str(item_id))
        object.__setattr__(self, "_queue_name", str(queue_name))
        object.__setattr__(self, "_reference", None if reference is None else str(reference))
        object.__setattr__(self, "_priority", self._coerce_priority(priority))
        try:
            retries_val = int(retries)
        except Exception:
            retries_val = 0
        object.__setattr__(self, "_retries", retries_val)
        object.__setattr__(self, "_attempt", retries_val + 1)
        object.__setattr__(self, "_content", content)
        object.__setattr__(self, "_frozen", True)

    # Immutable properties
    @property
    def id(self) -> str:
        return self._id

    @property
    def queue_name(self) -> str:
        return self._queue_name

    @property
    def reference(self) -> str | None:
        return self._reference

    @property
    def priority(self):
        return self._priority

    @property
    def retries(self) -> int:
        return self._retries

    @property
    def attempt(self) -> int:
        return self._attempt

    @property
    def content(self) -> Any:
        return self._content

    # Guardrails to keep attribute-only usage
    def __getitem__(self, key: Any) -> Any:  # pragma: no cover - guardrail
        raise TypeError("QueueItem does not support item access; use attributes instead")

    def __iter__(self):  # pragma: no cover - guardrail
        raise TypeError("QueueItem is immutable and non-iterable; use attributes instead")

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover - guardrail
        if getattr(self, "_frozen", False):
            raise TypeError("QueueItem is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:  # pragma: no cover - guardrail
        raise TypeError("QueueItem attributes cannot be deleted")

    def __str__(self) -> str:
        return (
            f"QueueItem(id={self._id!r}, queue={self._queue_name!r}, "
            f"attempt={self._attempt}, priority={self._priority}, reference={self._reference!r})"
        )

    def __repr__(self) -> str:
        return (
            "QueueItem("
            f"id={self._id!r}, queue_name={self._queue_name!r}, reference={self._reference!r}, "
            f"priority={self._priority!r}, retries={self._retries!r}, attempt={self._attempt!r}, "
            f"content={self._content!r}"
            ")"
        )

    @staticmethod
    def _coerce_priority(raw: Any):
        """Convert backend integer priority to the Priority enum when available."""
        if raw is None:
            return None
        try:
            from bv.runtime.queue import Priority  # Local import to avoid circular at module load

            if isinstance(raw, Priority):
                return raw
            return Priority(int(raw))
        except Exception:
            # Preserve the raw value if it cannot be coerced; avoids raising during deserialization
            try:
                return int(raw)
            except Exception:
                return raw
