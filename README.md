# CodeGuardian

**CodeGuardian** is a **code-first, on‑prem AI engineering crew** built with **CrewAI**.
It analyzes bugs, searches large repositories efficiently using **local RAG**, and **implements fixes directly in the target project** — without relying on cloud services.

The system is designed to scale to **large repositories (10k+ files)** and behaves similarly to the **Continue IDE plugin**:

* explicit indexing
* re-indexing **only when necessary**
* no hidden side effects

---

## Key Principles

* ✅ Fully on‑prem (LLM + embeddings)
* ✅ Code‑first (no YAML configs)
* ✅ Explicit & incremental indexing
* ✅ Git‑aware change detection
* ✅ Minimal context passed between agents
* ✅ Deterministic behavior

---

## Architecture Overview

### Agents

**Senior Software Architect**

* Reads bug description & logs
* Respects `.gitignore` from the **target project**
* Uses semantic RAG search (local)
* Produces a structured **Change Plan**

**Senior Software Engineer**

* Consumes the Change Plan via task context
* Locates exact files
* Implements fixes **directly in the target repo**
* Writes **minimal diffs only**

---

## Repository Structure

```
codeguardian/
├─ src/codeguardian/
│  ├─ agents.py
│  ├─ tasks.py
│  ├─ crew.py
│  ├─ index.py              # explicit indexing command
│  └─ tools/
│     ├─ tools.py           # tool wiring & index logic
│     └─ local_rag_tool.py  # Ollama + Chroma RAG tool
├─ content/.chroma/         # persistent vector index
├─ pyproject.toml
└─ README.md
```

---

## Target Project vs CodeGuardian Repo

| Purpose                       | Path           |
| ----------------------------- | -------------- |
| CodeGuardian repo             | anywhere       |
| Target project to analyze/fix | `PROJECT_PATH` |
| Bug input files               | `INPUTS_PATH`  |
| Vector index                  | `CHROMA_DIR`   |

> `.gitignore` is **always read from the target project**, never from CodeGuardian.

---

## Requirements

* Python **3.10+**
* **uv**
* Git
* **Ollama** (for embeddings)
* On‑prem **OpenAI‑compatible LLM endpoint**

---

## Installation

```bash
uv sync
```

This creates a local `.venv` automatically.

---

## Virtual Environment (Windows + Git Bash)

### Activate `.venv`

```bash
source .venv/Scripts/activate
```

You should see:

```
(.venv) username@machine
```

### Deactivate

```bash
deactivate
```

> **Recommended:** even with `.venv`, prefer `uv run` for deterministic execution.

---

## Environment Variables

```bash
export PROJECT_PATH="/c/project-backend"
export INPUTS_PATH="/c/inputs"
export BUG_DESC_FILE="bug-desc.txt"
export BUG_LOG_FILE="bug-log.txt"

export CHROMA_DIR="/c/projects/codeguardian/.cache/.chroma"

export OLLAMA_BASE_URL="http://localhost:11434"
export EMBED_MODEL="nomic-embed-text:latest"

export FORCE_REINDEX="0"
export AUTO_INDEX_NO_GIT="0"
export INDEX_MAX_FILES_BACKEND="4000"
export INDEX_MAX_FILES_FRONTEND="4000"
```

---

## Indexing Model (Continue‑like)

Indexing is **explicit and controlled**.

### First‑time Indexing

```bash
uv run python -m codeguardian.index
```

### Normal Execution

```bash
uv run crewai run
```

Re‑indexing happens **only if**:

* Git `HEAD` changed and relevant files were modified
* Uncommitted relevant changes exist
* Index configuration changed
* `FORCE_REINDEX=1`

---

## Git‑Aware Change Detection

* `git diff old..new`
* `git status --porcelain`

Only **relevant file changes** trigger re‑indexing.

---

## Task & Context Flow

1. **Architect Task**

    * Reads bug files and `.gitignore`
    * Uses local RAG search
    * Outputs a structured **Change Plan**

2. **Engineer Task**

    * Receives Change Plan via `task.context`
    * Applies fixes directly in the target repository

No intermediate files.
No duplicated context.

---

## Why No YAML?

* Full control in Python
* Static typing
* Debuggable
* No magic defaults
* No hidden CrewAI scaffold behavior

---

## Typical Workflow

```bash
source .venv/Scripts/activate
uv run python -m codeguardian.index
uv run crewai run
```

(or skip activation and just use `uv run`)

---

## Guarantees

* No cloud calls
* No OpenAI embeddings
* No Qdrant
* Fully local RAG
* Deterministic behavior
* Scales to large repositories

---

## Summary

**CodeGuardian behaves like a professional on‑prem AI engineer:**

* indexes only when needed
* respects Git and `.gitignore`
* scales cleanly
* modifies code responsibly
