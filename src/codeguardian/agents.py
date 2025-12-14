from crewai import Agent, LLM


def build_senior_software_engineer(llm: LLM) -> Agent:
    return Agent(
        role="Senior Software Engineer (Cloud-Native & Distributed Systems)",
        goal=(
            "Analyze issues and design minimal, robust fixes in distributed cloud-native systems "
            "(Spring Boot, REST APIs, async messaging, resilience patterns)."
        ),
        backstory=(
            "Senior software engineer with strong experience in distributed systems, "
            "data consistency, retries, idempotency, concurrency, and production debugging."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=18,
        max_retry_limit=2,
        allow_code_execution=False,
        tools=[],
    )


def build_test_automation_expert(llm: LLM) -> Agent:
    return Agent(
        role="Test Automation Expert (Playwright)",
        goal=(
            "Design stable Playwright end-to-end tests to validate fixes and prevent regressions, "
            "with strong focus on CI reliability and anti-flakiness."
        ),
        backstory=(
            "Expert in Playwright automation: stable locators, deterministic test data, "
            "parallel execution, and debugging flaky E2E tests."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=14,
        max_retry_limit=2,
        allow_code_execution=False,
        tools=[],
    )


def build_devops_expert(llm: LLM) -> Agent:
    return Agent(
        role="DevOps Expert (Build, Deploy & Runtime)",
        goal=(
            "Provide reproducible build, deploy and run instructions and ensure the application "
            "can be started reliably locally and in CI/CD."
        ),
        backstory=(
            "Experienced with Maven/Gradle, Docker, CI/CD pipelines, and runtime troubleshooting "
            "(ports, env vars, config, health checks)."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=14,
        max_retry_limit=2,
        allow_code_execution=False,
        tools=[],
    )
