from typing import Type, Optional
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from codeguardian.config.settings import settings

class ProjectFileWriterInput(BaseModel):
    """Input schema for ProjectFileWriterTool."""
    file_path: str = Field(..., description="The path to the file to write, RELATIVE to the project root (e.g., 'src/main/java/com/example/Service.java').")
    content: str = Field(..., description="The content to write to the file.")
    overwrite: bool = Field(default=True, description="Whether to overwrite the file if it exists.")

class ProjectFileWriterTool(BaseTool):
    name: str = "Project File Writer"
    description: str = (
        "Writes content to a file within the target project directory. "
        "Automatically resolves paths relative to the configured PROJECT_PATH. "
        "Use this tool to implement code changes."
    )
    args_schema: Type[BaseModel] = ProjectFileWriterInput

    def _run(self, file_path: str, content: str, overwrite: bool = True) -> str:
        try:
            # Resolve path relative to PROJECT_PATH
            # Remove leading slashes/backslashes to ensure it's treated as relative
            clean_path = file_path.lstrip("/\\")
            full_path = (settings.project_path / clean_path).resolve()

            # Security check: ensure we are still inside PROJECT_PATH
            if not str(full_path).startswith(str(settings.project_path.resolve())):
                return f"Error: Attempted to write outside project path: {full_path}"

            if full_path.exists() and not overwrite:
                return f"Error: File {full_path} already exists and overwrite=False."

            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            full_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote to {full_path}"

        except Exception as e:
            return f"Error writing file: {str(e)}"
