"""
pipeline/ranker.py
LangGraph-based ranking pipeline orchestrator.
Nodes: parse_jd → embed_jd → retrieve_candidates → score → rerank → output
"""

import json
import os
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from pipeline.jd_parser import parse_jd, parse_jd_offline
from pipeline.embedder import get_engine, build_jd_text
from pipeline.scorer import score_all_candidates


# ── State definition ──────────────────────────────────────────────────────────

class RankingState(TypedDict):
    raw_jd: str
    parsed_jd: Optional[Dict[str, Any]]
    jd_text: Optional[str]
    semantic_results: Optional[List[Dict]]
    all_candidates: Optional[List[Dict]]
    scored_candidates: Optional[List[Dict]]
    shortlist: Optional[List[Dict]]
    top_k: int
    error: Optional[str]


# ── Node functions ─────────────────────────────────────────────────────────────

def node_parse_jd(state: RankingState) -> RankingState:
    """Node 1: Parse raw JD into structured dict."""
    try:
        use_llm = bool(os.getenv("GROQ_API_KEY"))
        if use_llm:
            parsed = parse_jd(state["raw_jd"])
        else:
            parsed = parse_jd_offline(state["raw_jd"])
        return {**state, "parsed_jd": parsed, "error": None}
    except Exception as e:
        # Fallback to offline
        parsed = parse_jd_offline(state["raw_jd"])
        return {**state, "parsed_jd": parsed, "error": f"LLM parse failed, used offline: {e}"}


def node_embed_jd(state: RankingState) -> RankingState:
    """Node 2: Build JD text representation for embedding."""
    try:
        jd_text = build_jd_text(state["parsed_jd"])
        return {**state, "jd_text": jd_text}
    except Exception as e:
        return {**state, "error": f"JD embedding text build failed: {e}"}


def node_retrieve_candidates(state: RankingState) -> RankingState:
    """Node 3: Semantic search in ChromaDB for top candidates."""
    all_candidates = []
    try:
        if os.path.exists("data/candidates.json"):
            with open("data/candidates.json") as f:
                all_candidates = json.load(f)
    except Exception:
        all_candidates = []

    try:
        engine = get_engine()
        count = engine.get_collection_count()
        if count == 0 and os.path.exists("data/candidates.json"):
            print("No candidates indexed. Indexing now...")
            engine.index_candidates("data/candidates.json")

        results = engine.search_candidates(state.get("jd_text", ""), top_k=state.get("top_k", 20))
        return {**state, "semantic_results": results, "all_candidates": all_candidates}
    except Exception as e:
        print(f"Retrieval warning: {e}")
        return {**state, "semantic_results": [], "all_candidates": all_candidates}


def node_score_candidates(state: RankingState) -> RankingState:
    """Node 4: Multi-signal scoring of retrieved candidates."""
    try:
        candidates = state.get("all_candidates") or []
        if not candidates and os.path.exists("data/candidates.json"):
            with open("data/candidates.json") as f:
                candidates = json.load(f)

        parsed_jd = state.get("parsed_jd") or {}
        semantic_results = state.get("semantic_results") or []

        scored = score_all_candidates(
            candidates,
            parsed_jd,
            semantic_results
        )
        return {**state, "scored_candidates": scored}
    except Exception as e:
        return {**state, "error": f"Scoring failed: {e}"}


