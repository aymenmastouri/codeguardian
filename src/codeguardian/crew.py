import os
from dotenv import load_dotenv
from crewai import Crew, Process, LLM
from crewai.project import CrewBase, crew

from .agents import (
    build_senior_software_architect, 
    build_senior_software_engineer,
    build_devops_engineer,
    build_qa_engineer
)
from .tasks import (
    analysis_and_design_task, 
    implementation_task,
    build_and_test_task,
    functional_verification_task
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

        t1 = analysis_and_design_task(architect)
        t2 = implementation_task(engineer)
        t3 = build_and_test_task(devops)
        t4 = functional_verification_task(qa)

        # Chain context
        t2.context = [t1]
        t3.context = [t2] # DevOps needs to know what changed
        t4.context = [t1, t3] # QA needs bug desc (from t1 context or file) and build status

        return Crew(
            agents=[architect, engineer, devops, qa],
            tasks=[t1, t2, t3, t4],
            process=Process.sequential,
            tracing=True,
            verbose=True,
        )
