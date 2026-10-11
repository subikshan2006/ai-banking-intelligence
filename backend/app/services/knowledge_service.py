import json
import logging
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from app.models.policy import PolicyDocument

logger = logging.getLogger(__name__)

class KnowledgeService:
    """Local RAG retrieval service over versioned synthetic banking policies."""

    def search_policies(self, db: Session, query: str, top_k: int = 3) -> dict[str, Any]:
        docs = db.query(PolicyDocument).all()
        if not docs:
            return {
                "query": query,
                "matches": [],
                "answer_supported": False,
                "summary": "No policy documents currently indexed."
            }

        # Build corpus of passages
        passages_metadata = []
        corpus = []

        for doc in docs:
            p_list = []
            try:
                p_list = json.loads(doc.passages)
            except Exception:
                p_list = [{"id": f"{doc.id}-P1", "text": doc.content}]

            for p in p_list:
                corpus.append(p["text"])
                passages_metadata.append({
                    "passage_id": p.get("id", f"{doc.id}-P"),
                    "document_id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "version": doc.version,
                    "text": p["text"]
                })

        if not corpus:
            return {
                "query": query,
                "matches": [],
                "answer_supported": False,
                "summary": "No readable policy passages indexed."
            }

        # TF-IDF Vectorization and Cosine Similarity
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vec = vectorizer.transform([query])
        
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
        top_indices = scores.argsort()[::-1][:top_k]

        matches = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.08:  # relevance threshold
                meta = passages_metadata[idx]
                matches.append({
                    "document_id": meta["document_id"],
                    "passage_id": meta["passage_id"],
                    "title": meta["title"],
                    "category": meta["category"],
                    "version": meta["version"],
                    "relevance_score": round(score, 3),
                    "supporting_passage": meta["text"]
                })

        if not matches:
            return {
                "query": query,
                "matches": [],
                "answer_supported": False,
                "summary": "The available sample policy documents do not contain enough information to address this query."
            }

        return {
            "query": query,
            "matches": matches,
            "answer_supported": True,
            "primary_source": f"{matches[0]['document_id']} ({matches[0]['title']} {matches[0]['version']})",
            "summary": f"Retrieved {len(matches)} relevant policy passage(s) grounded in bank compliance documentation."
        }

knowledge_service = KnowledgeService()
