import os
import json
import subprocess
from pathlib import Path
from functools import lru_cache
from typing import Optional, List

from crewai_tools import FileReadTool, FileWriterTool
from codeguardian.tools.local_rag_tool import LocalDirectoryRagTool


# -------------------------
# Paths
# -------------------------
def _project_dir() -> Path:
    # TARGET repository you want to analyze/change
    return Path(os.getenv("PROJECT_PATH", r"C:\project-backend")).resolve()


def _inputs_dir() -> Path:
    return Path(os.getenv("INPUTS_PATH", r"C:\inputs")).resolve()


def _chroma_dir() -> Path:
    return Path(os.getenv("CHROMA_DIR", "./content/.chroma")).resolve()


def _index_meta_path() -> Path:
    # store last indexed git head + settings snapshot
    return _chroma_dir() / "index.meta.json"


# -------------------------
# BUG files
# -------------------------
def bug_files_tools():
    inputs = _inputs_dir()
    desc = os.getenv("BUG_DESC_FILE", "bug-desc.txt")
    log = os.getenv("BUG_LOG_FILE", "bug-log.txt")
    return [
        FileReadTool(file_path=str((inputs / desc).resolve())),
        FileReadTool(file_path=str((inputs / log).resolve())),
    ]


# -------------------------
# RAG tool (cached per process)
# -------------------------
@lru_cache(maxsize=1)
def directory_search_tool() -> LocalDirectoryRagTool:
    # IMPORTANT: no indexing side effects here
    return LocalDirectoryRagTool(
        directory=str(_project_dir()),
        persist_directory=str(_chroma_dir()),
    )


# -------------------------
# Index configuration (globs)
# -------------------------
def _backend_include_globs() -> List[str]:
    return [
        "src/main/java/**",
        "src/test/java/**",
        "src/main/resources/**",
        "**/pom.xml",
        "**/*.gradle",
        "**/*.properties",
        "**/*.yml",
        "**/*.yaml",
        "**/*.xml",
        "**/*.sql",
    ]


def _backend_exclude_globs() -> List[str]:
    return ["**/target/**", "**/build/**"]


def _frontend_include_globs() -> List[str]:
    return [
        "src/**",
        "projects/**",
        "angular.json",
        "package.json",
        "tsconfig*.json",
        "**/*.ts",
        "**/*.html",
        "**/*.scss",
        "**/*.css",
        "**/*.md",
    ]


def _frontend_exclude_globs() -> List[str]:
    return ["**/node_modules/**", "**/dist/**", "**/.angular/**", "**/.cache/**"]


def _index_settings_snapshot() -> dict:
    """
    Minimal snapshot. If you change these knobs, we can decide to reindex.
    (Not 'enterprise heavy', but enough to avoid surprises.)
    """
    return {
        "project_dir": str(_project_dir()),
        "chroma_dir": str(_chroma_dir()),
        "backend_include": _backend_include_globs(),
        "backend_exclude": _backend_exclude_globs(),
        "frontend_include": _frontend_include_globs(),
        "frontend_exclude": _frontend_exclude_globs(),
        "embed_model": os.getenv("EMBED_MODEL", "nomic-embed-text:latest"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "chunk_chars": int(os.getenv("CHUNK_CHARS", "1800")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "200")),
        "max_file_bytes": int(os.getenv("MAX_FILE_BYTES", "2000000")),
    }


# -------------------------
# Meta read/write
# -------------------------
def _read_meta() -> Optional[dict]:
    p = _index_meta_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_meta(git_head: Optional[str]) -> None:
    _chroma_dir().mkdir(parents=True, exist_ok=True)
    meta = {
        "git_head": git_head,
        "settings": _index_settings_snapshot(),
    }
    _index_meta_path().write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")


# -------------------------
# Git helpers
# -------------------------
def _is_git_repo(repo: Path) -> bool:
    return (repo / ".git").exists()


def _git_head(repo: Path) -> Optional[str]:
    if not _is_git_repo(repo):
        return None
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def _git_changed_files(repo: Path, old_head: str, new_head: str) -> List[str]:
    """
    Returns changed files between two commits as repo-relative paths (with forward slashes).
    """
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "diff", "--name-only", f"{old_head}..{new_head}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        files = []
        for line in out.splitlines():
            line = line.strip().replace("\\", "/")
            if line:
                files.append(line)
        return files
    except Exception:
        return []

def _git_dirty_files(repo: Path) -> list[str]:
    """
    Returns files with uncommitted changes (staged or unstaged)
    as repo-relative paths.
    """
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "status", "--porcelain"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        files = []
        for line in out.splitlines():
            if not line.strip():
                continue
            # Format: XY path
            path = line[3:].strip().replace("\\", "/")
            if path:
                files.append(path)
        return files
    except Exception:
        return []

