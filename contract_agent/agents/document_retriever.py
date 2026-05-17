from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

CHUNK_SIZE = 1000


class DocumentRetriever:
    """Simple optional Chroma-backed document retriever.

    This class uses `chromadb` when available. If the dependency is missing the
    retriever becomes a no-op returning empty results so the agent remains
    functional without the vector store.
    """

    def __init__(self, docs_path: Path | None = None, persist_path: Path | None = None):
        self.enabled = False
        self._client = None
        self._collection = None
        try:
            import chromadb  # type: ignore
            from chromadb.utils import embedding_functions  # type: ignore

            self.chromadb = chromadb
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            self.enabled = True
        except Exception:
            self.chromadb = None
            self.embedding_fn = None
            self.enabled = False

        self.docs_path = Path(docs_path) if docs_path else None
        self.persist_path = Path(persist_path) if persist_path else None

        if self.enabled and self.docs_path and self.docs_path.exists():
            self._client = chromadb.Client(chromadb.config.Settings())
            # persistent storage if requested
            try:
                if self.persist_path:
                    self._client = chromadb.PersistentClient(path=str(self.persist_path))  # type: ignore
            except Exception:
                # ignore persistence issues and fall back to in-memory
                pass
            self._collection = self._ensure_collection("data_contract_docs")
            self.index_from_dir(self.docs_path)

    def _ensure_collection(self, name: str):
        if not self.enabled:
            return None
        try:
            return self._client.get_collection(name=name)
        except Exception:
            return self._client.create_collection(name=name, embedding_function=self.embedding_fn)

    def index_from_dir(self, path: Path) -> None:
        if not self.enabled or not self._collection:
            return
        texts = []
        metadatas = []
        ids = []
        for file in sorted(path.glob("*.md")):
            content = file.read_text(encoding="utf-8")
            for i, chunk in enumerate(self._chunk_text(content, CHUNK_SIZE)):
                texts.append(chunk)
                metadatas.append({"source": str(file.relative_to(path)), "chunk_index": i})
                ids.append(f"{file.name}::{i}")
        if texts:
            try:
                self._collection.add(documents=texts, metadatas=metadatas, ids=ids)
            except Exception:
                # guard against collection re-creation or other errors
                pass

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return top_k documents as dicts {'text', 'source', 'score'}.

        If the vector store is not available, return an empty list.
        """
        if not self.enabled or not self._collection:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=top_k)
            hits = []
            for texts, metadatas, distances in zip(results.get("documents", []), results.get("metadatas", []), results.get("distances", [])):
                for text, meta, dist in zip(texts, metadatas, distances):
                    hits.append({"text": text, "source": meta.get("source"), "score": float(dist)})
            return hits
        except Exception:
            return []

    @staticmethod
    def _chunk_text(text: str, size: int) -> Iterable[str]:
        start = 0
        length = len(text)
        while start < length:
            end = min(start + size, length)
            yield text[start:end]
            start = end
