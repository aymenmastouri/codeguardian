import os
from dotenv import load_dotenv
from crewai import Crew, Process, LLM
from crewai.project import CrewBase, crew

from .agents import (
    build_senior_software_architect, 
    build_senior_software_engineer,
    build_devops_engineer,
    build_qa_engineer,
    build_engineering_manager
)
from .tasks import (
    analysis_and_design_task, 
    implementation_task,
    build_and_test_task,
    functional_verification_task,
    manager_review_task
)
from .tools.tools import (
    architect_tools, 
    engineer_tools, 
    devops_tools,
    qa_tools,
    ensure_repo_indexed
)

load_dotenv(override=True)


def _llm() -> LLM:
    return LLM(
        model=os.getenv("MODEL"),
        base_url=os.getenv("API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


@CrewBase
class Codeguardian:
    """Full Pipeline: Architect -> Engineer -> DevOps -> QA"""

    @crew
    def crew(self) -> Crew:
        llm = _llm()

        msg = ensure_repo_indexed()
        print(msg)

        architect = build_senior_software_architect(llm, tools=architect_tools())
        engineer = build_senior_software_engineer(llm, tools=engineer_tools())
        devops = build_devops_engineer(llm, tools=devops_tools())
        qa = build_qa_engineer(llm, tools=qa_tools())
        manager = build_engineering_manager(llm, tools=[]) # Manager delegates, doesn't need direct tools usually, or maybe read tools

        t1 = analysis_and_design_task(architect)
        t2 = implementation_task(engineer)
        t3 = build_and_test_task(devops)
        t4 = functional_verification_task(qa)
        t5 = manager_review_task(manager, context_tasks=[t3, t4])

        # Chain context
        t2.context = [t1]
        t3.context = [t2] # DevOps needs to know what changed
        t4.context = [t1, t3] # QA needs bug desc (from t1 context or file) and build status

        return Crew(
            agents=[architect, engineer, devops, qa, manager],
            tasks=[t1, t2, t3, t4, t5],
            process=Process.sequential,
            tracing=True,
            verbose=True,
        )
