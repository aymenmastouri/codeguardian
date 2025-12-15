import os
from dotenv import load_dotenv
from crewai import Crew, Process, LLM
from crewai.project import CrewBase, crew

from .agents import build_senior_software_architect, build_senior_software_engineer
from .tasks import analysis_and_design_task, implementation_task
from .tools.tools import architect_tools, engineer_tools, ensure_repo_indexed

load_dotenv(override=True)


def _llm() -> LLM:
    return LLM(
        model=os.getenv("MODEL"),
        base_url=os.getenv("API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


@CrewBase
class Codeguardian:
    """Final minimal version: Architect (analyze) -> Engineer (implement)"""

    @crew
    def crew(self) -> Crew:
        llm = _llm()

        msg = ensure_repo_indexed()
        print(msg)

        architect = build_senior_software_architect(llm, tools=architect_tools())
        engineer = build_senior_software_engineer(llm, tools=engineer_tools())

        t1 = analysis_and_design_task(architect)
        t2 = implementation_task(engineer)
        t2.context = [t1]
        return Crew(
            agents=[architect, engineer],
            tasks=[t1, t2],
            process=Process.sequential,
            verbose=True,
        )
