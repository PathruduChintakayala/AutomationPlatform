# How to use bv-sdk-cli

The `bv-sdk-cli` is a developer CLI for building, validating, and publishing automation packages for the Bot Velocity platform.

## Prerequisites

- Python 3.10 or higher
- pip
- (Optional) Network access to Orchestrator for publishing

## Installation

### For Development (editable install)

```bash
cd bv-sdk-cli
pip install -e .
```

### For Production Use

```bash
pip install bv-sdk-cli
```

After installation, the `bv` command is available globally.

## Quick Start

### 1. Initialize a New Project

```bash
mkdir my-automation
cd my-automation
bv init --name my-automation --type rpa
```

This creates:
- `bvproject.yaml` - Project configuration
- `main.py` - Sample entrypoint
- `dist/` - Build output directory

### 2. Validate Your Project

```bash
bv validate
```

### 3. Build a Package

```bash
bv build
```

Creates `dist/<name>-<version>.bvpackage`

### 4. Run Locally

```bash
bv run
```

Or run a specific entrypoint:

```bash
bv run --entry my_entrypoint
```

### 5. Publish Locally

```bash
bv publish local
```

Bumps version and copies to `published/` directory.

### 6. Publish to Orchestrator

First, authenticate:

```bash
bv auth login --api-url http://localhost:8000 --ui-url http://localhost:5173
```

Then publish:

```bash
bv publish orchestrator
```

## All Commands

| Command | Description |
|---------|-------------|
| `bv init` | Initialize a new project |
| `bv validate` | Validate project configuration |
| `bv build` | Build a .bvpackage |
| `bv run` | Run an entrypoint locally |
| `bv publish local` | Publish locally with version bump |
| `bv publish orchestrator` | Publish to BV Orchestrator |
| `bv auth login` | Authenticate for developer mode |
| `bv auth status` | Show authentication status |
| `bv auth logout` | Delete local authentication |
| `bv assets list` | List assets from Orchestrator |
| `bv assets get <name>` | Get a specific asset |
| `bv queues list` | List queues from Orchestrator |
| `bv queues put <queue> --input <json>` | Add item to queue |
| `bv queues get <queue>` | Get next item from queue |

## Version Bumping

Publish commands support version bumping:

```bash
bv publish local --patch   # 1.0.0 -> 1.0.1 (default)
bv publish local --minor   # 1.0.0 -> 1.1.0
bv publish local --major   # 1.0.0 -> 2.0.0
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BV_AUTH_DIR` | Override auth file location (default: `~/.bv/`) |
| `BV_ORCHESTRATOR_URL` | Orchestrator URL for runner mode |
| `BV_ROBOT_TOKEN` | Robot token for runner mode |
| `BV_SDK_RUN` | Set to `1` to enable runtime SDK (set automatically by `bv run`) |

## Building the Package

```bash
cd bv-sdk-cli
pip install hatchling
python -m build
```

This creates wheel and sdist in the `dist/` folder.
