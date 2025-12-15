import os
import time
from pathlib import Path
from typing import Iterable, List, Dict, Optional
from fnmatch import fnmatch

import requests
import chromadb
from pydantic import BaseModel, Field, PrivateAttr
from crewai.tools import BaseTool


class LocalRagSearchArgs(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(5, ge=1, le=20, description="Top-K results to return")


class LocalDirectoryRagTool(BaseTool):
    """
    CrewAI BaseTool:
      - Local semantic search over a directory
      - Embeddings: Ollama (nomic-embed-text)
      - Vector DB: Chroma persistent store
      - Indexing: ONLY via index_paths(globs=...) (incremental + chunking)
    """

    name: str = "local_directory_rag_search"
    description: str = (
        "Local semantic search over a directory using Ollama embeddings + ChromaDB. "
        "Index selected areas via index_paths(include_globs=[...])."
    )
    args_schema: type[BaseModel] = LocalRagSearchArgs

    # Private runtime attributes (Pydantic-safe)
    _directory: Path = PrivateAttr()
    _persist_directory: str = PrivateAttr()
    _collection_name: str = PrivateAttr()

    _ollama_base: str = PrivateAttr()
    _embed_model: str = PrivateAttr()
    _timeout_s: int = PrivateAttr()

    _max_file_bytes: int = PrivateAttr()
    _chunk_chars: int = PrivateAttr()
    _chunk_overlap: int = PrivateAttr()

    _exts: set[str] = PrivateAttr()
    _exclude_dirs: set[str] = PrivateAttr()

    _client = PrivateAttr()
    _collection = PrivateAttr()

    def __init__(
            self,
            directory: str,
            persist_directory: str = "./content/.chroma",
            collection_name: str = "codeguardian",
            ollama_base_url: Optional[str] = None,
            embed_model: Optional[str] = None,
            max_file_bytes: int = 2_000_000,
            chunk_chars: int = 1800,
            chunk_overlap: int = 200,
            exts: Optional[set[str]] = None,
            exclude_dirs: Optional[set[str]] = None,
            request_timeout_s: int = 120,
            **kwargs,
    ):
        super().__init__(**kwargs)

        self._directory = Path(directory)
        self._persist_directory = str(Path(persist_directory).resolve())
        self._collection_name = collection_name

        self._ollama_base = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._embed_model = embed_model or os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
        self._timeout_s = request_timeout_s

        self._max_file_bytes = max_file_bytes
        self._chunk_chars = chunk_chars
        self._chunk_overlap = chunk_overlap

        self._exts = exts or {
            ".java", ".xml", ".properties", ".yml", ".yaml", ".sql", ".md",
            ".ts", ".tsx", ".html", ".scss", ".css", ".json",
            ".gradle", ".toml", ".txt", ".py"
        }
        self._exclude_dirs = exclude_dirs or {
            ".git", ".venv", "node_modules", "dist", "build", "target", ".idea",
            "__pycache__", ".pytest_cache"
        }

        self._client = chromadb.PersistentClient(path=self._persist_directory)
        self._collection = self._client.get_or_create_collection(self._collection_name)

    # -------------------------
    # CrewAI entrypoint
    # -------------------------
    def _run(self, query: str, k: int = 5) -> str:
        q_emb = self._embed_one(query)
        res = self._collection.query(query_embeddings=[q_emb], n_results=int(k))

        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]

        if not docs:
            return "No results."

        out = []
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            path = meta.get("path", "unknown")
            chunk = meta.get("chunk", "?")
            out.append(f"### {i+1}) {path} (chunk {chunk})\n{doc[:1200]}\n")
        return "\n".join(out)

    # -------------------------
    # ONLY indexing API you want
    # -------------------------
    def index_paths(
            self,
            include_globs: List[str],
            exclude_globs: Optional[List[str]] = None,
            max_files_per_run: int = 500,
    ) -> str:
        if not include_globs:
            return "index_paths: include_globs is empty. Nothing indexed."

        exclude_globs = exclude_globs or []

        added_files = 0
        added_chunks = 0
        skipped_already = 0
        skipped_unreadable = 0
        t0 = time.time()

        for p in self._iter_files_filtered(include_globs, exclude_globs):
            try:
                st = p.stat()
            except OSError:
                skipped_unreadable += 1
                continue

            path = str(p)
            mtime = int(st.st_mtime)
            size = int(st.st_size)

            if self._already_indexed(p, mtime, size):
                skipped_already += 1
                continue

            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                skipped_unreadable += 1
                continue

            if not content.strip():
                continue

            chunks = self._chunk_text(content)
            if not chunks:
                continue

            # Remove older chunks for this file (best effort)
            try:
                self._collection.delete(where={"path": path})
            except Exception:
                pass

            ids: List[str] = []
            docs: List[str] = []
            metas: List[Dict] = []
            embs: List[List[float]] = []

            for i, ch in enumerate(chunks):
                doc_id = f"{path}::{i}::mtime={mtime}::size={size}"
                ids.append(doc_id)
                docs.append(ch)
                metas.append({"path": path, "chunk": i, "mtime": mtime, "size": size})

            for d in docs:
                embs.append(self._embed_one(d))

            self._collection.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)

            added_files += 1
            added_chunks += len(ids)

            if added_files >= int(max_files_per_run):
                break

        dt = time.time() - t0
        return (
            f"index_paths: indexed {added_files} files / {added_chunks} chunks in {dt:.1f}s "
            f"(skipped already={skipped_already}, unreadable={skipped_unreadable}) "
            f"persist={self._persist_directory}"
        )

    # -------------------------
    # Internals
    # -------------------------
    def _embed_one(self, text: str) -> List[float]:
        r = requests.post(
            f"{self._ollama_base}/api/embeddings",
            json={"model": self._embed_model, "prompt": text},
            timeout=self._timeout_s,
        )
        r.raise_for_status()
        return r.json()["embedding"]

    def _iter_files(self) -> Iterable[Path]:
        for p in self._directory.rglob("*"):
            if not p.is_file():
                continue
            if any(part in self._exclude_dirs for part in p.parts):
                continue
            if p.suffix.lower() not in self._exts:
                continue
            try:
                if p.stat().st_size > self._max_file_bytes:
                    continue
            except OSError:
                continue
            yield p

    def _iter_files_filtered(self, include_globs: List[str], exclude_globs: List[str]) -> Iterable[Path]:
        root = self._directory
        for p in self._iter_files():
            try:
                rel = str(p.relative_to(root)).replace("\\", "/")
            except Exception:
                continue

            if not any(fnmatch(rel, g) for g in include_globs):
                continue
            if any(fnmatch(rel, g) for g in exclude_globs):
                continue
            yield p

    def _chunk_text(self, text: str) -> List[str]:
        text = text.replace("\r\n", "\n").strip()
        if not text:
            return []
        if len(text) <= self._chunk_chars:
            return [text]

        chunks: List[str] = []
        step = max(1, self._chunk_chars - self._chunk_overlap)
        for start in range(0, len(text), step):
            chunk = text[start : start + self._chunk_chars].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _already_indexed(self, p: Path, mtime: int, size: int) -> bool:
        marker_id = f"{str(p)}::0::mtime={mtime}::size={size}"
        try:
            got = self._collection.get(ids=[marker_id])
            return bool(got and got.get("ids") and len(got["ids"]) == 1)
        except Exception:
            return False
