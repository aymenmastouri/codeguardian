import os
import subprocess
from typing import Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class BuildToolInput(BaseModel):
    command: Optional[str] = Field(None, description="Optional specific command to run. If None, auto-detects.")

class BuildTool(BaseTool):
    name: str = "build_project_tool"
    description: str = (
        "Detects the build system (Gradle, Maven, NPM) in the PROJECT_PATH and runs the build/compile command. "
        "Returns the stdout/stderr of the build process."
    )
    args_schema: Type[BaseModel] = BuildToolInput

    def _run(self, command: Optional[str] = None) -> str:
        project_path = os.getenv("PROJECT_PATH")
        if not project_path:
            return "Error: PROJECT_PATH environment variable not set."

        if command:
            cmd = command
        else:
            # Auto-detect
            if os.path.exists(os.path.join(project_path, "gradlew")) or os.path.exists(os.path.join(project_path, "gradlew.bat")):
                cmd = "./gradlew clean build -x test" if os.name != 'nt' else "gradlew.bat clean build -x test"
            elif os.path.exists(os.path.join(project_path, "mvnw")) or os.path.exists(os.path.join(project_path, "mvnw.cmd")):
                cmd = "./mvnw clean compile" if os.name != 'nt' else "mvnw.cmd clean compile"
            elif os.path.exists(os.path.join(project_path, "package.json")):
                cmd = "npm install && npm run build"
            else:
                return "Error: Could not auto-detect build system (no gradlew, mvnw, or package.json found)."

        try:
            # Run in the project directory
            result = subprocess.run(
                cmd,
                cwd=project_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300 # 5 minute timeout
            )
            if result.returncode == 0:
                return f"BUILD SUCCESS:\n{result.stdout}"
            else:
                return f"BUILD FAILED:\n{result.stderr}\n{result.stdout}"
        except Exception as e:
            return f"Execution Error: {str(e)}"

class UnitTestTool(BaseTool):
    name: str = "run_unit_tests_tool"
    description: str = (
        "Runs unit tests for the project. Auto-detects Gradle/Maven/NPM."
    )
    args_schema: Type[BaseModel] = BuildToolInput

    def _run(self, command: Optional[str] = None) -> str:
        project_path = os.getenv("PROJECT_PATH")
        if not project_path:
            return "Error: PROJECT_PATH environment variable not set."

        if command:
            cmd = command
        else:
            if os.path.exists(os.path.join(project_path, "gradlew")) or os.path.exists(os.path.join(project_path, "gradlew.bat")):
                cmd = "./gradlew test" if os.name != 'nt' else "gradlew.bat test"
            elif os.path.exists(os.path.join(project_path, "mvnw")) or os.path.exists(os.path.join(project_path, "mvnw.cmd")):
                cmd = "./mvnw test" if os.name != 'nt' else "mvnw.cmd test"
            elif os.path.exists(os.path.join(project_path, "package.json")):
                cmd = "npm test"
            else:
                return "Error: Could not auto-detect build system."

        try:
            result = subprocess.run(
                cmd,
                cwd=project_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return f"TESTS PASSED:\n{result.stdout}"
            else:
                return f"TESTS FAILED:\n{result.stderr}\n{result.stdout}"
        except Exception as e:
            return f"Execution Error: {str(e)}"
