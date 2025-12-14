import os
from typing import List

from dotenv import load_dotenv
from crewai import Crew, Process, Task, LLM
from crewai.project import CrewBase, crew
from crewai.agents.agent_builder.base_agent import BaseAgent

from .agents import (
    build_senior_software_engineer,
    build_test_automation_expert,
    build_devops_expert,
)

from .tasks import (
    build_triage_and_fix_task,
    build_playwright_regression_task,
    build_build_deploy_runbook_task,
)

load_dotenv(override=True)


def _llm() -> LLM:
    openai_api_key = os.getenv("OPENAI_API_KEY", "test")
    model = os.getenv("MODEL", "openai/kaitchup/Llama-3.3-70B-Instruct-AutoRound-GPTQ-4bit")
    api_base = os.getenv("API_BASE", "http://bmf-ai.apps.ce.capgemini.com/chat/v1")

    return LLM(
        model=model,
        base_url=api_base,
        api_key=openai_api_key,
    )


@CrewBase
class Codeguardian:
    """Codeguardian crew (best practice, code-first, no YAML)"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @crew
    def crew(self) -> Crew:
        llm = _llm()

        issue_text = os.getenv("ISSUE_TEXT", "Bug: API returns 500 when payload field 'x' is missing.")
        app_context = os.getenv("APP_CONTEXT", "Backend: Spring Boot; UI: Web; E2E: Playwright; Deploy: Docker/K8s.")
        constraints = os.getenv("CONSTRAINTS", "- Minimal diff\n- Backward compatible\n- Add regression tests\n")

        senior_software_engineer = build_senior_software_engineer(llm)
        test_automation_expert = build_test_automation_expert(llm)
        devops_expert = build_devops_expert(llm)

        t1 = build_triage_and_fix_task(
            agent=senior_software_engineer,
            issue_text=issue_text,
            app_context=app_context,
            constraints=constraints,
        )

        t2 = build_playwright_regression_task(
            agent=test_automation_expert,
            issue_text=issue_text,
            triage_summary="",
            app_context=app_context,
        )

        t3 = build_build_deploy_runbook_task(
            agent=devops_expert,
            issue_text=issue_text,
            test_plan="",
            app_context=app_context,
        )

        return Crew(
            agents=[senior_software_engineer, test_automation_expert, devops_expert],
            tasks=[t1, t2, t3],
            process=Process.sequential,
            verbose=True,
        )
