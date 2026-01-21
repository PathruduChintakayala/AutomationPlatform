from __future__ import annotations

from typing import Any

from bv.runtime.secret import SecretHandle


class CredentialHandle:
    """Attribute-based credential accessor with masked representations."""

    __slots__ = ("_name", "_username", "_password")

    def __init__(self, name: str, username: str, password: SecretHandle) -> None:
        self._name = str(name)
        self._username = str(username)
        self._password = password

    @property
    def name(self) -> str:
        return self._name

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> SecretHandle:
        return self._password

    # Dict-style access is intentionally blocked to avoid unsafe usage.
    def __getitem__(self, key: Any) -> Any:  # pragma: no cover - guardrail
        raise TypeError("CredentialHandle does not support item access; use .username and .password")

    def __iter__(self):  # pragma: no cover - guardrail
        raise TypeError("CredentialHandle cannot be iterated or serialized")

    def __bool__(self) -> bool:  # pragma: no cover - guardrail
        raise TypeError("CredentialHandle cannot be used in boolean context; access its fields explicitly")

    def __str__(self) -> str:
        return f"CredentialHandle(name={self._name!r}, username={self._username!r}, password='***')"

    def __repr__(self) -> str:
        return f"CredentialHandle(name={self._name!r}, username={self._username!r}, password=SecretHandle(masked))"

    def __json__(self) -> Any:  # pragma: no cover - guardrail
        raise TypeError("CredentialHandle cannot be JSON serialized; extract fields explicitly")
