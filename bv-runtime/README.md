# bv-runtime

Authoritative runtime SDK reference for Bot Velocity automations.

## 1. Overview
- bv-runtime is the in-runner SDK used by Bot Velocity automations during execution (`bv run` or runner-managed jobs).
- It provides focused capabilities: asset access (including secrets and credentials), queue operations (lease/update one item at a time), and structured logging to Orchestrator.
- It is intentionally **not** a general-purpose or admin SDK; use platform admin APIs or CLI for management tasks.

## 2. Execution Context & Guardrails
- The runtime enforces execution inside a BV runner context or SDK dev context via `require_bv_run()`; using these APIs outside `bv run` or a runner context fails fast.
- Authentication is required and already provisioned in runner context via a local sqlite store (`~/.bv/runner_context.db`) or via local `bv auth login` for development.
- Distinctions:
  - **Runtime execution:** Automations running via runner use this SDK to talk to Orchestrator with scoped credentials.
  - **Admin APIs:** Separate, not exposed here; this SDK cannot create queues or assets.
  - **SDK CLI:** Developer tooling (`bv auth`, `bv run`) sets up context but is not part of the runtime API.

## 3. Assets API

### 3.1 Text / Int / Bool Assets
```python
from bv.runtime import assets

value = assets.get_asset("CONFIG_VALUE")
```

### 3.2 Secrets (SecretHandle pattern)
- `SecretHandle` defers plaintext retrieval until `.value()` is called.
- Secrets are never printed; `str(secret)` is masked and JSON/boolean usage is blocked.

```python
from bv.runtime import assets

secret = assets.get_secret("API_KEY")
api_key = secret.value()
```

### 3.3 Credentials (CredentialHandle)
- Provides `username` plus a password `SecretHandle`.
- Password plaintext is only available via `.value()` on the handle.

```python
from bv.runtime import assets

cred = assets.get_credential("DB_CREDENTIAL")

cred.username
password = cred.password.value()
```

Security model: plaintext secrets and passwords are resolved just-in-time from Orchestrator; they are masked in representations and never stored in environment variables.

## 4. Queue API (Primary Focus)
Use the singular facade:

```python
from bv.runtime import queue
```

### 4.1 QueueItem Object
Attributes (immutable, no dict access):
- `id`: queue item ID
- `queue_name`: name of the queue
- `reference`: optional reference string
- `priority`: `Priority` enum (`LOW`, `NORMAL`, `MEDIUM`, `HIGH`)
- `retries`: number of previous failures
- `attempt`: derived as `retries + 1`
- `content`: parsed JSON payload

`QueueItem` is immutable and blocks dict-style access to avoid silent mutations.

### 4.2 Enqueue (queue.add)
```python
from bv.runtime import queue
from bv.runtime.queue import Priority

item = queue.add(
	"orders",
	content={"invoice": 123},
	reference="INV-001",
	priority=Priority.HIGH,
)
```
- Default priority is `Priority.NORMAL`.
- `reference` is optional metadata for downstream correlation.
- Returns a `QueueItem` with retries=0 and attempt=1.

**Note:** The runtime SDK checks for `BV_SDK_RUN=1` (dev mode) or a runner sqlite context (runner mode). If running scripts manually (e.g. `python main.py`), you must set `BV_SDK_RUN=1`.

```python
item = queue.get("orders")

if item is None:
	return
```
- Returns the next available item or `None` when the queue is empty.
- Items are leased; visibility timeouts and retries are handled by Orchestrator.
- `retries` counts prior failures; `attempt` is derived as `retries + 1`.

### 4.4 Update Status (queue.set_status)
Use typed enums:

```python
from bv.runtime import queue
from bv.runtime.queue import Status, ErrorType

# DONE
queue.set_status(
	item.id,
	Status.DONE,
	output={"processed": True},
)

# FAILED (Business)
queue.set_status(
	item.id,
	Status.FAILED,
	error_type=ErrorType.BUSINESS,
	error_reason="Invoice already paid",
)

# FAILED (Application)
queue.set_status(
	item.id,
	Status.FAILED,
	error_type=ErrorType.APPLICATION,
	error_reason="Unhandled exception",
)
```
- `Status` values: `DONE`, `FAILED`, `ABANDONED` (ABANDONED is set when leases expire ~24h without completion).
- `ErrorType.BUSINESS` marks terminal business errors; `ErrorType.APPLICATION` is retryable depending on orchestrator policy.
- Validation rules are enforced at runtime (DONE forbids errors; FAILED requires both error fields; ABANDONED requires an error reason).

## 5. Logging API
```python
from bv.runtime import log_message, LogLevel

log_message("Processing started", LogLevel.INFO)
log_message("Validation failed", LogLevel.WARN)
log_message("Unhandled error", LogLevel.ERROR)
```
- Logs are sent to Orchestrator with the current run context.
- Levels: `DEBUG`, `INFO`, `WARN`, `ERROR` (see `LogLevel`).

## 6. End-to-End Examples

### 6.1 Simple Queue Worker
```python
from bv.runtime import queue
from bv.runtime.queue import Status, ErrorType

item = queue.get("orders")
if item is None:
	return

try:
	# process item.content here
	queue.set_status(item.id, Status.DONE, output={"processed": True})
except ValueError as exc:  # business rule violation
	queue.set_status(
		item.id,
		Status.FAILED,
		error_type=ErrorType.BUSINESS,
		error_reason=str(exc),
	)
except Exception as exc:
	queue.set_status(
		item.id,
		Status.FAILED,
		error_type=ErrorType.APPLICATION,
		error_reason=str(exc),
	)
```

### 6.2 Business vs Application Error Handling
- Business errors (`ErrorType.BUSINESS`) are terminal and should be used for known, non-retryable conditions (e.g., duplicate invoice, already paid).
- Application errors (`ErrorType.APPLICATION`) signal transient or unexpected failures and may be retried by orchestrator policies.

### 6.3 Asset + Queue Combined Example
```python
from bv.runtime import assets, queue
from bv.runtime.queue import Priority, Status, ErrorType

api_key = assets.get_secret("API_KEY").value()
item = queue.add(
	"orders",
	content={"invoice": 123, "api_key": api_key},
	reference="INV-123",
	priority=Priority.MEDIUM,
)

fetched = queue.get("orders")
if fetched:
	# do work...
	queue.set_status(fetched.id, Status.DONE, output={"ok": True})
```

## 7. Design Principles
- Typed APIs over raw dicts to prevent silent breakage.
- No silent behavior: validation errors are explicit and fail fast.
- No magic retries in the SDK; retry decisions are orchestrator-owned.
- Security-first: secrets and credentials are masked, lazy-resolved, and never printed.
- Runtime ≠ Admin: operational actions only; no management surfaces.

## 8. What bv-runtime Does NOT Do
- No admin operations (no asset/queue creation or deletion).
- No manual requeue/backoff controls beyond status updates.
- No background scheduling utilities.
- No batch queue APIs; operations are single-item by design.

## 9. Versioning & Compatibility Notes
- The runtime is allowed to introduce breaking changes aligned with orchestrator releases; always pin via your project lockfile.
- Backward compatibility for deprecated APIs (e.g., plural queues) is intentionally not maintained.