def node_rerank(state: RankingState) -> RankingState:
    """
    Node 5: Re-rank with diversity boost.
    Ensures the shortlist isn't all same seniority/role_type.
    Applies a small diversity multiplier to second-occurrence duplicates.
    """
    try:
        scored = state["scored_candidates"]
        if not scored:
            return {**state, "shortlist": []}

        seen_seniority = {}
        seen_role_type = {}
        reranked = []

        for candidate in scored:
            meta = candidate.get("metadata", {})
            sen = meta.get("seniority", "mid")
            rt = meta.get("role_type", "other")

            # Diversity penalty for over-represented types
            sen_count = seen_seniority.get(sen, 0)
            rt_count = seen_role_type.get(rt, 0)

            diversity_mult = 1.0
            if sen_count >= 3:
                diversity_mult *= 0.95
            if rt_count >= 4:
                diversity_mult *= 0.95

            adjusted_score = round(candidate["scores"]["composite"] * diversity_mult, 4)
            candidate["scores"]["composite_reranked"] = adjusted_score

            seen_seniority[sen] = sen_count + 1
            seen_role_type[rt] = rt_count + 1
            reranked.append(candidate)

        # Sort by reranked score
        reranked.sort(key=lambda x: x["scores"]["composite_reranked"], reverse=True)

        # Add rank numbers
        for i, c in enumerate(reranked):
            c["rank"] = i + 1

        shortlist = reranked[:10]
        return {**state, "shortlist": shortlist}
    except Exception as e:
        return {**state, "error": f"Rerank failed: {e}"}


def node_output(state: RankingState) -> RankingState:
    """Node 6: Final output — trim and annotate shortlist."""
    shortlist = state.get("shortlist", [])
    final = []
    for c in shortlist:
        final.append({
            "rank": c.get("rank"),
            "candidate_id": c.get("candidate_id"),
            "name": c.get("name"),
            "composite_score": c["scores"].get("composite_reranked", c["scores"]["composite"]),
            "score_breakdown": {
                "semantic_similarity": c["scores"]["semantic"],
                "skill_match": c["scores"]["skill_match"],
                "career_growth": c["scores"]["career_growth"],
                "activity": c["scores"]["activity"],
                "experience_fit": c["scores"]["experience_fit"],
            },
            "metadata": c.get("metadata", {}),
        })
    return {**state, "shortlist": final}


# ── Build LangGraph ───────────────────────────────────────────────────────────

def build_ranking_graph():
    workflow = StateGraph(RankingState)

    workflow.add_node("parse_jd", node_parse_jd)
    workflow.add_node("embed_jd", node_embed_jd)
    workflow.add_node("retrieve_candidates", node_retrieve_candidates)
    workflow.add_node("score_candidates", node_score_candidates)
    workflow.add_node("rerank", node_rerank)
    workflow.add_node("output", node_output)

    workflow.set_entry_point("parse_jd")
    workflow.add_edge("parse_jd", "embed_jd")
    workflow.add_edge("embed_jd", "retrieve_candidates")
    workflow.add_edge("retrieve_candidates", "score_candidates")
    workflow.add_edge("score_candidates", "rerank")
    workflow.add_edge("rerank", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


def run_ranking_pipeline(raw_jd: str, top_k: int = 20) -> Dict[str, Any]:
    """
    Main entry point. Pass raw JD text, get back ranked shortlist.
    Returns full state including shortlist and parsed_jd.
    """
    graph = build_ranking_graph()
    initial_state: RankingState = {
        "raw_jd": raw_jd,
        "parsed_jd": None,
        "jd_text": None,
        "semantic_results": None,
        "all_candidates": None,
        "scored_candidates": None,
        "shortlist": None,
        "top_k": top_k,
        "error": None,
    }
    result = graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    sample_jd = """
    We are hiring a Senior Python & ML Engineer in Bengaluru.
    Requirements:
    - 4+ years experience with Python
    - Strong background in Machine Learning and LangChain
    - Experience building REST APIs with FastAPI
    - Docker and Kubernetes knowledge
    - Good understanding of RAG pipelines and vector databases
    Nice to have: AWS experience, open source contributions, PostgreSQL
    """

    print("Running ranking pipeline...")
    result = run_ranking_pipeline(sample_jd)

    print("\n=== PARSED JD ===")
    print(json.dumps(result["parsed_jd"], indent=2))

    print("\n=== TOP 5 SHORTLIST ===")
    for c in (result["shortlist"] or [])[:5]:
        print(f"#{c['rank']} {c['name']} | score={c['composite_score']} | skills={c['metadata']['skills'][:4]}")

    if result.get("error"):
        print(f"\nWarning: {result['error']}")
