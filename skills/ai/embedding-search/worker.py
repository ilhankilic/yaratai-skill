# filepath: skills/ai/embedding-search/worker.py
import logging, math, re, time
from collections import Counter
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Simple TF-based semantic search (no external deps)."""
    skill_id = "ai.embedding-search"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            docs: list = input.data.get("documents", [])
            query: str = input.data.get("query", "").strip()
            if not docs or not query:
                return SkillOutput(success=False, error="'documents' and 'query' required.")
            top_k: int = input.data.get("top_k", 5)
            threshold: float = input.data.get("similarity_threshold", 0.0)

            start = time.time()
            q_vec = self._vectorize(query)
            scored = []
            for doc in docs:
                d_vec = self._vectorize(doc.get("text", ""))
                score = self._cosine(q_vec, d_vec)
                if score >= threshold:
                    scored.append((score, doc))

            scored.sort(key=lambda x: x[0], reverse=True)
            results = [{"id": d.get("id", ""), "text": d.get("text", "")[:200],
                        "score": round(s, 4), "metadata": d.get("metadata", {}), "rank": i+1}
                       for i, (s, d) in enumerate(scored[:top_k])]

            elapsed = (time.time() - start) * 1000

            return SkillOutput(success=True, data={
                "results": results, "query_embedding_dim": len(q_vec),
                "documents_indexed": len(docs), "search_duration_ms": round(elapsed, 2),
            }, metadata={"skill_id": self.skill_id, "method": "tf_cosine"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _vectorize(self, text: str) -> dict[str, float]:
        words = re.findall(r"\w+", text.lower())
        counts = Counter(words)
        total = sum(counts.values()) or 1
        return {w: c / total for w, c in counts.items()}

    def _cosine(self, a: dict, b: dict) -> float:
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        na = math.sqrt(sum(v**2 for v in a.values())) or 1
        nb = math.sqrt(sum(v**2 for v in b.values())) or 1
        return dot / (na * nb)
