"""
pipeline/embedder.py
Embeds candidate profiles and JD into vectors using serverless APIs with deterministic fallbacks.
Stores and retrieves from ChromaDB.
"""

import os
import json
import hashlib
import requests
from typing import List, Dict, Any

# Lazy imports to avoid errors if not installed yet
def _get_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None

def _get_chroma():
    import chromadb
    return chromadb

CHROMA_PATH = "data/chroma_db"


def _fallback_vector(text: str, dim: int = 384) -> List[float]:
    """Fast deterministic feature vector based on word hashes (used if remote API & local model fail)."""
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec
    for w in words:
        h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    norm = sum(x*x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def build_candidate_text(candidate: Dict[str, Any]) -> str:
    """Convert a candidate profile dict into a rich text string for embedding."""
    parts = []
    parts.append(f"Name: {candidate.get('name', '')}")
    parts.append(f"Summary: {candidate.get('summary', '')}")
    parts.append(f"Experience: {candidate.get('years_experience', 0)} years")
    parts.append(f"Seniority: {candidate.get('seniority', '')}")
    parts.append(f"Role type: {candidate.get('role_type', '')}")

    skills = candidate.get("skills", [])
    if skills:
        parts.append(f"Skills: {', '.join(skills)}")

    edu = candidate.get("education", {})
    if edu:
        parts.append(f"Education: {edu.get('degree', '')} from {edu.get('college', '')}, CGPA {edu.get('cgpa', '')}")

    exp = candidate.get("experience", [])
    for job in exp[:3]:
        parts.append(f"Worked at {job.get('company', '')} as {job.get('role', '')} for {job.get('duration_years', 0)} years")

    certs = candidate.get("certifications", [])
    if certs:
        parts.append(f"Certifications: {', '.join(certs)}")

    github = candidate.get("github", {})
    if github:
        parts.append(f"GitHub: {github.get('repos', 0)} repos, {github.get('contributions_last_year', 0)} contributions/year, {github.get('open_source_prs', 0)} open source PRs")

    activity = candidate.get("activity_signals", {})
    if activity:
        parts.append(f"LeetCode: {activity.get('leetcode_solved', 0)} problems solved")
        parts.append(f"Hackathons: {activity.get('hackathon_participations', 0)} participated")

    return ". ".join(parts)


def build_jd_text(parsed_jd: Dict[str, Any]) -> str:
    """Convert parsed JD dict into text for embedding."""
    parts = []
    parts.append(f"Job title: {parsed_jd.get('job_title', '')}")
    parts.append(f"Seniority: {parsed_jd.get('seniority_level', '')}")
    parts.append(f"Role type: {parsed_jd.get('role_type', '')}")

    req_skills = parsed_jd.get("required_skills", [])
    if req_skills:
        parts.append(f"Required skills: {', '.join(req_skills)}")

    nice_skills = parsed_jd.get("nice_to_have_skills", [])
    if nice_skills:
        parts.append(f"Nice to have: {', '.join(nice_skills)}")

    responsibilities = parsed_jd.get("key_responsibilities", [])
    if responsibilities:
        parts.append(f"Responsibilities: {', '.join(responsibilities)}")

    implicit = parsed_jd.get("implicit_expectations", [])
    if implicit:
        parts.append(f"Expectations: {', '.join(implicit)}")

    parts.append(f"Experience required: {parsed_jd.get('min_experience_years', 0)} years")
    parts.append(f"Summary: {parsed_jd.get('summary', '')}")

    return ". ".join(parts)


class EmbeddingEngine:
    def __init__(self):
        self.model = None
        self.chroma_client = None
        self.collection = None

    def _query_hf_api(self, texts: List[str]) -> List[List[float]]:
        """Queries the Hugging Face Serverless Inference API for embeddings."""
        urls = [
            "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction",
            "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        ]
        headers = {}
        token = os.getenv("HF_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        for api_url in urls:
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json={"inputs": texts, "options": {"wait_for_model": True}},
                    timeout=10
                )
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        # If returned as 3D tensor [batch, seq_len, dim], mean-pool
                        if isinstance(result[0], list) and len(result[0]) > 0 and isinstance(result[0][0], list):
                            pooled_results = []
                            for doc_tokens in result:
                                num_tokens = len(doc_tokens)
                                dim = len(doc_tokens[0])
                                mean_vector = [0.0] * dim
                                for token_vector in doc_tokens:
                                    for idx, val in enumerate(token_vector):
                                        mean_vector[idx] += val
                                mean_vector = [val / num_tokens for val in mean_vector]
                            pooled_results.append(mean_vector)
                            return pooled_results
                        return result
            except Exception as e:
                print(f"HF API endpoint {api_url} failed: {e}")
        return []

    def _load_chroma(self):
        if self.chroma_client is None:
            chromadb = _get_chroma()
            os.makedirs(CHROMA_PATH, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
            self.collection = self.chroma_client.get_or_create_collection(
                name="candidates",
                metadata={"hnsw:space": "cosine"}
            )

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        res = self.embed_texts([text])
        if res and len(res) > 0:
            return res[0]
        return _fallback_vector(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts with multi-tier fallback."""
        if not texts:
            return []

        # 1. Try Serverless HF API
        embeddings = self._query_hf_api(texts)
        if embeddings and len(embeddings) == len(texts):
            return embeddings

        # 2. Try Local Model if installed
        try:
            if self.model is None:
                self.model = _get_sentence_transformer()
            if self.model is not None:
                return self.model.encode(texts).tolist()
        except Exception as e:
            print(f"Local SentenceTransformer embedding failed: {e}")

        # 3. Deterministic hash fallback (Guaranteed to work 100%)
        print("Using deterministic word-hash vector fallback for embeddings.")
        return [_fallback_vector(t) for t in texts]

    def index_candidates(self, candidates_path: str = "data/candidates.json"):
        """Load candidates from JSON and store in ChromaDB."""
        self._load_chroma()

        if not os.path.exists(candidates_path):
            print(f"Warning: {candidates_path} not found.")
            return

        with open(candidates_path) as f:
            candidates = json.load(f)

        print(f"Indexing {len(candidates)} candidates...")

        batch_size = 20
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            texts = [build_candidate_text(c) for c in batch]
            embeddings = self.embed_texts(texts)
            ids = [c["id"] for c in batch]
            metadatas = [
                {
                    "name": c.get("name", ""),
                    "skills": ",".join(c.get("skills", [])),
                    "years_experience": c.get("years_experience", 0),
                    "seniority": c.get("seniority", ""),
                    "role_type": c.get("role_type", ""),
                    "location": c.get("location", ""),
                    "github_score": c.get("github", {}).get("github_score", 0.0),
                    "career_growth_score": c.get("career_signals", {}).get("career_growth_score", 0.0),
                    "activity_score": c.get("activity_signals", {}).get("linkedin_activity_score", 0.0),
                    "expected_salary_lpa": c.get("expected_salary_lpa", 0.0),
                }
                for c in batch
            ]
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            print(f"  Indexed {min(i + batch_size, len(candidates))}/{len(candidates)}")

        print("Indexing complete.")

    def search_candidates(self, jd_text: str, top_k: int = 20) -> List[Dict]:
        """Semantic search: find top-k candidates matching the JD."""
        self._load_chroma()

        jd_embedding = self.embed_text(jd_text)

        results = self.collection.query(
            query_embeddings=[jd_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        candidates_out = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                dist = results["distances"][0][i] if results.get("distances") else 0.5
                candidates_out.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "semantic_distance": dist,
                    "semantic_score": round(max(0.0, 1.0 - dist), 4)
                })

        return candidates_out

    def get_collection_count(self) -> int:
        self._load_chroma()
        return self.collection.count()


# Singleton
_engine = None

def get_engine() -> EmbeddingEngine:
    global _engine
    if _engine is None:
        _engine = EmbeddingEngine()
    return _engine


if __name__ == "__main__":
    engine = get_engine()
    engine.index_candidates()
    print(f"Total indexed: {engine.get_collection_count()}")
