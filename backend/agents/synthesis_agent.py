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

class SynthesisAgent:
    def _synthesize_results(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Synthesizes and formats final results.
        """
        try:
            print(f"📋 SYNTHESIS AGENT: Finalizing results...")

            # Format final analysis
            final_analysis = {
                "columns": state["generated_columns"],
                "data": state["preliminary_findings"],
                "metadata": {
                    "query_intent": state["query_intent"],
                    "documents_analyzed": len(state["preliminary_findings"]),
                    "confidence_scores": state["confidence_scores"],
                    "retrieval_confidence": state.get("retrieval_confidence", 0.0),
                    "legal_terms_found": state["legal_terms"],
                    "evidence_chains": len(state.get("evidence_chains", []))
                }
            }

            # Store results in database
            self._store_results_in_db(state, final_analysis)

            print(f"✅ Synthesis complete!")
            print(f"📊 Final stats: {len(final_analysis['data'])} documents, {len(final_analysis['columns'])} columns")

            return {
                **state,
                "final_analysis": final_analysis,
                "processing_step": "synthesis_complete"
            }

        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return {
                **state,
                "final_analysis": {"error": str(e)},
                "error_message": f"Synthesis failed: {str(e)}",
                "processing_step": "synthesis_error"
            }

    def _store_results_in_db(self, state: ContractAnalysisState, final_analysis: Dict):
        """
        Store analysis results in Supabase
        """
        try:
            matrix_id = state["matrix_id"]

            # Update matrix with final columns
            supabase.table("matrices").update({
                "columns": final_analysis["columns"]
            }).eq("id", matrix_id).execute()

            # Store individual document results
            doc_name_mapping = state.get("doc_name_to_chunk_id", {})
            for doc_name, doc_data in final_analysis["data"].items():
                if isinstance(doc_data, dict) and "error" not in doc_name.lower():
                    # Get the correct chunk ID from the mapping
                    chunk_id = doc_name_mapping.get(doc_name)

                    if chunk_id:
                        supabase.table("matrix_data").insert({
                            "matrix_id": matrix_id,
                            "document_chunk_id": chunk_id,
                            "row_data": doc_data
                        }).execute()
                    else:
                        print(f"Warning: No chunk ID found for document: {doc_name}")

            print(f"💾 Results stored in database for matrix {matrix_id}")

        except Exception as e:
            print(f"Warning: Database storage failed: {e}")
