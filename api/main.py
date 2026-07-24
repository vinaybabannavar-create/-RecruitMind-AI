"""
api/main.py
FastAPI backend for RecruitMind AI.

Endpoints:
  POST /rank         - Full ranking pipeline
  POST /explain      - Add explanations to a shortlist
  GET  /candidates   - List all indexed candidates
  GET  /health       - Health check
  POST /index        - Re-index candidates
"""

import json
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()  # Load .env file so GROQ_API_KEY is available

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.ranker import run_ranking_pipeline
from pipeline.explainer import add_explanations
from pipeline.embedder import get_engine


# ── Lifespan: Auto-index candidates on startup if ChromaDB is empty ───────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("RecruitMind AI starting up...")
    try:
        engine = get_engine()
        # ── Auto-index if ChromaDB is empty ─────────────────────────────────
        count = engine.get_collection_count()
        if count == 0:
            print("ChromaDB empty — auto-indexing candidates...")
            engine.index_candidates("data/candidates.json")
            print(f"Auto-indexed {engine.get_collection_count()} candidates.")
        else:
            print(f"ChromaDB ready — {count} candidates already indexed.")
    except Exception as e:
        print(f"Warning: Startup init failed: {e}")
    yield

app = FastAPI(
    title="RecruitMind AI",
    description="Intelligent Candidate Discovery — AI-powered ranking system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────

class RankRequest(BaseModel):
    jd_text: str
    top_k: int = 10
    with_explanations: bool = True


class ExplainRequest(BaseModel):
    shortlist: List[Dict[str, Any]]
    parsed_jd: Dict[str, Any]


class IndexRequest(BaseModel):
    candidates_path: str = "data/candidates.json"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check."""
    engine = get_engine()
    try:
        count = engine.get_collection_count()
        indexed = True
    except Exception:
        count = 0
        indexed = False

    return {
        "status": "ok",
        "candidates_indexed": count,
        "vector_db_ready": indexed,
        "llm_available": bool(os.getenv("GROQ_API_KEY")),
        "version": "1.0.0"
    }


@app.post("/rank")
def rank_candidates(request: RankRequest):
    """
    Main endpoint. Takes a raw job description, returns ranked shortlist.
    """
    if not request.jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty")

    if len(request.jd_text) < 30:
        raise HTTPException(status_code=400, detail="jd_text too short. Provide a proper job description.")

    start = time.time()

    try:
        result = run_ranking_pipeline(raw_jd=request.jd_text, top_k=max(request.top_k * 2, 20))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

    shortlist = result.get("shortlist", [])
    parsed_jd = result.get("parsed_jd", {})

    if not shortlist:
        return {
            "shortlist": [],
            "parsed_jd": parsed_jd,
            "total_candidates_evaluated": 0,
            "processing_time_sec": round(time.time() - start, 2),
            "warning": result.get("error")
        }

    # Trim to requested top_k
    shortlist = shortlist[:request.top_k]

    # Add explanations if requested
    if request.with_explanations:
        try:
            shortlist = add_explanations(shortlist, parsed_jd)
        except Exception:
            pass  # Explanations are best-effort

    elapsed = round(time.time() - start, 2)

    return {
        "shortlist": shortlist,
        "parsed_jd": parsed_jd,
        "total_candidates_evaluated": len(result.get("scored_candidates") or []),
        "processing_time_sec": elapsed,
        "warning": result.get("error")
    }


@app.post("/explain")
def explain_shortlist(request: ExplainRequest):
    """Add LLM/rule-based explanations to an already-ranked shortlist."""
    try:
        enriched = add_explanations(request.shortlist, request.parsed_jd)
        return {"shortlist": enriched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates")
def list_candidates(limit: int = 20, offset: int = 0):
    """Return all candidates from the JSON file."""
    try:
        with open("data/candidates.json") as f:
            candidates = json.load(f)
        total = len(candidates)
        page = candidates[offset: offset + limit]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "candidates": page
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="candidates.json not found. Run data/generate_candidates.py first.")


@app.post("/index")
def index_candidates(request: IndexRequest, background_tasks: BackgroundTasks):
    """Re-index all candidates into ChromaDB (runs in background)."""
    def do_index():
        engine = get_engine()
        engine.index_candidates(request.candidates_path)

    background_tasks.add_task(do_index)
    return {"message": "Indexing started in background. Check /health for status."}


@app.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str):
    """Fetch a single candidate by ID."""
    try:
        with open("data/candidates.json") as f:
            candidates = json.load(f)
        for c in candidates:
            if c["id"] == candidate_id:
                return c
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="candidates.json not found")


class CompareRequest(BaseModel):
    candidate_ids: List[str]
    jd_text: str = ""

@app.post("/compare")
def compare_candidates(request: CompareRequest):
    """Compare 2-3 candidates side by side with full score breakdown."""
    if len(request.candidate_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 candidate IDs to compare.")
    if len(request.candidate_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 candidates can be compared at once.")
    try:
        with open("data/candidates.json") as f:
            all_candidates = json.load(f)
        candidate_map = {c["id"]: c for c in all_candidates}
        results = []
        for cid in request.candidate_ids:
            candidate = candidate_map.get(cid)
            if not candidate:
                raise HTTPException(status_code=404, detail=f"Candidate {cid} not found.")
            from pipeline.scorer import score_candidate
            from pipeline.jd_parser import parse_jd_offline
            parsed_jd = parse_jd_offline(request.jd_text) if request.jd_text else {
                "required_skills": [], "nice_to_have_skills": [],
                "min_experience_years": 0, "max_experience_years": None,
                "seniority_level": "mid", "role_type": "backend"
            }
            scored = score_candidate(candidate, parsed_jd, 0.75)
            results.append({
                "candidate_id": cid,
                "name": candidate.get("name"),
                "scores": scored.get("scores", {}),
                "metadata": scored.get("metadata", {}),
                "skills": candidate.get("skills", []),
                "certifications": candidate.get("certifications", []),
                "years_experience": candidate.get("years_experience", 0),
                "seniority": candidate.get("seniority", ""),
                "location": candidate.get("location", ""),
                "github": candidate.get("github", {}),
                "activity_signals": candidate.get("activity_signals", {}),
            })
        return {"comparison": results, "candidate_count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


BIAS_KEYWORDS = [
    "young", "fresh graduate only", "energetic young", "digital native",
    "recent graduate", "college student", "boys", "girls", "male preferred",
    "female preferred", "native english", "mother tongue english",
    "local candidates only", "unmarried", "married preferred"
]

class BiasRequest(BaseModel):
    jd_text: str

@app.post("/bias-check")
def check_jd_bias(request: BiasRequest):
    """Check a job description for potentially biased language."""
    if not request.jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")
    jd_lower = request.jd_text.lower()
    found_flags = []
    for keyword in BIAS_KEYWORDS:
        if keyword.lower() in jd_lower:
            found_flags.append({
                "term": keyword,
                "reason": f"The term '{keyword}' may indicate age, gender, or origin bias.",
                "suggestion": "Consider using neutral, skills-based language instead."
            })
    bias_score = min(100, len(found_flags) * 20)
    return {
        "bias_flags": found_flags,
        "bias_score": bias_score,
        "bias_level": "High" if bias_score >= 60 else ("Medium" if bias_score >= 20 else "Low"),
        "total_flags": len(found_flags),
        "recommendation": "Review and rewrite flagged sections using inclusive, skills-focused language." if found_flags else "No obvious bias detected. JD language appears neutral.",
        "jd_word_count": len(request.jd_text.split())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
