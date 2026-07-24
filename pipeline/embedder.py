"""
pipeline/embedder.py
Embeds candidate profiles and JD into vectors using sentence-transformers.
Stores and retrieves from ChromaDB.
"""

import os
import json
from typing import List, Dict, Any

# Lazy imports to avoid errors if not installed yet
def _get_sentence_transformer():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")

def _get_chroma():
    import chromadb
    return chromadb

CHROMA_PATH = "data/chroma_db"


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
        api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        headers = {}
        # Render has internet access and can query the public API. Optional HF_TOKEN can be used
        token = os.getenv("HF_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            print(f"Requesting embeddings from Hugging Face Serverless API (batch size: {len(texts)})...")
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": texts, "options": {"wait_for_model": True}},
                timeout=25
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    # Check if result is 3D: [batch, seq_len, dim] -> perform mean pooling
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
            print(f"HF Inference API returned non-200: {response.status_code}. Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error calling HF Inference API: {e}")
        return []

    def _load_model(self):
        # We don't pre-load model at startup to save memory.
        pass

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
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        embeddings = self._query_hf_api(texts)
        if embeddings and len(embeddings) == len(texts):
            return embeddings
            
        print("Falling back to local SentenceTransformer model...")
        if self.model is None:
            self.model = _get_sentence_transformer()
        return self.model.encode(texts).tolist()

    def index_candidates(self, candidates_path: str = "data/candidates.json"):
        """Load candidates from JSON and store in ChromaDB."""
        self._load_model()
        self._load_chroma()

        with open(candidates_path) as f:
            candidates = json.load(f)

        print(f"Indexing {len(candidates)} candidates...")

        # Process in batches
        batch_size = 20
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            texts = [build_candidate_text(c) for c in batch]
            embeddings = self.embed_texts(texts)
            ids = [c["id"] for c in batch]
            metadatas = [
                {
                    "name": c["name"],
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
        self._load_model()
        self._load_chroma()

        jd_embedding = self.embed_text(jd_text)

        results = self.collection.query(
            query_embeddings=[jd_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        candidates_out = []
        for i in range(len(results["ids"][0])):
            candidates_out.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "semantic_distance": results["distances"][0][i],
                "semantic_score": round(1 - results["distances"][0][i], 4)
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

    test_jd_text = "Senior Python ML Engineer with LangChain, FastAPI, Docker experience. 4+ years."
    results = engine.search_candidates(test_jd_text, top_k=5)
    for r in results:
        print(f"  {r['id']} | {r['metadata']['name']} | semantic_score={r['semantic_score']}")
