from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
import httpx
from bv.runtime.auth import AuthError, AuthContext, require_auth


class OrchestratorError(RuntimeError):
    pass


@dataclass(frozen=True)
class OrchestratorResponse:
    status_code: int
    data: Any


class OrchestratorClient:
    """Authenticated HTTP client for BV Orchestrator (runtime SDK)."""

    def __init__(
        self,
        *,
        auth_context: AuthContext | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._ctx = auth_context
        self._client = httpx.Client(timeout=float(timeout_seconds))

    def _auth(self) -> AuthContext:
        if self._ctx is None:
            self._ctx = require_auth()
        return self._ctx

    @property
    def base_url(self) -> str:
        return self._auth().api_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        ctx = self._auth()
        headers = {
            "Accept": "application/json",
        }
        if ctx.user and ctx.user.username and ctx.user.username.startswith("robot:"):
            headers["X-Robot-Token"] = ctx.access_token
        else:
            headers["Authorization"] = f"Bearer {ctx.access_token}"
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
    ) -> OrchestratorResponse:
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        try:
            resp = self._client.request(
                method.upper(),
                url,
                headers=self._headers(),
                params=params,
                json=json,
                data=data,
                files=files,
            )
        except httpx.RequestError as exc:
            raise OrchestratorError(f"Unable to reach Orchestrator at {self.base_url}: {exc}") from exc

        if resp.status_code == 401:
            raise OrchestratorError("Not authenticated. Run bv auth login or set BV_ORCHESTRATOR_URL and BV_ROBOT_TOKEN")
        if resp.status_code == 403:
            # Try to extract detailed permission error message
            try:
                error_data = resp.json()
                detail = error_data.get("detail") if isinstance(error_data, dict) else None
                if detail:
                    raise OrchestratorError(f"Permission denied: {detail}")
            except Exception:
                pass
            raise OrchestratorError("Permission denied")

        data_out: Any
        try:
            data_out = resp.json()
        except Exception:
            data_out = resp.text

        if resp.status_code >= 400:
            message = None
            if isinstance(data_out, dict):
                message = data_out.get("detail") or data_out.get("message") or data_out.get("error")
            if not message:
                message = data_out if isinstance(data_out, str) else repr(data_out)
            raise OrchestratorError(f"Orchestrator error {resp.status_code}: {message}")

        return OrchestratorResponse(status_code=resp.status_code, data=data_out)

    def resolve_secret(self, name: str) -> str:
        """Resolve a secret's plaintext value via the runtime endpoint."""
        resp = self.request("POST", "/api/runtime/secrets/resolve", json={"name": name})
        data_out = resp.data

        if isinstance(data_out, dict):
            if "value" in data_out:
                return str(data_out.get("value") or "")
            # Fallback: allow orchestrator to return raw string field name
            if len(data_out) == 1:
                try:
                    return str(next(iter(data_out.values())) or "")
                except Exception:
                    pass

        if isinstance(data_out, str):
            return data_out

        return str(data_out or "")

    def get_credential_metadata(self, name: str) -> dict[str, str]:
        """Fetch credential metadata (username only) without resolving the password."""
        resp = self.request("GET", f"/api/runtime/credentials/{name}")
        data_out = resp.data

        username = ""
        if isinstance(data_out, dict):
            username = str(data_out.get("username") or "")
        else:
            username = str(data_out or "")

        return {"username": username}

