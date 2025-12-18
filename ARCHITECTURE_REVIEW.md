# CodeGuardian Architecture Review

**Date:** December 18, 2025
**Version:** 2.0 (Self-Healing Pipeline)

## 1. Architecture Overview: "Manager-Led Recovery"

The CodeGuardian project has evolved from a simple linear chain into a **Self-Healing, Quality-Gated Autonomous Crew**. This architecture mimics a high-functioning engineering team where a Manager oversees the process and coordinates recovery when things go wrong.

### The Workflow

1.  **Phase 1: Analysis & Implementation (Linear)**
    *   **Architect:** Analyzes the bug report and codebase to produce a `Patch Plan`.
    *   **Engineer:** Implements the fix in the target repository.
2.  **Phase 2: Verification (Gated)**
    *   **DevOps:** Detects the build system (Gradle/Maven/NPM), runs the build, and executes unit tests.
        *   *Self-Correction:* Can autonomously fix simple compilation errors (e.g., missing semicolons, imports).
    *   **QA:** Verifies the fix against the "Expected Result" from the bug report.
3.  **Phase 3: Management (Loop-Back)**
    *   **Engineering Manager:** Reviews the outputs from DevOps and QA.
    *   *Decision Logic:*
        *   **Success:** Signs off on the release.
        *   **Failure:** **Delegates** tasks back to the `Engineer` (to fix specific errors) and `DevOps` (to re-test), creating a recovery loop.

---

## 2. Agent Roles & Capabilities

| Agent | Role | Key Capabilities | Tools |
| :--- | :--- | :--- | :--- |
| **Senior Architect** | Analysis | Read-only analysis, RAG search, Plan generation. | `FileReadTool`, `LocalDirectoryRagTool`, `DirectoryReadTool` |
| **Senior Engineer** | Implementation | Code modification, Atomic changes. | `FileReadTool`, `FileWriterTool`, `DirectoryReadTool` |
| **DevOps Engineer** | Build & CI | Build system detection, **Self-Healing** (compilation fixes). | `BuildTool`, `UnitTestTool`, `FileWriterTool` |
| **QA Engineer** | Verification | Functional testing, Requirements verification. | `UnitTestTool`, `FileReadTool` |
| **Engineering Manager** | Orchestration | **Delegation**, Error analysis, Recovery coordination. | *Delegation Capabilities* |

---

## 3. Key Improvements

### A. Feedback Loops
*   **Old System:** If the Engineer introduced a syntax error, the process would end in failure.
*   **New System:** The **DevOps Agent** attempts to fix it immediately. If that fails, the **Manager** catches the failure and explicitly assigns a "Fix Task" back to the Engineer, ensuring the job gets done.

### B. Robust Tooling
*   **`BuildTool`:** Automatically detects if the project uses Gradle, Maven, or NPM and runs the correct commands.
*   **`DirectoryReadTool`:** Allows agents to explore the file structure, preventing "file not found" hallucinations.
*   **`LocalDirectoryRagTool`:** Now includes a `reset()` function to ensure no stale data persists when switching projects.

### C. Configuration
*   **Externalized Config:** Glob patterns and file extensions are now managed in `src/codeguardian/config/rag_config.yaml`, making the tool adaptable to any tech stack without code changes.

---

## 4. Conclusion

The system is now a **Level 3 Autonomous Agent** (Conditional Autonomy). It can handle standard coding tasks and recover from common errors (compilation failures, test failures) without human intervention, only escalating or failing after multiple recovery attempts.
