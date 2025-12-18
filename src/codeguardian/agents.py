from crewai import Agent, LLM

def build_senior_software_architect(llm: LLM, tools=None) -> Agent:
    return Agent(
        role="Senior Software Architect (Analysis & Design)",
        goal="Analyze bug inputs + repo structure and produce an actionable change plan (no implementation).",
        backstory="Senior architect with strong distributed systems and production debugging experience.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=18,
        max_retry_limit=2,
        allow_code_execution=False,
        tools=tools or [],
    )

def build_senior_software_engineer(llm: LLM, tools=None) -> Agent:
    return Agent(
        role="Senior Software Engineer (Implementation)",
        goal="Implement the approved fix in the target repo with minimal diff and clear change summary.",
        backstory="Senior engineer focused on safe, clean, production-ready changes.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=25,
        max_retry_limit=2,
        allow_code_execution=False,
        tools=tools or [],

    )

def build_devops_engineer(llm: LLM, tools=None) -> Agent:
    return Agent(
        role="DevOps Engineer (Build & Integration)",
        goal="Ensure the project builds successfully and unit tests pass. Fix compilation errors if they occur.",
        backstory="Expert DevOps engineer who specializes in CI/CD pipelines and fixing build breakages.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
        max_retry_limit=2,
        allow_code_execution=False, # Uses BuildTool
        tools=tools or [],
    )

def build_qa_engineer(llm: LLM, tools=None) -> Agent:
    return Agent(
        role="QA Engineer (Functional Verification)",
        goal="Verify the fix by reproducing the bug steps and ensuring the expected result is met.",
        backstory="Detail-oriented QA engineer who ensures no regressions and verifies bug fixes against requirements.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
        max_retry_limit=2,
        allow_code_execution=False,
        tools=tools or [],
    )
