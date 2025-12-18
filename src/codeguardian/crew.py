import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process, LLM
from crewai.project import CrewBase, crew
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from .config.settings import settings
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
        model=settings.openai_model_name,
        base_url=settings.openai_api_base,
        api_key=settings.openai_api_key,
    )


@CrewBase
class Codeguardian:
    """Full Pipeline: Architect -> Engineer -> DevOps -> QA"""

    @crew
    def crew(self) -> Crew:
        logger = logging.getLogger(__name__)
        llm = _llm()

        msg = ensure_repo_indexed()
        logger.info(msg)

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

        # Knowledge Sources
        knowledge_sources = self._load_knowledge_sources()
        
        # Configure Ollama environment for embeddings
        os.environ["OLLAMA_HOST"] = settings.ollama_base_url
        os.environ["EMBEDDINGS_OLLAMA_MODEL_NAME"] = settings.embed_model
        os.environ["EMBEDDINGS_OLLAMA_BASE_URL"] = settings.ollama_base_url

        return Crew(
            agents=[architect, engineer, devops, qa],
            tasks=[t1, t2, t3, t4],
            process=Process.sequential,
            tracing=True,
            verbose=True,
            knowledge_sources=knowledge_sources,
            embedder={
                "provider": "ollama",
                "config": {
                    "model": settings.embed_model,
                    "base_url": settings.ollama_base_url,
                }
            }
        )


    def _load_knowledge_sources(self):
        """Load knowledge sources from the knowledge directory."""
        knowledge_sources = []
        knowledge_dir = Path("knowledge")
        if knowledge_dir.exists():
            # CrewAI seems to prepend 'knowledge/' to the path.
            # So we pass just the filename.
            files = [f.name for f in knowledge_dir.glob("*.txt")]
            if files:
                knowledge_sources.append(TextFileKnowledgeSource(file_paths=files))
        return knowledge_sources
