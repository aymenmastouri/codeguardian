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
- ROOT CAUSE ANALYSIS (RCA) - If this is a bug, explain WHY it happened.
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
- Check for initialization of fields to avoid NullPointerException.
- Check for incorrect or unused imports.
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

EXTERNAL GUIDELINES (MANDATORY):
- You MUST query your Knowledge Base for "Testing Guidelines" or "Unit Test Standards" before writing any code.
- Adhere strictly to the patterns found in the Knowledge Base (e.g., JUnit 5, Gherkin style, naming conventions).

TESTING & VERIFICATION (MANDATORY):
- You are responsible for creating/updating a COMPREHENSIVE test suite.
- 1. UNIT TESTS (REQUIRED): Cover all new/modified logic with high branch coverage.
- 2. INTEGRATION TESTS (REQUIRED): Ensure the component interacts correctly with its dependencies (Whitebox).
- 3. E2E TESTS (OPTIONAL): If this is a user-facing feature/bug, add a high-level test case.
- If existing tests are weak, refactor them to match the Knowledge Base standards.

SELF-VALIDATION (MANDATORY):
- BEFORE finishing, you MUST run the build and tests using BuildTool and UnitTestTool.
- If they fail, FIX THEM immediately. Do not hand off broken code.

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
- Verify imports: Remove unused imports, ensure correct classes are imported.

Output:
IMPLEMENTATION SUMMARY
- Changed files (relative paths) + per-file summary
- Verification steps
- Deviations (if any)
""",
        expected_output="Implementation summary with changed files and verification steps.",
        agent=agent,
    )

def build_and_test_task(agent: Agent) -> Task:
    return Task(
        description="""
You are the DevOps Engineer.

1) Detect the build system (Gradle, Maven, NPM) using BuildTool (auto-detect).
2) Run the build command using BuildTool.
3) If the build FAILS:
   - Analyze the error log.
   - If it is a simple compilation error (e.g., missing import, syntax error, typo) caused by the recent changes:
     - Read the broken file.
     - FIX IT using FileWriterTool.
     - Rerun the build.
   - If it is a complex error or dependency issue you cannot fix:
     - Report the failure details.
4) If the build SUCCEEDS:
   - Run unit tests using UnitTestTool.
   - If tests fail, report the failure.

Output:
BUILD REPORT
- Status: SUCCESS / FAILURE
- Build Logs (snippet)
- Test Results
- Fixes Applied (if any)
""",
        expected_output="Build report indicating success or failure, with details of any fixes applied.",
        agent=agent,
    )

def functional_verification_task(agent: Agent) -> Task:
    return Task(
        description="""
You are the QA Engineer.

1) Read the "Steps to Reproduce" and "Expected Result" from the bug description.
2) FUNCTIONAL TESTING:
   - Verify the fix works from a user perspective.
   - WRITE or EXTEND functional tests (e.g., Jasmine/Selenium/Cypress concepts) if missing.
   - Consult the Knowledge Base for "Testing Guidelines".
3) DEPLOYABILITY CHECK:
   - Ensure the application is ready for deployment.
   - Verify no critical regressions.
4) EXECUTE VERIFICATION:
   - Use UnitTestTool to run the full test suite.
   - If tests are missing or insufficient, REJECT the build and ask for more tests.
5) Compare Actual Result vs Expected Result.
6) VERIFY ACCEPTANCE CRITERIA (ACs):
   - Ensure all ACs defined in the ticket/bug description are met.

Output:
QA VERIFICATION REPORT
- Status: RELEASE READY / REJECTED
- Functional Test Coverage
- Acceptance Criteria Verification (Pass/Fail for each AC)
- Evidence (logs, test outputs)
""",
        expected_output="QA report confirming functional quality and release readiness.",
        agent=agent,
    )


