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
- ROOT CAUSE ANALYSIS (RCA)
- ARCHITECTURAL SOLUTION (design approach, patterns to use, components to modify)
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
- The Architect's output (including RCA, ARCHITECTURAL SOLUTION, and PATCH_PLAN_JSON) is provided as TASK CONTEXT.
- PATCH_PLAN_JSON is NOT a file.
- DO NOT attempt to read "PATCH_PLAN_JSON" via FileReadTool or any filesystem path.
- Extract the JSON only from the context markers:
  ---PATCH_PLAN_JSON_START---
  ...json...
  ---PATCH_PLAN_JSON_END---

DESIGN BEFORE IMPLEMENTATION (MANDATORY):
1) READ and UNDERSTAND the Architect's RCA and ARCHITECTURAL SOLUTION
2) DESIGN your technical solution:
   - What classes/methods will you modify?
   - What null checks, validations, or error handling will you add?
   - What edge cases must be covered?
   - How will you structure the tests?
3) DOCUMENT your technical design approach in your final answer
4) ONLY THEN start implementing

MANDATORY FILE OPERATIONS (STRICT):

A) FOR FILES IN PATCH PLAN (target_files[]) - MODIFY EXISTING:
   
   Step 1: Build the FULL absolute path to READ the existing file
   - absolute_path = PROJECT_PATH + "/" + target_files[].path
   - Example: "C:/project-backend/src/main/java/org/project_backend/project/example/BuggyService.java"
   - Use FileReadTool with this absolute path
   
   Step 2: Modify the content in memory
   - Apply the changes described in the patch plan
   
   Step 3: Write back to the SAME file (OVERWRITE)
   - Use FileWriterTool with these EXACT parameters:
     * filename: The FULL relative path from target_files[].path
       Example: "src/main/java/org/project_backend/project/example/BuggyService.java"
     * directory: PROJECT_PATH
       Example: "C:/project-backend"
     * content: The complete new file content
     * overwrite: True
   
   CRITICAL: MODIFY existing files from patch plan, do NOT create duplicates!

B) FOR NEW FILES (e.g., new test classes, new helpers) - CREATE:
   
   - You CAN and SHOULD create new test files if needed
   - BEFORE creating, check if the file already exists by trying FileReadTool first
   - If the file EXISTS: Read it, modify it, and write with overwrite: True
   - If the file DOES NOT EXIST: Create it with overwrite: False (or True)
   - Use FileWriterTool with:
     * filename: Full relative path for the new file
       Example: "src/test/java/org/project_backend/project/example/BuggyServiceIntegrationTest.java"
     * directory: PROJECT_PATH
     * content: The complete file content
     * overwrite: True (if modifying existing) or False (if creating new)
   
   - Ensure proper package structure matches directory structure
   - Follow project conventions for file naming and location
   
CRITICAL: Always check if a file exists before deciding to create vs modify!

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
- AFTER implementing all changes, you MUST run BuildTool and UnitTestTool.
- If the build or tests FAIL, you MUST FIX the issues immediately.
- ITERATE until all tests PASS.
- DO NOT finish this task until the build is GREEN and all tests PASS.
- YOU are the ONLY agent permitted to modify application source code. Ensure it is correct before DevOps sees it.
- Your task is INCOMPLETE if you hand off broken code.

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
- Ensure Test Package Alignment: Tests must reside in the same package structure as the class under test, or import it correctly.
- Fix Package Declarations: Ensure the 'package' statement matches the directory structure.

IMPORTANT: Never output empty actions or "None". Always either:
- Use a tool (FileReadTool, FileWriterTool, BuildTool, UnitTestTool, local_directory_rag_search)
- OR provide your Final Answer with the complete implementation summary

If you find yourself without a next action, you should either:
- Continue with the next file from the patch plan
- Run BuildTool to verify your changes
- Run UnitTestTool to validate tests
- Provide your Final Answer if all work is complete

COMPLETION CRITERIA (MANDATORY):
- Your task is COMPLETE only when:
  1. All target files from the patch plan have been modified
  2. All tests have been created/updated
  3. BuildTool shows SUCCESS
  4. UnitTestTool shows all tests PASSING
- If any of the above fails, CONTINUE working until all criteria are met.

Output:
IMPLEMENTATION SUMMARY
- Technical Design Approach (your solution design)
- Changed files (relative paths) + per-file summary
- Test Strategy (what tests were created/updated and why)
- Verification steps
- Build & Test Results (must be SUCCESS/PASS)
- Deviations (if any)
""",
        expected_output="Implementation summary with changed files and verification steps.",
        agent=agent,
    )

def build_and_test_task(agent: Agent) -> Task:
    return Task(
        description="""
You are the DevOps Engineer (Verification & Gatekeeper).

Your role: VERIFY the engineer's work is truly ready for production.

1) Detect the build system (Gradle, Maven, NPM) using BuildTool (auto-detect).
2) Run the build command using BuildTool.
3) Run the full test suite using UnitTestTool.
4) If the build or tests FAIL:
   - This should NOT happen - the engineer must deliver passing code.
   - REPORT the failure details immediately.
   - REJECT the handoff and send back to engineer.
   - YOU CANNOT FIX CODE - only verify it.
5) If the build and tests SUCCEED:
   - Confirm the build is stable and deployable.

Output:
BUILD REPORT
- Status: SUCCESS / FAILURE
- Build Logs (snippet)
- Test Results
""",
        expected_output="Build report indicating success or failure.",
        agent=agent,
    )

def functional_verification_task(agent: Agent) -> Task:
    return Task(
        description="""
You are the QA Engineer (Black-Box Functional Testing).

Your goal: Verify the fix works from the END-USER perspective, not just unit tests.

1) Read the "Steps to Reproduce" and "Expected Result" from the bug description.

2) BLACK-BOX FUNCTIONAL TESTING (MANDATORY):
   - Execute the "Steps to Reproduce" from the bug description.
   - For REST APIs: Describe how to test with curl/Postman (e.g., "curl http://localhost:8080/bug")
   - For Web Apps: Describe E2E test scenarios (e.g., Playwright, Selenium, Cypress)
   - For Backend Services: Verify behavior through exposed interfaces
   - YOU MUST verify the actual running application, not just read test code.

3) EXECUTE VERIFICATION:
   - Use UnitTestTool to confirm all unit/integration tests pass.
   - Review test coverage - if critical scenarios are missing, REJECT.

4) COMPARE RESULTS:
   - Actual Result (from your functional test) vs Expected Result (from bug description)
   - Does the fix actually solve the user's problem?

5) VERIFY ACCEPTANCE CRITERIA (ACs):
   - Check each AC defined in the ticket/bug description.
   - Mark each as PASS or FAIL.

6) DECISION:
   - RELEASE READY: All ACs met, functional test confirms fix, no regressions
   - REJECTED: Fix incomplete, tests insufficient, or regressions detected

Output:
QA VERIFICATION REPORT
- Status: RELEASE READY / REJECTED
- Functional Test Execution (how you verified - curl command, E2E scenario, etc.)
- Actual Result vs Expected Result
- Acceptance Criteria Verification (Pass/Fail for each AC)
- Test Coverage Assessment
- Evidence (logs, test outputs, API responses)
- Rejection Reason (if rejected)
""",
        expected_output="QA report confirming functional quality and release readiness.",
        agent=agent,
    )


