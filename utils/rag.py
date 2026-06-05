# utils/rag.py
"""
Enterprise RAG Engine — Feature #3
Retrieval-Augmented Generation using:
  - sentence-transformers (all-MiniLM-L6-v2) for embeddings
  - FAISS for fast vector similarity search
  - Ollama (local LLM) for answer generation
  - No external API keys required
"""

import json
import os
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers / faiss not installed — using keyword fallback")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class RAGResult:
    answer: str
    source: str
    page: str
    category: str
    relevance_score: float
    context_chunks: list[str]


class EnterpriseRAG:
    """
    RAG pipeline:
      1. Load HR policy documents from JSON
      2. Build FAISS index on first run (then cache)
      3. At query time: embed query → retrieve top-K chunks → generate answer
    """

    def __init__(
        self,
        policies_path: str = "./data/policies.json",
        index_path: str = "./data/faiss_index",
        model_name: str = "all-MiniLM-L6-v2",
        ollama_model: str = "llama3",
    ):
        self.policies_path = policies_path
        self.index_path = index_path
        self.ollama_model = ollama_model
        self.policies: list[dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index = None

        if ST_AVAILABLE:
            logger.info(f"Loading embedding model: {model_name}")
            self.embed_model = SentenceTransformer(model_name)
        else:
            self.embed_model = None

        self._load_policies()
        self._build_or_load_index()

    def _load_policies(self):
        with open(self.policies_path, "r") as f:
            self.policies = json.load(f)
        logger.info(f"Loaded {len(self.policies)} policy documents")

    def _build_or_load_index(self):
        if not ST_AVAILABLE:
            return

        index_file = Path(self.index_path + ".index")
        embeddings_file = Path(self.index_path + ".npy")

        if index_file.exists() and embeddings_file.exists():
            logger.info("Loading cached FAISS index")
            self.index = faiss.read_index(str(index_file))
            self.embeddings = np.load(str(embeddings_file))
            return

        logger.info("Building FAISS index from policy documents...")
        texts = [p["content"] for p in self.policies]
        self.embeddings = self.embed_model.encode(texts, show_progress_bar=True)
        self.embeddings = np.array(self.embeddings, dtype=np.float32)

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        faiss.write_index(self.index, str(index_file))
        np.save(str(embeddings_file), self.embeddings)
        logger.info(f"FAISS index built and saved ({len(texts)} vectors, dim={dim})")

    def retrieve(self, query: str, top_k: int = 3) -> list[tuple[dict, float]]:
        """Retrieve top-K relevant policy chunks for a query."""
        if not ST_AVAILABLE or self.index is None:
            return self._keyword_fallback(query)

        query_vec = self.embed_model.encode([query], show_progress_bar=False)
        query_vec = np.array(query_vec, dtype=np.float32)

        distances, indices = self.index.search(query_vec, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.policies):
                score = 1.0 / (1.0 + float(dist))  # Convert L2 distance to similarity
                results.append((self.policies[idx], score))
        return results

    def _keyword_fallback(self, query: str) -> list[tuple[dict, float]]:
        """Simple keyword matching when embeddings unavailable."""
        q = query.lower()
        scored = []
        for p in self.policies:
            score = 0
            for word in q.split():
                if word in p["content"].lower() or word in p["title"].lower():
                    score += 1
            if score > 0:
                scored.append((p, score / len(q.split())))
        return sorted(scored, key=lambda x: -x[1])[:3]

    def generate_answer(self, query: str, context_chunks: list[str]) -> str:
        """Generate answer using Ollama local LLM."""
        if not OLLAMA_AVAILABLE:
            return self._rule_based_answer(query, context_chunks)

        context = "\n\n".join(context_chunks)
        prompt = f"""You are an Enterprise HR AI assistant. Answer the employee's question using ONLY the provided HR policy context.
Be concise, accurate, and mention the policy source.

HR Policy Context:
{context}

Employee Question: {query}

Answer:"""

        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Ollama unavailable: {e} — using rule-based answer")
            return self._rule_based_answer(query, context_chunks)

    def _rule_based_answer(self, query: str, context_chunks: list[str]) -> str:
        """Fallback: return the most relevant chunk directly."""
        if context_chunks:
            return f"Based on HR Policy:\n\n{context_chunks[0]}"
        return "I could not find a relevant policy for your query. Please contact HR."

    def query(self, question: str, employee_grade: str = "L3", location: str = "Chennai") -> RAGResult:
        """
        Full RAG pipeline: retrieve → contextualize → generate.
        Feature #6: Context-aware — includes employee grade + location.
        """
        enriched_query = f"{question} for {location} branch {employee_grade} grade employee"
        results = self.retrieve(enriched_query, top_k=3)

        if not results:
            return RAGResult(
                answer="No relevant HR policy found. Please contact your HR Business Partner.",
                source="N/A", page="N/A", category="unknown",
                relevance_score=0.0, context_chunks=[],
            )

        top_policy, top_score = results[0]
        context_chunks = [r[0]["content"] for r in results]

        answer = self.generate_answer(question, context_chunks)

        return RAGResult(
            answer=answer,
            source=top_policy["source"],
            page=str(top_policy.get("page", "N/A")),
            category=top_policy["category"],
            relevance_score=round(top_score * 100, 1),
            context_chunks=context_chunks,
        )


# Singleton
rag_engine = EnterpriseRAG()
