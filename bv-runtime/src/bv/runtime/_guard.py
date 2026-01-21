from __future__ import annotations

import os
from bv.runtime.auth import has_runner_context


def require_bv_run() -> None:
    if os.environ.get("BV_SDK_RUN") != "1" and not has_runner_context():
        raise RuntimeError("bv.runtime is only available when running via bv run or a BV runner context")

