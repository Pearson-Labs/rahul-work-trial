import os
import json
from typing import List, Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from ..data_storage.database import supabase
from ..data_storage.pinecone_store import get_pinecone_store
from .state import ContractAnalysisState

load_dotenv()

class RetrievalAgent:
    def __init__(self):
        self.pinecone_store = get_pinecone_store()

    def _rerank_results(self, results: List[Dict], state: ContractAnalysisState) -> List[Dict]:
        """Re-rank results based on multiple signals"""
        try:
            # Simple re-ranking based on legal term matching and score
            legal_terms_lower = [term.lower() for term in state["legal_terms"]]

            def score_result(result):
                base_score = result.get("score", 0.5)
                text = result.get("chunk_text", "").lower()

                # Bonus for legal term matches
                term_matches = sum(1 for term in legal_terms_lower if term in text)
                term_bonus = term_matches * 0.1

                # Penalty for very short chunks (likely boilerplate)
                length_penalty = 0.05 if len(result.get("chunk_text", "")) < 300 else 0

                return base_score + term_bonus - length_penalty

            results.sort(key=score_result, reverse=True)
            return results

        except Exception as e:
            print(f"Warning: Re-ranking failed: {e}")
            return results

    def _calculate_retrieval_confidence(self, results: List[Dict], state: ContractAnalysisState) -> float:
        """Calculate confidence in retrieval results"""
        try:
            if not results:
                return 0.0

            # Base confidence from average scores
            scores = [r.get("score", 0.5) for r in results[:5]]  # Top 5
            avg_score = sum(scores) / len(scores) if scores else 0.5

            # Boost for legal term coverage
            legal_term_coverage = 0.0
            if state["legal_terms"]:
                found_terms = set()
                for result in results[:10]:
                    text = result.get("chunk_text", "").lower()
                    for term in state["legal_terms"]:
                        if term.lower() in text:
                            found_terms.add(term)
                legal_term_coverage = len(found_terms) / len(state["legal_terms"])

            # Combined confidence
            confidence = (avg_score * 0.7) + (legal_term_coverage * 0.3)
            return min(confidence, 1.0)

        except Exception as e:
            print(f"Warning: Confidence calculation failed: {e}")
            return 0.5

    def intelligent_retrieval(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Performs hybrid retrieval using semantic search, keyword search, and legal term matching.
        """
        try:
            print(f"🔎 RETRIEVAL AGENT: Starting hybrid search...")

            # Semantic search with original query
            semantic_results = self.pinecone_store.search_similar_chunks(
                query=state["original_query"],
                top_k=15,  # Get more results for better coverage
                score_threshold=0.4  # Lower threshold to capture more potential matches
            )

            # Keyword search with legal terms
            keyword_results = []
            if state["legal_terms"]:
                legal_query = " OR ".join(state["legal_terms"])
                keyword_results = self.pinecone_store.search_similar_chunks(
                    query=legal_query,
                    top_k=10,
                    score_threshold=0.3
                )

            # Search with expanded queries
            expanded_results = []
            for expanded_query in state["expanded_queries"][:3]:  # Limit to first 3
                results = self.pinecone_store.search_similar_chunks(
                    query=expanded_query,
                    top_k=8,
                    score_threshold=0.35
                )
                expanded_results.extend(results)

            # Combine and deduplicate results
            all_results = semantic_results + keyword_results + expanded_results
            seen_ids = set()
            hybrid_results = []

            for result in all_results:
                if result["id"] not in seen_ids:
                    seen_ids.add(result["id"])
                    hybrid_results.append(result)

            # Re-rank results by combining different signals
            hybrid_results = self._rerank_results(hybrid_results, state)

            # Calculate retrieval confidence
            retrieval_confidence = self._calculate_retrieval_confidence(hybrid_results, state)

            print(f"📊 Semantic results: {len(semantic_results)}")
            print(f"🔑 Keyword results: {len(keyword_results)}")
            print(f"📝 Expanded results: {len(expanded_results)}")
            print(f"🎯 Final hybrid results: {len(hybrid_results)}")
            print(f"📈 Retrieval confidence: {retrieval_confidence:.2f}")

            return {
                **state,
                "semantic_results": semantic_results,
                "keyword_results": keyword_results,
                "hybrid_results": hybrid_results[:20],  # Limit to top 20
                "retrieval_confidence": retrieval_confidence,
                "processing_step": "retrieval_complete"
            }

        except Exception as e:
            print(f"❌ Retrieval error: {e}")
            return {
                **state,
                "semantic_results": [],
                "keyword_results": [],
                "hybrid_results": [],
                "retrieval_confidence": 0.0,
                "error_message": f"Retrieval failed: {str(e)}",
                "processing_step": "retrieval_error"
            }