# CodeGuardian

**CodeGuardian** is a code-first, on-premise AI crew built with **CrewAI**.
It analyzes bugs, searches large repositories efficiently using **local RAG**, and **implements fixes directly in the target project** — without relying on cloud services.

The system is designed to scale to **large repositories (10k+ files)** and behaves similarly to the **Continue IDE plugin**:
- indexing is explicit
- re-indexing happens **only when necessary**
- no hidden side effects

---

## Key Principles

- ✅ On-prem only (LLM + embeddings)
- ✅ Code-first (no YAML configs)
- ✅ Separation of concerns
- ✅ Incremental & smart indexing
- ✅ Git-aware change detection
- ✅ Minimal context passed between agents

---

## Architecture Overview

### Agents

**Senior Software Architect**
- Reads bug description & logs
- Respects `.gitignore` from the target repository
- Uses semantic RAG search
- Produces a structured Change Plan

**Senior Software Engineer**
- Consumes the Change Plan via task context
- Locates exact files
- Implements fixes directly in the target repo
- Writes minimal diffs only

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

| Purpose | Path |
|------|-----|
| CodeGuardian repo | anywhere |
| Target project to analyze/fix | PROJECT_PATH |
| Bug input files | INPUTS_PATH |
| Vector index | CHROMA_DIR |

`.gitignore` is always read from the **target project**, never from CodeGuardian.

---

## Requirements

- Python 3.10+
- uv
- Git
- Ollama (for embeddings)
- On-prem OpenAI-compatible LLM endpoint

---

## Installation

```
uv sync
```

---

## Environment Variables

```
PROJECT_PATH=C:\project-backend
INPUTS_PATH=C:\inputs
BUG_DESC_FILE=bug-desc.txt
BUG_LOG_FILE=bug-log.txt

CHROMA_DIR=C:\projects\codeguardian\.cache\.chroma

OLLAMA_BASE_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text:latest

FORCE_REINDEX=0
AUTO_INDEX_NO_GIT=0
INDEX_MAX_FILES_BACKEND=4000
INDEX_MAX_FILES_FRONTEND=4000
```

---

## Indexing Model (Continue-like)

Indexing is explicit and controlled.

### First-time Indexing

```
uv run python -m codeguardian.index
```

### Normal Execution

```
crewai run
```

Re-indexing happens only if:
- Git HEAD changed and relevant files were modified
- Uncommitted relevant changes exist
- Index configuration changed
- FORCE_REINDEX=1

---

## Git-Aware Change Detection

- git diff old..new
- git status --porcelain

Only relevant file changes trigger re-indexing.

---

## Task & Context Flow

1. Architect Task:
    - Reads bug files and .gitignore
    - Uses RAG search
    - Outputs Change Plan

2. Engineer Task:
    - Receives Change Plan via task.context
    - Implements fix directly

No intermediate files. No duplicated context.

---

## Why No YAML?

- Full control in Python
- Static typing
- Debuggable
- No magic defaults

---

## Typical Workflow

```
uv run python -m codeguardian.index
crewai run
```

---

## Guarantees

- No cloud calls
- No OpenAI embeddings
- No Qdrant
- Fully local RAG
- Deterministic behavior
- Scales to large repos

---

## Summary

CodeGuardian behaves like a professional on-prem AI engineer:
- indexes only when needed
- respects git and .gitignore
- scales cleanly
- modifies code responsibly
