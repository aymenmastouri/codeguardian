# CodeGuardian

**CodeGuardian** is a **code-first, on‑prem AI engineering crew** built with **CrewAI**.
It acts as an autonomous software engineering team that analyzes bugs, searches large repositories efficiently using **local RAG**, implements fixes, enforces testing standards, and verifies release readiness — all without relying on cloud services.

The system is designed to scale to **large repositories (10k+ files)** and behaves similarly to the **Continue IDE plugin**:

* explicit indexing
* re-indexing **only when necessary**
* no hidden side effects

---

## Key Principles

* ✅ Fully on‑prem (LLM + embeddings)
* ✅ Code‑first Agents & Tasks
* ✅ Explicit & incremental indexing
* ✅ Git‑aware change detection
* ✅ **Knowledge-Driven Development** (Enforces Testing Standards)
* ✅ Deterministic behavior

---

## Architecture Overview: "Quality-Gated Pipeline"

The system implements a **Linear, Quality-Gated Autonomous Pipeline** where each role has strict validation responsibilities.

### The Workflow

1.  **Phase 1: Analysis & Design**
    *   **Senior Architect (Tech Lead):** Analyzes the bug report and codebase. Designs the solution and delegates the implementation plan. Owns technical quality.
2.  **Phase 2: Implementation & Whitebox Testing**
    *   **Senior Engineer:** Implements the fix in the target repository.
    *   **Mandatory:** Updates/Fixes **Unit Tests** and **Integration Tests** (Whitebox).
    *   **Self-Validation:** Must run the build and tests locally to ensure success before finishing.
3.  **Phase 3: Build & Integration**
    *   **DevOps Engineer:** Detects the build system (Gradle/Maven/NPM), runs the CI build, and executes the full test suite.
    *   *Self-Correction:* Can autonomously fix simple compilation errors.
4.  **Phase 4: Functional Verification & Release**
    *   **QA Engineer:** Performs **Functional Testing** and verifies **Deployability**.
    *   Ensures the application is release-ready and meets all Acceptance Criteria.

### Agent Roles

| Agent | Role | Key Capabilities | Tools |
| :--- | :--- | :--- | :--- |
| **Senior Architect** | Technical Lead | Analysis, Design, Delegation, RAG search. | `FileReadTool`, `LocalDirectoryRagTool`, `DirectoryReadTool` |
| **Senior Engineer** | Implementation | Code modification, **Unit/Integration Testing**, Self-Validation. | `FileReadTool`, `FileWriterTool`, `DirectoryReadTool`, `BuildTool`, `UnitTestTool` |
| **DevOps Engineer** | Build & CI | Build system detection, **Self-Healing** (compilation fixes). | `BuildTool`, `UnitTestTool`, `FileWriterTool` |
| **QA Engineer** | Release Verification | **Functional Testing**, Deployability Check, Release Sign-off. | `UnitTestTool`, `FileReadTool` |

---

## Knowledge Base (Testing Standards)

CodeGuardian enforces strict testing standards via its **Knowledge Base**. Agents are instructed to consult these files before writing code or tests.

*   `knowledge/be-test-junit.txt`: Standards for Java/SpringBoot/JUnit 5 tests (Gherkin style, coverage rules).
*   `knowledge/fe-test-jasmine.txt`: Standards for Angular/Jasmine tests.

The Knowledge Base is indexed using **Ollama** embeddings (`nomic-embed-text`) for efficient retrieval.

---

## Repository Structure

```
codeguardian/
├─ src/codeguardian/
│  ├─ agents.py             # 4 Agents (Arch, Eng, DevOps, QA)
│  ├─ tasks.py              # Task definitions & logic
│  ├─ crew.py               # Orchestration & Knowledge Loading
│  ├─ index.py              # Explicit indexing command
│  ├─ config/
│  │  ├─ settings.py        # Pydantic Configuration
│  │  └─ rag_config.yaml    # RAG file patterns
│  └─ tools/
│     ├─ tools.py           # Tool wiring
│     ├─ local_rag_tool.py  # Ollama + Chroma RAG
│     └─ build_tools.py     # Gradle/Maven/NPM wrappers
├─ knowledge/               # Text-based testing standards
├─ content/.chroma/         # Persistent vector index
├─ pyproject.toml
└─ README.md
```

---

## Configuration

Configuration is managed via `.env` and `src/codeguardian/config/settings.py`.

### Environment Variables (`.env`)

```ini
# Target Project
PROJECT_PATH=C:/path/to/your/target/repo
INPUTS_PATH=C:/path/to/bug/reports

# LLM Configuration (OpenAI Compatible)
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
OPENAI_MODEL_NAME=qwen2.5-coder-32b-instruct

# Embeddings (Ollama)
EMBED_MODEL=nomic-embed-text
```

---

## Requirements

* Python **3.10+**
* **uv** (Python package manager)
* Git
* **Ollama** (for embeddings: `ollama pull nomic-embed-text`)
* On‑prem **OpenAI‑compatible LLM endpoint** (e.g., LM Studio, Ollama)

---

## How to Run

1.  **Install Dependencies**:
    ```powershell
    uv sync
    ```

2.  **Configure Environment**:
    Copy `.env.template` to `.env` and set your paths and LLM details.

3.  **Prepare Bug Report**:
    Place `bug-desc.txt` and `bug-log.txt` in your `INPUTS_PATH`.

4.  **Run CodeGuardian**:
    ```powershell
    uv run codeguardian
    ```

This will start the crew, index the repository (if needed), and execute the pipeline.
