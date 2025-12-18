from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Centralized configuration management using Pydantic Settings.
    Reads from environment variables and .env file.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Required paths - Fail fast if not provided
    project_path: Path = Field(..., description="Path to the target project to analyze/fix")
    
    # Optional paths with sensible defaults
    inputs_path: Path = Field(default=Path("inputs"), description="Path to input files (bug reports, etc)")
    chroma_dir: Path = Field(default=Path("./content/.chroma"), description="Path to ChromaDB storage")
    
    # Bug files
    bug_desc_file: str = Field(default="bug-desc.txt", description="Name of the bug description file")
    bug_log_file: str = Field(default="bug-log.txt", description="Name of the bug log file")

    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_name: str = Field(default="gpt-4o", alias="MODEL") # Note: .env uses MODEL, not OPENAI_MODEL_NAME
    openai_api_base: Optional[str] = Field(default=None, alias="API_BASE")
    
    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    embed_model: str = Field(default="nomic-embed-text:latest", alias="EMBED_MODEL")

    @property
    def index_meta_path(self) -> Path:
        return self.chroma_dir / "index.meta.json"

    @property
    def bug_desc_path(self) -> Path:
        return (self.inputs_path / self.bug_desc_file).resolve()

    @property
    def bug_log_path(self) -> Path:
        return (self.inputs_path / self.bug_log_file).resolve()

# Singleton instance
try:
    settings = Settings()
except Exception as e:
    print(f"Configuration Error: {e}")
    print("Please ensure your .env file is correctly configured with PROJECT_PATH.")
    # We don't exit here to allow tools to import this module for type checking, 
    # but runtime usage will fail if settings isn't initialized.
    # Re-raising is safer for "Fail Fast"
    raise