# -------------------------
# Glob relevance check (for changed files)
# -------------------------
def _matches_any(path: str, globs: List[str]) -> bool:
    # We want "**" support similar to fnmatch; LocalDirectoryRagTool uses fnmatch internally.
    # We'll use fnmatch here too (works fine with ** patterns).
    from fnmatch import fnmatch
    return any(fnmatch(path, g) for g in globs)


def _is_relevant_change(changed_files: List[str]) -> bool:
    """
    True if any changed file falls into our indexing include globs (and not excluded).
    """
    b_inc, b_exc = _backend_include_globs(), _backend_exclude_globs()
    f_inc, f_exc = _frontend_include_globs(), _frontend_exclude_globs()

    for rel in changed_files:
        # Exclude first
        if _matches_any(rel, b_exc) or _matches_any(rel, f_exc):
            continue

        # Include?
        if _matches_any(rel, b_inc) or _matches_any(rel, f_inc):
            return True

    return False


# -------------------------
# Indexing functions
# -------------------------
def _index_backend(tool: LocalDirectoryRagTool) -> None:
    tool.index_paths(
        include_globs=_backend_include_globs(),
        exclude_globs=_backend_exclude_globs(),
        max_files_per_run=int(os.getenv("INDEX_MAX_FILES_BACKEND", "4000")),
    )


def _index_frontend(tool: LocalDirectoryRagTool) -> None:
    tool.index_paths(
        include_globs=_frontend_include_globs(),
        exclude_globs=_frontend_exclude_globs(),
        max_files_per_run=int(os.getenv("INDEX_MAX_FILES_FRONTEND", "4000")),
    )


def ensure_repo_indexed(force: bool = False) -> str:
    """
    Continue-like behavior:
    - First time: index
    - Next runs: check git HEAD; if unchanged -> skip
    - If HEAD changed: only re-index if changed files are relevant to our include_globs
    - FORCE_REINDEX=1 always indexes
    """
    if os.getenv("FORCE_REINDEX", "0") == "1":
        force = True

    repo = _project_dir()
    meta = _read_meta()
    head = _git_head(repo)

    # No meta => first time
    if meta is None:
        tool = directory_search_tool()
        _index_backend(tool)
        _index_frontend(tool)
        _write_meta(head)
        return "Index created (first run)."

    # If settings changed, re-index (simple & safe)
    prev_settings = meta.get("settings") or {}
    cur_settings = _index_settings_snapshot()
    if not force and prev_settings != cur_settings:
        tool = directory_search_tool()
        _index_backend(tool)
        _index_frontend(tool)
        _write_meta(head)
        return "Index updated (settings changed)."

    # If not a git repo (or git head unknown), we cannot do cheap change detection
    if head is None:
        if force:
            tool = directory_search_tool()
            _index_backend(tool)
            _index_frontend(tool)
            _write_meta(None)
            return "Index updated (forced, no git detected)."
        # default: skip to avoid heavy scans
        if os.getenv("AUTO_INDEX_NO_GIT", "0") == "1":
            tool = directory_search_tool()
            _index_backend(tool)
            _index_frontend(tool)
            _write_meta(None)
            return "Index updated (AUTO_INDEX_NO_GIT=1)."
        return "Index check skipped (no git detected). Set AUTO_INDEX_NO_GIT=1 or FORCE_REINDEX=1."

    old_head = meta.get("git_head")
    if not force and old_head == head:
        return f"Index up-to-date (git HEAD unchanged: {head[:10]}…)."

    # HEAD changed -> check relevant diffs
    changed_committed = _git_changed_files(repo, old_head, head)
    changed_dirty = _git_dirty_files(repo)

    all_changed = list(set(changed_committed + changed_dirty))

    if all_changed and not _is_relevant_change(all_changed):
        _write_meta(head)
        return (
            "Index skipped (git changed but not relevant). "
            f"HEAD={head[:10]}…, dirty_files={len(changed_dirty)}"
        )

    # Otherwise re-index
    tool = directory_search_tool()
    _index_backend(tool)
    _index_frontend(tool)
    _write_meta(head)
    return f"Index updated. HEAD={head[:10]}…"


# -------------------------
# Agent toolsets
# -------------------------
def architect_tools():
    project = _project_dir()
    return [
        FileReadTool(file_path=str((project / ".gitignore").resolve())),  # from TARGET repo
        *bug_files_tools(),
        directory_search_tool(),
    ]


def engineer_tools():
    project = _project_dir()
    return [
        FileReadTool(file_path=str((project / ".gitignore").resolve())),
        *bug_files_tools(),
        directory_search_tool(),
        FileWriterTool(),
    ]
