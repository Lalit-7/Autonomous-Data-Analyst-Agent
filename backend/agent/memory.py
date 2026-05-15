"""
Session memory system using ChromaDB — stores and retrieves Q&A pairs for follow-up context.
Uses lazy initialization to avoid blocking server startup.
"""

import uuid
import json
import re
from datetime import datetime
from collections import defaultdict


def _get_chromadb():
    """Lazy-load ChromaDB. Returns (chromadb_client, True) or (None, False)."""
    try:
        import chromadb
        client = chromadb.Client()
        return client, True
    except Exception:
        return None, False


class SessionMemory:
    """Manages session-level memory. Uses ChromaDB when available, falls back to keyword matching."""

    def __init__(self):
        """Initialize memory storage. Returns None."""
        self._fallback_sessions = defaultdict(list)
        self._chroma_client = None
        self._chroma_available = None
        self._chroma_collections = {}

    def _ensure_chroma(self):
        """Lazy-init ChromaDB on first use. Returns True if available."""
        if self._chroma_available is None:
            self._chroma_client, self._chroma_available = _get_chromadb()
        return self._chroma_available

    def _get_collection(self, session_id: str):
        """Get or create a ChromaDB collection for a session. Returns the collection."""
        if session_id not in self._chroma_collections:
            name = f"s_{session_id.replace('-', '')[:48]}"
            self._chroma_collections[session_id] = self._chroma_client.get_or_create_collection(name=name)
        return self._chroma_collections[session_id]

    def _tokenize(self, text: str) -> set:
        """Tokenize text for fallback similarity. Returns set of tokens."""
        return set(re.findall(r'\b[a-z]{2,}\b', text.lower()))

    def _similarity(self, a: set, b: set) -> float:
        """Jaccard similarity. Returns float."""
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def store_interaction(self, session_id: str, query: str, response: str, metadata: dict = None):
        """Store a Q&A interaction in session memory. Returns None."""
        timestamp = datetime.now().isoformat()
        document = f"User asked: {query}\n\nAgent responded: {response[:2000]}"

        if self._ensure_chroma():
            try:
                collection = self._get_collection(session_id)
                meta = {"query": query[:500], "timestamp": timestamp, "type": "interaction"}
                if metadata:
                    for k, v in metadata.items():
                        if isinstance(v, (str, int, float, bool)):
                            meta[k] = v
                collection.add(documents=[document], ids=[str(uuid.uuid4())], metadatas=[meta])
                return
            except Exception:
                pass

        # Fallback: in-memory storage
        self._fallback_sessions[session_id].append({
            "id": str(uuid.uuid4()),
            "query": query[:500],
            "document": document,
            "tokens": self._tokenize(document),
            "timestamp": timestamp,
        })

    def retrieve_context(self, session_id: str, query: str, n_results: int = 5) -> str:
        """Retrieve relevant past interactions. Returns a formatted context string."""
        if self._ensure_chroma():
            try:
                collection = self._get_collection(session_id)
                if collection.count() == 0:
                    return "No previous interactions in this session."
                results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
                if results["documents"] and results["documents"][0]:
                    parts = [f"--- Previous Interaction {i+1} ---\n{doc}" for i, doc in enumerate(results["documents"][0])]
                    return "\n\n".join(parts)
                return "No relevant previous context found."
            except Exception:
                pass

        # Fallback
        entries = self._fallback_sessions.get(session_id, [])
        if not entries:
            return "No previous interactions in this session."

        query_tokens = self._tokenize(query)
        scored = [(self._similarity(query_tokens, e["tokens"]), e) for e in entries]
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:n_results]

        parts = [f"--- Previous Interaction {i+1} ---\n{e['document']}" for i, (_, e) in enumerate(top)]
        return "\n\n".join(parts) if parts else "No relevant previous context found."

    def get_session_history(self, session_id: str) -> list:
        """Get all interactions for a session. Returns list of dicts."""
        entries = self._fallback_sessions.get(session_id, [])
        return [{"document": e["document"], "query": e["query"], "timestamp": e["timestamp"]}
                for e in sorted(entries, key=lambda x: x["timestamp"])]

    def clear_session(self, session_id: str):
        """Clear all memory for a session. Returns None."""
        if session_id in self._fallback_sessions:
            del self._fallback_sessions[session_id]
        if session_id in self._chroma_collections:
            try:
                self._chroma_client.delete_collection(self._chroma_collections[session_id].name)
            except Exception:
                pass
            del self._chroma_collections[session_id]


# Singleton instance
memory = SessionMemory()
