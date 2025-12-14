from crewai import Task
from crewai import Agent


def build_triage_and_fix_task(
        agent: Agent,
        issue_text: str,
        app_context: str = "",
        constraints: str = "",
) -> Task:
    return Task(
        description=f"""
You are a Senior Software Engineer (Cloud-Native & Distributed Systems).

Analyze the reported issue and propose a minimal, safe fix.
Focus on production-grade thinking: backward compatibility, resilience, and minimal blast radius.

Issue:
{issue_text}

Context:
{app_context}

Constraints:
{constraints}

Deliverables:
1) Root cause hypotheses (ranked)
2) Minimal fix strategy (step-by-step)
3) Concrete code-change guidance (modules/files/classes you would touch)
4) Distributed-systems risks (timeouts/retries/idempotency/concurrency)
5) Observability notes (logs/metrics/traces) to confirm the fix in production
""",
        expected_output="""
A structured triage report with:
- ranked root cause hypotheses
- minimal fix plan
- concrete code change guidance
- risk analysis (distributed systems)
- observability recommendations
""",
        agent=agent,
    )


def build_playwright_regression_task(
        agent: Agent,
        issue_text: str,
        triage_summary: str = "",
        app_context: str = "",
) -> Task:
    return Task(
        description=f"""
You are a Test Automation Expert (Playwright).

Design a Playwright regression test approach that validates the fix and prevents future regressions.
Focus on stability and CI reliability (anti-flakiness, deterministic test data, robust locators).

Issue:
{issue_text}

Triage summary:
{triage_summary}

Context:
{app_context}

Deliverables:
1) Test strategy (scope and coverage)
2) Given/When/Then test cases
3) Implementation guidance (locators, waits, retries, assertions)
4) Flakiness prevention checklist
5) Suggested test structure (file names, folders)
""",
        expected_output="""
A Playwright E2E regression plan including:
- strategy and coverage
- test cases (Given/When/Then)
- implementation guidelines (locators/waits/retries)
- flakiness prevention checklist
- suggested file/folder layout
""",
        agent=agent,
    )


def build_build_deploy_runbook_task(
        agent: Agent,
        issue_text: str,
        test_plan: str = "",
        app_context: str = "",
) -> Task:
    return Task(
        description=f"""
You are a DevOps Expert (Build, Deploy & Runtime).

Create a reproducible runbook to build, test, deploy and start the application.
Assume developers need copy/paste commands and clear environment variables.
Focus on reliability, fast feedback, and troubleshooting.

Issue:
{issue_text}

Playwright test plan:
{test_plan}

Context:
{app_context}

Deliverables:
1) Local build commands (Maven/Gradle variants)
2) Local run/start instructions (Spring Boot and containerized options)
3) Playwright execution steps (how to run E2E in CI and locally)
4) CI/CD pipeline outline (stages, caching hints)
5) Deploy outline (Docker/K8s/Helm - minimal steps)
6) Troubleshooting section (common failures + quick checks)
""",
        expected_output="""
A practical runbook with:
- exact build/test/run commands
- required env vars
- CI/CD outline
- deploy outline
- troubleshooting checklist
""",
        agent=agent,
    )
