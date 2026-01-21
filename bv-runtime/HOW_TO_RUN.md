# How to use bv-runtime

The `bv-runtime` package is a runtime SDK used by Bot Velocity automations during execution. It is not meant to be run directly - it's a library that automations import.

## Prerequisites

- Python 3.10 or higher
- pip

## Installation

### For Development (editable install)

```bash
cd bv-runtime
pip install -e .
```

### For Use in Automation Projects

Add `bv-runtime` to your project's dependencies. The SDK-CLI includes it by default when you run `bv init`.

## Usage

The runtime SDK provides three main capabilities:

### 1. Assets API

```python
from bv.runtime import assets

# Get a text/int/bool asset
value = assets.get_asset("CONFIG_VALUE")

# Get a secret (masked by default)
secret = assets.get_secret("API_KEY")
api_key = secret.value()  # Reveals plaintext

# Get a credential
cred = assets.get_credential("DB_CREDENTIAL")
username = cred.username
password = cred.password.value()
```

### 2. Queue API

```python
from bv.runtime import queue
from bv.runtime.queue import Priority, Status, ErrorType

# Add an item to a queue
item = queue.add(
    "orders",
    content={"invoice": 123},
    reference="INV-001",
    priority=Priority.HIGH,
)

# Get the next item from a queue
item = queue.get("orders")
if item:
    # Process item.content
    queue.set_status(item.id, Status.DONE, output={"processed": True})
```

### 3. Logging API

```python
from bv.runtime import log_message, LogLevel

log_message("Processing started", LogLevel.INFO)
log_message("Validation failed", LogLevel.WARN)
```

## Important Notes

- The runtime SDK **only works inside a BV runner context** (when `BV_SDK_RUN=1` is set)
- For local development, use `bv run` from the SDK-CLI which sets this environment variable
- Direct script execution (e.g., `python main.py`) will fail unless you set `BV_SDK_RUN=1` manually

## Building the Package

```bash
cd bv-runtime
pip install hatchling
python -m build
```

This creates wheel and sdist in the `dist/` folder.
