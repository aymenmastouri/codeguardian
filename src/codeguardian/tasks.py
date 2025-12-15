from crewai import Task
from crewai import Agent

def analysis_and_design_task(agent: Agent) -> Task:
    return Task(
        description="""
You are the Senior Software Architect.

MANDATORY ORDER:
1) Read .gitignore first (FileReadTool) and treat ignored paths as non-existent.
2) Read bug-desc.txt and bug-log.txt (FileReadTool).
3) Use DirectorySearchTool to find the most relevant code/config files based on:
   - exception names
   - stack traces
   - endpoint paths
   - logger/class/package names
4) Only after search: read a SMALL number of top files (max 10) using FileReadTool.

Deliver:
- CHANGE PLAN (human readable)
- PATCH PLAN JSON (between markers)

PATCH PLAN JSON RULES (MANDATORY):
- PATCH PLAN MUST be valid JSON and enclosed by the markers.
- IMPORTANT: All target file paths MUST be RELATIVE to PROJECT_PATH.
  Example:
    "src/main/java/.../BuggyService.java"
  NOT:
    "C:\\project-backend\\src\\main\\java\\...\\BuggyService.java"
- Do NOT include absolute paths, drive letters, or PROJECT_PATH prefix.
- Use forward slashes (/) in JSON paths.

---PATCH_PLAN_JSON_START---
{ ... }
---PATCH_PLAN_JSON_END---


Rules:
- Do NOT implement anything
- Do NOT write files
""",
        expected_output="Change plan + Patch plan JSON with exact target files and precise instructions.",
        agent=agent,
    )

def implementation_task(agent: Agent) -> Task:
    return Task(
        description="""
You are the Senior Software Engineer (Implementation).

CONTEXT RULE (MANDATORY):
- The Architect's output (including PATCH_PLAN_JSON) is provided as TASK CONTEXT.
- PATCH_PLAN_JSON is NOT a file.
- DO NOT attempt to read "PATCH_PLAN_JSON" via FileReadTool or any filesystem path.
- Extract the JSON only from the context markers:
  ---PATCH_PLAN_JSON_START---
  ...json...
  ---PATCH_PLAN_JSON_END---

MANDATORY FILE SELECTION (STRICT):
- For EACH entry in PATCH PLAN JSON target_files[]:
  1) Build absolute path = PROJECT_PATH + "/" + target_files[].path
  2) Read THAT file using FileReadTool
  3) Implement the listed changes in THAT file using FileWriterTool (minimal diff)
- DO NOT use local_directory_rag_search to find target files from the plan.

WHEN RAG IS ALLOWED:
- Use local_directory_rag_search ONLY to find additional dependency/config files AFTER reading the target files.
- If using RAG, apply these filters:
  - IGNORE src/test/**
  - IGNORE *Test.java
  - Prefer src/main/java/** and src/main/resources/**

OTHER RULES:
- Respect .gitignore strictly.
- Only modify files under PROJECT_PATH.
- Backward compatible changes only.
- Add/adjust tests only if required by acceptance criteria.

Output:
IMPLEMENTATION SUMMARY
- Changed files (relative paths) + per-file summary
- Verification steps
- Deviations (if any)
""",
        expected_output="Implementation summary with changed files and verification steps.",
        agent=agent,
    )
