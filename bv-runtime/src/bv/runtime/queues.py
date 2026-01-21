"""Plural queue API removed; use bv.runtime.queue instead."""

from __future__ import annotations


def __getattr__(name):  # pragma: no cover - explicit break
    raise AttributeError(
        "The plural 'bv.runtime.queues' API has been removed. "
        "Import 'bv.runtime.queue' and use queue.add/get/set_status instead."
    )

