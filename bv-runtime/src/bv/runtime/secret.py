from __future__ import annotations

from typing import Any, Callable

from bv.runtime.client import OrchestratorClient, OrchestratorError


class SecretHandle:
    """Lazy, non-caching handle to resolve secrets on demand."""

    __slots__ = ("_name", "_client_factory")

    def __init__(self, name: str, client_factory: Callable[[], OrchestratorClient] | None = None) -> None:
        self._name = str(name)
        # Client factory ensures we never cache plaintext secrets while still reusing the runtime client logic.
        self._client_factory = client_factory or OrchestratorClient

    @property
    def name(self) -> str:
        return self._name

    def value(self) -> str:
        """Resolve the plaintext secret from the orchestrator on demand."""
        client = self._client_factory()
        try:
            return client.resolve_secret(self._name)
        except OrchestratorError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise OrchestratorError(f"Failed to resolve secret '{self._name}': {exc}") from exc

    def __str__(self) -> str:
        return "***"

    def __repr__(self) -> str:
        return f"SecretHandle(name={self._name!r}, masked='***')"

    def __bool__(self) -> bool:  # pragma: no cover - guardrail
        raise TypeError("SecretHandle cannot be used in boolean context; call .value() to resolve the secret")

    def __json__(self) -> Any:  # pragma: no cover - guardrail
        raise TypeError("SecretHandle cannot be JSON serialized; call .value() to resolve the secret")

    def __format__(self, format_spec: str) -> str:  # pragma: no cover - guardrail
        return str(self)
